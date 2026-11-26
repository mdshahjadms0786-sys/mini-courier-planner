# Runtime measurement tables

Generated 2026-11-26 15:31 on Windows 11 / Intel64 Family 6 Model 154 Stepping 4, GenuineIntel, Python 3.14.2. All times are the **minimum of 3-15 repeats, in milliseconds**, measured with `time.perf_counter()`.

## 1. Sorting (parcels by deadline, priority, id)

| n | Merge Sort | Quick Sort (random pivot) | Quick Sort (middle pivot) | Insertion Sort | Insertion Sort (pre-sorted) | Built-in sorted() |
|---:|---:|---:|---:|---:|---:|---:|
| 10 | 0.018 | 0.020 | 0.023 | 0.011 | 0.008 | 0.004 |
| 100 | 0.163 | 0.201 | 0.195 | 0.291 | 0.033 | 0.025 |
| 500 | 0.936 | 1.212 | 1.447 | 6.250 | 0.138 | 0.145 |
| 1000 | 2.031 | 2.541 | 3.772 | 26.582 | 0.266 | 0.302 |
| 2000 | 4.247 | 6.207 | 11.317 | 112.447 | 0.540 | 0.673 |
| 5000 | 12.356 | 16.642 | 58.775 | - | 1.517 | 1.745 |
| 10000 | 27.178 | 36.720 | 219.432 | - | 3.455 | 3.668 |

`-` = not run (O(n^2) would take too long).

## 2a. 0/1 Knapsack - growing n (W = 500 kg)

| n | W | DP cells n*W | Full DP table | 1-D DP (value only) |
|---:|---:|---:|---:|---:|
| 10 | 500 | 5,000 | 0.424 | 0.305 |
| 50 | 500 | 25,000 | 2.167 | 1.531 |
| 100 | 500 | 50,000 | 4.286 | 2.956 |
| 250 | 500 | 125,000 | 10.762 | 7.329 |
| 500 | 500 | 250,000 | 22.172 | 14.651 |
| 1000 | 500 | 500,000 | 44.307 | 29.117 |

## 2b. 0/1 Knapsack - growing capacity W (n = 200)

| n | W | DP cells n*W | Full DP table | 1-D DP (value only) |
|---:|---:|---:|---:|---:|
| 200 | 50 | 10,000 | 0.800 | 0.494 |
| 200 | 100 | 20,000 | 1.612 | 0.981 |
| 200 | 250 | 50,000 | 3.855 | 2.539 |
| 200 | 500 | 100,000 | 8.878 | 5.795 |
| 200 | 1000 | 200,000 | 19.156 | 13.002 |
| 200 | 2000 | 400,000 | 41.326 | 27.081 |

## 3. Dijkstra (single source, binary heap)

| V | E | time |
|---:|---:|---:|
| 10 | 19 | 0.023 |
| 50 | 109 | 0.083 |
| 100 | 215 | 0.150 |
| 250 | 535 | 0.353 |
| 500 | 1045 | 0.689 |
| 1000 | 2099 | 1.369 |
| 2000 | 4177 | 2.836 |

## 4a. Nearest Neighbour TSP - scaling

| stops | time |
|---:|---:|
| 5 | 0.017 |
| 10 | 0.025 |
| 25 | 0.063 |
| 50 | 0.196 |
| 100 | 0.639 |
| 200 | 2.447 |
| 400 | 9.922 |

## 4b. Nearest Neighbour vs exact brute force

| stops | trials | NN time | brute-force time | mean NN/optimal | worst NN/optimal | NN optimal in |
|---:|---:|---:|---:|---:|---:|---:|
| 3 | 20 | 0.004 | 0.009 | 1.013 | 1.096 | 60% |
| 4 | 20 | 0.006 | 0.034 | 1.054 | 1.139 | 30% |
| 5 | 20 | 0.007 | 0.173 | 1.049 | 1.271 | 40% |
| 6 | 20 | 0.009 | 1.035 | 1.056 | 1.189 | 30% |
| 7 | 20 | 0.015 | 8.169 | 1.084 | 1.204 | 15% |
| 8 | 5 | 0.022 | 70.367 | 1.027 | 1.084 | 40% |
| 9 | 5 | 0.027 | 665.612 | 1.043 | 1.071 | 0% |

## 5. Complete planner on the test datasets

| dataset | parcels | locations | roads | capacity | selected | stops | route km | Sorting | Reachability check | Knapsack DP | Dijkstra | TSP (Nearest Neighbour) | Total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| small | 10 | 8 | 17 | 20 | 5 | 3 | 305.55 | 0.012 | 0.017 | 0.026 | 0.048 | 0.010 | 0.119 |
| medium | 100 | 60 | 127 | 100 | 27 | 23 | 610.46 | 0.159 | 0.105 | 0.800 | 1.799 | 0.076 | 3.177 |
| large | 1000 | 300 | 609 | 500 | 194 | 139 | 1605.93 | 2.022 | 0.644 | 43.035 | 60.563 | 1.807 | 109.687 |
