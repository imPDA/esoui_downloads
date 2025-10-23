from datetime import datetime, timedelta
import logging
from pathlib import Path

import shutil
import subprocess
import tempfile

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from fake_useragent import UserAgent
import requests

from prefect import flow, serve, task, get_run_logger
from prefect.runtime import flow_run
from prefect.schedules import Interval

import pandas as pd

from pydantic import ValidationError

from core.database import create_tables, get_db
from core.schemas import AddonSchema, DownloadsSchema, UpdateSchema
from models import Addon


API_URL = 'https://api.mmoui.com/v4/game/ESO/filelist.json'


FAKE_HEADERS = {
    'User-Agent': UserAgent(platforms='desktop').chrome,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    # 'Accept-Encoding': 'gzip, deflate, br, zstd',
}


@task
def initialize_database():
    create_tables()


@task
def get_addons_list():
    response = requests.get(API_URL, headers=FAKE_HEADERS)
    response.raise_for_status()

    return response.json()


@task
def save_to_file(data):
    flow_id = flow_run.id
    timestamp = flow_run.scheduled_start_time.strftime('%Y%m%d_%H%M%S')
    
    # json_path = f'{OUTPUT_PATH}/output_{flow_id}_{timestamp}.json'
    # with open(json_path, 'w') as f:
    #     json.dump(data, f)
    
    # csv_path = f'/data/output_{flow_id}_{timestamp}.csv'
    # pd.DataFrame(data).to_csv(csv_path)

    df = pd.DataFrame(data)

    del df['donationUrl']

    output_path = Path(__file__).parent.parent / 'output'

    parquet_path = output_path / f'snapshot_{timestamp}_{flow_id}.parquet'
    df.to_parquet(parquet_path, index=False)

    return parquet_path


@task
def compress_with_xz(input_path: Path):
    try:
        subprocess.run(
            ['xz', '-9e', str(input_path)],
            check=True,
            capture_output=True,
            text=True
        )       
    except subprocess.CalledProcessError as e:
        print(f'❌ Compression failed (code {e.returncode}):')
        print(e.stderr)
        raise
    except FileNotFoundError:
        print('❌ xz/tar not installed!')
        raise

    return Path(f'{input_path}.xz')


@task
def decompress_with_xz(compressed_path: Path, output_dir: Path) -> Path:
    temp_compressed_path = output_dir / compressed_path.name
    shutil.copy2(compressed_path, temp_compressed_path)

    subprocess.run(
        ['xz', '-d', str(temp_compressed_path)],
        check=True,
        capture_output=True,
        text=True
    )

    output_path = output_dir / compressed_path.stem
    if not output_path.exists():
        raise Exception('Decompressed file was not created!')

    return output_path


@task
def extract_downloads(addons: list[Addon]):
    timestamp = flow_run.scheduled_start_time

    insert_data = []
    for addon in addons:
        insert_data.append({'esoui_id': addon.id, 'downloads': addon.downloads, 'timestamp': timestamp})

    insert_downloads = insert(DownloadsSchema).values(insert_data)

    if len(insert_data) < 1:
        return

    with get_db() as session:
        session.execute(insert_downloads)
        session.commit()


@task
def validate(addons: list[dict]) -> list[Addon]:
    logger = get_run_logger()
    validated = []

    for addon in addons:
        try:
            addon = Addon(**addon)
            validated.append(addon)
        except ValidationError as ve:
            logger.warning(ve)

    return validated


@task
def update_addons_info(addons: list[Addon]):
    get_addon = lambda esoui_id: (
        select(AddonSchema)
        .where(AddonSchema.esoui_id == esoui_id)
    )

    with get_db() as session:
        for addon in addons:
            db_addon = session.scalars(get_addon(addon.id)).one_or_none()

            if db_addon:
                db_addon.title = addon.title
                db_addon.author = addon.author
                db_addon.category = addon.categoryId
                db_addon.url = addon.fileInfoUri
            else:
                get_run_logger().info(f'New addon added: {addon.title} ({addon.id}, by {addon.author})')
                db_addon = AddonSchema(
                    esoui_id=addon.id,
                    title=addon.title,
                    author=addon.author,
                    category=addon.categoryId,
                    url=addon.fileInfoUri,
                )
                session.add(db_addon)
        
        session.commit()


@task
def extract_latest_update(addons: list[Addon]):
    insert_data = []
    for addon in addons:
        insert_data.append({'esoui_id': addon.id, 'timestamp': addon.lastUpdate, 'version': addon.version, 'checksum': addon.checksum})

    insert_updates = (
        insert(UpdateSchema)
        .values(insert_data)
        .on_conflict_do_nothing()
        .returning(UpdateSchema.esoui_id)
    )

    if len(insert_data) < 1:
        return

    with get_db() as session:
        result = session.execute(insert_updates)
        rows_inserted = len(result.fetchall())
        session.commit()

        return rows_inserted


@task
def find_parquet_xz_files():
    output_path = Path(__file__).parent.parent / 'output'
    PATTERN = '*.parquet.xz'

    if not output_path.exists():
        raise FileNotFoundError(f'Folder not found: {output_path}')
    
    files = list(output_path.glob(PATTERN))
    files.sort()
    
    get_run_logger().info(f'Found {len(files)} .parquet.xz files')

    return files


@task
def load_parquet(parquet_path: Path) -> list[dict]:
    df = pd.read_parquet(parquet_path)
    records = df.to_dict(orient='records')

    return records


@task
def process_single_file(compressed_path: Path, temp_dir: Path) -> dict:
    get_run_logger().info(f'Processing {compressed_path}')

    try:
        parquet_path = decompress_with_xz(compressed_path, temp_dir)
        addon_records = load_parquet(parquet_path)
        
        if not addon_records:
            return
        
        addons = validate(addon_records)
        rows_inserted = extract_latest_update(addons)

        return rows_inserted
    except Exception:
        get_run_logger().exception(f'Failed to process {compressed_path}')


@flow
def extract_data_from_archive():
    files = find_parquet_xz_files()

    if not files:
        return

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        for file_path in files:
            get_run_logger().setLevel(logging.WARNING)
            rows_inserted = process_single_file(file_path, temp_path)
            get_run_logger().setLevel(logging.INFO)
            get_run_logger().info(f'{rows_inserted} addons updated (from {file_path.name})')


@flow
def take_esoui_snapshot():
    initialize_database()

    results = get_addons_list()

    output_file = save_to_file(results)
    compress_with_xz(output_file)

    validated_data = validate(results)
    update_addons_info(validated_data)
    extract_downloads(validated_data)
    extract_latest_update(validated_data)


if __name__ == '__main__':
    take_snapshot_deployment = take_esoui_snapshot.to_deployment(
        name='take-esoui-snapshot-deployment', 
        schedule=Interval(
            timedelta(minutes=30),
            anchor_date=datetime(2025, 1, 1, 0, 0),
            timezone='Europe/Moscow'
        )
    )
    
    extract_data_from_archive_deployment = extract_data_from_archive.to_deployment(
        name='extract_data_from_archive-deploymant',
    )

    serve(
        take_snapshot_deployment,
        extract_data_from_archive_deployment,
    )
