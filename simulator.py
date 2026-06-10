from graph import Graph
from schemas import ZoneType


class Drone:
    """
    Represent one drone moving along one assigned path.

    Attributes:
        drone_id (int): The drone identifier.
        path (list[str]): The path assigned to the drone.
        path_index (int): The current index of the drone in its path.
        delivered (bool): Whether the drone has reached the destination.
        in_transit (bool): Whether the drone is in restricted-zone transit.
        transit_from (str | None): The starting zone of the transit.
        transit_to (str | None): The destination zone of the transit.
    """

    def __init__(self, drone_id: int, path: list[str]) -> None:
        """
        Initialize a drone with its identifier and assigned path.

        Args:
            drone_id (int): The drone identifier.
            path (list[str]): The path assigned to the drone.
        """
        self.drone_id: int = drone_id
        self.path: list[str] = path
        self.path_index: int = 0
        self.delivered: bool = False
        self.in_transit: bool = False
        self.transit_from: str | None = None
        self.transit_to: str | None = None


class Simulator:
    """
    Simulate drone movements turn by turn.

    Attributes:
        graph (Graph): The graph representing the map.
        paths (list[list[str]]): The list of paths used by the drones.
        nb_drones (int): The number of drones in the simulation.
        drones (list[Drone]): The list of active drone instances.
        turn_count (int): The current turn number.
        last_turn_had_progress (bool): Whether the last turn had progress.
        history (list[dict[int, str]]): List of drone positions per turn.
        turn_debug_history (list[dict[str, object]]): Debug data per turn.
    """

    def __init__(self, graph: Graph, paths: list[list[str]]) -> None:
        """
        Initialize the simulator with a graph and available paths.

        Args:
            graph (Graph): The graph representing the map.
            paths (list[list[str]]): The list of available paths.
        """
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
        self.turn_debug_history: list[dict[str, object]] = []

        self._create_drones()
        self.history.append(self._capture_positions())

    def _get_connection_name(self, left: str, right: str) -> str:
        """
        Return the display name of a connection.

        Args:
            left (str): The name of the first zone.
            right (str): The name of the second zone.

        Returns:
            str: The connection display name.
        """
        return f"{left}-{right}"

    def _capture_positions(self) -> dict[int, str]:
        """
        Capture the current zone of each drone.

        Returns:
            dict[int, str]: Map of drone IDs to their current zone names.
        """
        positions: dict[int, str] = {}

        for drone in self.drones:
            positions[drone.drone_id] = self._get_current_zone(drone)

        return positions

    def _validate_paths(self, paths: list[list[str]]) -> None:
        """
        Validate that each path contains at least a start and an end zone.

        Args:
            paths (list[list[str]]): The list of paths to validate.
        """
        for path in paths:
            if len(path) < 2:
                raise ValueError("path must contain at least start and end")

    def _create_drones(self) -> None:
        """
        Create drones and assign them to the best available paths.
        """
        path_loads = [0 for _ in self.paths]

        for drone_id in range(1, self.nb_drones + 1):
            path_index = self._choose_path_index(path_loads)
            path_loads[path_index] += 1
            self.drones.append(Drone(drone_id, self.paths[path_index]))

    def _choose_path_index(self, path_loads: list[int]) -> int:
        """
        Choose the path with the best score based on length and current load.

        Args:
            path_loads (list[int]): The current drone loads per path.

        Returns:
            int: The index of the chosen path.
        """
        best_index = 0
        best_score = len(self.paths[0]) + path_loads[0]

        for index, path in enumerate(self.paths):
            score = len(path) + path_loads[index]

            if score < best_score:
                best_index = index
                best_score = score

        return best_index

    def _all_delivered(self) -> bool:
        """
        Return whether all drones have reached the end zone.

        Returns:
            bool: True if all drones are delivered, False otherwise.
        """
        for drone in self.drones:
            if not drone.delivered:
                return False

        return True

    def _save_turn_debug(
        self,
        movements: list[str],
        zone_occupancy: dict[str, int],
        connection_usage: dict[tuple[str, str], int],
    ) -> None:
        """
        Save internal debug data for one simulation turn.

        Args:
            movements (list[str]): The movements made during the turn.
            zone_occupancy (dict[str, int]): The occupancy of each zone.
            connection_usage (dict[tuple[str, str], int]): Connection usage.
        """
        self.turn_debug_history.append(
            {
                "movements": movements.copy(),
                "zone_occupancy": zone_occupancy.copy(),
                "connection_usage": connection_usage.copy(),
            }
        )

    def _get_current_zone(self, drone: Drone) -> str:
        """
        Return the current zone of a drone.

        Args:
            drone (Drone): The drone to query.

        Returns:
            str: The current zone name.
        """
        return drone.path[drone.path_index]

    def _get_next_zone(self, drone: Drone) -> str | None:
        """
        Return the next zone of a drone, if one exists.

        Args:
            drone (Drone): The drone to query.

        Returns:
            str | None: Next zone name, or None if end of path is reached.
        """
        next_index = drone.path_index + 1

        if next_index >= len(drone.path):
            return None

        return drone.path[next_index]

    def _make_connection_usage_key(
        self,
        left: str,
        right: str,
    ) -> tuple[str, str]:
        """
        Create a normalized key for connection usage.

        Args:
            left (str): The first zone.
            right (str): The second zone.

        Returns:
            tuple[str, str]: The normalized connection key.
        """
        left = left.strip()
        right = right.strip()

        if left < right:
            return left, right
        return right, left

    def _build_zone_occupancy(self) -> dict[str, int]:
        """
        Build the current occupancy count for each intermediate zone.

        Returns:
            dict[str, int]: Map of zone occupancy counts.
        """
        zone_occupancy: dict[str, int] = {}

        for drone in self.drones:
            if drone.delivered:
                continue

            if drone.in_transit:
                if drone.transit_to is None:
                    raise ValueError(
                        f"drone D{drone.drone_id} has invalid transit state"
                    )
                zone_name = drone.transit_to
            else:
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
        """
        Decrease the occupancy count of a zone.

        Args:
            zone_name (str): The name of the zone.
            zone_occupancy (dict[str, int]): Zone occupancy counts map.
        """
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
        """
        Increase the occupancy count of a zone.

        Args:
            zone_name (str): The name of the zone.
            zone_occupancy (dict[str, int]): Zone occupancy counts map.
        """
        if self.graph.is_start(zone_name) or self.graph.is_end(zone_name):
            return

        zone_occupancy[zone_name] = zone_occupancy.get(zone_name, 0) + 1

    def _get_connection_usage(
        self,
        left: str,
        right: str,
        connection_usage: dict[tuple[str, str], int],
    ) -> int:
        """
        Return the current usage count of a connection.

        Args:
            left (str): The first zone.
            right (str): The second zone.
            connection_usage (dict[tuple[str, str], int]): Connection usage.

        Returns:
            int: The current usage count.
        """
        key = self._make_connection_usage_key(left, right)

        return connection_usage.get(key, 0)

    def _increase_connection_usage(
        self,
        left: str,
        right: str,
        connection_usage: dict[tuple[str, str], int],
    ) -> None:
        """
        Increase the usage count of a connection.

        Args:
            left (str): The first zone.
            right (str): The second zone.
            connection_usage (dict[tuple[str, str], int]): Connection usage.
        """
        key = self._make_connection_usage_key(left, right)

        connection_usage[key] = connection_usage.get(key, 0) + 1

    def _is_restricted_zone(self, zone_name: str) -> bool:
        """
        Return whether a zone is restricted.

        Args:
            zone_name (str): The name of the zone.

        Returns:
            bool: True if the zone is restricted, False otherwise.
        """
        zone = self.graph.get_zone(zone_name)

        return zone.zone_type == ZoneType.RESTRICTED

    def _can_move(
        self,
        drone: Drone,
        zone_occupancy: dict[str, int],
        connection_usage: dict[tuple[str, str], int],
    ) -> bool:
        """
        Return whether a drone can move to its next zone.

        Args:
            drone (Drone): The drone to query.
            zone_occupancy (dict[str, int]): Zone occupancy counts map.
            connection_usage (dict[tuple[str, str], int]): Connection usage.

        Returns:
            bool: True if the drone can move, False otherwise.
        """
        if drone.delivered:
            return False

        if drone.in_transit:
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
        """
        Move a drone or start a restricted-zone transit.

        Args:
            drone (Drone): The drone to move.

        Returns:
            str: Description of the movement or transit start.
        """
        next_zone = self._get_next_zone(drone)

        if next_zone is None:
            raise ValueError(f"drone D{drone.drone_id} cannot move")

        current_zone = self._get_current_zone(drone)

        if self._is_restricted_zone(next_zone):
            drone.in_transit = True
            drone.transit_from = current_zone
            drone.transit_to = next_zone

            connection_name = self._get_connection_name(
                current_zone,
                next_zone,
            )

            return f"D{drone.drone_id}-{connection_name}"

        drone.path_index += 1

        if self.graph.is_end(next_zone):
            drone.delivered = True

        return f"D{drone.drone_id}-{next_zone}"

    def _simulate_turn(self) -> list[str]:
        """
        Simulate one turn and return the movements made during it.

        Returns:
            list[str]: The movements made during the turn.
        """
        movements: list[str] = []
        zone_occupancy = self._build_zone_occupancy()
        connection_usage: dict[tuple[str, str], int] = {}
        self.last_turn_had_progress = False

        for drone in self.drones:
            if drone.delivered:
                continue

            if drone.in_transit:
                movement = self._finish_transit(drone)
                movements.append(movement)
                self.last_turn_had_progress = True
                continue

            current_zone = self._get_current_zone(drone)

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

                if drone.in_transit:
                    self._increase_zone_occupancy(
                        next_zone,
                        zone_occupancy,
                    )
                else:
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
        self._save_turn_debug(
            movements,
            zone_occupancy,
            connection_usage,
        )

        return movements

    def _finish_transit(self, drone: Drone) -> str:
        """
        Finish a restricted-zone transit and move the drone to its target.

        Args:
            drone (Drone): The drone in transit.

        Returns:
            str: Description of the movement.
        """
        if not drone.in_transit:
            raise ValueError(f"drone D{drone.drone_id} is not in transit")

        if drone.transit_to is None:
            raise ValueError(
                f"drone D{drone.drone_id} has no transit destination"
            )

        destination = drone.transit_to
        expected_next_zone = self._get_next_zone(drone)

        if expected_next_zone != destination:
            raise ValueError(
                f"drone D{drone.drone_id} transit destination is invalid"
            )

        drone.path_index += 1
        drone.in_transit = False
        drone.transit_from = None
        drone.transit_to = None

        if self.graph.is_end(destination):
            drone.delivered = True

        return f"D{drone.drone_id}-{destination}"

    def _format_turn_output(self, movements: list[str]) -> str:
        """
        Format the movements of one turn as an output line.

        Args:
            movements (list[str]): The movements made during the turn.

        Returns:
            str: The formatted turn output.
        """
        return " ".join(movements)

    def run(self) -> list[str]:
        """
        Run the simulation until all drones are delivered.

        Returns:
            list[str]: The output lines for each turn.
        """
        output_lines: list[str] = []

        while not self._all_delivered():
            movements = self._simulate_turn()

            if not movements and not self.last_turn_had_progress:
                raise ValueError("simulation is stuck: no drone moved")

            output_lines.append(self._format_turn_output(movements))
            self.history.append(self._capture_positions())

        return output_lines

    def format_turn_debug(self, turn_index: int) -> list[str]:
        """
        Format basic debug information for one turn.

        Args:
            turn_index (int): The index of the turn.

        Returns:
            list[str]: The formatted debug lines.
        """
        if turn_index >= len(self.turn_debug_history):
            return []

        turn_debug = self.turn_debug_history[turn_index]
        movements = turn_debug["movements"]

        if not isinstance(movements, list):
            return []

        return [
            f"--- Turn {turn_index + 1} debug ---",
            f"movements: {len(movements)}",
        ]
