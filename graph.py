from schemas import ConnectionSchema, ParsedMap, ZoneSchema


class Graph:

    def __init__(self, parsed_map: ParsedMap) -> None:
        self.zones: dict[str, ZoneSchema] = parsed_map.zones
        self.start_name: str = parsed_map.start_name
        self.end_name: str = parsed_map.end_name
        self.connections_list: list[ConnectionSchema] = (
            parsed_map.connections
        )
        self.adjacency: dict[str, list[str]] = {}

        for zone_name in self.zones:
            self.adjacency[zone_name] = []
        self._build_adjacency()

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
