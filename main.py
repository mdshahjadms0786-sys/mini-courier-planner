"""Mini-Courier Planner - command-line application.

Usage
    python main.py                      interactive menu (sample data)
    python main.py --demo               run the complete workflow once, no menu
    python main.py --parcels FILE --graph FILE [--capacity KG] [--demo]
    python main.py --benchmark          run the performance benchmark + charts

The menu lets every algorithm be run on its own; option 7 runs the whole
pipeline end to end.
"""

import argparse
import os
import sys

# Make "algorithms" / "modules" importable however the script is started.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from algorithms.sorting import SORTING_ALGORITHMS                 # noqa: E402
from modules.courier_planner import (CourierPlanner, format_packing_plan,  # noqa: E402
                                     format_route, format_shortest_paths,
                                     format_summary)
from modules.parcel_manager import (DataError, format_parcel_table,  # noqa: E402
                                    load_parcel_file, sort_parcels)
from modules.route_manager import format_graph, load_graph_file, plot_route  # noqa: E402

DEFAULT_PARCELS = os.path.join(PROJECT_ROOT, "data", "parcels.json")
DEFAULT_GRAPH = os.path.join(PROJECT_ROOT, "data", "delivery_graph.json")
SCREENSHOT_DIR = os.path.join(PROJECT_ROOT, "screenshots")

MENU = """
========== MINI COURIER PLANNER ==========
 Data: {parcels} parcels | {nodes} locations | capacity {capacity} kg
------------------------------------------
 1. Display All Parcels
 2. Sort and Prioritize Parcels
 3. Optimize Package Selection (0/1 Knapsack DP)
 4. Display Delivery Graph
 5. Calculate Shortest Paths (Dijkstra)
 6. Generate Delivery Route (Nearest Neighbour TSP)
 7. Display Complete Courier Plan
 8. Run Performance Benchmark
 9. Generate Runtime Charts
10. Exit
 0. Load another dataset / change capacity
=========================================="""


