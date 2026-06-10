*This project has been created as part of the 42 curriculum by elarue.*

# Fly-in

Fly-in is a Python project that simulates autonomous drones moving from a start hub to an end hub through a graph of connected zones.

The goal is to move all drones to the destination in as few turns as possible while respecting movement, routing and capacity constraints.

---

## Description

The program reads a map file describing:

* the number of drones;
* one start hub;
* one end hub;
* regular hubs;
* connections between hubs;
* optional metadata such as capacities, colors and zone types.

Each drone starts at `start_hub` and must reach `end_hub`.

At each turn, a drone may move to the next zone of its assigned path if all rules allow it. If the drone cannot move, it waits and does not appear in the output for that turn.

The project supports:

* multiple drones;
* multiple paths;
* blocked zones;
* restricted zones;
* priority zones;
* zone capacities with `max_drones`;
* connection capacities with `max_link_capacity`;
* turn-by-turn simulation;
* optional Pygame visualization.

Project architecture:

```txt
parser.py      -> reads and validates map files
schemas.py     -> defines typed data models
graph.py       -> builds the graph
pathfinder.py  -> finds valid paths
simulator.py   -> moves drones turn by turn
visualizer.py  -> displays the simulation with Pygame
main.py        -> launches the full program
```

---

## Instructions

### Install dependencies

```bash
make install
```

Or:

```bash
pip3 install -r requirements.txt
```

Main dependencies:

* `pydantic`
* `pygame`
* `flake8`
* `mypy`

---

### Run the simulation

```bash
make run MAP=maps/easy/01_linear_path.txt
```

Equivalent command:

```bash
python3 main.py maps/easy/01_linear_path.txt
```

---

### Run with debug output

```bash
make debug MAP=maps/easy/01_linear_path.txt
```

Equivalent command:

```bash
python3 main.py maps/easy/01_linear_path.txt --debug
```

Debug mode displays:

* parsed configuration;
* zones;
* connections;
* graph adjacency;
* selected paths;
* simulation output;
* total number of turns.

---

### Run the visualizer

```bash
make visual MAP=maps/easy/01_linear_path.txt
```

Equivalent command:

```bash
python3 main.py maps/easy/01_linear_path.txt --visual
```

---

### Run visualizer with debug output

```bash
make visual-debug MAP=maps/easy/01_linear_path.txt
```

---

### Change the maximum number of paths

```bash
make run MAP=maps/hard/02_capacity_hell.txt MAX_PATHS=3
```

Equivalent command:

```bash
python3 main.py maps/hard/02_capacity_hell.txt --max-paths 3
```

`MAX_PATHS` controls how many paths the pathfinder may use to distribute drones.

---

### Important

`MAP` must point to a file, not a folder.

Correct:

```bash
make run MAP=maps/challenger/01_ultimate_challenge.txt
```

Incorrect:

```bash
make run MAP=maps/challenger/
```

---

## Makefile Commands

| Command                        | Description                   |
| ------------------------------ | ----------------------------- |
| `make install`                 | Install dependencies          |
| `make run MAP=<file>`          | Run the simulation            |
| `make debug MAP=<file>`        | Run with debug output         |
| `make visual MAP=<file>`       | Run the Pygame visualizer     |
| `make visual-debug MAP=<file>` | Run with debug and visualizer |
| `make lint`                    | Run `flake8` and `mypy`       |
| `make clean`                   | Remove cache files            |
| `make re`                      | Clean and run again           |

---

## Input Format

A map file must start with:

```txt
nb_drones: 3
```

Then it must define one start hub:

```txt
start_hub: start 0 0 [color=green max_drones=3]
```

One end hub:

```txt
end_hub: goal 3 0 [color=red max_drones=3]
```

Regular hubs:

```txt
hub: a 1 0 [zone=normal color=blue max_drones=1]
hub: b 2 0 [zone=priority color=yellow max_drones=1]
hub: tunnel 2 1 [zone=restricted color=orange max_drones=1]
hub: wall 1 1 [zone=blocked color=red]
```

Connections:

