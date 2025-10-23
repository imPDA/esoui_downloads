from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DownloadResponse(BaseModel):
    name: str
    x: list[datetime]
    y: list[int]
    author: Optional[str] = None
    max: Optional[int] = None


class ReleaseResponse(BaseModel):
    timestamp: datetime
    version: str


class AddonResponse(BaseModel):
    esoui_id: int
    title: str
    author: str
    category: int
    downloads_per_last_30_days: Optional[int] = None
    # favorites: int   


class AddonDownloadSpeedResponse(BaseModel):
    x: list[datetime]
    y: list[float]


class Filters(BaseModel):
    addons: Optional[list[int]] = None
    author: Optional[str] = None
    deprecated: Optional[bool] = False
