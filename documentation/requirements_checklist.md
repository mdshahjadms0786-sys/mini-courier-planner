# Requirement Checklist

Every requirement from the assignment document (and the detailed brief) is mapped to the
code that implements it, the documentation that explains it, and the evidence that it works.
Evidence files are in `screenshots/` (real captured output), `performance/` and `tests/`.

## General instructions (assignment document)

| Requirement | Code | Documentation | Evidence |
|---|---|---|---|
| Implemented in Python, structured, readable, commented | whole project | README §3 | source files |
| All specified algorithms implemented | `algorithms/*.py` | report §6–7 | `04_unit_tests` |
| Tested with suitable datasets, multiple input sizes | `data/`, `performance/benchmarking.py` | report §9, §12 | `runtime_tables.md`, charts |
| Submit source, docs, datasets, screenshots, runtime charts, execution steps | all folders | README | `screenshots/`, `performance/charts/` |
| Viva: explain, trace, modify, complexity, compare, unseen data, fix errors | — | `viva_questions.md`, `demonstration_guide.md` | `05_medium_dataset_plan` (unseen data) |

## Phase 1: Courier Problem Design and Planning (20)

| Requirement | Code | Documentation | Evidence |
|---|---|---|---|
| Problem definition and objectives | — | `system_design.md` §1–2, report §2–3 | — |
| Parcel attributes (id, weight, priority, deadline, destination) | `Parcel` in `parcel_manager.py` | `system_design.md` §3.1 | `data/parcels.json` |
| Delivery point representation | `DeliveryGraph` in `route_manager.py` | §3.2 | `data/delivery_graph.json` |
| Graph structure and edge weights | `build_graph()` | §3.2–3.3 | menu option 4 in `02_menu_session` |
| Algorithm selection and justification | — | §4 (with alternatives) | — |
| Sorting / knapsack / shortest-path / route logic | `algorithms/` | §4, §7 | `01_complete_plan_sample` |
| How the algorithms integrate | `courier_planner.py` | §5–7 | `01_complete_plan_sample` |
| System architecture | — | §5, report §5 | — |
| Data structure explanation | — | §3.3 | — |
| Workflow diagram | — | §6 (Mermaid and text) | — |
| Sample input and expected output | `data/parcels.json` | §7, report §9 | `01_complete_plan_sample`, integration test `test_sample_plan` |

## Phase 2: Package Prioritization and Box Filling (20)

| Requirement | Code | Documentation | Evidence |
|---|---|---|---|
| Prioritise by deadline / priority | `priority_key()`, `sort_parcels()` | `algorithm_analysis.md` §1 | `02_menu_session` (option 2) |
| Appropriate sorting algorithm and why | `merge_sort()` | §1, `system_design.md` §4 | `sorting_comparison.png` |
| Before and after sorting results | `App.show_sorting()` | §1 table | `02_menu_session` |
| 0/1 Knapsack with DP | `knapsack_01()` | §2 | `test_matches_brute_force_and_respects_capacity` |
| Maximum capacity constraint | `knapsack_01()` validation | §2 | test asserts weight ≤ capacity; `07_zero_capacity` |
| Optimal parcel selection | backtracking in `knapsack_01()` | §2 (greedy 268 vs DP 308) | `01_complete_plan_sample` |
| DP table display | `format_dp_table()` | §2 extract | `01_complete_plan_sample`, `06_capacity_override` |
| Total selected weight | `KnapsackResult.total_weight` | §2 | "19 kg of 20 kg (95.0% full)" |
| Packing-plan result and explanation | `format_packing_plan()` | `system_design.md` §7 | selected / left-behind / undeliverable lists |

## Phase 3: Route Maker and Graph Processing (20)

