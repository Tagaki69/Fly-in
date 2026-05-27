*This project has been created as part of the 42 curriculum by elarue.*

# Fly-in

Fly-in is a Python project that simulates a fleet of autonomous drones moving from a start hub to an end hub through a graph of connected zones.

The goal is to move all drones to the destination in as few simulation turns as possible while respecting movement, capacity, routing, and zone constraints.

The project includes:

- a custom map parser;
- an object-oriented graph representation;
- a pathfinding system based on weighted path costs;
- a turn-based simulation engine;
- support for multiple drones and multiple paths;
- support for zone and connection capacities;
- support for special zone types;
- a Pygame visualizer to display the simulation.

---

## Description

The input map describes a network of zones connected by bidirectional links.

Each drone starts from the `start_hub` and must reach the `end_hub`.

At each simulation turn, drones may move to an adjacent connected zone if all constraints allow it.

The main constraints handled by this project are:

- `max_drones`: maximum number of drones allowed in a zone at the same time;
- `max_link_capacity`: maximum number of drones allowed to cross the same connection during one turn;
- `blocked` zones: inaccessible zones;
- `restricted` zones: zones with an additional movement cost;
- `priority` zones: preferred zones during pathfinding;
- simultaneous movements;
- multiple path allocation;
- basic deadlock avoidance through path selection and movement checks.

---

## Project Requirements

This project follows the subject requirements:

- Python 3.10 or later;
- no graph logic library such as `networkx` or `graphlib`;
- object-oriented design;
- type hints;
- `flake8` compliance;
- `mypy` static type checking;
- Makefile with common commands;
- visual representation of the simulation;
- clear terminal output following the required movement format.

---

## Installation

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
make install
```

Or directly:

```bash
pip3 install -r requirements.txt
```

---

## Dependencies

The project uses:

* `pydantic` for typed data validation;
* `pygame` for the graphical visualizer;
* `flake8` for code style checks;
* `mypy` for static typing checks.

---

## Usage

### Run the simulation

```bash
make run MAP=maps/easy/01_linear_path.txt
```

Equivalent command:

```bash
python3 main.py maps/easy/01_linear_path.txt
```

This mode only prints the simulation movements.

Example output:

```txt
D1-zone_a D2-zone_b
D1-zone_c D2-goal
D1-goal
```

---

### Run in debug mode

```bash
make debug MAP=maps/easy/01_linear_path.txt
```

Equivalent command:

```bash
python3 main.py maps/easy/01_linear_path.txt --debug
```

Debug mode prints:

* parsed configuration;
* start and end zones;
* all zones;
* all connections;
* graph adjacency;
* selected paths;
* simulation output;
* total number of turns.

---

### Run the graphical visualizer

```bash
make visual MAP=maps/easy/01_linear_path.txt
```

Equivalent command:

```bash
python3 main.py maps/easy/01_linear_path.txt --visual
```

The visualizer opens a Pygame window showing:

* zones as nodes;
* connections as lines;
* selected paths with highlighted colors;
* drones moving turn by turn;
* zone capacities;
* connection capacities;
* restricted and priority badges;
* current simulation turn.

---

### Run visualizer with debug output

```bash
make visual-debug MAP=maps/easy/01_linear_path.txt
```

---

### Change the number of selected paths

```bash
make run MAP=maps/hard/02_capacity_hell.txt MAX_PATHS=3
```

Equivalent command:

```bash
python3 main.py maps/hard/02_capacity_hell.txt --max-paths 3
```

`MAX_PATHS` controls how many paths the pathfinder tries to use for distributing drones.

---

## Makefile Commands

| Command                        | Description                          |
| ------------------------------ | ------------------------------------ |
| `make install`                 | Install project dependencies         |
| `make run MAP=<file>`          | Run the simulation                   |
| `make debug MAP=<file>`        | Run with debug output                |
| `make visual MAP=<file>`       | Run with the Pygame visualizer       |
| `make visual-debug MAP=<file>` | Run with debug output and visualizer |
| `make test`                    | Run Python syntax checks             |
| `make lint`                    | Run `flake8` and `mypy`              |
| `make clean`                   | Remove cache files                   |
| `make re`                      | Clean and run again                  |

---

## Input File Format

A map file must start with the number of drones:

```txt
nb_drones: 5
```

Then it must define one start hub:

```txt
start_hub: start 0 0 [color=green max_drones=5]
```

One end hub:

```txt
end_hub: goal 10 0 [color=green max_drones=5]
```

And any number of regular hubs:

```txt
hub: zone_a 1 0 [zone=normal color=blue max_drones=2]
hub: zone_b 2 0 [zone=restricted color=orange max_drones=1]
hub: zone_c 3 0 [zone=priority color=cyan max_drones=3]
hub: wall 4 0 [zone=blocked color=red]
```

Connections are defined with:

```txt
connection: start-zone_a
connection: zone_a-zone_b [max_link_capacity=2]
connection: zone_b-goal
```

Comments start with `#` and are ignored.

