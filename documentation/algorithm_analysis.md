# Algorithm Analysis (Phases 2, 3 and 4)

Every number in this document comes from real runs on the development machine
(Windows 11, Intel 64-bit, Python 3.14.2). Absolute times will be different on another
computer, but the growth trends should be the same. Source files:
`performance/results/runtime_tables.md`, `performance/results/benchmark_results.json`,
and `screenshots/*.txt`.

---

## 1. Merge Sort: parcel prioritisation (`algorithms/sorting.py`)

**Sort key:** `(deadline, priority, id)`, ascending. The earliest deadline comes first.
Parcels with the same deadline are ordered by priority (1 before 5), and the id makes the
order fully deterministic.

```
merge_sort(A):
    if |A| <= 1: return A
    mid = |A| / 2
    L = merge_sort(A[0..mid-1]);  R = merge_sort(A[mid..])
    return merge(L, R)            # take from L when keys are equal -> stable
```

The implementation computes each key **once** ("decorate-sort-undecorate"), so the key
function is not called O(n log n) times.

**Before and after sorting (sample data):**

| Before (file order) | After Merge Sort |
|---|---|
| P01 (4 h, pr 1), P02 (6 h, pr 2), P03 (8 h, pr 3), P04 (3 h, pr 1), P05 (24 h, pr 4), P06 (5 h, pr 2), P07 (48 h, pr 5), P08 (12 h, pr 3), P09 (10 h, pr 2), P10 (6 h, pr 1), P11 (30 h, pr 4), P12 (2 h, pr 1) | P12 (2 h), P04 (3 h), P01 (4 h), P06 (5 h), **P10 (6 h, pr 1), P02 (6 h, pr 2)**, P03 (8 h), P09 (10 h), P08 (12 h), P05 (24 h), P11 (30 h), P07 (48 h) |

P10 and P02 have the same deadline, so priority breaks the tie. Menu option 2 also checks
that Quick Sort and Insertion Sort give exactly the same order.

| | Best | Average | Worst | Extra space | Stable |
|---|---|---|---|---|---|
| **Merge Sort** | O(n log n) | O(n log n) | O(n log n) | O(n) | Yes |
| Quick Sort (random pivot) | O(n log n) | O(n log n) expected | O(n^2) | O(n) here (new lists) | Yes in this version |
| Insertion Sort | O(n) | O(n^2) | O(n^2) | O(1) (O(n) here for keys) | Yes |

---

## 2. 0/1 Knapsack with Dynamic Programming (`algorithms/knapsack.py`)

**State:** `dp[i][c]` = the best total value using only the first *i* parcels with a box of
capacity *c*.

```
dp[0][c] = 0
dp[i][c] = dp[i-1][c]                                   if w_i > c
         = max(dp[i-1][c], dp[i-1][c - w_i] + v_i)      otherwise
answer   = dp[n][W]
backtrack: for i = n..1: if dp[i][c] != dp[i-1][c]: take parcel i; c -= w_i
```

**Why DP is needed and greedy is not enough:** in the sample, a greedy rule such as "take
the most urgent first" or "take the highest value first" would load P04 + P01 + P06 + P10
(20 kg, value 268). The DP finds P04, P01, P06, P03, P08 and P11, which weigh **19 kg and
score 308**. That is 40 points more. The table's last row shows dp[11][20] = 308 (see
`screenshots/01_complete_plan_sample.txt`).

**DP table extract (sample, capacity 20):**

```
Item          c=0 ... c=4  c=5  c=6 ... c=9 ... c=11 ... c=17 ... c=20
(none)          0       0    0    0       0        0        0        0
P04 w5 v71      0       0   71   71      71       71       71       71
P01 w4 v70      0      70   71   71     141      141      141      141
P06 w2 v59      0      70   71  129     141      200      200      200
P10 w9 v68      0      70   71  129     141      200      200      268
...
P11 w2 v20      0      79  105  129     175      200      288      308
P07 w7 v10      0      79  105  129     175      200      288      308   <- dp[11][20], the answer
```

| | Time | Space |
|---|---|---|
| Full table plus backtracking | O(n * W) | O(n * W) |
| 1-D optimisation (value only) | O(n * W) | **O(W)** |

O(nW) is **pseudo-polynomial**. It grows with the *numeric value* of W, not with the number of
bits needed to write W. Measured: doubling W from 1000 to 2000 doubles the time (19.2 ms to
41.3 ms), and 10 times more parcels gives about 10 times the time (4.3 ms to 44.3 ms).

---

## 3. Dijkstra's Algorithm: shortest paths (`algorithms/dijkstra.py`)

