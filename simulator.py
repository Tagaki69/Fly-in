from graph import Graph
from schemas import ZoneType


class Drone:
    """Represent one drone moving along one assigned path."""

    def __init__(self, drone_id: int, path: list[str]) -> None:
        self.drone_id: int = drone_id
        self.path: list[str] = path
        self.path_index: int = 0
        self.delivered: bool = False
        self.wait_turns: int = 0


class Simulator:
    """Simulate drone movements turn by turn."""

    def __init__(self, graph: Graph, paths: list[list[str]]) -> None:
        if not paths:
            raise ValueError("simulator needs at least one path")

        self._validate_paths(paths)

        self.graph: Graph = graph
        self.paths: list[list[str]] = paths
        self.nb_drones: int = graph.nb_drones
        self.drones: list[Drone] = []
        self.turn_count: int = 0
        self.last_turn_had_progress: bool = False

        self.history: list[dict[int, str]] = []

        self._create_drones()
        self.history.append(self._capture_positions())

    def _capture_positions(self) -> dict[int, str]:
        positions: dict[int, str] = {}

        for drone in self.drones:
            positions[drone.drone_id] = self._get_current_zone(drone)

        return positions

    def _validate_paths(self, paths: list[list[str]]) -> None:
        for path in paths:
            if len(path) < 2:
                raise ValueError("path must contain at least start and end")

    def _create_drones(self) -> None:
        path_loads = [0 for _ in self.paths]

        for drone_id in range(1, self.nb_drones + 1):
            path_index = self._choose_path_index(path_loads)
            path_loads[path_index] += 1
            self.drones.append(Drone(drone_id, self.paths[path_index]))

    def _choose_path_index(self, path_loads: list[int]) -> int:
        best_index = 0
        best_score = len(self.paths[0]) + path_loads[0]

        for index, path in enumerate(self.paths):
            score = len(path) + path_loads[index]

            if score < best_score:
                best_index = index
                best_score = score

        return best_index

    def _all_delivered(self) -> bool:
        for drone in self.drones:
            if not drone.delivered:
                return False

        return True

    def _get_current_zone(self, drone: Drone) -> str:
        return drone.path[drone.path_index]

    def _get_next_zone(self, drone: Drone) -> str | None:
        next_index = drone.path_index + 1

        if next_index >= len(drone.path):
            return None

        return drone.path[next_index]

    def _make_connection_usage_key(
        self,
        left: str,
        right: str,
    ) -> tuple[str, str]:
        left = left.strip()
        right = right.strip()

        if left < right:
            return left, right
        return right, left

    def _build_zone_occupancy(self) -> dict[str, int]:
        zone_occupancy: dict[str, int] = {}

        for drone in self.drones:
            if drone.delivered:
                continue

            zone_name = self._get_current_zone(drone)

            if self.graph.is_start(zone_name):
                continue

            if self.graph.is_end(zone_name):
                continue

            zone_occupancy[zone_name] = (
                zone_occupancy.get(zone_name, 0) + 1
            )

        return zone_occupancy

    def _decrease_zone_occupancy(
        self,
        zone_name: str,
        zone_occupancy: dict[str, int],
    ) -> None:
        if self.graph.is_start(zone_name) or self.graph.is_end(zone_name):
            return

        if zone_name not in zone_occupancy:
            return

        zone_occupancy[zone_name] -= 1

        if zone_occupancy[zone_name] <= 0:
            del zone_occupancy[zone_name]

    def _increase_zone_occupancy(
        self,
        zone_name: str,
        zone_occupancy: dict[str, int],
    ) -> None:
        if self.graph.is_start(zone_name) or self.graph.is_end(zone_name):
            return

        zone_occupancy[zone_name] = zone_occupancy.get(zone_name, 0) + 1

    def _get_connection_usage(
        self,
        left: str,
        right: str,
        connection_usage: dict[tuple[str, str], int],
    ) -> int:
        key = self._make_connection_usage_key(left, right)

        return connection_usage.get(key, 0)

    def _increase_connection_usage(
        self,
        left: str,
        right: str,
        connection_usage: dict[tuple[str, str], int],
    ) -> None:
        key = self._make_connection_usage_key(left, right)

        connection_usage[key] = connection_usage.get(key, 0) + 1

    def _is_restricted_zone(self, zone_name: str) -> bool:
        zone = self.graph.get_zone(zone_name)

        return zone.zone_type == ZoneType.RESTRICTED

    def _can_move(
        self,
        drone: Drone,
        zone_occupancy: dict[str, int],
        connection_usage: dict[tuple[str, str], int],
    ) -> bool:
        if drone.delivered:
            return False

        if drone.wait_turns > 0:
            return False

        next_zone = self._get_next_zone(drone)

        if next_zone is None:
            return False

        current_zone = self._get_current_zone(drone)
        connection = self.graph.get_connection(current_zone, next_zone)
        current_link_usage = self._get_connection_usage(
            current_zone,
            next_zone,
            connection_usage,
        )

        if current_link_usage >= connection.max_link_capacity:
            return False

        if self.graph.is_blocked(next_zone):
            return False

        if self.graph.is_start(next_zone):
            return True

        if self.graph.is_end(next_zone):
            return True

        next_zone_data = self.graph.get_zone(next_zone)
        current_count = zone_occupancy.get(next_zone, 0)

        return current_count < next_zone_data.max_drones

    def _move_drone(self, drone: Drone) -> str:
        next_zone = self._get_next_zone(drone)

        if next_zone is None:
            raise ValueError(f"drone D{drone.drone_id} cannot move")

        drone.path_index += 1

        if self.graph.is_end(next_zone):
            drone.delivered = True
            drone.wait_turns = 0
        elif self._is_restricted_zone(next_zone):
            drone.wait_turns = 1

        return f"D{drone.drone_id}-{next_zone}"

    def _simulate_turn(self) -> list[str]:
        movements: list[str] = []
        zone_occupancy = self._build_zone_occupancy()
        connection_usage: dict[tuple[str, str], int] = {}
        self.last_turn_had_progress = False

        for drone in self.drones:
            if drone.delivered:
                continue

            current_zone = self._get_current_zone(drone)

            if drone.wait_turns > 0:
                drone.wait_turns -= 1
                self.last_turn_had_progress = True
                continue

            self._decrease_zone_occupancy(
                current_zone,
                zone_occupancy,
            )

            if self._can_move(
                drone,
                zone_occupancy,
                connection_usage,
            ):
                next_zone = self._get_next_zone(drone)

                if next_zone is None:
                    raise ValueError("next zone is missing")

                movement = self._move_drone(drone)
                movements.append(movement)
                self.last_turn_had_progress = True

                self._increase_connection_usage(
                    current_zone,
                    next_zone,
                    connection_usage,
                )

                new_zone = self._get_current_zone(drone)

                self._increase_zone_occupancy(
                    new_zone,
                    zone_occupancy,
                )
            else:
                self._increase_zone_occupancy(
                    current_zone,
                    zone_occupancy,
                )

        self.turn_count += 1

        return movements

    def _format_turn_output(self, movements: list[str]) -> str:
        return " ".join(movements)

    def run(self) -> list[str]:
        output_lines: list[str] = []

        while not self._all_delivered():
            movements = self._simulate_turn()

            if not movements and not self.last_turn_had_progress:
                raise ValueError("simulation is stuck: no drone moved")

            output_lines.append(self._format_turn_output(movements))
            self.history.append(self._capture_positions())

        return output_lines
