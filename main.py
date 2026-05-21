import sys

from graph import Graph
from parser import parse_file
from pathfinder import Pathfinder


def print_parsed_map(graph: Graph) -> None:
    """Print parsed map data."""
    print("=== CONFIG ===")
    print(f"nb_drones: {graph.zones}")

    print("\n=== START / END ===")
    print(f"start: {graph.start_name}")
    print(f"end: {graph.end_name}")

    print("\n=== ZONES ===")
    for name, zone in graph.zones.items():
        print(
            f"{name}: "
            f"x={zone.x}, "
            f"y={zone.y}, "
            f"type={zone.zone_type.value}, "
            f"color={zone.color}, "
            f"max_drones={zone.max_drones}"
        )

    print("\n=== CONNECTIONS ===")
    for connection in graph.connections_list:
        print(
            f"{connection.left} <-> {connection.right} "
            f"(capacity={connection.max_link_capacity})"
        )


def print_graph(graph: Graph) -> None:
    """Print graph adjacency list."""
    print("\n=== GRAPH ADJACENCY ===")
    graph.display()


def print_shortest_path(graph: Graph) -> None:
    """Find and print shortest path."""
    pathfinder = Pathfinder(graph)
    path = pathfinder.find_shortest_path()

    print("\n=== SHORTEST PATH ===")
    print(" -> ".join(path))

    print("\n=== PATH DETAILS ===")
    total_cost = 0

    for index, zone_name in enumerate(path):
        zone = graph.get_zone(zone_name)

        if index == 0:
            print(f"{zone_name}: start, cost=0")
            continue

        cost = graph.get_movement_cost(zone_name)
        total_cost += cost

        print(
            f"{zone_name}: "
            f"type={zone.zone_type.value}, "
            f"cost={cost}, "
            f"total={total_cost}"
        )

    print(f"\nTotal cost: {total_cost}")


def main() -> None:
    """Run parser, graph builder and pathfinder."""
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <map_file>")
        sys.exit(1)

    filename = sys.argv[1]

    try:
        parsed_map = parse_file(filename)
        graph = Graph(parsed_map)

        print_parsed_map(graph)
        print_graph(graph)
        print_shortest_path(graph)

    except FileNotFoundError as error:
        print(error)
        sys.exit(1)
    except ValueError as error:
        print(error)
        sys.exit(1)


if __name__ == "__main__":
    main()