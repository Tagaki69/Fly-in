from schemas import ConnectionSchema, ParsedMap, ZoneSchema, ZoneType


class Graph:

    def __init__(self, parsed_map: ParsedMap) -> None:
        self.zones: dict[str, ZoneSchema] = parsed_map.zones
        self.start_name: str = parsed_map.start_name
        self.end_name: str = parsed_map.end_name
        self.connections_list: list[ConnectionSchema] = (
            parsed_map.connections
        )
        self.adjacency: dict[str, list[str]] = {}
        self.connections: dict[tuple[str, str], ConnectionSchema] = {}

        for zone_name in self.zones:
            self.adjacency[zone_name] = []
        self._build_adjacency()
        self._build_connections_dict()

    def _build_adjacency(self) -> None:
        for connection in self.connections_list:
            left = connection.left
            right = connection.right

            self.adjacency[left].append(right)
            self.adjacency[right].append(left)

    def get_neighbors(self, zone_name: str) -> list[str]:
        if zone_name not in self.adjacency:
            raise ValueError(f"unknown zone: {zone_name}")

        return self.adjacency[zone_name]

    def get_zone(self, zone_name: str) -> ZoneSchema:
        if zone_name not in self.zones:
            raise ValueError(f"unknown zone: {zone_name}")

        return self.zones[zone_name]

    def _make_connection_key(self, left: str, right: str) -> tuple[str, str]:
        left = left.strip()
        right = right.strip()

        if not left or not right:
            raise ValueError("connection zones must not be empty")

        if left == right:
            raise ValueError("connection must link two different zones")

        if left < right:
            return left, right
        return right, left

    def _build_connections_dict(self) -> None:
        for connection in self.connections_list:
            key = self._make_connection_key(
                connection.left,
                connection.right,
            )
            self.connections[key] = connection

    def get_connection(self, left: str, right: str) -> ConnectionSchema:
        key = self._make_connection_key(left, right)

        if key not in self.connections:
            raise ValueError(f"unknown connection: {left}-{right}")

        return self.connections[key]

    def is_blocked(self, zone_name: str) -> bool:
        zone = self.get_zone(zone_name)

        return zone.zone_type == ZoneType.BLOCKED

    def get_movement_cost(self, zone_name: str) -> int:
        zone = self.get_zone(zone_name)

        if zone.zone_type == ZoneType.BLOCKED:
            raise ValueError(f"blocked zone is not reachable: {zone_name}")

        if zone.zone_type == ZoneType.RESTRICTED:
            return 2

        return 1

    def is_start(self, zone_name: str) -> bool:
        self.get_zone(zone_name)

        return zone_name == self.start_name

    def is_end(self, zone_name: str) -> bool:
        self.get_zone(zone_name)

        return zone_name == self.end_name

    def display(self) -> None:
        for zone_name, neighbors in self.adjacency.items():
            neighbors_text = ", ".join(neighbors)
            print(f"{zone_name} -> {neighbors_text}")