```
dist[all] = inf; dist[s] = 0; heap = [(0, s)]
while heap:
    (d, u) = pop_min(heap)
    if u visited: continue            # stale entry
    mark u visited
    for (v, w) in adj[u]:
        if d + w < dist[v]:           # relaxation
            dist[v] = d + w; prev[v] = u; push(heap, (dist[v], v))
```

**Hand trace from Depot on the sample graph** (the order in which nodes leave the heap):

| Pop | dist | Updates |
|---|---|---|
| Depot | 0 | Market 3.5, Station 4.5 |
| Market | 3.5 | School 7.3, TechPark 10.0 (Station stays 4.5 < 6.7) |
| Station | 4.5 | Library 8.0, Hospital 9.1 (School stays 7.3 < 8.7) |
| School | 7.3 | Mall 11.1 (Hospital stays 9.1, TechPark stays 10.0) |
| Library | 8.0 | (no improvement) |
| Hospital | 9.1 | Stadium 12.9 (Mall stays 11.1 < 12.4) |
| TechPark | 10.0 | Airport 14.2 |
| Mall | 11.1 | Riverside 14.8 |
| Stadium, Airport, Riverside | 12.9, 14.2, 14.8 | (no improvement) |
| Hilltop | inf | never reached: **unreachable** |

The program prints exactly these distances (`screenshots/03_menu_dijkstra_tsp.txt`). The
test suite also compares Dijkstra with an independent Bellman-Ford implementation on 40
random graphs.

The planner runs Dijkstra from the depot and from each of the *k* stops. That gives the
k x k distance matrix the TSP step needs: **O(k (V + E) log V)**.

| | Time | Space |
|---|---|---|
| Dijkstra with a binary heap | O((V + E) log V) | O(V) (+ heap O(E)) |

Measured on sparse road graphs (E is about 2V): 100 to 1000 nodes took 0.150 ms to 1.369 ms
(9.1 times), and 1000 to 2000 nodes took 1.369 ms to 2.836 ms (2.1 times). Both are close to
linear, as O((V+E) log V) predicts when E grows in proportion to V.

---

## 4. Nearest Neighbour TSP: overall route (`algorithms/tsp.py`)

```
route = [depot]; current = depot; unvisited = stops
while unvisited:
    next = the unvisited stop with the smallest dist[current][next]   # greedy choice
    append next; current = next
append depot                                                           # close the tour
```

**Trace (sample, stops = Mall, Hospital, School, Library, Riverside):**

| At | Candidates (km) | Choose |
|---|---|---|
| Depot | School 7.3, Library 8.0, Hospital 9.1, Mall 11.1, Riverside 14.8 | School |
| School | Mall 3.8, Hospital 4.2, Riverside 7.5, Library 7.7 | Mall |
| Mall | Hospital 3.3, Riverside 3.7, Library 7.4 | Hospital |
| Hospital | Library 4.1, Riverside 7.0 | Library |
| Library | Riverside 11.1 | Riverside |
| Riverside | return to Depot 14.8 | Depot |

Total = 7.3 + 3.8 + 3.3 + 4.1 + 11.1 + 14.8 = **44.4 km**.

**Why this is not optimal:** at Mall the greedy rule picked Hospital (3.3 km) over Riverside
(3.7 km). Saving 0.4 km there left Riverside stranded at the far edge of the map, so it cost
11.1 + 14.8 km later. The brute-force optimum, `Depot -> School -> Mall -> Riverside ->
Hospital -> Library -> Depot`, is **33.9 km**. That makes NN 31% longer on this instance.
With capacity 35 kg (`screenshots/06_capacity_override.txt`), NN *did* find the optimal
38.5 km tour. NN is a heuristic: sometimes its tour is optimal, often it is not, and it
never guarantees optimality.

| | Time | Space | Optimal? |
|---|---|---|---|
| Nearest Neighbour | O(k^2) | O(k) | **No**, approximation |
| Brute force (verification only) | O(k! * k) | O(k) | Yes |

Measured: 4 times more stops (100 to 400) gave 15.5 times the time (0.639 ms to 9.922 ms),
close to the 16 times that a quadratic algorithm predicts. Brute force went from 70 ms
(8 stops) to 666 ms (9 stops), about 9 times, which matches k!. Over 110 random instances
with 3 to 9 stops, NN tours were on average **1.3% to 8.4% longer** than optimal, and in the
worst case 27.1% longer.

---

## 5. Whole-pipeline complexity

With n parcels, capacity W, k stops, and a graph with V nodes and E edges:

