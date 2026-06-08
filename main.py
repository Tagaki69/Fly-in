import argparse
import sys

from graph import Graph
from parser import parse_file
from pathfinder import Pathfinder
from simulator import Simulator


def print_parsed_map(graph: Graph) -> None:
    """Print parsed map data."""
    print("=== CONFIG ===")
    print(f"nb_drones: {graph.nb_drones}")

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


def print_paths(paths: list[list[str]]) -> None:
    """Print selected paths."""
    print("\n=== PATHS ===")

    for index, path in enumerate(paths, start=1):
        print(f"path {index}: {' -> '.join(path)}")


def print_simulation(
    output_lines: list[str],
    debug: bool,
    simulator: Simulator,
) -> None:
    """Print simulation output."""
    if debug:
        print("\n=== SIMULATION ===")

    for index, line in enumerate(output_lines):
        print(line)

        if debug:
            for debug_line in simulator.format_turn_debug(index):
                print(debug_line)

    if debug:
        print(f"\nTotal turns: {len(output_lines)}")


def run_visualizer(
    graph: Graph,
    paths: list[list[str]],
    simulator: Simulator,
) -> None:
    """Run Pygame visualizer."""
    from visualizer import PygameVisualizer

    visualizer = PygameVisualizer(graph)
    visualizer.run(
        history=simulator.history,
        paths=paths,
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run Fly-in drone simulation.",
    )

    parser.add_argument(
        "map_file",
        help="Path to the map file.",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print parser, graph and path debug information.",
    )

    parser.add_argument(
        "--visual",
        action="store_true",
        help="Open Pygame visualizer.",
    )

    parser.add_argument(
        "--max-paths",
        type=int,
        default=5,
        help="Maximum number of paths to use.",
    )

    return parser.parse_args()


def main() -> None:
    """Run parser, graph builder, pathfinder and simulator."""
    args = parse_args()

    try:
        parsed_map = parse_file(args.map_file)
        graph = Graph(parsed_map)
        pathfinder = Pathfinder(graph)

        max_paths = min(graph.nb_drones, args.max_paths)
        paths = pathfinder.find_multiple_paths(max_paths)

        simulator = Simulator(graph, paths)
        output_lines = simulator.run()

        if args.debug:
            print_parsed_map(graph)
            print_graph(graph)
            print_paths(paths)

        if args.visual:
            run_visualizer(graph, paths, simulator)

        print_simulation(output_lines, args.debug, simulator)

    except (FileNotFoundError, PermissionError, ValueError) as error:
        print(error)
        sys.exit(1)


if __name__ == "__main__":
    main()
