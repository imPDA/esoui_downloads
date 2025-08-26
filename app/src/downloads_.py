from contextlib import contextmanager
from datetime import datetime, timezone
import os
from uuid import uuid4, UUID
from sqlalchemy import DateTime, Engine, ForeignKey, UniqueConstraint, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class DownloadsSchema(Base):
    __tablename__ = 'downloads'
    # __table_args__ = (
    #     UniqueConstraint('esoui_id', 'timestamp', name='uq_esoui_id_timestamp'),
    # )

    # id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    esoui_id: Mapped[int] = mapped_column(ForeignKey('addon.esoui_id'), primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), primary_key=True)
    downloads: Mapped[int] = mapped_column(nullable=False)


class AddonSchema(Base):
    __tablename__ = 'addon'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    esoui_id: Mapped[int] = mapped_column(nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(nullable=False)
    author: Mapped[str] = mapped_column(nullable=False)
    category: Mapped[int] = mapped_column(nullable=False)
    url: Mapped[str] = mapped_column(nullable=False)
