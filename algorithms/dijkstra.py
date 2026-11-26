"""Dijkstra's single-source shortest-path algorithm (Phase 3).

Graph format (adjacency list):
    graph = {
        "Depot": {"A": 4, "B": 2},
        "A":     {"Depot": 4, "C": 5},
        ...
    }
Every edge weight is a non-negative distance in km. Dijkstra is correct only
for non-negative weights, so negative weights raise ValueError.

Complexity with a binary heap (heapq): O((V + E) log V) time, O(V) space.
"""

import heapq
import math
from typing import Dict, List, Optional, Tuple

Graph = Dict[str, Dict[str, float]]


def validate_graph(graph: Graph) -> None:
    """Raise ValueError if the graph has a negative or non-numeric weight."""
    for node, neighbours in graph.items():
        for neighbour, weight in neighbours.items():
            if not isinstance(weight, (int, float)) or isinstance(weight, bool):
                raise ValueError(f"edge {node}->{neighbour} has non-numeric weight {weight!r}")
            if weight < 0:
                raise ValueError(f"edge {node}->{neighbour} has negative weight {weight}")


def dijkstra(graph: Graph, source: str) -> Tuple[Dict[str, float], Dict[str, Optional[str]]]:
    """Compute shortest distances from ``source`` to every node.

    Returns (distances, previous):
      distances[v] = length of the shortest path source -> v (math.inf if
                     v is unreachable)
      previous[v]  = node before v on that path (None for source/unreachable)
    """
    if source not in graph:
        raise KeyError(f"source node {source!r} is not in the graph")

    # Include nodes that only appear as edge targets.
    nodes = set(graph)
    for neighbours in graph.values():
        nodes.update(neighbours)

    distances = {node: math.inf for node in nodes}
    previous: Dict[str, Optional[str]] = {node: None for node in nodes}
    distances[source] = 0
    heap = [(0, source)]
    visited = set()

    while heap:
        current_distance, node = heapq.heappop(heap)
        if node in visited:
            continue            # stale heap entry (a shorter one was used)
        visited.add(node)
        for neighbour, weight in graph.get(node, {}).items():
            if weight < 0:
                raise ValueError(f"negative edge weight {node}->{neighbour}")
            new_distance = current_distance + weight
            if new_distance < distances[neighbour]:      # relaxation step
                distances[neighbour] = new_distance
                previous[neighbour] = node
                heapq.heappush(heap, (new_distance, neighbour))
    return distances, previous


def reconstruct_path(previous: Dict[str, Optional[str]], source: str, target: str) -> List[str]:
    """Return the node list source -> target, or [] if target is unreachable."""
    if target not in previous:
        return []
    path = []
    node: Optional[str] = target
    while node is not None:
        path.append(node)
        if node == source:
            break
        node = previous[node]
    path.reverse()
    return path if path and path[0] == source else []


def shortest_path(graph: Graph, source: str, target: str) -> Tuple[float, List[str]]:
    """Convenience wrapper: (distance, path) for one source/target pair."""
    distances, previous = dijkstra(graph, source)
    if target not in distances:
        raise KeyError(f"target node {target!r} is not in the graph")
    return distances[target], reconstruct_path(previous, source, target)
