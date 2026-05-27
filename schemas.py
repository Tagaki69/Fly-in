from enum import Enum
from pydantic import BaseModel, Field


class ZoneType(str, Enum):
    """Define the available types for a map zone."""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class FlyinConfig(BaseModel):
    """Represent the global configuration of the Flyin map."""

    nb_drones: int = Field(gt=0)


class ZoneSchema(BaseModel):
    """Represent a zone with its position, type, color, and drone capacity."""

    name: str
    x: int
    y: int
    zone_type: ZoneType = ZoneType.NORMAL
    color: str = "none"
    max_drones: int = Field(default=1, gt=0)


class ConnectionSchema(BaseModel):
    """Represent a connection between two zones."""

    left: str
    right: str
    max_link_capacity: int = Field(default=1, gt=0)


class ParsedMap(BaseModel):
    """Represent a fully parsed map with its configuration, zones, and
    connections."""

    config: FlyinConfig
    zones: dict[str, ZoneSchema]
    start_name: str
    end_name: str
    connections: list[ConnectionSchema]
