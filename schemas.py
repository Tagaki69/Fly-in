from enum import Enum
from pydantic import BaseModel, Field


class ZoneType(str, Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class FlyinConfig(BaseModel):
    nb_drones: int = Field(gt=0)


class ZoneSchema(BaseModel):
    name: str
    x: int
    y: int
    zone_type: ZoneType = ZoneType.NORMAL
    color: str = "none"
    max_drones: int = Field(default=1, gt=0)


class ConnectionSchema(BaseModel):
    left: str
    right: str
    max_link_capacity: int = Field(default=1, gt=0)


class ParsedMap(BaseModel):
    config: FlyinConfig
    zones: dict[str, ZoneSchema]
    start_name: str
    end_name: str
    connections: list[ConnectionSchema]

