from heapq import heappop, heappush

from graph import Graph
from schemas import ZoneType


class Pathfinder:
    """
    Find one or more valid paths through a graph.

    Attributes:
        graph (Graph): The graph representing the map.
    """

    def __init__(self, graph: Graph) -> None:
        """
        Initialize the pathfinder with a graph.

        Args:
            graph (Graph): The graph representing the map.
        """
        self.graph: Graph = graph

    def find_shortest_path(self) -> list[str]:
        """
        Find the shortest path from the start zone to the end zone.

        Returns:
            list[str]: The list of zone names in the shortest path.
        """
        start = self.graph.start_name
        end = self.graph.end_name

        if self.graph.is_blocked(start):
            raise ValueError(f"start zone is blocked: {start}")

        if self.graph.is_blocked(end):
            raise ValueError(f"end zone is blocked: {end}")

        return self._dijkstra(start, end)

    def find_multiple_paths(self, max_paths: int) -> list[list[str]]:
        """
        Find multiple compatible paths from the start zone to the end zone.

        Args:
            max_paths (int): The maximum number of paths to find.

        Returns:
            list[list[str]]: The list of compatible paths.
        """
        if max_paths <= 0:
            raise ValueError("max_paths must be positive")

        max_candidates = max_paths * 80
        candidates = self._find_candidate_paths(max_candidates)

        if not candidates:
            raise ValueError("no path found")

        best_cost = min(self._path_total_cost(path) for path in candidates)
        candidates = [
            path
            for path in candidates
            if self._path_total_cost(path) <= best_cost + 8
        ]

        return self._select_best_paths(candidates, max_paths)

    def _dijkstra(self, start: str, end: str) -> list[str]:
        """
        Find the lowest-cost path between two zones using Dijkstra's algorithm.

        Args:
            start (str): The name of the start zone.
            end (str): The name of the end zone.

        Returns:
            list[str]: The list of zone names in the shortest path.
        """
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

                if self._should_update_path(
                    known_distance,
                    known_priority,
                    new_distance,
                    new_priority,
                ):
                    distances[neighbor] = new_distance
                    priority_scores[neighbor] = new_priority
                    parents[neighbor] = current_zone
                    heappush(
                        queue,
                        (new_distance, new_priority, neighbor),
                    )

        raise ValueError(f"no path found from {start} to {end}")

    def _should_update_path(
        self,
        known_distance: int | None,
        known_priority: int | None,
        new_distance: int,
        new_priority: int,
    ) -> bool:
        """
        Return whether a path should replace the currently known path.

        Args:
            known_distance (int | None): The currently known distance.
            known_priority (int | None): The currently known priority penalty.
            new_distance (int): The new distance to the neighbor.
            new_priority (int): The new priority penalty.

        Returns:
            bool: True if the path should be updated, False otherwise.
        """
        if known_distance is None:
            return True

        if known_priority is None:
            return True

        if new_distance < known_distance:
            return True

        return (
            new_distance == known_distance
            and new_priority < known_priority
        )

    def _reconstruct_path(
        self,
        parents: dict[str, str | None],
        end: str,
    ) -> list[str]:
        """
        Reconstruct a path from the parents dictionary.

        Args:
            parents (dict[str, str | None]): Map of zones to parents.
            end (str): The destination zone name.

        Returns:
            list[str]: The reconstructed path as a list of zone names.
        """

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
        """
        Return unvisited and reachable neighbors for a zone.

        Args:
            zone_name (str): The name of the zone.
            visited (set[str]): The set of visited zone names.

        Returns:
            list[str]: The list of valid neighboring zone names.
        """
        valid_neighbors: list[str] = []

        for neighbor in self.graph.get_neighbors(zone_name):
            if neighbor in visited:
                continue

            if self.graph.is_blocked(neighbor):
                continue

            valid_neighbors.append(neighbor)

        return valid_neighbors

    def _get_priority_penalty(self, zone_name: str) -> int:
        """
        Return the priority penalty for a zone.

        Args:
            zone_name (str): The name of the zone.

        Returns:
            int: The priority penalty (0 for priority zone, 1 otherwise).
        """
        zone = self.graph.get_zone(zone_name)

        if zone.zone_type == ZoneType.PRIORITY:
            return 0

        return 1

    def _find_candidate_paths(self, max_candidates: int) -> list[list[str]]:
        """
        Find candidate paths up to the given maximum number of candidates.

        Args:
            max_candidates (int): The maximum number of candidates.

        Returns:
            list[list[str]]: The list of candidate paths.
        """
        start = self.graph.start_name
        end = self.graph.end_name
        max_depth = len(self.graph.zones)
        candidates: list[list[str]] = []
        stack: list[tuple[str, list[str]]] = [(start, [start])]

        while stack and len(candidates) < max_candidates:
            current_zone, path = stack.pop()

            if current_zone == end:
                candidates.append(path)
                continue

            if len(path) > max_depth:
                continue

            neighbors = self.graph.get_neighbors(current_zone)
            neighbors = self._sort_neighbors_by_cost(neighbors)

            for neighbor in reversed(neighbors):
                if neighbor in path:
                    continue

                if self.graph.is_blocked(neighbor):
                    continue

                stack.append((neighbor, path + [neighbor]))

        return candidates

    def _sort_neighbors_by_cost(self, neighbors: list[str]) -> list[str]:
        """
        Sort reachable neighbors by movement cost, priority penalty, and name.

        Args:
            neighbors (list[str]): The list of neighbor names.

        Returns:
            list[str]: The sorted list of neighbor names.
        """
        valid_neighbors: list[str] = []

        for neighbor in neighbors:
            if self.graph.is_blocked(neighbor):
                continue

            valid_neighbors.append(neighbor)

        return sorted(
            valid_neighbors,
            key=lambda zone_name: (
                self.graph.get_movement_cost(zone_name),
                self._get_priority_penalty(zone_name),
                zone_name,
            ),
        )

    def _path_total_cost(self, path: list[str]) -> int:
        """
        Return the total movement cost of a path.

        Args:
            path (list[str]): The path as a list of zone names.

        Returns:
            int: The total movement cost of the path.
        """
        total_cost = 0

        for zone_name in path[1:]:
            total_cost += self.graph.get_movement_cost(zone_name)

        return total_cost

    def _path_edges(self, path: list[str]) -> set[tuple[str, str]]:
        """
        Return the directed edges used by a path.

        Args:
            path (list[str]): The path as a list of zone names.

        Returns:
            set[tuple[str, str]]: The set of directed edges.
        """
        edges: set[tuple[str, str]] = set()

        for index in range(len(path) - 1):
            edges.add((path[index], path[index + 1]))

        return edges

    def _has_reversed_edge_conflict(
        self,
        path: list[str],
        selected_paths: list[list[str]],
    ) -> bool:
        """
        Return whether a path conflicts with selected paths by using a reversed
        edge.

        Args:
            path (list[str]): The path to check.
            selected_paths (list[list[str]]): The list of selected paths.

        Returns:
            bool: True if there is a reversed edge conflict, False otherwise.
        """
        path_edges = self._path_edges(path)

        for selected_path in selected_paths:
            selected_edges = self._path_edges(selected_path)

            for left, right in path_edges:
                if (right, left) in selected_edges:
                    return True

        return False

    def _path_overlap_score(
        self,
        path: list[str],
        selected_paths: list[list[str]],
    ) -> int:
        """
        Return the number of middle zones shared with selected paths.

        Args:
            path (list[str]): The path to check.
            selected_paths (list[list[str]]): The list of selected paths.

        Returns:
            int: The overlap score.
        """
        path_middle = set(path[1:-1])
        score = 0

        for selected_path in selected_paths:
            selected_middle = set(selected_path[1:-1])
            score += len(path_middle & selected_middle)

        return score

    def _path_selection_score(
        self,
        path: list[str],
        selected_paths: list[list[str]],
    ) -> int:
        """
        Return the selection score of a path compared with selected paths.

        Args:
            path (list[str]): The path to evaluate.
            selected_paths (list[list[str]]): The list of selected paths.

        Returns:
            int: The path selection score.
        """
        overlap_penalty = 5

        return (
            self._path_total_cost(path)
            + self._path_overlap_score(path, selected_paths)
            * overlap_penalty
        )

    def _select_best_paths(
        self,
        candidates: list[list[str]],
        max_paths: int,
    ) -> list[list[str]]:
        """
        Select the best compatible paths from a list of candidate paths.

        Args:
            candidates (list[list[str]]): The list of candidate paths.
            max_paths (int): The maximum number of paths to select.

        Returns:
            list[list[str]]: The selected best paths.
        """
        selected_paths: list[list[str]] = []
        remaining_paths = candidates.copy()

        while remaining_paths and len(selected_paths) < max_paths:
            compatible_paths = [
                path
                for path in remaining_paths
                if not self._has_reversed_edge_conflict(
                    path,
                    selected_paths,
                )
            ]

            if not compatible_paths:
                break

            best_path = min(
                compatible_paths,
                key=lambda path: (
                    self._path_selection_score(path, selected_paths),
                    self._path_total_cost(path),
                    len(path),
                ),
            )

            selected_paths.append(best_path)
            remaining_paths.remove(best_path)

        if not selected_paths:
            raise ValueError("no compatible path found")

        return sorted(selected_paths, key=self._path_total_cost)
