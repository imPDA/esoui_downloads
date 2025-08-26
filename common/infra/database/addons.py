from contextlib import contextmanager
import os

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker

from .schemas import Base


DATABASE_URL = f'postgresql://{os.getenv('ADDONS_USERNAME')}:{os.getenv('ADDONS_PASSWORD')}@{os.getenv('ADDONS_DATABASE_HOST')}:{os.getenv('ADDONS_DATABASE_PORT')}/{os.getenv('ADDONS_DATABASE_NAME')}'


engine = create_engine(DATABASE_URL)
session = sessionmaker(bind=engine)


@contextmanager
def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()


def create_tables(engine: Engine = engine):
    Base.metadata.create_all(bind=engine)
