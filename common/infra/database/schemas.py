from datetime import datetime, timezone
from uuid import uuid4, UUID
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ErrorsSchema(Base):
    __tablename__ = 'error'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)


class DownloadsSchema(Base):
    __tablename__ = 'downloads'

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


class UpdateSchema(Base):
    __tablename__ = 'update'

    esoui_id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, primary_key=True)

    version: Mapped[str] = mapped_column(nullable=False)
    checksum: Mapped[str] = mapped_column(nullable=False)