---

## Metadata

### Zone metadata

| Metadata     |  Default | Description                        |
| ------------ | -------: | ---------------------------------- |
| `zone`       | `normal` | Zone type                          |
| `color`      |   `none` | Visual color                       |
| `max_drones` |      `1` | Maximum drones allowed in the zone |

### Connection metadata

| Metadata            | Default | Description                                                         |
| ------------------- | ------: | ------------------------------------------------------------------- |
| `max_link_capacity` |     `1` | Maximum drones allowed to cross the connection during the same turn |

---

## Zone Types

| Type         |     Cost | Behavior                    |
| ------------ | -------: | --------------------------- |
| `normal`     |        1 | Standard zone               |
| `blocked`    | infinite | Cannot be entered           |
| `restricted` |        2 | Costs more turns to cross   |
| `priority`   |        1 | Preferred by the pathfinder |

---

## Simulation Rules

The simulation is turn-based.

At each turn, each drone may:

* move to an adjacent connected zone;
* wait if movement is not possible;
* stay delivered once it reaches the end zone.

The simulator enforces:

* no movement into blocked zones;
* no movement through unknown connections;
* zone capacity with `max_drones`;
* connection capacity with `max_link_capacity`;
* unlimited occupancy for the start zone;
* unlimited delivered drones at the end zone;
* waiting behavior for restricted zones;
* simultaneous movement when constraints allow it.

Drones that do not move during a turn are omitted from the output line.

The simulation ends when all drones reach the end zone.

---

## Output Format

Each line represents one simulation turn.

Each movement follows this format:

```txt
D<ID>-<zone>
```

Example:

```txt
D1-roof1 D2-corridorA
D1-roof2 D2-tunnelB
D1-goal D2-goal
```

`D<ID>` is the drone identifier.

`<zone>` is the destination zone reached during this turn.

---

## Architecture

```txt
.
├── main.py
├── parser.py
├── schemas.py
├── graph.py
├── pathfinder.py
├── simulator.py
├── visualizer.py
├── requirements.txt
├── Makefile
└── maps/
```

### `schemas.py`

Contains typed Pydantic models:

* `FlyinConfig`;
* `ZoneSchema`;
* `ConnectionSchema`;
* `ParsedMap`;
* `ZoneType`.

### `parser.py`

Reads and validates map files.

It handles:

* comments;
* metadata blocks;
* duplicate zones;
* duplicate connections;
* invalid zone types;
* invalid capacities;
* unknown zones in connections;
* missing start or end zones.

### `graph.py`

Builds the internal graph structure.

It stores:

* zones;
* connections;
* adjacency lists;
* start and end zone names;
* drone count.

It also provides helper methods for:

* neighbors;
* zone lookup;
* connection lookup;
* movement cost;
* blocked zones;
* start and end detection.

### `pathfinder.py`

Computes paths from start to end.

It provides:

* a Dijkstra-based shortest path method;
* a multiple-path search method;
* path cost calculation;
* priority-zone handling;
* overlap penalty between selected paths;
* reversed-edge conflict avoidance.

### `simulator.py`

Runs the turn-by-turn simulation.

It handles:

* drone creation;
* path assignment;
* movement validation;
* zone occupancy;
* connection usage;
* restricted-zone waiting;
* delivered drones;
* simulation history for the visualizer.

### `visualizer.py`

Displays the simulation with Pygame.

It shows:

* graph structure;
* selected paths;
* drones;
* zone labels;
* zone capacities;
* connection capacities;
* restricted and priority badges;
* current turn;
* keyboard controls.

---

## Algorithm Strategy

The algorithm is split into three main phases.

### 1. Parsing and validation

The parser reads the map and converts every line into typed objects.

Invalid input stops the program with a clear error message containing the line number and the cause.

### 2. Pathfinding

The project uses a Dijkstra-based approach to compute weighted shortest paths.

Movement costs are based on the destination zone:

* `normal`: cost 1;
* `priority`: cost 1 but preferred in tie-breaking;
* `restricted`: cost 2;
* `blocked`: ignored.

For multiple drones, the pathfinder searches several candidate paths and selects paths using:

* total path cost;
* path length;
* overlap with already selected paths;
* reversed-edge conflict detection.

This helps distribute drones across multiple routes and reduce bottlenecks.

### 3. Turn scheduling

The simulator processes drones turn by turn.

For each drone, it checks:

* whether the drone is already delivered;
* whether it must wait because of a restricted zone;
* whether the next zone exists;
* whether the next zone is blocked;
* whether the next zone has enough capacity;
* whether the connection has enough remaining capacity for the current turn.