```
T = O(n log n)              sort
  + O((V+E) log V)          reachability check (Dijkstra from the depot)
  + O(n W)                  knapsack
  + O(k (V+E) log V)        Dijkstra from each stop
  + O(k^2)                  Nearest Neighbour
Space = O(n W + k V + V + E)
```

---

## 6. Phase 4: performance results and interpretation

All tables: `performance/results/runtime_tables.md`. Charts: `performance/charts/`.

### 6.1 Sorting (charts/sorting_comparison.png)

| n | Merge | Quick (random pivot) | Quick (middle pivot) | Insertion | Insertion, pre-sorted | built-in `sorted()` |
|---:|---:|---:|---:|---:|---:|---:|
| 1,000 | 2.03 ms | 2.54 | 3.77 | 26.58 | 0.27 | 0.30 |
| 10,000 | 27.18 ms | 36.72 | 219.43 | not run | 3.46 | 3.67 |

* For 10 times more parcels, Merge Sort took 13.4 times longer. That matches n log n:
  10 x log(10000)/log(1000) = 13.3.
* Insertion Sort took 18 times longer when n grew 4 times (500 to 2000). That is quadratic.
  On already-sorted input it is linear and very fast, which is its best case.
* **A real finding during testing:** the first Quick Sort used the *middle* element as the
  pivot. On our parcel data the recursion went 286 levels deep at n = 10,000 (the ideal is
  about 14), so Quick Sort became 8 times slower than Merge Sort. A **random pivot** fixed this.
  This is exactly why Merge Sort, whose worst case is guaranteed, was chosen for the planner.
* Python's built-in `sorted()` (Timsort, written in C) is about 7 times faster than our pure-Python
  Merge Sort. Most of the difference is the cost of the Python interpreter, not the algorithm.

### 6.2 Knapsack (charts/knapsack_scaling.png)

Time grows linearly in both n and W, as O(nW) predicts. The 1-D version is about 1.5 times
faster and uses O(W) memory instead of O(nW). It cannot list the chosen parcels without
extra bookkeeping, so the planner uses the full table.

### 6.3 Dijkstra and TSP (charts/dijkstra_scaling.png, charts/tsp_comparison.png)

Dijkstra grows almost linearly on sparse graphs. NN grows quadratically but stays tiny
(10 ms for 400 stops). Brute force becomes impractical after about 10 stops.

### 6.4 End-to-end (charts/end_to_end_breakdown.png)

| Dataset | Parcels | Locations | Selected | Stops | Route | Sort | Knapsack | Dijkstra | NN | **Total** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| small | 10 | 8 | 5 | 3 | 305.6 km | 0.012 ms | 0.026 | 0.048 | 0.010 | **0.12 ms** |
| medium | 100 | 60 | 27 | 23 | 610.5 km | 0.159 | 0.800 | 1.799 | 0.076 | **3.2 ms** |
| large | 1000 | 300 | 194 | 139 | 1605.9 km | 2.022 | 43.0 | 60.6 | 1.807 | **110 ms** |

**Observations.** Dijkstra (run once per stop) and the knapsack together take 82% of the
time for the medium dataset and 94% for the large one (where the knapsack table has
n x W = 500,000 cells). For the large dataset, sorting and NN together take less than 4%. Even the large case (1000 parcels, 300 locations) is planned in about 0.1
seconds.

### 6.5 Optimisation suggestions (future work)

1. **Dijkstra once per stop costs O(k (V+E) log V).** Stop Dijkstra early once all stops are
   settled, use A* with straight-line distance as the heuristic, or precompute all-pairs
   distances for a fixed city map and cache them between runs.
2. **Knapsack O(nW).** Use the 1-D array plus a compact "taken" bitset to save memory. Scale
   weights (for example, round to 0.5 kg) to shrink W. Use NumPy to vectorise each row.
   Use branch-and-bound when W is very large.
3. **Better tours.** Improve the NN tour with **2-opt** or Or-opt local search, which
   typically removes most of the gap to optimal. Use Held-Karp DP (O(k^2 2^k)) for up to
   about 15 stops. Christofides gives a proven 1.5 approximation on metric graphs.
4. **Deadlines.** The medium dataset shows 12 late parcels (`screenshots/05_medium_dataset_plan.txt`):
   the tour minimises distance, not lateness. A TSP with time windows, or "earliest
   deadline as a tie-breaker", would address this.
5. **Engineering.** Use the built-in `sorted()` (Timsort, written in C) in production,
   multiple vans (vehicle routing), and a compiled language or PyPy for big instances.
