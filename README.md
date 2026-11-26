# Mini-Courier Planner

DAA Capstone Assignment (ETCCDA302): a Python prototype that takes a list of parcels and
delivery points and produces an **optimised packing plan** and an **ordered delivery route**.

| Step | Algorithm | File |
|---|---|---|
| Prioritise parcels | Merge Sort (Quick and Insertion Sort for comparison) | `algorithms/sorting.py` |
| Fill the van | 0/1 Knapsack, Dynamic Programming | `algorithms/knapsack.py` |
| Shortest road distances | Dijkstra (binary heap) | `algorithms/dijkstra.py` |
| Delivery order | Nearest Neighbour TSP (approximate) | `algorithms/tsp.py` |
| Performance | `time.perf_counter` and Matplotlib | `performance/benchmarking.py` |

## 1. Setup

You need Python 3.8 or later.

```
cd Mini-Courier-Planner
pip install -r requirements.txt        # installs matplotlib (only needed for charts/maps)
```

## 2. Running

| Command | What it does |
|---|---|
| `python main.py` | Interactive menu (options 1 to 10, and 0 to load other data) |
| `python main.py --demo` | Runs the **complete workflow** at once and saves `screenshots/route_map.png` |
| `python main.py --capacity 35 --demo` | Same, with a different van capacity |
| `python main.py --parcels data/test_datasets/medium_parcels.json --graph data/test_datasets/medium_graph.json --demo` | Runs on another (unseen) dataset |
| `python main.py --benchmark` | Runs all benchmarks, then writes the tables and charts (about 1 minute) |
| `python -m unittest discover -s tests -v` | Runs the 36 automated tests |
| `python data/generate_datasets.py` | Regenerates the small, medium and large test datasets (seeded) |
| `python tools/capture_evidence.py` | Re-runs every scenario and saves its real output to `screenshots/` |

The menu:

```
========== MINI COURIER PLANNER ==========
 1. Display All Parcels
 2. Sort and Prioritize Parcels
 3. Optimize Package Selection (0/1 Knapsack DP)
 4. Display Delivery Graph
 5. Calculate Shortest Paths (Dijkstra)
 6. Generate Delivery Route (Nearest Neighbour TSP)
 7. Display Complete Courier Plan
 8. Run Performance Benchmark
 9. Generate Runtime Charts
10. Exit
 0. Load another dataset / change capacity
```

## 3. Project structure

```
Mini-Courier-Planner/
├── main.py                       CLI menu / --demo / --benchmark
├── requirements.txt
├── algorithms/                   pure, independently testable algorithms
│   ├── sorting.py  knapsack.py  dijkstra.py  tsp.py
├── modules/
│   ├── parcel_manager.py         Parcel model, validation, sorting + knapsack glue
│   ├── route_manager.py          graph, reachability, Dijkstra matrix, TSP route, map
│   └── courier_planner.py        the integrated, timed pipeline + text reports
├── data/
│   ├── parcels.json  delivery_graph.json      hand-made sample (12 parcels, 12 places)
│   ├── generate_datasets.py
│   └── test_datasets/            small / medium / large  (*_parcels.json, *_graph.json)
├── performance/
│   ├── benchmarking.py
│   ├── results/                  benchmark_results.json, runtime_tables.md
│   └── charts/                   5 runtime charts (PNG)
├── tests/test_algorithms.py      36 unit + integration tests
├── tools/capture_evidence.py     runs the program and records real output
├── screenshots/                  output evidence (.txt + rendered .png), route maps
└── documentation/
    ├── project_report.md         FINAL REPORT (all required sections)
    ├── system_design.md          Phase 1 design
    ├── algorithm_analysis.md     traces, complexity, Phase 4 analysis
    ├── viva_questions.md         35 Q&A + tracing + modification exercises
    ├── demonstration_guide.md    step-by-step demo script
    └── requirements_checklist.md requirement -> code -> docs -> evidence
```

## 4. Input format

`parcels.json`:

```json
{ "vehicle_capacity_kg": 20,
  "parcels": [ {"id": "P01", "weight": 4, "priority": 1, "deadline": 4, "destination": "Hospital"} ] }
```

`weight` is an integer number of kg, `priority` runs from 1 (Critical) to 5 (Low), and
`deadline` is in hours after dispatch.

`delivery_graph.json`:

```json
{ "depot": "Depot", "directed": false,
  "nodes": {"Depot": {"x": 0, "y": 0}, "Market": {"x": 3, "y": 1}},
  "edges": [["Depot", "Market", 3.5]] }
```

Edges are written as `[from, to, km]`, and the km value must be 0 or more.

## 5. Sample result (`python main.py --demo`)

```
Parcels selected (DP)      : 6  (19 kg, value 308)       capacity 20 kg
Undeliverable              : P12 -> Hilltop (no road)
Route                      : Depot -> School -> Mall -> Hospital -> Library -> Riverside -> Depot
Total route distance       : 44.4 km   (exact optimum 33.9 km: NN is an approximation)
```

## 6. Before you submit

Fill in the placeholders on the cover page of `documentation/project_report.md`:
`[STUDENT NAME]`, `[ROLL NUMBER]`, `[SECTION]`, `[SEMESTER]`, `[SUBMISSION DATE]` and `[REPOSITORY LINK]`.
