"""Travelling Salesman route planning (Phase 3).

IMPORTANT DISTINCTION
  * Dijkstra (dijkstra.py) answers: "What is the shortest road path between
    TWO locations?"  It is EXACT.
  * The TSP asks: "In which ORDER should the van visit ALL the stops and
    come back to the depot so the whole tour is as short as possible?"
    TSP is NP-hard, so for realistic sizes we use the Nearest Neighbour
    heuristic, which is FAST (O(n^2)) but APPROXIMATE: it does NOT always
    return the globally optimal tour. ``brute_force_tsp`` (exact, O(n!)) is
    included only to measure how far from optimal the heuristic is on small
    inputs.

Both functions work on a distance matrix ``dist[a][b]`` whose entries are
the Dijkstra shortest-path distances between stops (the "metric closure" of
the road graph).
"""

import itertools
import math
from typing import Dict, List, Sequence, Tuple

DistanceMatrix = Dict[str, Dict[str, float]]


def route_length(route: Sequence[str], dist: DistanceMatrix) -> float:
    """Sum of distances between consecutive stops of ``route``."""
    return sum(dist[a][b] for a, b in zip(route, route[1:]))


def nearest_neighbor_tsp(dist: DistanceMatrix, start: str, stops: Sequence[str],
                         return_to_start: bool = True) -> Tuple[List[str], float]:
    """Greedy Nearest Neighbour tour.

    Start at ``start``; repeatedly move to the closest unvisited stop; finally
    return to ``start``. Ties are broken by stop name so the result is
    deterministic.

    Returns (route, total_distance). Raises ValueError if some stop cannot be
    reached (infinite distance) - callers should remove unreachable stops
    first.
    """
    unvisited = [s for s in dict.fromkeys(stops) if s != start]   # unique, no depot
    route = [start]
    current = start
    while unvisited:
        next_stop = min(unvisited, key=lambda s: (dist[current][s], s))
        if math.isinf(dist[current][next_stop]):
            raise ValueError(f"stop {next_stop!r} is unreachable from {current!r}")
        route.append(next_stop)
        unvisited.remove(next_stop)
        current = next_stop
    if return_to_start and len(route) > 1:
        if math.isinf(dist[current][start]):
            raise ValueError(f"cannot return from {current!r} to {start!r}")
        route.append(start)
    return route, route_length(route, dist)


def brute_force_tsp(dist: DistanceMatrix, start: str, stops: Sequence[str],
                    return_to_start: bool = True, max_stops: int = 9) -> Tuple[List[str], float]:
    """Exact TSP by trying every permutation. O(n!) - small inputs only."""
    unique_stops = [s for s in dict.fromkeys(stops) if s != start]
    if len(unique_stops) > max_stops:
        raise ValueError(f"brute force limited to {max_stops} stops (got {len(unique_stops)})")
    if not unique_stops:
        return [start], 0.0
    best_route, best_length = None, math.inf
    for order in itertools.permutations(unique_stops):
        route = [start, *order] + ([start] if return_to_start else [])
        length = route_length(route, dist)
        if length < best_length:
            best_route, best_length = route, length
    return best_route, best_length
