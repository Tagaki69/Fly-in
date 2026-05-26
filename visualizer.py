import math

import pygame  # type: ignore[import-untyped]

from graph import Graph
from schemas import ZoneType


class PygameVisualizer:
    """Display and animate a Fly-in simulation with Pygame."""

    def __init__(self, graph: Graph) -> None:
        self.graph: Graph = graph
        self.width: int = 1280
        self.height: int = 800
        self.padding: int = 80
        self.node_radius: int = 18
        self.drone_radius: int = 8
        self.fps: int = 60
        self.frame_delay: int = 700

        self.screen: pygame.Surface | None = None
        self.clock: pygame.time.Clock | None = None
        self.font: pygame.font.Font | None = None
        self.small_font: pygame.font.Font | None = None

        self.scale: float = 1.0
        self.offset_x: float = 0.0
        self.offset_y: float = 0.0

    def run(
        self,
        history: list[dict[int, str]],
        paths: list[list[str]] | None = None,
    ) -> None:
        """Run the Pygame animation loop."""
        if not history:
            raise ValueError("visualizer needs simulation history")

        pygame.init()
        pygame.display.set_caption("Fly-in Visualizer")

        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 16)
        self.small_font = pygame.font.SysFont("arial", 13)

        self._compute_transform()

        running = True
        paused = True
        frame_index = 0
        last_update = pygame.time.get_ticks()

        while running:
            running, frame_index, paused = self._handle_events(
                frame_index,
                len(history),
                paused,
            )

            now = pygame.time.get_ticks()

            if not paused and now - last_update >= self.frame_delay:
                frame_index += 1
                last_update = now

                if frame_index >= len(history):
                    frame_index = len(history) - 1
                    paused = True

            self._draw_scene(
                history=history,
                paths=paths,
                frame_index=frame_index,
                paused=paused,
            )

            pygame.display.flip()

        if self.clock is not None:
            self.clock.tick(self.fps)

    pygame.quit()

    def _handle_events(
        self,
        frame_index: int,
        history_length: int,
        paused: bool,
    ) -> tuple[bool, int, bool]:
        """Handle keyboard and window events."""
        running = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type != pygame.KEYDOWN:
                continue

            if event.key in (pygame.K_ESCAPE, pygame.K_q):
                running = False

            elif event.key == pygame.K_SPACE:
                paused = not paused

            elif event.key == pygame.K_RIGHT:
                paused = True
                frame_index = min(frame_index + 1, history_length - 1)

            elif event.key == pygame.K_LEFT:
                paused = True
                frame_index = max(frame_index - 1, 0)

            elif event.key == pygame.K_r:
                frame_index = 0
                paused = True

            elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                self.frame_delay = max(100, self.frame_delay - 100)

            elif event.key == pygame.K_MINUS:
                self.frame_delay += 100

        return running, frame_index, paused

    def _draw_scene(
        self,
        history: list[dict[int, str]],
        paths: list[list[str]] | None,
        frame_index: int,
        paused: bool,
    ) -> None:
        """Draw the full current frame."""
        if self.screen is None:
            return

        self.screen.fill((245, 247, 250))

        self._draw_connections()

        if paths is not None:
            self._draw_paths(paths)

        self._draw_zones()
        self._draw_drones(history[frame_index])
        self._draw_hud(frame_index, len(history), paused)
        self._draw_controls()
        self._draw_legend()

    def _compute_transform(self) -> None:
        """Compute map coordinate to screen coordinate transform."""
        xs = [zone.x for zone in self.graph.zones.values()]
        ys = [zone.y for zone in self.graph.zones.values()]

        min_x = min(xs)
        max_x = max(xs)
        min_y = min(ys)
        max_y = max(ys)

        map_width = max(max_x - min_x, 1)
        map_height = max(max_y - min_y, 1)

        usable_width = self.width - self.padding * 2
        usable_height = self.height - self.padding * 2

        scale_x = usable_width / map_width
        scale_y = usable_height / map_height

        self.scale = min(scale_x, scale_y)
        self.offset_x = self.padding - min_x * self.scale
        self.offset_y = self.padding + max_y * self.scale

    def _to_screen(self, x: int, y: int) -> tuple[int, int]:
        """Convert map coordinates to screen coordinates."""
        screen_x = int(x * self.scale + self.offset_x)
        screen_y = int(self.offset_y - y * self.scale)

        return screen_x, screen_y

    def _draw_connections(self) -> None:
        """Draw all map connections."""
        if self.screen is None:
            return

        for connection in self.graph.connections_list:
            left = self.graph.get_zone(connection.left)
            right = self.graph.get_zone(connection.right)

            start_pos = self._to_screen(left.x, left.y)
            end_pos = self._to_screen(right.x, right.y)

            pygame.draw.line(
                self.screen,
                (185, 190, 200),
                start_pos,
                end_pos,
                2,
            )

    def _draw_paths(self, paths: list[list[str]]) -> None:
        """Draw selected paths with stronger colors."""
        if self.screen is None:
            return

        for path_index, path in enumerate(paths):
            color = self._get_path_color(path_index)

            for index in range(len(path) - 1):
                current_zone = self.graph.get_zone(path[index])
                next_zone = self.graph.get_zone(path[index + 1])

                start_pos = self._to_screen(
                    current_zone.x,
                    current_zone.y,
                )
                end_pos = self._to_screen(
                    next_zone.x,
                    next_zone.y,
                )

                pygame.draw.line(
                    self.screen,
                    color,
                    start_pos,
                    end_pos,
                    5,
                )

    def _draw_zones(self) -> None:
        """Draw all zones."""
        if self.screen is None:
            return

        for zone_name, zone in self.graph.zones.items():
            x, y = self._to_screen(zone.x, zone.y)
            color = self._get_zone_color(zone_name)
            radius = self.node_radius

            if self.graph.is_start(zone_name) or self.graph.is_end(zone_name):
                radius = self.node_radius + 5

            pygame.draw.circle(
                self.screen,
                color,
                (x, y),
                radius,
            )
            pygame.draw.circle(
                self.screen,
                (30, 30, 30),
                (x, y),
                radius,
                2,
            )

            self._draw_zone_label(zone_name, x, y, radius)

    def _draw_zone_label(
        self,
        zone_name: str,
        x: int,
        y: int,
        radius: int,
    ) -> None:
        """Draw a zone label."""
        if self.screen is None or self.small_font is None:
            return

        label = zone_name

        if self.graph.is_start(zone_name):
            label = f"START {zone_name}"

        if self.graph.is_end(zone_name):
            label = f"END {zone_name}"

        text = self.small_font.render(label, True, (20, 20, 20))
        rect = text.get_rect(center=(x, y - radius - 12))

        self.screen.blit(text, rect)

    def _draw_drones(self, positions: dict[int, str]) -> None:
        """Draw drones at their current positions."""
        if self.screen is None:
            return

        grouped = self._group_drones_by_zone(positions)

        for zone_name, drone_ids in grouped.items():
            zone = self.graph.get_zone(zone_name)
            base_x, base_y = self._to_screen(zone.x, zone.y)
            drone_count = len(drone_ids)

            for index, drone_id in enumerate(drone_ids):
                drone_x, drone_y = self._get_drone_position(
                    base_x,
                    base_y,
                    index,
                    drone_count,
                )

                pygame.draw.circle(
                    self.screen,
                    (15, 23, 42),
                    (drone_x, drone_y),
                    self.drone_radius,
                )
                pygame.draw.circle(
                    self.screen,
                    (255, 255, 255),
                    (drone_x, drone_y),
                    self.drone_radius,
                    2,
                )

                self._draw_drone_label(drone_id, drone_x, drone_y)

    def _group_drones_by_zone(
        self,
        positions: dict[int, str],
    ) -> dict[str, list[int]]:
        """Group drones by their current zone."""
        grouped: dict[str, list[int]] = {}

        for drone_id, zone_name in positions.items():
            grouped.setdefault(zone_name, []).append(drone_id)

        return grouped

    def _get_drone_position(
        self,
        base_x: int,
        base_y: int,
        index: int,
        count: int,
    ) -> tuple[int, int]:
        """Return an offset position for a drone inside a zone."""
        if count == 1:
            return base_x, base_y

        angle = 2 * math.pi * index / count
        distance = self.node_radius + 12

        offset_x = int(math.cos(angle) * distance)
        offset_y = int(math.sin(angle) * distance)

        return base_x + offset_x, base_y + offset_y

    def _draw_drone_label(
        self,
        drone_id: int,
        x: int,
        y: int,
    ) -> None:
        """Draw drone id label."""
        if self.screen is None or self.small_font is None:
            return

        label = self.small_font.render(
            f"D{drone_id}",
            True,
            (15, 23, 42),
        )
        rect = label.get_rect(center=(x, y + 18))

        self.screen.blit(label, rect)

    def _draw_hud(
        self,
        frame_index: int,
        history_length: int,
        paused: bool,
    ) -> None:
        """Draw turn information."""
        if self.screen is None or self.font is None:
            return

        status = "PAUSE" if paused else "PLAY"
        text = f"Tour {frame_index}/{history_length - 1}  |  {status}"

        surface = self.font.render(text, True, (15, 23, 42))
        rect = surface.get_rect(topleft=(20, 20))

        pygame.draw.rect(
            self.screen,
            (255, 255, 255),
            rect.inflate(20, 12),
            border_radius=8,
        )
        pygame.draw.rect(
            self.screen,
            (15, 23, 42),
            rect.inflate(20, 12),
            2,
            border_radius=8,
        )

        self.screen.blit(surface, rect)

    def _draw_controls(self) -> None:
        """Draw keyboard controls."""
        if self.screen is None or self.small_font is None:
            return

        controls = [
            "Espace: pause/play",
            "← / →: tour précédent / suivant",
            "+ / -: vitesse",
            "R: reset",
            "Q ou ESC: quitter",
        ]

        y = self.height - 120

        for line in controls:
            surface = self.small_font.render(line, True, (30, 30, 30))
            self.screen.blit(surface, (20, y))
            y += 20

    def _draw_legend(self) -> None:
        """Draw zone type legend."""
        if self.screen is None or self.small_font is None:
            return

        items = [
            ("normal", self._rgb("#3498db")),
            ("priority", self._rgb("#f1c40f")),
            ("restricted", self._rgb("#e67e22")),
            ("blocked", self._rgb("#e74c3c")),
            ("start/end", self._rgb("#2ecc71")),
            ("drone", (15, 23, 42)),
        ]

        x = self.width - 180
        y = 20

        for label, color in items:
            pygame.draw.circle(self.screen, color, (x, y + 8), 8)

            text = self.small_font.render(label, True, (30, 30, 30))
            self.screen.blit(text, (x + 18, y))

            y += 24

    def _get_zone_color(self, zone_name: str) -> tuple[int, int, int]:
        """Return RGB color for a zone."""
        if self.graph.is_start(zone_name):
            return self._rgb("#2ecc71")

        if self.graph.is_end(zone_name):
            return self._rgb("#2ecc71")

        zone = self.graph.get_zone(zone_name)
        custom_color = self._get_custom_color(zone.color)

        if custom_color is not None:
            return custom_color

        if zone.zone_type == ZoneType.BLOCKED:
            return self._rgb("#e74c3c")

        if zone.zone_type == ZoneType.RESTRICTED:
            return self._rgb("#e67e22")

        if zone.zone_type == ZoneType.PRIORITY:
            return self._rgb("#f1c40f")

        return self._rgb("#3498db")

    def _get_custom_color(self, color_name: str) -> tuple[int, int, int] | None:
        """Convert map color names to RGB colors."""
        colors = {
            "none": None,
            "green": self._rgb("#2ecc71"),
            "blue": self._rgb("#3498db"),
            "red": self._rgb("#e74c3c"),
            "orange": self._rgb("#e67e22"),
            "purple": self._rgb("#9b59b6"),
            "black": self._rgb("#2c3e50"),
            "brown": self._rgb("#8e5a2a"),
            "maroon": self._rgb("#800000"),
            "gold": self._rgb("#f1c40f"),
            "darkred": self._rgb("#8b0000"),
            "violet": self._rgb("#8e44ad"),
            "crimson": self._rgb("#dc143c"),
            "rainbow": self._rgb("#ff66cc"),
            "cyan": self._rgb("#00bcd4"),
            "yellow": self._rgb("#f1c40f"),
        }

        return colors.get(color_name.strip().lower())

    def _get_path_color(self, index: int) -> tuple[int, int, int]:
        """Return RGB color for a selected path."""
        colors = [
            "#1abc9c",
            "#9b59b6",
            "#e67e22",
            "#e74c3c",
            "#2980b9",
            "#27ae60",
            "#f39c12",
            "#34495e",
        ]

        return self._rgb(colors[index % len(colors)])

    def _rgb(self, hex_color: str) -> tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip("#")

        return (
            int(hex_color[0:2], 16),
            int(hex_color[2:4], 16),
            int(hex_color[4:6], 16),
        )
