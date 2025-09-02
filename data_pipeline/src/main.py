from datetime import datetime, timedelta
from pathlib import Path

import subprocess
from typing import Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from fake_useragent import UserAgent
import requests

from prefect import flow, serve, task, get_run_logger
from prefect.runtime import flow_run
from prefect.schedules import Interval

import pandas as pd

from pydantic import BaseModel, ConfigDict, Json, ValidationError, field_validator

from common.infra.database.addons import create_tables, get_db
from common.infra.database.schemas import AddonSchema, DownloadsSchema, UpdateSchema

from old_database import move_old_database


API_URL = 'https://api.mmoui.com/v4/game/ESO/filelist.json'


FAKE_HEADERS = {
    'User-Agent': UserAgent(platforms='desktop').chrome,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    # 'Accept-Encoding': 'gzip, deflate, br, zstd',
}


class Addon(BaseModel):
    model_config = ConfigDict(extra='ignore')
    
    id: int
    categoryId: int
    version: str
    lastUpdate: datetime
    title: str
    author: str
    fileInfoUri: str
    downloads: int
    downloadsMonthly: int
    favorites: int
    gameVersions: Optional[list[str]] = None
    checksum: str

    @field_validator('lastUpdate', mode='before')
    @classmethod
    def convert_unix_timestamp(cls, value):
        if isinstance(value, int):
            if value > 9999999999:
                value = value / 1000
            return datetime.fromtimestamp(value)
        return value


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

    insert_updates = insert(UpdateSchema).values(insert_data).on_conflict_do_nothing()

    if len(insert_data) < 1:
        return

    with get_db() as session:
        session.execute(insert_updates)
        session.commit()


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
    d1 = take_esoui_snapshot.to_deployment(
        name='take-esoui-snapshot-deployment', 
        schedule=Interval(
            timedelta(minutes=30),
            anchor_date=datetime(2025, 1, 1, 0, 0),
            timezone='Europe/Moscow'
        )
    )

    # d2 = move_old_database.to_deployment(
    #     name='move-old-database-deployment',
    # )

    serve(d1)
