"""Delivery graph management and route building (Phase 3).

delivery_graph.json format
    {
      "depot": "Depot",
      "directed": false,
      "nodes": {"Depot": {"x": 0, "y": 0}, "Mall": {"x": 3, "y": 4}, ...},
      "edges": [["Depot", "Mall", 5.0], ...]          # [from, to, km]
    }
The graph is stored as an adjacency list  {node: {neighbour: km}}  because
road networks are sparse (each place connects to only a few others), so an
adjacency list uses O(V + E) memory instead of O(V^2) for a matrix, and
Dijkstra only needs to iterate over a node's real neighbours.
"""

import json
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from algorithms.dijkstra import dijkstra, reconstruct_path
from algorithms.tsp import nearest_neighbor_tsp
from modules.parcel_manager import DataError


@dataclass
class DeliveryGraph:
    depot: str
    adjacency: Dict[str, Dict[str, float]]
    coordinates: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    directed: bool = False

    @property
    def nodes(self) -> List[str]:
        return sorted(self.adjacency)

    @property
    def edge_count(self) -> int:
        total = sum(len(n) for n in self.adjacency.values())
        return total if self.directed else total // 2

    def has_node(self, name: str) -> bool:
        return name in self.adjacency


def build_graph(data: Dict) -> DeliveryGraph:
    """Validate a graph dictionary and build a DeliveryGraph."""
    if not isinstance(data, dict):
        raise DataError("graph data must be a JSON object")
    nodes = data.get("nodes")
    edges = data.get("edges", [])
    depot = data.get("depot")
    directed = bool(data.get("directed", False))
    if not isinstance(nodes, dict) or not nodes:
        raise DataError("graph must define a non-empty 'nodes' object")
    if depot not in nodes:
        raise DataError(f"depot {depot!r} is not one of the graph nodes")

    adjacency: Dict[str, Dict[str, float]] = {name: {} for name in nodes}
    coordinates = {}
    for name, info in nodes.items():
        if isinstance(info, dict) and "x" in info and "y" in info:
            coordinates[name] = (float(info["x"]), float(info["y"]))

    for edge in edges:
        if not isinstance(edge, (list, tuple)) or len(edge) != 3:
            raise DataError(f"edge {edge!r} must be [from, to, distance]")
        a, b, km = edge
        if a not in adjacency or b not in adjacency:
            raise DataError(f"edge {edge!r} uses an unknown node")
        if not isinstance(km, (int, float)) or isinstance(km, bool) or km < 0 or math.isnan(km):
            raise DataError(f"edge {edge!r} must have a non-negative distance")
        if a == b:
            continue                                   # ignore self-loops
        # Keep the shortest edge if the same road is listed twice.
        adjacency[a][b] = min(km, adjacency[a].get(b, math.inf))
        if not directed:
            adjacency[b][a] = min(km, adjacency[b].get(a, math.inf))
    return DeliveryGraph(depot, adjacency, coordinates, directed)


def load_graph_file(path: str) -> DeliveryGraph:
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        raise DataError(f"graph file not found: {path}") from None
    except json.JSONDecodeError as error:
        raise DataError(f"graph file is not valid JSON: {error}") from None
    return build_graph(data)


# --------------------------------------------------------------------------
# Shortest paths between stops (Dijkstra) and the overall tour (TSP)
# --------------------------------------------------------------------------
@dataclass
class ShortestPathTable:
    """Dijkstra results from each stop: distances and predecessor maps."""
    distances: Dict[str, Dict[str, float]]
    previous: Dict[str, Dict[str, Optional[str]]]

    def path(self, source: str, target: str) -> List[str]:
        return reconstruct_path(self.previous[source], source, target)


def compute_shortest_paths(graph: DeliveryGraph, stops: Sequence[str]) -> ShortestPathTable:
    """Run Dijkstra once from every stop (depot included).

    This gives the "metric closure": the true road distance between every
    pair of stops, which the TSP heuristic then uses.
    """
    distances, previous = {}, {}
    for stop in dict.fromkeys([graph.depot, *stops]):
        distances[stop], previous[stop] = dijkstra(graph.adjacency, stop)
    return ShortestPathTable(distances, previous)


def split_reachable(graph: DeliveryGraph, destinations: Sequence[str]) -> Tuple[List[str], List[str]]:
    """Separate destinations into (reachable round-trip from depot, not)."""
    from_depot, _ = dijkstra(graph.adjacency, graph.depot)
    reachable, unreachable = [], []
    for dest in dict.fromkeys(destinations):
        if not graph.has_node(dest) or math.isinf(from_depot.get(dest, math.inf)):
            unreachable.append(dest)
            continue
        if graph.directed:                      # must also be able to come back
            back, _ = dijkstra(graph.adjacency, dest)
            if math.isinf(back[graph.depot]):
                unreachable.append(dest)
                continue
        reachable.append(dest)
    return reachable, unreachable


@dataclass
class RoutePlan:
    stop_order: List[str]                 # TSP order of stops (depot ... depot)
    total_distance: float
    legs: List[Tuple[str, str, float, List[str]]]   # (from, to, km, road path)
    full_path: List[str]                  # every node driven through


