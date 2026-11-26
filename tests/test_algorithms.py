"""Automated tests for every algorithm and for the integrated planner.

Run from the project folder:
    python -m unittest discover -s tests -v
"""

import itertools
import json
import math
import os
import random
import sys
import tempfile
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from algorithms.dijkstra import dijkstra, reconstruct_path, shortest_path, validate_graph  # noqa: E402
from algorithms.knapsack import knapsack_01, knapsack_max_value_1d  # noqa: E402
from algorithms.sorting import insertion_sort, merge_sort, quick_sort  # noqa: E402
from algorithms.tsp import brute_force_tsp, nearest_neighbor_tsp, route_length  # noqa: E402
from modules.courier_planner import CourierPlanner  # noqa: E402
from modules.parcel_manager import (DataError, Parcel, load_parcel_file,  # noqa: E402
                                    parse_parcels, priority_key, sort_parcels)
from modules.route_manager import build_graph, load_graph_file, split_reachable  # noqa: E402

SORTS = [merge_sort, quick_sort, insertion_sort]
DATA = os.path.join(PROJECT_ROOT, "data")


# ==========================================================================
# Sorting
# ==========================================================================
class TestSorting(unittest.TestCase):
    def test_empty_and_single(self):
        for sort in SORTS:
            self.assertEqual(sort([]), [])
            self.assertEqual(sort([7]), [7])

    def test_matches_builtin_on_random_data(self):
        rng = random.Random(1)
        for _ in range(50):
            data = [rng.randint(-50, 50) for _ in range(rng.randint(0, 60))]
            for sort in SORTS:
                self.assertEqual(sort(data), sorted(data), sort.__name__)

    def test_sorted_reversed_and_duplicates(self):
        for data in ([1, 2, 3, 4], [4, 3, 2, 1], [5, 5, 5], [2, 1, 2, 1]):
            for sort in SORTS:
                self.assertEqual(sort(data), sorted(data))

    def test_input_not_modified(self):
        data = [3, 1, 2]
        for sort in SORTS:
            sort(data)
            self.assertEqual(data, [3, 1, 2])

    def test_stability_with_key(self):
        records = [("a", 2), ("b", 1), ("c", 2), ("d", 1)]
        expected = [("b", 1), ("d", 1), ("a", 2), ("c", 2)]
        for sort in SORTS:
            self.assertEqual(sort(records, key=lambda r: r[1]), expected, sort.__name__)

    def test_parcel_priority_order(self):
        parcels = [Parcel("A", 1, 3, 10, "X"), Parcel("B", 1, 1, 10, "X"),
                   Parcel("C", 1, 5, 2, "X"), Parcel("D", 1, 1, 10, "X")]
        ordered = [p.id for p in sort_parcels(parcels)]
        # Deadline 2 first; then deadline 10 by priority 1,1,3; B before D by id.
        self.assertEqual(ordered, ["C", "B", "D", "A"])
        self.assertEqual(sort_parcels(parcels), sorted(parcels, key=priority_key))


# ==========================================================================
# 0/1 Knapsack
# ==========================================================================
def brute_force_knapsack(weights, values, capacity):
    best = 0
    for r in range(len(weights) + 1):
        for combo in itertools.combinations(range(len(weights)), r):
            if sum(weights[i] for i in combo) <= capacity:
                best = max(best, sum(values[i] for i in combo))
    return best


