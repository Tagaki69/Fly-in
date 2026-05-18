import sys

from parser import parse_file


def print_parsed_map(filename: str) -> None:
    parsed_map = parse_file(filename)

    print("=== CONFIG ===")
    print(f"nb_drones: {parsed_map.config.nb_drones}")

    print("\n=== START / END ===")
    print(f"start: {parsed_map.start_name}")
    print(f"end: {parsed_map.end_name}")

    print("\n=== ZONES ===")
    for name, zone in parsed_map.zones.items():
        print(
            f"{name}: "
            f"x={zone.x}, "
            f"y={zone.y}, "
            f"type={zone.zone_type.value}, "
            f"color={zone.color}, "
            f"max_drones={zone.max_drones}"
        )

    print("\n=== CONNECTIONS ===")
    for connection in parsed_map.connections:
        print(
            f"{connection.left} <-> {connection.right} "
            f"(capacity={connection.max_link_capacity})"
        )


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <map_file>")
        return

    filename = sys.argv[1]

    try:
        print_parsed_map(filename)
    except FileNotFoundError as error:
        print(error)
    except ValueError as error:
        print(error)


if __name__ == "__main__":
    main()