class App:
    def __init__(self, parcels_path, graph_path, capacity=None):
        self.load(parcels_path, graph_path, capacity)

    # ------------------------------------------------------------------ data
    def load(self, parcels_path, graph_path, capacity=None):
        parcels, file_capacity = load_parcel_file(parcels_path)
        graph = load_graph_file(graph_path)
        self.parcels_path, self.graph_path = parcels_path, graph_path
        self.parcels, self.graph = parcels, graph
        self.capacity = file_capacity if capacity is None else capacity
        if self.capacity < 0:
            raise DataError("capacity cannot be negative")
        self._plan = None

    def plan(self):
        """Run (and cache) the full pipeline; menu steps reuse the result."""
        if self._plan is None:
            self._plan = CourierPlanner(self.parcels, self.capacity, self.graph).run()
        return self._plan

    # --------------------------------------------------------------- actions
    def show_parcels(self):
        print(format_parcel_table(self.parcels, "ALL PARCELS (as loaded from file):"))

    def show_sorting(self):
        print(format_parcel_table(self.parcels, "BEFORE sorting (file order):"))
        print()
        ordered = sort_parcels(self.parcels, "Merge Sort")
        print(format_parcel_table(ordered, "AFTER Merge Sort (deadline asc, then priority, then id):"))
        # Cross-check: every sorting algorithm must give the same order.
        same = all(sort_parcels(self.parcels, name) == ordered for name in SORTING_ALGORITHMS)
        print(f"\nCross-check with Quick Sort and Insertion Sort: {'identical order' if same else 'MISMATCH'}")

    def show_packing(self):
        print(format_packing_plan(self.plan()))

    def show_graph(self):
        print(format_graph(self.graph))

    def show_shortest_paths(self):
        print(format_shortest_paths(self.plan()))

    def show_route(self):
        print(format_route(self.plan()))
        self.save_route_map()

    def save_route_map(self):
        result = self.plan()
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        image = plot_route(self.graph, result.route, os.path.join(SCREENSHOT_DIR, "route_map.png"))
        if image:
            print(f"\nRoute map saved to {os.path.relpath(image, PROJECT_ROOT)}")

    def show_complete_plan(self):
        result = self.plan()
        sections = [
            ("STEP 1-2  PARCELS", format_parcel_table(self.parcels)),
            ("STEP 3  PRIORITISED ORDER (Merge Sort)", format_parcel_table(result.sorted_parcels)),
            ("STEP 4  PACKING PLAN (0/1 Knapsack DP)", format_packing_plan(result)),
            ("STEP 5-7  SHORTEST PATHS (Dijkstra)", format_shortest_paths(result)),
            ("STEP 8-9  DELIVERY ROUTE (Nearest Neighbour TSP)", format_route(result)),
        ]
        for title, body in sections:
            print(f"\n----- {title} -----\n{body}")
        print()
        print(format_summary(result))

    def run_benchmark(self, charts=True):
        from performance.benchmarking import run_all
        run_all(make_charts=charts)

    def make_charts(self):
        from performance.benchmarking import charts_from_saved_results
        charts_from_saved_results()

    def change_dataset(self):
        print("Press Enter to keep the current value.")
        p = input(f"Parcel file [{os.path.relpath(self.parcels_path, PROJECT_ROOT)}]: ").strip() or self.parcels_path
        g = input(f"Graph file  [{os.path.relpath(self.graph_path, PROJECT_ROOT)}]: ").strip() or self.graph_path
        c = input("Capacity kg [from file]: ").strip()
        p, g = (x if os.path.isabs(x) else os.path.join(PROJECT_ROOT, x) for x in (p, g))
        capacity = None
        if c:
            if not c.isdigit():
                print("Capacity must be a non-negative whole number - dataset not changed.")
                return
            capacity = int(c)
        try:
            self.load(p, g, capacity)
            print(f"Loaded {len(self.parcels)} parcels, {len(self.graph.adjacency)} locations, "
                  f"capacity {self.capacity} kg.")
        except DataError as error:
            print(f"Could not load dataset: {error}")

    # ------------------------------------------------------------------ menu
    def menu(self):
        actions = {
            "1": self.show_parcels, "2": self.show_sorting, "3": self.show_packing,
            "4": self.show_graph, "5": self.show_shortest_paths, "6": self.show_route,
            "7": self.show_complete_plan, "8": self.run_benchmark, "9": self.make_charts,
            "0": self.change_dataset,
        }
        while True:
            print(MENU.format(parcels=len(self.parcels), nodes=len(self.graph.adjacency),
                              capacity=self.capacity))
            try:
                choice = input("Enter your choice (0-10): ").strip()
            except EOFError:
                print()
                return
            if choice == "10":
                print("Goodbye!")
                return
            action = actions.get(choice)
            if action is None:
                print(f"Invalid choice {choice!r}. Please enter a number from 0 to 10.")
                continue
            print()
            try:
                action()
            except (DataError, ValueError, KeyError) as error:
                print(f"Error: {error}")
            try:
                input("\nPress Enter to return to the menu...")
            except EOFError:
                print()
                return


def main(argv=None):
    parser = argparse.ArgumentParser(description="Mini-Courier Planner (DAA capstone)")
    parser.add_argument("--parcels", default=DEFAULT_PARCELS, help="parcel JSON file")
    parser.add_argument("--graph", default=DEFAULT_GRAPH, help="delivery graph JSON file")
    parser.add_argument("--capacity", type=int, help="override vehicle capacity in kg")
    parser.add_argument("--demo", action="store_true", help="run the full workflow without the menu")
    parser.add_argument("--benchmark", action="store_true", help="run benchmarks and draw charts")
    args = parser.parse_args(argv)

    if args.benchmark:
        from performance.benchmarking import run_all
        run_all(make_charts=True)
        return 0
    try:
        app = App(args.parcels, args.graph, args.capacity)
    except DataError as error:
        print(f"Error: {error}")
        return 1
    if args.demo:
        app.show_complete_plan()
        app.save_route_map()
        return 0
    app.menu()
    return 0


if __name__ == "__main__":
    sys.exit(main())