class TestKnapsack(unittest.TestCase):
    def test_textbook_example(self):
        result = knapsack_01([1, 3, 4, 5], [1, 4, 5, 7], 7)
        self.assertEqual(result.max_value, 9)
        self.assertEqual(sorted(result.selected_indices), [1, 2])   # weights 3 + 4
        self.assertEqual(result.total_weight, 7)

    def test_dp_table_shape_and_answer(self):
        result = knapsack_01([2, 3], [3, 4], 5)
        self.assertEqual(len(result.dp_table), 3)
        self.assertEqual(len(result.dp_table[0]), 6)
        self.assertEqual(result.dp_table[-1][-1], result.max_value)
        self.assertEqual(result.max_value, 7)

    def test_matches_brute_force_and_respects_capacity(self):
        rng = random.Random(7)
        for _ in range(150):
            n = rng.randint(0, 9)
            weights = [rng.randint(1, 12) for _ in range(n)]
            values = [rng.randint(0, 40) for _ in range(n)]
            capacity = rng.randint(0, 30)
            result = knapsack_01(weights, values, capacity)
            self.assertEqual(result.max_value, brute_force_knapsack(weights, values, capacity))
            self.assertLessEqual(result.total_weight, capacity)
            self.assertEqual(sum(values[i] for i in result.selected_indices), result.max_value)
            self.assertEqual(len(set(result.selected_indices)), len(result.selected_indices))
            self.assertEqual(knapsack_max_value_1d(weights, values, capacity), result.max_value)

    def test_zero_capacity(self):
        result = knapsack_01([1, 2], [10, 20], 0)
        self.assertEqual((result.max_value, result.selected_indices, result.total_weight), (0, [], 0))

    def test_no_items(self):
        result = knapsack_01([], [], 10)
        self.assertEqual((result.max_value, result.selected_indices), (0, []))

    def test_every_item_too_heavy(self):
        self.assertEqual(knapsack_01([11, 12], [5, 6], 10).selected_indices, [])

    def test_all_items_fit(self):
        result = knapsack_01([1, 2, 3], [5, 5, 5], 100)
        self.assertEqual(result.selected_indices, [0, 1, 2])

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            knapsack_01([1, 2], [1], 5)              # length mismatch
        with self.assertRaises(ValueError):
            knapsack_01([1], [1], -1)                # negative capacity
        with self.assertRaises(TypeError):
            knapsack_01([1], [1], 2.5)               # non-integer capacity
        with self.assertRaises(ValueError):
            knapsack_01([1.5], [1], 5)               # non-integer weight
        with self.assertRaises(ValueError):
            knapsack_01([-1], [1], 5)                # negative weight


# ==========================================================================
# Dijkstra
# ==========================================================================
SAMPLE_GRAPH = {
    "A": {"B": 4, "C": 2},
    "B": {"A": 4, "C": 1, "D": 5},
    "C": {"A": 2, "B": 1, "D": 8, "E": 10},
    "D": {"B": 5, "C": 8, "E": 2},
    "E": {"C": 10, "D": 2},
    "Z": {},                                  # isolated node
}


def bellman_ford(graph, source):
    """Independent reference implementation used to verify Dijkstra."""
    nodes = set(graph) | {n for nb in graph.values() for n in nb}
    dist = {n: math.inf for n in nodes}
    dist[source] = 0
    for _ in range(len(nodes) - 1):
        for u, neighbours in graph.items():
            for v, w in neighbours.items():
                if dist[u] + w < dist[v]:
                    dist[v] = dist[u] + w
    return dist


class TestDijkstra(unittest.TestCase):
    def test_known_distances(self):
        dist, prev = dijkstra(SAMPLE_GRAPH, "A")
        self.assertEqual(dist, {"A": 0, "B": 3, "C": 2, "D": 8, "E": 10, "Z": math.inf})
        self.assertEqual(reconstruct_path(prev, "A", "E"), ["A", "C", "B", "D", "E"])

    def test_path_length_equals_distance(self):
        dist, prev = dijkstra(SAMPLE_GRAPH, "A")
        for target in "BCDE":
            path = reconstruct_path(prev, "A", target)
            self.assertAlmostEqual(sum(SAMPLE_GRAPH[a][b] for a, b in zip(path, path[1:])), dist[target])

    def test_unreachable_node(self):
        distance, path = shortest_path(SAMPLE_GRAPH, "A", "Z")
        self.assertTrue(math.isinf(distance))
        self.assertEqual(path, [])

    def test_source_to_itself(self):
        self.assertEqual(shortest_path(SAMPLE_GRAPH, "B", "B"), (0, ["B"]))

    def test_matches_bellman_ford_on_random_graphs(self):
        rng = random.Random(3)
        for _ in range(40):
            n = rng.randint(2, 25)
            graph = {i: {} for i in range(n)}
            for _ in range(rng.randint(0, n * 3)):
                a, b = rng.randrange(n), rng.randrange(n)
                if a != b:
                    graph[a][b] = rng.randint(0, 20)
            dist, _ = dijkstra(graph, 0)
            self.assertEqual(dist, bellman_ford(graph, 0))

    def test_invalid_inputs(self):
        with self.assertRaises(KeyError):
            dijkstra(SAMPLE_GRAPH, "missing")
        with self.assertRaises(ValueError):
            dijkstra({"A": {"B": -1}, "B": {}}, "A")
        with self.assertRaises(ValueError):
            validate_graph({"A": {"B": -3}})


