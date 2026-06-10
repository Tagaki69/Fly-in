from enum import Enum
from pydantic import BaseModel, Field


class ZoneType(str, Enum):
    """
    Define the available types for a map zone.

    Attributes:
        NORMAL (str): Normal zone type.
        BLOCKED (str): Blocked zone type.
        RESTRICTED (str): Restricted zone type.
        PRIORITY (str): Priority zone type.
    """

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class FlyinConfig(BaseModel):
    """
    Represent the global configuration of the Flyin map.

    Attributes:
        nb_drones (int): The number of drones in the simulation.
    """

    nb_drones: int = Field(gt=0)


class ZoneSchema(BaseModel):
    """
    Represent a zone with its position, type, color, and drone capacity.

    Attributes:
        name (str): The name of the zone.
        x (int): The X coordinate of the zone.
        y (int): The Y coordinate of the zone.
        zone_type (ZoneType): The type of the zone.
        color (str): The display color of the zone.
        max_drones (int): The maximum number of drones allowed in the zone.
    """

    name: str
    x: int
    y: int
    zone_type: ZoneType = ZoneType.NORMAL
    color: str = "none"
    max_drones: int = Field(default=1, gt=0)


class ConnectionSchema(BaseModel):
    """
    Represent a connection between two zones.

    Attributes:
        left (str): The name of the first zone.
        right (str): The name of the second zone.
        max_link_capacity (int): The maximum link capacity of the connection.
    """

    left: str
    right: str
    max_link_capacity: int = Field(default=1, gt=0)


class ParsedMap(BaseModel):
    """
    Represent a fully parsed map with its configuration, zones, and
    connections.

    Attributes:
        config (FlyinConfig): The global configuration.
        zones (dict[str, ZoneSchema]): The dictionary of zones.
        start_name (str): The name of the start zone.
        end_name (str): The name of the end zone.
        connections (list[ConnectionSchema]): The list of connections.
    """

    config: FlyinConfig
    zones: dict[str, ZoneSchema]
    start_name: str
    end_name: str
    connections: list[ConnectionSchema]
