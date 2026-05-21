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
                return self._reconstruct_path(parents, end)

            for neighbor in self._get_valid_neighbors(current_zone, visited):

                movement_cost = self.graph.get_movement_cost(neighbor)
                new_distance = current_distance + movement_cost

                priority_penalty = self._get_priority_penalty(neighbor)

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

    def _reconstruct_path(
        self,
        parents: dict[str, str | None],
        end: str,
    ) -> list[str]:

        path: list[str] = []
        cursor: str | None = end

        while cursor is not None:
            if cursor not in parents:
                raise ValueError(f"missing parent for zone: {cursor}")

            path.append(cursor)
            cursor = parents[cursor]

        path.reverse()
        return path

    def _get_valid_neighbors(
        self,
        zone_name: str,
        visited: set[str],
    ) -> list[str]:
        valid_neighbors: list[str] = []

        for neighbor in self.graph.get_neighbors(zone_name):
            if neighbor in visited:
                continue

            if self.graph.is_blocked(neighbor):
                continue

            valid_neighbors.append(neighbor)

        return valid_neighbors

    def _get_priority_penalty(self, zone_name: str) -> int:
        zone = self.graph.get_zone(zone_name)

        if zone.zone_type == ZoneType.PRIORITY:
            return 0

        return 1