| Requirement | Code | Documentation | Evidence |
|---|---|---|---|
| Weighted graph representation | adjacency list in `route_manager.py` | `system_design.md` §3.3 | menu option 4 |
| Customer / location management | node validation, `split_reachable()` | §8 | P12 reported as undeliverable |
| Dijkstra for individual shortest paths | `dijkstra()`, `reconstruct_path()` | `algorithm_analysis.md` §3 (hand trace) | `03_menu_dijkstra_tsp`; Bellman-Ford test |
| Shortest-path output | `format_shortest_paths()` | §3 | distance matrix in `03_menu_dijkstra_tsp` |
| Nearest Neighbour TSP | `nearest_neighbor_tsp()` | §4 (trace) | `03_menu_dijkstra_tsp` |
| Starting depot | `"depot"` in the graph JSON | `system_design.md` §3.2 | route starts and ends at Depot |
| Final ordered delivery sequence | `RoutePlan.stop_order`, legs with road paths | §4 | `01_complete_plan_sample` |
| Total route distance | `route_length()`, `RoutePlan.total_distance` | §4 (44.4 km worked) | test checks distance = sum of legs |
| Route visualisation | `plot_route()` | report §10 | `screenshots/route_map.png`, `route_map_medium.png` |
| Dijkstra vs NN TSP clearly distinguished; NN not claimed optimal | brute-force check in planner | `system_design.md` §4 note, `algorithm_analysis.md` §4 | 44.4 km vs optimum 33.9 km; test `test_nn_never_beats_optimal_and_can_be_worse` |

## Phase 4: Performance Testing and Optimization (20)

| Requirement | Code | Documentation | Evidence |
|---|---|---|---|
| Small / medium / large datasets | `data/generate_datasets.py` | report §9 | `data/test_datasets/` |
| Sorting, knapsack, Dijkstra, TSP timing | `bench_*()` | `algorithm_analysis.md` §6 | `runtime_tables.md` §1–4 |
| Overall application timing | `CourierPlanner.run()` timings, `bench_end_to_end()` | §6.4 | `runtime_tables.md` §5, plan summaries |
| Python timing tools | `time.perf_counter`, `gc` handling | report §12 | — |
| Matplotlib runtime charts | `draw_charts()` | report §12 | `performance/charts/*.png` (5 charts) |
| Comparison across input sizes | — | §6.1–6.4 | charts and tables |
| Test cases and results | `tests/test_algorithms.py` (36 tests) | report §11 | `04_unit_tests` (all OK) |
| Explanation of observed results | — | §6, report §14 | — |
| Optimisation suggestions | `knapsack_max_value_1d` (an implemented example) | §6.5, report §16 | 1-D DP about 1.5x faster |

## Phase 5: Final Report and Demonstration (20)

| Report section | Location in `project_report.md` |
|---|---|
| Cover page, title, student placeholders | top of the report |
| Introduction, problem statement, objectives | §1–3 |
| System requirements, architecture | §4–5 |
| Algorithms used and explanations | §6–7 |
| Implementation details | §8 |
| Sample datasets | §9 |
| Screenshots / evidence | §10 |
| Testing methodology | §11 |
| Runtime analysis and charts | §12 |
| Time and space complexity | §13 |
| Results and discussion | §14 |
| Limitations, future improvements, conclusion, references | §15–18 |
| Execution instructions | `README.md`, Appendix A |
| Complete source code | `algorithms/`, `modules/`, `main.py`, `performance/`, `tests/` |
| Output evidence | `screenshots/` |
| Demonstration guide | `demonstration_guide.md` |
| Viva questions (≥25, plus tracing and modification exercises) | `viva_questions.md` (35 Q&A, 5 tracing questions, 10 modification exercises) |

## Edge cases verified

| Case | Behaviour | Evidence |
|---|---|---|
| Empty parcel list | Empty plan, route = Depot, 0 km | `test_no_parcels` |
| Zero capacity | Nothing selected | `test_zero_capacity`, `07_zero_capacity` |
| Unreachable location | Parcel reported, not loaded | `test_sample_plan`, sample P12 |
| Unknown destination | Parcel reported, not loaded | `test_unknown_destination` |
| One-way road with no way back | Destination treated as unreachable | `test_directed_graph_one_way_unreachable` |
| Invalid JSON / missing file / bad fields / negative weights | Clear error, no crash | `TestDataValidation`, `08_invalid_inputs` |
| Invalid menu input / invalid capacity typed | Message, and the menu continues | `02_menu_session`, `08_invalid_inputs` |

## Items for the student to complete

* Fill in the cover-page placeholders (`[STUDENT NAME]`, `[ROLL NUMBER]`, `[SECTION]`, `[SEMESTER]`, `[SUBMISSION DATE]`, `[REPOSITORY LINK]`).
* Optionally add real window screenshots (Win+Shift+S) to `screenshots/` if your faculty requires them.
