from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator


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
