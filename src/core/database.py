from contextlib import contextmanager
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .schemas import Base


DATABASE_URL = f'postgresql://{os.getenv('ADDONS_USERNAME')}:{os.getenv('ADDONS_PASSWORD')}@{os.getenv('ADDONS_DATABASE_HOST')}:{os.getenv('ADDONS_DATABASE_PORT')}/{os.getenv('ADDONS_DATABASE_NAME')}'


ENGINE = create_engine(DATABASE_URL)
Session = sessionmaker(bind=ENGINE)


def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_cm():
    db = Session()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(bind=ENGINE)
