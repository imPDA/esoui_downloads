from datetime import datetime
import sqlite3

from prefect import flow, task
from sqlalchemy.dialects.postgresql import insert

from core.database import create_tables, Session
from core.schemas import DownloadsSchema


@task
def fill_from_sqlite(sqlite_path: str):
    chunk_size = 10000

    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM downloads_snapshots')
    total_rows = cursor.fetchone()[0]
    print(f'Total rows to process: {total_rows}')
    
    offset = 0
    processed = 0

    cursor.execute('''SELECT * FROM downloads_snapshots ORDER BY snapshot_id''')
    
    with Session() as session:
        while True:
            cursor.execute(
                '''SELECT * FROM downloads_snapshots 
                   WHERE addon_id NOT IN (3171, 4150, 4152, 4177, 4179, 4196, 4199, 4200)
                   ORDER BY snapshot_id 
                   LIMIT ? OFFSET ?''', 
                (chunk_size, offset)
            )

            rows = cursor.fetchall()
            if not rows:
                break

            data = [{
                'esoui_id': row[1],
                'timestamp': datetime.fromtimestamp(row[3]),
                'downloads': row[2],
            } for row in rows]
            
            stmt = insert(DownloadsSchema).values(data).on_conflict_do_nothing()
            session.execute(stmt)

            processed += len(rows)
            offset += chunk_size

            print(f'Processed {processed}/{total_rows} rows ({processed / total_rows * 100:.1f}%)')
        
            session.commit()
    
    conn.close()


@flow
def move_old_database(sqlite_path: str):
    create_tables()

    fill_from_sqlite(sqlite_path)
