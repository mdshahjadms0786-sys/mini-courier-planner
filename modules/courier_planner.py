"""The integrated courier-planning pipeline (Phases 1-3 working together).

    parcels ──► [Merge Sort] ──► prioritised list
                                      │
    graph ──► [Dijkstra from depot] ──┤  drop parcels whose destination is
                                      │  unknown / unreachable
                                      ▼
                 [0/1 Knapsack DP] ──► parcels loaded in the van
                                      │ distinct destinations = stops
                                      ▼
                 [Dijkstra from every stop] ──► stop-to-stop distance matrix
                                      ▼
                 [Nearest Neighbour TSP] ──► visiting order + total km
                                      ▼
                 ETA per stop, deadline check, summary

Each step is timed with time.perf_counter() so the planner itself reports
how long every algorithm took.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from algorithms.knapsack import KnapsackResult, format_dp_table
from algorithms.tsp import brute_force_tsp
from modules.parcel_manager import (Parcel, format_parcel_table, select_parcels,
                                    sort_parcels)
from modules.route_manager import (DeliveryGraph, RoutePlan, ShortestPathTable,
                                   compute_shortest_paths, format_km, plan_route,
                                   split_reachable)

DEFAULT_SPEED_KMH = 30.0      # average city van speed used for ETAs
OPTIMAL_CHECK_LIMIT = 8       # brute-force the exact tour only up to 8 stops


@dataclass
class PlanResult:
    capacity: int
    sort_algorithm: str
    all_parcels: List[Parcel]
    sorted_parcels: List[Parcel]
    undeliverable: List[Parcel]
    selected: List[Parcel]
    left_behind: List[Parcel]
    knapsack: KnapsackResult
    stops: List[str]
    paths: ShortestPathTable
    route: RoutePlan
    eta_hours: Dict[str, float]                 # stop -> arrival time (h)
    late_parcels: List[Tuple[Parcel, float]]    # (parcel, eta) eta > deadline
    speed_kmh: float
    optimal_route: Optional[List[str]] = None   # exact tour (small inputs only)
    optimal_distance: Optional[float] = None
    timings: Dict[str, float] = field(default_factory=dict)   # seconds


class CourierPlanner:
    def __init__(self, parcels: Sequence[Parcel], capacity: int, graph: DeliveryGraph,
                 sort_algorithm: str = "Merge Sort", speed_kmh: float = DEFAULT_SPEED_KMH):
        if capacity < 0:
            raise ValueError("capacity cannot be negative")
        if speed_kmh <= 0:
            raise ValueError("speed must be positive")
        self.parcels = list(parcels)
        self.capacity = capacity
        self.graph = graph
        self.sort_algorithm = sort_algorithm
        self.speed_kmh = speed_kmh

    def run(self, keep_dp_table: bool = True) -> PlanResult:
        timings = {}
        start_total = time.perf_counter()

        # Step 3: prioritise parcels.
        t = time.perf_counter()
        sorted_parcels = sort_parcels(self.parcels, self.sort_algorithm)
        timings["Sorting"] = time.perf_counter() - t

        # Remove parcels that cannot be delivered (unknown / unreachable place)
        # BEFORE packing, so the van never carries an undeliverable parcel.
        t = time.perf_counter()
        reachable, _ = split_reachable(self.graph, [p.destination for p in sorted_parcels])
        reachable_set = set(reachable)
        deliverable = [p for p in sorted_parcels if p.destination in reachable_set]
        undeliverable = [p for p in sorted_parcels if p.destination not in reachable_set]
        timings["Reachability check"] = time.perf_counter() - t

        # Step 4: 0/1 knapsack.
        t = time.perf_counter()
        selected, knap = select_parcels(deliverable, self.capacity, keep_table=keep_dp_table)
        timings["Knapsack DP"] = time.perf_counter() - t
        selected_ids = {p.id for p in selected}
        left_behind = [p for p in deliverable if p.id not in selected_ids]

        # Step 5-7: destinations and Dijkstra shortest paths between them.
        stops = list(dict.fromkeys(p.destination for p in selected if p.destination != self.graph.depot))
        t = time.perf_counter()
        paths = compute_shortest_paths(self.graph, stops)
        timings["Dijkstra"] = time.perf_counter() - t

        # Step 8-9: Nearest-Neighbour tour and total distance.
        t = time.perf_counter()
        route = plan_route(self.graph, stops, paths)
        timings["TSP (Nearest Neighbour)"] = time.perf_counter() - t

        eta = self._arrival_times(route)
        late = [(p, eta.get(p.destination, 0.0)) for p in selected
                if eta.get(p.destination, 0.0) > p.deadline]

        timings["Total"] = time.perf_counter() - start_total
        result = PlanResult(self.capacity, self.sort_algorithm, self.parcels, sorted_parcels,
                            undeliverable, selected, left_behind, knap, stops, paths, route,
                            eta, late, self.speed_kmh, timings=timings)

        # For small inputs, also compute the EXACT best tour (brute force,
        # O(n!)) purely to show how close the heuristic got. Not part of the
        # timed pipeline.
        if 0 < len(stops) <= OPTIMAL_CHECK_LIMIT:
            result.optimal_route, result.optimal_distance = brute_force_tsp(
                paths.distances, self.graph.depot, stops)
        return result

    def _arrival_times(self, route: RoutePlan) -> Dict[str, float]:
        """Hours after dispatch at which each stop is first reached."""
        eta, driven = {self.graph.depot: 0.0}, 0.0
        for _, b, km, _ in route.legs:
            driven += km
            eta.setdefault(b, driven / self.speed_kmh)
        return eta


# --------------------------------------------------------------------------
# Text report of a plan
# --------------------------------------------------------------------------
def format_packing_plan(result: PlanResult, show_dp_table: bool = True) -> str:
    k = result.knapsack
    lines = [f"Vehicle capacity: {result.capacity} kg",
             f"Parcels considered (deliverable): {len(result.selected) + len(result.left_behind)}"]
    if show_dp_table and k.dp_table:
        # Row i of the table corresponds to the i-th deliverable parcel
        # in priority order (row 0 = no parcels).
        deliverable = [p for p in result.sorted_parcels if p not in result.undeliverable]
        labels = ["(none)"] + [f"{p.id} w{p.weight} v{p.value}" for p in deliverable]
        lines += ["", "DP table  dp[i][c] = best value using the first i parcels with capacity c:",
                  format_dp_table(k.dp_table, labels, max_columns=21)]
    lines += ["", format_parcel_table(result.selected, "SELECTED parcels (packing plan):"),
              f"\nMaximum total value: {k.max_value}",
              f"Total selected weight: {k.total_weight} kg of {result.capacity} kg "
              f"({(k.total_weight / result.capacity * 100) if result.capacity else 0:.1f}% full)"]
    if result.left_behind:
        lines += ["", format_parcel_table(result.left_behind, "Left for the next trip:")]
    if result.undeliverable:
        lines += ["", format_parcel_table(result.undeliverable,
                                          "UNDELIVERABLE (destination unknown or unreachable):")]
    return "\n".join(lines)


def format_shortest_paths(result: PlanResult) -> str:
    depot = result.route.stop_order[0]
    lines = [f"Dijkstra shortest paths from the depot '{depot}' (exact, one source -> one target):"]
    if not result.stops:
        lines.append("  (no delivery stops selected)")
    for stop in result.stops:
        km = result.paths.distances[depot][stop]
        path = " -> ".join(result.paths.path(depot, stop))
        lines.append(f"  {depot} -> {stop:<12} {format_km(km):>10}   via {path}")
    if len(result.stops) > 1 and len(result.stops) <= 12:
        names = [depot, *result.stops]
        width = max(8, max(len(n) for n in names) + 1)
        lines += ["", "Stop-to-stop shortest distance matrix (km) used by the TSP step:",
                  " " * width + "".join(n[:width - 1].rjust(width) for n in names)]
        for a in names:
            lines.append(a[:width - 1].ljust(width) +
                         "".join(f"{result.paths.distances[a][b]:.1f}".rjust(width) for b in names))
    return "\n".join(lines)


def format_route(result: PlanResult) -> str:
    route = result.route
    lines = ["Nearest Neighbour TSP route (APPROXIMATE - a good tour, not guaranteed optimal):",
             "  Visit order: " + " -> ".join(route.stop_order)]
    for n, (a, b, km, road) in enumerate(route.legs, start=1):
        lines.append(f"  Leg {n:>2}: {a:<12} -> {b:<12} {km:6.1f} km   road: {' -> '.join(road)}")
    lines.append(f"  TOTAL ROUTE DISTANCE: {route.total_distance:.1f} km")
    if result.optimal_distance is not None:
        gap = route.total_distance - result.optimal_distance
        pct = gap / result.optimal_distance * 100 if result.optimal_distance else 0.0
        lines += ["", "Check against the EXACT optimum (brute force over all "
                  f"{len(result.stops)}! orders - feasible only for small inputs):",
                  "  Optimal order: " + " -> ".join(result.optimal_route),
                  f"  Optimal distance: {result.optimal_distance:.1f} km   "
                  f"Nearest Neighbour is {gap:.1f} km ({pct:.1f}%) longer"
                  + ("  -> NN found an optimal tour here" if gap < 1e-9 else "")]
    return "\n".join(lines)


def format_summary(result: PlanResult) -> str:
    bar = "=" * 70
    lines = [bar, "COMPLETE COURIER PLAN SUMMARY", bar,
             f"Parcels loaded from file   : {len(result.all_parcels)}",
             f"Sorting algorithm          : {result.sort_algorithm}",
             f"Undeliverable parcels      : {len(result.undeliverable)}",
             f"Vehicle capacity           : {result.capacity} kg",
             f"Parcels selected (DP)      : {len(result.selected)}  "
             f"({result.knapsack.total_weight} kg, value {result.knapsack.max_value})",
             f"Parcels left for next trip : {len(result.left_behind)}",
             f"Delivery stops             : {len(result.stops)}",
             f"Route                      : {' -> '.join(result.route.stop_order)}",
             f"Total route distance       : {result.route.total_distance:.1f} km", "",
             f"Delivery schedule (ETA at {result.speed_kmh:g} km/h average):"]
    for p in result.selected:
        eta = result.eta_hours.get(p.destination, 0.0)
        status = "LATE" if eta > p.deadline else "on time"
        lines.append(f"  {p.id:<6} -> {p.destination:<12} ETA {eta:5.2f} h  deadline {p.deadline:>3} h  {status}")
    if result.late_parcels:
        lines.append(f"  WARNING: {len(result.late_parcels)} parcel(s) would miss the deadline.")
    lines += ["", "Step timings (time.perf_counter):"]
    for step, seconds in result.timings.items():
        lines.append(f"  {step:<26} {seconds * 1000:10.3f} ms")
    lines.append(bar)
    return "\n".join(lines)
