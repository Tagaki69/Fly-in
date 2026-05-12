from typing import Literal, Any
from pydantic import ValidationError
from schemas import FlyinConfig


def _read_clean_lines(filename: str) -> list[tuple[int, str]]:
    clean_lines: list[tuple[int, str]] = []

    try:
        with open("r", encoding="utf-8") as data:
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


if __name__ == "__main__":
    _parse_nb_drones("nb_drones: 5 6")