# ==========================================================================
# TSP (Nearest Neighbour vs exact brute force)
# ==========================================================================
def matrix_from_points(points):
    return {a: {b: math.dist(pa, pb) for b, pb in points.items()} for a, pa in points.items()}


class TestTSP(unittest.TestCase):
    def test_route_visits_every_stop_once_and_returns(self):
        points = {"D": (0, 0), "a": (1, 0), "b": (2, 0), "c": (2, 2), "d": (0, 2)}
        dist = matrix_from_points(points)
        route, length = nearest_neighbor_tsp(dist, "D", ["a", "b", "c", "d"])
        self.assertEqual(route[0], "D")
        self.assertEqual(route[-1], "D")
        self.assertEqual(sorted(route[1:-1]), ["a", "b", "c", "d"])
        self.assertAlmostEqual(length, route_length(route, dist))

    def test_known_greedy_order(self):
        dist = matrix_from_points({"D": (0, 0), "x": (1, 0), "y": (3, 0), "z": (6, 0)})
        route, length = nearest_neighbor_tsp(dist, "D", ["z", "x", "y"])
        self.assertEqual(route, ["D", "x", "y", "z", "D"])
        self.assertAlmostEqual(length, 12.0)

    def test_nn_never_beats_optimal_and_can_be_worse(self):
        rng = random.Random(11)
        worse_found = False
        for _ in range(60):
            points = {f"s{i}": (rng.uniform(0, 10), rng.uniform(0, 10)) for i in range(7)}
            points["D"] = (rng.uniform(0, 10), rng.uniform(0, 10))
            dist = matrix_from_points(points)
            stops = [s for s in points if s != "D"]
            _, nn_len = nearest_neighbor_tsp(dist, "D", stops)
            _, opt_len = brute_force_tsp(dist, "D", stops)
            self.assertGreaterEqual(nn_len + 1e-9, opt_len)
            worse_found |= nn_len > opt_len + 1e-9
        # Demonstrates that Nearest Neighbour is an APPROXIMATION.
        self.assertTrue(worse_found)

    def test_edge_cases(self):
        dist = {"D": {"D": 0}}
        self.assertEqual(nearest_neighbor_tsp(dist, "D", []), (["D"], 0))
        self.assertEqual(nearest_neighbor_tsp(dist, "D", ["D"]), (["D"], 0))
        two = matrix_from_points({"D": (0, 0), "a": (3, 4)})
        self.assertEqual(nearest_neighbor_tsp(two, "D", ["a", "a"])[0], ["D", "a", "D"])

    def test_unreachable_stop_raises(self):
        dist = {"D": {"D": 0, "a": math.inf}, "a": {"D": math.inf, "a": 0}}
        with self.assertRaises(ValueError):
            nearest_neighbor_tsp(dist, "D", ["a"])


# ==========================================================================
# Data loading / validation
# ==========================================================================
class TestDataValidation(unittest.TestCase):
    def good(self, **changes):
        raw = {"id": "P1", "weight": 3, "priority": 2, "deadline": 5, "destination": "A"}
        raw.update(changes)
        return raw

    def test_valid_parcel(self):
        self.assertEqual(parse_parcels([self.good()])[0].value, 4 * 10 + 19)

    def test_invalid_parcels(self):
        bad_cases = [self.good(weight=0), self.good(weight=2.5), self.good(weight="3"),
                     self.good(priority=0), self.good(priority=6), self.good(deadline=0),
                     self.good(destination=" "), self.good(id="")]
        for raw in bad_cases:
            with self.assertRaises(DataError, msg=str(raw)):
                parse_parcels([raw])
        missing = self.good()
        del missing["weight"]
        with self.assertRaises(DataError):
            parse_parcels([missing])
        with self.assertRaises(DataError):
            parse_parcels([self.good(), self.good()])          # duplicate id

    def test_invalid_graphs(self):
        nodes = {"Depot": {}, "A": {}}
        with self.assertRaises(DataError):
            build_graph({"depot": "X", "nodes": nodes})
        with self.assertRaises(DataError):
            build_graph({"depot": "Depot", "nodes": nodes, "edges": [["Depot", "A", -2]]})
        with self.assertRaises(DataError):
            build_graph({"depot": "Depot", "nodes": nodes, "edges": [["Depot", "Q", 2]]})
        with self.assertRaises(DataError):
            build_graph({"depot": "Depot", "nodes": {}})

    def test_bad_files(self):
        with self.assertRaises(DataError):
            load_parcel_file(os.path.join(DATA, "does_not_exist.json"))
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            handle.write("{ not json")
        try:
            with self.assertRaises(DataError):
                load_parcel_file(handle.name)
            with self.assertRaises(DataError):
                load_graph_file(handle.name)
        finally:
            os.remove(handle.name)


