from typing import Literal, Any
from pydantic import ValidationError
from schemas import FlyinConfig, ZoneSchema, ConnectionSchema, ParsedMap


def _read_clean_lines(filename: str) -> list[tuple[int, str]]:
    clean_lines: list[tuple[int, str]] = []

    try:
        with open(filename, "r", encoding="utf-8") as data:
            for line_number, line in enumerate(data, start=1):
                line = line.split("#", 1)[0].strip()
                if line:
                    clean_lines.append((line_number, line))
    except FileNotFoundError as error:
        raise FileNotFoundError(f"Error: {filename} not found") from error

    return clean_lines


LineType = Literal[
    "nb_drones",
    "start_hub",
    "end_hub",
    "hub",
    "connection",
]


def _get_line_type(line: str) -> LineType:
    if line.startswith("nb_drones:"):
        return "nb_drones"
    if line.startswith("start_hub:"):
        return "start_hub"
    if line.startswith("end_hub:"):
        return "end_hub"
    if line.startswith("hub:"):
        return "hub"
    if line.startswith("connection:"):
        return "connection"
    raise ValueError(f"unknown line type: {line}")


def _parse_nb_drones(line: str) -> FlyinConfig:
    prefix = "nb_drones:"

    if not line.startswith(prefix):
        raise ValueError("invalid nb_drones line")

    value = line[len(prefix):].strip()
    parts = value.split()

    if len(parts) != 1:
        raise ValueError("nb_drones must contain exactly one value")

    try:
        nb_drones = int(parts[0])
    except ValueError as error:
        raise ValueError("nb_drones must be an integer") from error

    try:
        return FlyinConfig(nb_drones=nb_drones)
    except ValidationError as error:
        raise ValueError("nb_drones must be a positive integer") from error


def _parse_metadata(line: str) -> tuple[str, dict[str, str]]:
    line = line.strip()

    if "[" not in line and "]" not in line:
        return line, {}

    if line.count("[") != 1 or line.count("]") != 1:
        raise ValueError("invalid metadata brackets")

    start = line.find("[")
    end = line.find("]")

    if start > end:
        raise ValueError("invalid metadata order")

    if end != len(line) - 1:
        raise ValueError("metadata must be at the end of the line")

    body = line[:start].strip()
    raw_metadata = line[start + 1:end].strip()

    if not body:
        raise ValueError("missing line body before metadata")

    if not raw_metadata:
        raise ValueError("empty metadata block")

    metadata: dict[str, str] = {}

    for item in raw_metadata.split():
        if item.count("=") != 1:
            raise ValueError(f"invalid metadata item: {item}")

        key, value = item.split("=", 1)

        if not key or not value:
            raise ValueError(f"invalid metadata item: {item}")

        if key in metadata:
            raise ValueError(f"duplicate metadata key: {key}")

        metadata[key] = value

    return body, metadata


def _parse_zone(line: str, line_type: LineType) -> ZoneSchema:
    if line_type not in ("start_hub", "end_hub", "hub"):
        raise ValueError("line type is not a zone")

    body, metadata = _parse_metadata(line)
    allowed_metadata = {"zone", "color", "max_drones"}
    unknown_keys = set(metadata) - allowed_metadata

    if unknown_keys:
        key = next(iter(unknown_keys))
        raise ValueError(f"unknown zone metadata: {key}")

    prefix = f"{line_type}:"

    if not body.startswith(prefix):
        raise ValueError(f"invalid {line_type} line")

    content = body[len(prefix):].strip()
    parts = content.split()

    if len(parts) != 3:
        raise ValueError("zone must contain exactly: name x y")

    name = parts[0]

    if "-" in name:
        raise ValueError("zone name must not contain '-'")

    try:
        x = int(parts[1])
        y = int(parts[2])
    except ValueError as error:
        raise ValueError("zone coordinates must be integers") from error

    data: dict[str, Any] = {
        "name": name,
        "x": x,
        "y": y,
    }

    if "zone" in metadata:
        data["zone_type"] = metadata["zone"]

    if "color" in metadata:
        data["color"] = metadata["color"]

    if "max_drones" in metadata:
        try:
            data["max_drones"] = int(metadata["max_drones"])
        except ValueError as error:
            raise ValueError("max_drones must be an integer") from error

    try:
        return ZoneSchema(**data)
    except ValidationError as error:
        raise ValueError(f"invalid zone data: {error}") from error