```txt
connection: start-a [max_link_capacity=1]
connection: a-b [max_link_capacity=1]
connection: b-goal [max_link_capacity=1]
```

Comments start with `#` and are ignored.

---

## Metadata

### Zone metadata

| Metadata     | Default  | Description                        |
| ------------ | -------- | ---------------------------------- |
| `zone`       | `normal` | Zone type                          |
| `color`      | `none`   | Optional visual color              |
| `max_drones` | `1`      | Maximum drones allowed in the zone |

### Connection metadata

| Metadata            | Default | Description                                  |
| ------------------- | ------- | -------------------------------------------- |
| `max_link_capacity` | `1`     | Maximum drones allowed on a link in one turn |

---

## Zone Types

| Type         | Cost     | Behavior                                |
| ------------ | -------- | --------------------------------------- |
| `normal`     | `1`      | Standard zone                           |
| `blocked`    | infinite | Cannot be entered                       |
| `restricted` | `2`      | Takes extra time to cross               |
| `priority`   | `1`      | Preferred by pathfinding in case of tie |

---

## Input and Output Example

### Input

```txt
nb_drones: 2

start_hub: start 0 0 [color=green max_drones=2]
hub: a 1 0 [zone=normal color=blue max_drones=1]
end_hub: goal 2 0 [color=red max_drones=2]

connection: start-a [max_link_capacity=1]
connection: a-goal [max_link_capacity=1]
```

### Explanation

There are two drones:

```txt
D1
D2
```

Both must follow:

```txt
start -> a -> goal
```

Zone `a` has:

```txt
max_drones=1
```

Only one drone can be inside `a` at the same time.

### Expected output

```txt
D1-a
D1-goal D2-a
D2-goal
```

### Output explanation

Turn 1:

```txt
D1-a
```

`D1` moves to `a`.
`D2` waits because `a` is full.

Turn 2:

```txt
D1-goal D2-a
```

`D1` leaves `a`, so `D2` can enter it.

Turn 3:

```txt
D2-goal
```

`D2` reaches the end.

Drones that do not move are not printed.

---

## Algorithm Explanation

The program works in three main phases:

```txt
1. Parsing and validation
2. Pathfinding
3. Turn-by-turn simulation
```

---

### 1. Parsing and validation

The parser reads the map file, removes comments and empty lines, then identifies each line by its prefix:

```txt
nb_drones:
start_hub:
end_hub:
hub:
connection:
```

It validates:

* `nb_drones` is the first instruction;
* there is one start hub;
* there is one end hub;
* zone names are unique;
* connections reference existing zones;
* metadata keys are valid;
* capacities are positive integers;
* start and end are not blocked.

`pydantic` is used to store typed data and validate constraints.

---

### 2. Graph representation

The map is represented as an undirected graph.

A connection:

```txt
connection: a-b
```

means the drone can move:

```txt
a -> b
b -> a
```

The graph stores:

* zones;
* connections;
* adjacency lists;
* start and end names;
* normalized connection keys.

The adjacency list allows fast neighbor lookup during pathfinding.

Example:

```python
{
    "start": ["a"],
    "a": ["start", "goal"],
    "goal": ["a"],
}
```

---

### 3. Pathfinding

The project uses Dijkstra because all zones do not have the same movement cost.

Costs:

```txt
normal      -> 1
priority    -> 1
restricted  -> 2
blocked     -> ignored
```

Dijkstra keeps:

* `distances`: best known cost from start;
* `parents`: previous zone used to rebuild the path;
* `visited`: already processed zones;
* `queue`: priority queue handled with `heapq`.

When the end is reached, the path is rebuilt from `parents` and reversed.

---

### 4. Multiple paths

Using a single path can create bottlenecks.

The pathfinder searches multiple candidate paths, then selects paths using:

* total cost;
* path length;
* overlap with selected paths;
* reversed-edge conflicts.

This is a design compromise: the program does not guarantee the absolute optimal result, but it produces valid and efficient routes while keeping the implementation readable.

---

### 5. Simulation

The simulator creates all drones and assigns each one to a path.

Each drone stores:

