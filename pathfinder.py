from graph import Graph
from heapq import heappop, heappush
from schemas import ZoneType


class Pathfinder:

    def __init__(self, graph: Graph) -> None:
        self.graph: Graph = graph

    def find_shortest_path(self) -> list[str]:
        start = self.graph.start_name
        end = self.graph.end_name

        if self.graph.is_blocked(start):
            raise ValueError(f"start zone is blocked: {start}")

        if self.graph.is_blocked(end):
            raise ValueError(f"end zone is blocked: {end}")

        return self._dijkstra(start, end)

    def _dijkstra(self, start: str, end: str) -> list[str]:
        distances: dict[str, int] = {start: 0}
        priority_scores: dict[str, int] = {start: 0}
        parents: dict[str, str | None] = {start: None}
        queue: list[tuple[int, int, str]] = [(0, 0, start)]
        visited: set[str] = set()

        while queue:
            current_distance, current_priority, current_zone = heappop(queue)

            if current_zone in visited:
                continue

            visited.add(current_zone)

            if current_zone == end:
                path: list[str] = []
                cursor: str | None = end

                while cursor is not None:
                    path.append(cursor)
                    cursor = parents[cursor]

                path.reverse()
                return path

            for neighbor in self.graph.get_neighbors(current_zone):
                if neighbor in visited:
                    continue

                if self.graph.is_blocked(neighbor):
                    continue

                movement_cost = self.graph.get_movement_cost(neighbor)
                new_distance = current_distance + movement_cost

                zone = self.graph.get_zone(neighbor)
                priority_penalty = 1

                if zone.zone_type == ZoneType.PRIORITY:
                    priority_penalty = 0

                new_priority = current_priority + priority_penalty
                known_distance = distances.get(neighbor)
                known_priority = priority_scores.get(neighbor)

                if (
                    known_distance is None
                    or known_priority is None
                    or new_distance < known_distance
                    or (
                        new_distance == known_distance
                        and new_priority < known_priority
                    )
                ):
                    distances[neighbor] = new_distance
                    priority_scores[neighbor] = new_priority
                    parents[neighbor] = current_zone
                    heappush(
                        queue,
                        (new_distance, new_priority, neighbor),
                    )

        raise ValueError(f"no path found from {start} to {end}")
