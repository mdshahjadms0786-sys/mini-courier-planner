# Viva Questions with Simple Answers

## A. Sorting

**1. Which sorting algorithm did you use and why?**
Merge Sort. It is O(n log n) in every case, so no input can make it slow. It is also
**stable**, so parcels with equal keys keep their arrival order.

**2. What does "stable" mean? Why does it matter here?**
A stable sort keeps items with equal keys in their original order. If two parcels have
the same deadline and priority, the one that arrived first stays first. That is fair and predictable.

**3. Which part of your merge function makes it stable?**
`if left[i][0] <= right[j][0]`. The `<=` takes the element from the left half on a tie.

**4. What is your sort key?**
`(deadline, priority, id)`. Python compares tuples element by element, so the deadline decides
first, then priority, then id.

**5. Why not Quick Sort?**
Its worst case is O(n^2) and depends on the pivot. We measured this: with a middle pivot,
Quick Sort was 8 times slower than Merge Sort at n = 10,000 because the recursion went 286
levels deep. A random pivot fixes this in practice, but Merge Sort's bound is guaranteed.

**6. When is Insertion Sort a good choice?**
For very small or almost-sorted lists. Its best case is O(n). In our benchmark, Insertion
Sort on pre-sorted input was about as fast as Python's built-in sort.

**7. Why is Python's `sorted()` faster than your Merge Sort?**
`sorted()` is Timsort, written in C. Ours runs in the Python interpreter. Both are O(n log n);
the difference is a constant factor.

## B. Dynamic Programming and 0/1 Knapsack

**8. What is Dynamic Programming?**
A method for problems with **overlapping subproblems** and **optimal substructure**. Each
subproblem is solved once, its answer is stored in a table, and later answers are built from it.

**9. Define the DP state and recurrence.**
`dp[i][c]` is the best value using the first i parcels with capacity c.
`dp[i][c] = max(dp[i-1][c], dp[i-1][c-w_i] + v_i)` if `w_i <= c`, otherwise `dp[i-1][c]`.

**10. Why "0/1"?**
Each parcel is either taken whole (1) or not taken (0). You cannot take part of a parcel.

**11. Why not a greedy algorithm?**
Greedy is optimal only for the *fractional* knapsack. In our sample, greedy loads 20 kg
for 268 points, while the DP finds 19 kg for 308 points.

**12. How do you find which parcels were selected?**
Backtrack from `dp[n][W]`. If `dp[i][c] != dp[i-1][c]`, parcel i was taken; then subtract its
weight from c and continue with row i-1.

**13. Time and space complexity of the knapsack?**
O(nW) time and O(nW) space. The 1-D version needs only O(W) space.

**14. Why is O(nW) called pseudo-polynomial?**
It depends on the *value* of W. If you write W with one more digit, the work grows about
ten times, so it is not polynomial in the input size.

**15. Why must weights be integers?**
Weights are used as column indexes in the DP table. Decimal weights would have to be scaled
first, for example to grams.

**16. What happens when the capacity is 0?**
Every `dp[i][0]` is 0, so nothing is selected and the route is just the depot. This is
tested, and shown in `screenshots/07_zero_capacity.txt`.

## C. Graphs and Dijkstra

**17. How did you represent the graph? Why?**
As an adjacency list, `{node: {neighbour: km}}`. Road networks are sparse, so this uses
O(V+E) memory instead of the O(V^2) a matrix needs.

**18. Explain Dijkstra in one line.**
Repeatedly take the unvisited node with the smallest known distance, mark it final, and
relax its edges.

**19. What is relaxation?**
If `dist[u] + w(u,v) < dist[v]`, update `dist[v]` and set `prev[v] = u`.

**20. Why does Dijkstra fail with negative weights?**
Once a node is marked final, it assumes no shorter path can appear later. A negative edge
could break that assumption. Our code raises an error for negative weights. Bellman-Ford handles them.

**21. Complexity of your Dijkstra?**
O((V+E) log V) with a binary heap (`heapq`).

**22. What are "stale" heap entries?**
When a node gets a shorter distance, we push a new entry instead of updating the old one.
The old entry is skipped later with `if node in visited: continue`.

**23. How do you handle an unreachable location?**
Its distance stays infinity. The planner removes such parcels *before* packing and reports
them as undeliverable (P12 to Hilltop in the sample).

## D. TSP and Nearest Neighbour