```txt
drone_id
path
path_index
delivered
in_transit
transit_from
transit_to
```

At each turn, the simulator:

1. builds zone occupancy;
2. resets connection usage;
3. processes each drone once;
4. checks if the drone can move;
5. updates zone occupancy;
6. updates connection usage;
7. saves movement output;
8. saves history for the visualizer.

---

### 6. Capacity handling

Zone capacity is handled with:

```python
zone_occupancy = {
    "a": 1,
}
```

Connection capacity is handled with:

```python
connection_usage = {
    ("a", "b"): 1,
}
```

Before testing a movement, the simulator temporarily removes the drone from its current zone. This allows simultaneous movement.

Example:

```txt
D1 leaves A
D2 enters A during the same turn
```

This is allowed if the capacity is respected at the end of the turn.

---

### 7. Restricted zones

Restricted zones take extra time.

When a drone enters a restricted zone, it is put in transit:

```txt
in_transit = True
transit_from = a
transit_to = tunnel
```

Example:

```txt
Turn 1: D1-a
Turn 2: D1-a-tunnel
Turn 3: D1-tunnel
Turn 4: D1-goal
```

---

## Visual Representation

The project includes a Pygame visualizer.

It displays:

* zones as circles;
* connections as lines;
* selected paths as colored thick lines;
* drones as labeled circles;
* zone names;
* zone capacities;
* connection capacities;
* restricted and priority badges;
* current turn number;
* play or pause status;
* keyboard controls.

---

### Visualizer inputs

The visualizer receives:

```txt
graph
history
paths
```

Example `history`:

```python
[
    {1: "start", 2: "start"},
    {1: "a", 2: "start"},
    {1: "goal", 2: "a"},
    {2: "goal"},
]
```

Example `paths`:

```python
[
    ["start", "a", "goal"],
    ["start", "b", "goal"],
]
```

---

### Visual elements

| Element             | Meaning             |
| ------------------- | ------------------- |
| Green node          | Start or end zone   |
| Red node            | Blocked zone        |
| Orange node         | Restricted zone     |
| Yellow node         | Priority zone       |
| Blue node           | Normal zone         |
| `R` badge           | Restricted zone     |
| `P` badge           | Priority zone       |
| `max:<number>`      | Zone capacity       |
| `L<number>`         | Connection capacity |
| `D1`, `D2`          | Drone identifiers   |
| Colored thick lines | Selected paths      |

---

### Visualizer controls

| Key             | Action               |
| --------------- | -------------------- |
| `Space`         | Pause or play        |
| `Right arrow`   | Next turn            |
| `Left arrow`    | Previous turn        |
| `+` or `=`      | Increase speed       |
| `-`             | Decrease speed       |
| `R`             | Reset to first frame |
| `Q` or `Escape` | Quit visualizer      |

---

### Why the visualizer is useful

The visualizer helps understand:

* drone distribution;
* why drones wait;
* bottlenecks;
* zone capacity effects;
* connection capacity effects;
* restricted-zone delays;
* selected paths;
* simulation correctness.

It is especially useful for complex maps where terminal output alone is hard to read.

---

## Error Handling

The parser reports errors for:

* missing `nb_drones`;
* wrong first instruction;
* missing start or end;
* duplicate zone;
* duplicate connection;
* invalid metadata;
* invalid capacity;
* unknown zone in connection;
* blocked start or end.

The simulator can also stop if no drone can move and the simulation is stuck.

---

## Quality Checks

Run checks with:

```bash
make lint
```

This runs:

```bash
flake8 .
mypy .
```

Run project tests with:

```bash
make test
```

---

## Resources

* Python documentation
* Pydantic documentation
* Pygame documentation
* Dijkstra's algorithm
* Graph theory
* flake8 documentation
* mypy documentation

---

## AI Usage

AI was used as a support tool during development.

It helped with:

* understanding the subject;
* explaining graph and pathfinding concepts;
* reviewing edge cases;
* creating test ideas;
* improving documentation;
* debugging support.

The implementation decisions, tests and final code remain the responsibility of the student.