If movement is valid, the drone moves and the simulator updates:

* zone occupancy;
* connection usage;
* drone position;
* drone delivery status;
* simulation history.

---

## Restricted Zones

Restricted zones have a movement cost of 2.

In this implementation, this is represented by forcing a drone to wait one turn after entering a restricted zone before it can move again.

This models the additional movement cost while keeping the simulation state easy to inspect and display.

---

## Priority Zones

Priority zones have the same movement cost as normal zones, but the pathfinder gives them a better priority score.

When two paths have the same total cost, paths using priority zones are preferred.

---

## Capacity Handling

### Zone capacity

Each zone has a maximum number of drones allowed at once.

Example:

```txt
hub: waiting_area 2 1 [max_drones=4]
```

This zone can contain up to 4 drones at the same time.

The start and end zones are special:

* all drones begin at the start zone;
* multiple drones may be delivered at the end zone.

### Connection capacity

Each connection has a maximum number of drones allowed to traverse it during the same turn.

Example:

```txt
connection: corridorA-tunnelB [max_link_capacity=2]
```

At most 2 drones can use this connection during one simulation turn.

---

## Visualizer

The graphical visualizer is built with Pygame.

Run it with:

```bash
python3 main.py maps/easy/01_linear_path.txt --visual
```

Controls:

| Key             | Action                   |
| --------------- | ------------------------ |
| `Space`         | Pause / play             |
| `Right arrow`   | Next turn                |
| `Left arrow`    | Previous turn            |
| `+`             | Increase animation speed |
| `-`             | Decrease animation speed |
| `R`             | Reset animation          |
| `Q` or `Escape` | Quit                     |

The visualizer helps understand:

* how drones are distributed across paths;
* where bottlenecks happen;
* how capacities affect movement;
* how restricted zones delay drones;
* how priority routes are used;
* how many drones are present on each zone.

---

## Performance Goals

The subject provides the following reference targets.

| Map type       |           Expected performance |
| -------------- | -----------------------------: |
| Easy maps      |             Less than 10 turns |
| Medium maps    |                    10–30 turns |
| Hard maps      |             Less than 60 turns |
| Challenger map | Optional target: beat 45 turns |

Specific targets include:

| Map                                 |                       Target |
| ----------------------------------- | ---------------------------: |
| Linear path with 2 drones           |                    ≤ 6 turns |
| Simple fork with 4 drones           |                    ≤ 8 turns |
| Basic capacity with 4 drones        |                    ≤ 6 turns |
| Dead end trap with 5 drones         |                   ≤ 12 turns |
| Circular loop with 6 drones         |                   ≤ 15 turns |
| Priority puzzle with 5 drones       |                   ≤ 12 turns |
| Maze nightmare with 8 drones        |                   ≤ 30 turns |
| Capacity hell with 12 drones        |                   ≤ 35 turns |
| Ultimate challenge with 15 drones   |                   ≤ 45 turns |
| The Impossible Dream with 25 drones | Optional reference: 45 turns |

---

## Error Handling

The parser stops on invalid input and displays a clear error message.

Examples of handled errors:

* missing `nb_drones`;
* missing `start_hub`;
* missing `end_hub`;
* duplicate zone name;
* duplicate connection;
* invalid metadata;
* invalid zone type;
* invalid capacity value;
* connection using an unknown zone;
* connection with invalid syntax.

---

## Quality Checks

Run syntax checks:

```bash
make test
```

Run style and type checks:

```bash
make lint
```

This runs:

```bash
flake8 .
mypy .
```

---

## Resources

### Python

* [Python documentation](https://docs.python.org/3/)
* [Python typing documentation](https://docs.python.org/3/library/typing.html)
* [heapq documentation](https://docs.python.org/3/library/heapq.html)

### Pydantic

* [Pydantic documentation](https://docs.pydantic.dev/)

### Pygame

* [Pygame documentation](https://www.pygame.org/docs/)

### Algorithms

* [Dijkstra's algorithm](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)
* [Graph theory](https://en.wikipedia.org/wiki/Graph_theory)
* [Pathfinding](https://en.wikipedia.org/wiki/Pathfinding)

### Code quality

* [flake8 documentation](https://flake8.pycqa.org/)
* [mypy documentation](https://mypy.readthedocs.io/)
* [PEP 257 docstrings](https://peps.python.org/pep-0257/)

---

## AI Usage

AI was used as a support tool during development.

It helped with:

* breaking down the subject requirements;
* explaining graph and pathfinding concepts;
* reviewing edge cases;
* creating test ideas;
* improving documentation;
* explaining bugs and debugging strategies;
* drafting parts of the README.