**24. What is the TSP?**
Find the shortest tour that visits every stop exactly once and returns to the start. It is NP-hard.

**25. Difference between Dijkstra and the TSP step?**
Dijkstra finds the shortest path between **two** places, and its answer is exact. The TSP
decides the **order** in which to visit **all** places. We use Nearest Neighbour, which is
approximate. Dijkstra supplies the distances that NN uses.

**26. How does Nearest Neighbour work?**
From the current place, go to the closest unvisited stop. Repeat until every stop is visited,
then return to the depot.

**27. Is Nearest Neighbour optimal?**
No. In the sample it gives 44.4 km while the optimum is 33.9 km (31% longer). On random
tests it averaged 1 to 8% longer, and 27% longer in the worst case.

**28. Why not always use brute force?**
It checks k! orders. 9 stops already took 0.67 s, so 15 stops would take years.

**29. How could the route be improved?**
Use 2-opt: reverse any segment of the tour that makes it shorter, and repeat. Held-Karp DP
is exact for about 15 stops. Christofides guarantees a tour at most 1.5 times the optimum.

## E. Complexity, testing, integration and design

**30. Overall complexity of the planner?**
O(n log n + nW + k(V+E) log V + k^2).

**31. Which step is slowest on large input? Why?**
Dijkstra, because it runs once per stop (140 runs). The knapsack is next (500,000 cells).

**32. How did you measure time?**
With `time.perf_counter()`, taking the minimum of 3 to 15 repeats with garbage collection
paused, the same method as `timeit`. Other programs can only slow a run down, so the
fastest run best reflects the algorithm.

**33. How did you check that your algorithms are correct?**
With 36 automated tests. They compare the sorts against `sorted()`, the knapsack against
brute force (150 random cases), and Dijkstra against Bellman-Ford (40 random graphs). They
also check that NN is never shorter than brute force, test edge cases, and run the full
planner on every dataset.

**34. Why are the algorithms in a separate package?**
So that each one is a pure function that can be tested and benchmarked on its own. The
modules layer adds file handling and parcel logic.

**35. Why remove undeliverable parcels before the knapsack?**
Otherwise the DP could fill the van with a parcel that can never be delivered, which wastes capacity.

## F. Code-tracing questions

**T1.** `merge_sort([5, 2, 4, 2])`: what does the final merge combine?
*Answer:* [2, 5] and [2, 4], giving [2, 2, 4, 5]. The first 2 (from the left half) comes first.

**T2.** `knapsack_01([1, 3, 4, 5], [1, 4, 5, 7], 7)`: answer and items?
*Answer:* value 9, items at indices 1 and 2 (weights 3 and 4). This is a unit test.

**T3.** Graph A-B 4, A-C 2, C-B 1, B-D 5, D-E 2, C-D 8, C-E 10. Shortest A to E?
*Answer:* A, C, B, D, E = 2 + 1 + 5 + 2 = **10**. The direct C to E road is 10, so going
through it would cost 12. This is also a unit test.

**T4.** Points D(0,0), x(1,0), y(3,0), z(6,0) on a line. NN tour?
*Answer:* D, x, y, z, D = 1 + 2 + 3 + 6 = 12.

**T5.** In the sample, why is P12 missing from the packing plan even though it is the most urgent parcel?
*Answer:* Its destination, Hilltop, has no roads (distance is infinity), so it is undeliverable.

## G. Practical modification exercises (be ready to do these live)

| Task | Where to change it |
|---|---|
| Sort by priority first, then deadline | `priority_key()` in `modules/parcel_manager.py`: return `(p.priority, p.deadline, p.id)` |
| Use Quick Sort in the planner | `CourierPlanner(..., sort_algorithm="Quick Sort")` |
| Change the van capacity | `python main.py --capacity 35`, or menu option 0 |
| Make the knapsack maximise the number of parcels | `Parcel.value`: return `1` |
| Make roads one-way | Set `"directed": true` in the graph JSON |
| Run on an unseen dataset | `python main.py --parcels my.json --graph mygraph.json --demo` |
| Don't return to the depot | `nearest_neighbor_tsp(..., return_to_start=False)` in `plan_route` |
| Change the average speed for ETAs | `DEFAULT_SPEED_KMH` in `modules/courier_planner.py` |
| Add a new location | Add a node with x/y under `nodes`, and at least one road under `edges` |
| Show the DP table for a different capacity | Menu option 0, enter a capacity, then option 3 |