def plan_route(graph: DeliveryGraph, stops: Sequence[str],
               paths: Optional[ShortestPathTable] = None) -> RoutePlan:
    """Nearest-Neighbour tour over the stops, expanded into road paths."""
    paths = paths or compute_shortest_paths(graph, stops)
    order, total = nearest_neighbor_tsp(paths.distances, graph.depot, stops)
    legs, full_path = [], [graph.depot]
    for a, b in zip(order, order[1:]):
        road = paths.path(a, b)
        legs.append((a, b, paths.distances[a][b], road))
        full_path.extend(road[1:])
    return RoutePlan(order, total, legs, full_path)


# --------------------------------------------------------------------------
# Display and visualisation
# --------------------------------------------------------------------------
def format_graph(graph: DeliveryGraph) -> str:
    lines = [f"Depot: {graph.depot}   Nodes: {len(graph.adjacency)}   "
             f"Roads: {graph.edge_count}   ({'directed' if graph.directed else 'undirected'})",
             "Adjacency list (neighbour: km):"]
    for node in graph.nodes:
        neighbours = ", ".join(f"{n}: {d:g}" for n, d in sorted(graph.adjacency[node].items()))
        lines.append(f"  {node:<12} -> {neighbours or '(no roads - isolated)'}")
    return "\n".join(lines)


def format_km(value: float) -> str:
    return "unreachable" if math.isinf(value) else f"{value:.1f} km"


def plot_route(graph: DeliveryGraph, plan: RoutePlan, output_file: str,
               title: str = "Delivery route (Nearest Neighbour TSP)") -> Optional[str]:
    """Save a PNG map of the graph with the planned route drawn on it."""
    if not graph.coordinates:
        return None
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(12, 7.5))
    xy = graph.coordinates
    # All roads in light grey.
    for a, neighbours in graph.adjacency.items():
        for b, km in neighbours.items():
            if a < b or graph.directed:
                ax.plot([xy[a][0], xy[b][0]], [xy[a][1], xy[b][1]], color="#cfcfcf", lw=1, zorder=1)
                mx, my = (xy[a][0] + xy[b][0]) / 2, (xy[a][1] + xy[b][1]) / 2
                ax.text(mx, my, f"{km:g}", fontsize=7, color="#999999", ha="center", va="center")
    # The route, leg by leg, with arrows. A road can be driven more than once
    # (e.g. out and back), so each leg gets its own colour and a small sideways
    # offset - otherwise later legs would hide earlier ones.
    leg_colors = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300",
                  "#6250d6", "#e34948"]
    span = max(1.0, max(max(abs(x), abs(y)) for x, y in xy.values()))
    for leg_no, (a_stop, b_stop, km, road) in enumerate(plan.legs):
        color = leg_colors[leg_no] if len(plan.legs) <= len(leg_colors) else "#2a78d6"
        shift = 0.012 * span * ((leg_no % 3) - 1)
        for a, b in zip(road, road[1:]):
            (x1, y1), (x2, y2) = xy[a], xy[b]
            length = math.hypot(x2 - x1, y2 - y1) or 1.0
            nx, ny = -(y2 - y1) / length * shift, (x2 - x1) / length * shift
            ax.annotate("", xy=(x2 + nx, y2 + ny), xytext=(x1 + nx, y1 + ny),
                        arrowprops=dict(arrowstyle="-|>", color=color, lw=2,
                                        shrinkA=6, shrinkB=9), zorder=2)
        if len(plan.legs) <= len(leg_colors):
            ax.plot([], [], color=color, lw=2, label=f"Leg {leg_no + 1}: {a_stop} -> {b_stop} ({km:.1f} km)")
    if plan.legs and len(plan.legs) <= len(leg_colors):
        ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=8, frameon=False,
                  title="Legs in driving order", title_fontsize=9)
    stops = set(plan.stop_order)
    for name, (x, y) in xy.items():
        if name == graph.depot:
            ax.scatter(x, y, s=260, marker="s", color="#d62728", zorder=3)
        elif name in stops:
            ax.scatter(x, y, s=180, color="#2ca02c", zorder=3)
        else:
            ax.scatter(x, y, s=80, color="#7f7f7f", zorder=3)
        ax.text(x, y + 0.35, name, fontsize=9, ha="center", va="bottom", zorder=4)
    for visit_no, name in enumerate(plan.stop_order[1:-1], start=1):
        x, y = xy[name]
        ax.text(x, y, str(visit_no), fontsize=8, color="white", ha="center", va="center",
                fontweight="bold", zorder=5)
    ax.set_title(f"{title}  -  total distance {plan.total_distance:.1f} km\n"
                 f"red square = depot, green = delivery stop (number = visit order), "
                 f"grey = other location, small numbers = road km", fontsize=10)
    ax.margins(0.08)
    ax.set_xlabel("x (km)")
    ax.set_ylabel("y (km)")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(output_file, dpi=130)
    plt.close(fig)
    return output_file