def _parse_connection(line: str) -> ConnectionSchema:
    body, metadata = _parse_metadata(line)
    allowed_metadata = {"max_link_capacity"}
    unknown_keys = set(metadata) - allowed_metadata

    if unknown_keys:
        key = next(iter(unknown_keys))
        raise ValueError(f"unknown connection metadata: {key}")

    prefix = "connection:"

    if not body.startswith(prefix):
        raise ValueError("invalid connection line")

    content = body[len(prefix):].strip()

    if not content:
        raise ValueError("missing connection value")

    if content.count("-") != 1:
        raise ValueError("connection must contain exactly one '-'")

    left, right = content.split("-", 1)
    left = left.strip()
    right = right.strip()

    if not left or not right:
        raise ValueError("connection zones must not be empty")

    if " " in left or " " in right:
        raise ValueError("connection zone names must not contain spaces")

    data: dict[str, Any] = {
        "left": left,
        "right": right,
    }

    if "max_link_capacity" in metadata:
        try:
            data["max_link_capacity"] = int(metadata["max_link_capacity"])
        except ValueError as error:
            raise ValueError("max_link_capacity must be an integer") from error

    try:
        return ConnectionSchema(**data)
    except ValidationError as error:
        raise ValueError(f"invalid connection data: {error}") from error


def _make_connection_key(left: str, right: str) -> tuple[str, str]:
    left = left.strip()
    right = right.strip()

    if not left or not right:
        raise ValueError("connection zones must not be empty")

    if left == right:
        raise ValueError("connection must link two different zones")

    if left < right:
        return left, right
    return right, left


def _validate_result(
    config: FlyinConfig | None,
    zones: dict[str, ZoneSchema],
    start_name: str | None,
    end_name: str | None,
    connections: list[ConnectionSchema],
) -> ParsedMap:

    if config is None:
        raise ValueError("missing nb_drones")

    if start_name is None:
        raise ValueError("missing start_hub")

    if end_name is None:
        raise ValueError("missing end_hub")

    if start_name not in zones:
        raise ValueError("start_hub is not registered in zones")

    if end_name not in zones:
        raise ValueError("end_hub is not registered in zones")

    if start_name == end_name:
        raise ValueError("start_hub and end_hub must be different")

    for connection in connections:
        if connection.left not in zones:
            raise ValueError(
                f"unknown zone in connection: {connection.left}"
            )

        if connection.right not in zones:
            raise ValueError(
                f"unknown zone in connection: {connection.right}"
            )

    return ParsedMap(
        config=config,
        zones=zones,
        start_name=start_name,
        end_name=end_name,
        connections=connections,
    )


def parse_file(filename: str) -> ParsedMap:
    clean_lines = _read_clean_lines(filename)

    if not clean_lines:
        raise ValueError("empty map file")

    config: FlyinConfig | None = None
    zones: dict[str, ZoneSchema] = {}
    start_name: str | None = None
    end_name: str | None = None
    connections: list[ConnectionSchema] = []
    connection_keys: set[tuple[str, str]] = set()

    for index, item in enumerate(clean_lines):
        line_number, line = item

        try:
            line_type = _get_line_type(line)

            if index == 0 and line_type != "nb_drones":
                raise ValueError("first instruction must be nb_drones")

            if line_type == "nb_drones":
                if config is not None:
                    raise ValueError("duplicate nb_drones line")
                config = _parse_nb_drones(line)

            elif line_type in ("start_hub", "end_hub", "hub"):
                zone = _parse_zone(line, line_type)

                if zone.name in zones:
                    raise ValueError(f"duplicate zone name: {zone.name}")

                zones[zone.name] = zone

                if line_type == "start_hub":
                    if start_name is not None:
                        raise ValueError("duplicate start_hub")
                    start_name = zone.name

                if line_type == "end_hub":
                    if end_name is not None:
                        raise ValueError("duplicate end_hub")
                    end_name = zone.name

            elif line_type == "connection":
                connection = _parse_connection(line)

                if connection.left not in zones:
                    raise ValueError(
                        f"unknown zone in connection: {connection.left}"
                    )

                if connection.right not in zones:
                    raise ValueError(
                        f"unknown zone in connection: {connection.right}"
                    )

                key = _make_connection_key(
                    connection.left,
                    connection.right,
                )

                if key in connection_keys:
                    raise ValueError("duplicate connection")

                connection_keys.add(key)
                connections.append(connection)

        except ValueError as error:
            raise ValueError(
                f"Parsing error line {line_number}: {error}"
            ) from error

    return _validate_result(
        config=config,
        zones=zones,
        start_name=start_name,
        end_name=end_name,
        connections=connections,
    )