# ==========================================================================
# Integrated planner
# ==========================================================================
class TestCourierPlanner(unittest.TestCase):
    def setUp(self):
        self.parcels, self.capacity = load_parcel_file(os.path.join(DATA, "parcels.json"))
        self.graph = load_graph_file(os.path.join(DATA, "delivery_graph.json"))

    def test_sample_plan(self):
        result = CourierPlanner(self.parcels, self.capacity, self.graph).run()
        self.assertLessEqual(result.knapsack.total_weight, self.capacity)
        self.assertEqual(result.knapsack.total_weight, sum(p.weight for p in result.selected))
        # Hilltop has no roads: its parcel must be reported, never loaded.
        self.assertEqual([p.id for p in result.undeliverable], ["P12"])
        self.assertNotIn("P12", [p.id for p in result.selected])
        # Every selected destination is visited exactly once, depot at both ends.
        route = result.route.stop_order
        self.assertEqual(route[0], "Depot")
        self.assertEqual(route[-1], "Depot")
        self.assertEqual(sorted(route[1:-1]), sorted(set(p.destination for p in result.selected)))
        # Total distance equals the sum of the legs.
        self.assertAlmostEqual(result.route.total_distance, sum(leg[2] for leg in result.route.legs))
        # Each leg's road path really has the length Dijkstra reported.
        for a, b, km, road in result.route.legs:
            self.assertEqual((road[0], road[-1]), (a, b))
            self.assertAlmostEqual(sum(self.graph.adjacency[x][y] for x, y in zip(road, road[1:])), km)
        # Hand-checked values for the sample data (see documentation).
        self.assertEqual(result.knapsack.max_value, 308)
        self.assertAlmostEqual(result.paths.distances["Depot"]["Mall"], 11.1)
        self.assertAlmostEqual(result.route.total_distance, 44.4)
        self.assertAlmostEqual(result.optimal_distance, 33.9)

    def test_zero_capacity(self):
        result = CourierPlanner(self.parcels, 0, self.graph).run()
        self.assertEqual(result.selected, [])
        self.assertEqual(result.route.stop_order, ["Depot"])
        self.assertEqual(result.route.total_distance, 0)

    def test_no_parcels(self):
        result = CourierPlanner([], 20, self.graph).run()
        self.assertEqual((result.selected, result.stops, result.route.total_distance), ([], [], 0))

    def test_unknown_destination(self):
        parcels = [Parcel("X1", 2, 1, 5, "Atlantis"), Parcel("X2", 2, 1, 5, "Mall")]
        result = CourierPlanner(parcels, 10, self.graph).run()
        self.assertEqual([p.id for p in result.undeliverable], ["X1"])
        self.assertEqual(result.route.stop_order, ["Depot", "Mall", "Depot"])

    def test_negative_capacity_rejected(self):
        with self.assertRaises(ValueError):
            CourierPlanner(self.parcels, -5, self.graph)

    def test_directed_graph_one_way_unreachable(self):
        graph = build_graph({"depot": "D", "directed": True, "nodes": {"D": {}, "A": {}},
                             "edges": [["D", "A", 3]]})
        reachable, unreachable = split_reachable(graph, ["A"])
        self.assertEqual((reachable, unreachable), ([], ["A"]))   # cannot return to depot

    def test_generated_datasets_run(self):
        folder = os.path.join(DATA, "test_datasets")
        for size in ("small", "medium", "large"):
            parcels, capacity = load_parcel_file(os.path.join(folder, f"{size}_parcels.json"))
            graph = load_graph_file(os.path.join(folder, f"{size}_graph.json"))
            result = CourierPlanner(parcels, capacity, graph).run(keep_dp_table=False)
            self.assertLessEqual(result.knapsack.total_weight, capacity)
            self.assertEqual(result.undeliverable, [])      # generator makes connected graphs
            self.assertEqual(sorted(result.route.stop_order[1:-1]), sorted(result.stops))


if __name__ == "__main__":
    unittest.main(verbosity=2)
