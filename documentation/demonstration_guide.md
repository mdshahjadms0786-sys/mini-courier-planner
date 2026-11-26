# Final Demonstration Guide (about 10 minutes)

Open a terminal in the `Mini-Courier-Planner` folder before you start.

## 0. Before the viva

```
pip install -r requirements.txt
python -m unittest discover -s tests        # should end with "OK"
python main.py --demo                       # quick check that everything runs
```

Keep these files open in separate tabs: `screenshots/route_map.png`,
`performance/charts/*.png`, `documentation/project_report.md`.

## 1. Introduce the problem (1 minute)

"The planner takes parcels and a road map. It decides which parcels go in the van and the
order in which to deliver them. It uses four algorithms: Merge Sort, 0/1 Knapsack DP,
Dijkstra and Nearest Neighbour TSP."

## 2. Live run through the menu: `python main.py`

| Option | What to point out |
|---|---|
| **1** Display parcels | 12 parcels and 58 kg in total, but the van holds only 20 kg. Each parcel's value comes from its priority and deadline |
| **2** Sort | Before and after. P10 and P02 both have a 6 h deadline, so priority breaks the tie. The cross-check shows all three sorts agree |
| **4** Graph | The adjacency list. Hilltop has no roads |
| **3** Knapsack | The DP table. The bottom-right cell (308) is the answer. Explain why P10 is left behind, and that P12 is undeliverable |
| **5** Dijkstra | Depot to Mall is 11.1 km via Market and School (not the 12.4 km route via Station and Hospital). Show the distance matrix |
| **6** TSP | The visit order, 44.4 km in total. Then the brute-force optimum, 33.9 km: **NN is approximate**. Open `screenshots/route_map.png` |
| **7** Complete plan | The whole pipeline, ETAs and per-step timings |
| **9** Charts | Regenerates the charts from the saved benchmark (use **8** only if there is a minute to spare) |
| **10** Exit | |

## 3. Show robustness (1 minute)

```
python main.py --capacity 0 --demo            # nothing selected, route = Depot
python main.py --parcels data/missing.json    # clean error message
python main.py                                 # then type: abc   (invalid choice handled)
```

## 4. Unseen or larger data (1 minute)

```
python main.py --parcels data/test_datasets/medium_parcels.json --graph data/test_datasets/medium_graph.json --demo
```

If the examiner gives you a new file, pass it with `--parcels` and `--graph`, or load it
with menu option 0.

## 5. Performance (2 minutes)

Open `performance/charts/`:

* `sorting_comparison.png`: Merge Sort grows as n log n and Insertion Sort as n^2. Quick
  Sort with a middle pivot degraded on our data, which is why Merge Sort was chosen.
* `knapsack_scaling.png`: the time is linear in n and in W, so it is O(nW) (pseudo-polynomial).
* `dijkstra_scaling.png`: almost linear on sparse graphs.
* `tsp_comparison.png`: NN is O(k^2), brute force is O(k!), and NN tours average 1 to 8% longer than optimal.
* `end_to_end_breakdown.png`: Dijkstra and the knapsack dominate. 1000 parcels take about 0.1 s.

## 6. Likely live tasks and where to edit

See section G of `viva_questions.md`. The most common tasks:

* "Sort by priority first": edit `priority_key()` in `modules/parcel_manager.py`.
* "Change capacity": `--capacity N`, or menu option 0.
* "Trace Dijkstra on this graph": use the hand-trace table in `algorithm_analysis.md` as a template.
