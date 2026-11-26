"""Generate reproducible synthetic test datasets (small / medium / large).

Run:  python data/generate_datasets.py

Each dataset is a pair of files in data/test_datasets/:
    <size>_parcels.json   parcels + vehicle capacity
    <size>_graph.json     road network with coordinates

Graph construction (guarantees a connected network):
  1. scatter N locations at random (x, y) points in a square;
  2. connect every location to its 3 nearest neighbours;
  3. connect each location to its nearest earlier location, which forms a
     spanning tree, so every place is reachable from the depot.
  Road length = straight-line distance x a random "road factor" 1.0-1.3.

A fixed random seed makes the files identical every time they are generated.
"""

import json
import math
import os
import random
import sys

SIZES = {
    #          parcels  locations  capacity_kg
    "small":  (10,      8,         20),
    "medium": (100,     60,        100),
    "large":  (1000,    300,       500),
}


def make_graph(num_nodes, rng, area=100.0):
    names = ["Depot"] + [f"L{i:03d}" for i in range(1, num_nodes)]
    coords = {name: (round(rng.uniform(0, area), 2), round(rng.uniform(0, area), 2)) for name in names}

    def euclid(a, b):
        (x1, y1), (x2, y2) = coords[a], coords[b]
        return math.hypot(x1 - x2, y1 - y2)

    edges = {}

    def add(a, b):
        key = tuple(sorted((a, b)))
        if key not in edges:
            edges[key] = round(euclid(a, b) * rng.uniform(1.0, 1.3), 2)

    for i, a in enumerate(names):
        nearest = sorted((n for n in names if n != a), key=lambda n: euclid(a, n))[:3]
        for b in nearest:
            add(a, b)
        if i > 0:                                   # spanning-tree link
            add(a, min(names[:i], key=lambda n: euclid(a, n)))

    return {
        "depot": "Depot",
        "directed": False,
        "nodes": {n: {"x": x, "y": y} for n, (x, y) in coords.items()},
        "edges": [[a, b, km] for (a, b), km in sorted(edges.items())],
    }


def make_parcels(num_parcels, destinations, capacity, rng):
    return {
        "vehicle_capacity_kg": capacity,
        "parcels": [
            {
                "id": f"P{i:04d}",
                "weight": rng.randint(1, 15),
                "priority": rng.randint(1, 5),
                "deadline": rng.choice([2, 4, 6, 8, 12, 24, 48]),
                "destination": rng.choice(destinations),
            }
            for i in range(1, num_parcels + 1)
        ],
    }


def generate_all(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    for size, (num_parcels, num_nodes, capacity) in SIZES.items():
        rng = random.Random(2026 + num_parcels)
        graph = make_graph(num_nodes, rng)
        destinations = [n for n in graph["nodes"] if n != "Depot"]
        parcels = make_parcels(num_parcels, destinations, capacity, rng)
        for suffix, payload in (("parcels", parcels), ("graph", graph)):
            path = os.path.join(output_dir, f"{size}_{suffix}.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=1)
        print(f"{size:<7} {num_parcels:>5} parcels  {num_nodes:>4} locations  "
              f"{len(graph['edges']):>5} roads  capacity {capacity} kg")


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    generate_all(sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "test_datasets"))
