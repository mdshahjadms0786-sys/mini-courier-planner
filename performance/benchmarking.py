"""Performance testing for Phase 4.

Run:  python performance/benchmarking.py        (or  python main.py --benchmark)

What is measured (all with time.perf_counter, wall-clock seconds):
  1. Sorting       - Merge Sort vs Quick Sort vs Insertion Sort vs Python's
                     built-in sorted() (Timsort, C implementation, reference)
  2. Knapsack DP   - growing number of parcels n (fixed capacity W) and
                     growing capacity W (fixed n); full-table vs 1-D version
  3. Dijkstra      - growing number of locations V (sparse road graphs)
  4. TSP           - Nearest Neighbour for growing number of stops, and
                     NN vs exact brute force (time AND tour quality) for
                     small numbers of stops
  5. End-to-end    - the complete planner on the small / medium / large
                     datasets in data/test_datasets/, broken down by step

Timing method: each measurement is repeated (more repeats for fast calls)
and the MINIMUM is reported: other programs on the computer can only slow a
run down, so the fastest run best reflects the algorithm itself. As in
Python's timeit module, garbage collection is paused during each timed call.
Inputs are generated with a fixed random seed, so runs are reproducible
(the absolute times depend on the computer, the growth trends do not).

Outputs
  performance/results/benchmark_results.json   raw numbers
  performance/results/runtime_tables.md        tables for the report
  performance/charts/*.png                     Matplotlib charts
"""

import gc
import json
import math
import os
import platform
import random
import statistics
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from algorithms.dijkstra import dijkstra                                  # noqa: E402
from algorithms.knapsack import knapsack_01, knapsack_max_value_1d        # noqa: E402
from algorithms.sorting import (insertion_sort, merge_sort, quick_sort,   # noqa: E402
                                quick_sort_middle_pivot)
from algorithms.tsp import brute_force_tsp, nearest_neighbor_tsp          # noqa: E402
from data.generate_datasets import make_graph                             # noqa: E402
from modules.courier_planner import CourierPlanner                        # noqa: E402
from modules.parcel_manager import Parcel, load_parcel_file, priority_key  # noqa: E402
from modules.route_manager import build_graph, load_graph_file            # noqa: E402

RESULTS_DIR = os.path.join(PROJECT_ROOT, "performance", "results")
CHARTS_DIR = os.path.join(PROJECT_ROOT, "performance", "charts")
RESULTS_FILE = os.path.join(RESULTS_DIR, "benchmark_results.json")

# Validated categorical palette, used in this fixed order (never cycled).
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
INK, INK_2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"


# --------------------------------------------------------------------------
# Timing helper
# --------------------------------------------------------------------------
def measure(function, *args, min_repeats=5, max_repeats=15, budget_s=0.4):
    """Best (minimum) wall-clock time in seconds of function(*args) over
    several repeats. Background programs can only make a run SLOWER, never
    faster, so the minimum is the cleanest estimate of the algorithm's own
    cost (this is what the timeit documentation recommends).

    Like Python's timeit module, the garbage collector is switched off
    during each timed call so that random GC pauses do not distort results.
    """
    times = []
    start = time.perf_counter()
    while len(times) < max_repeats:
        gc.collect()
        gc.disable()
        try:
            t = time.perf_counter()
            function(*args)
            times.append(time.perf_counter() - t)
        finally:
            gc.enable()
        if len(times) >= min_repeats and time.perf_counter() - start > budget_s:
            break
    return min(times)


def random_parcels(n, rng):
    return [Parcel(f"P{i}", rng.randint(1, 15), rng.randint(1, 5),
                   rng.choice([2, 4, 6, 8, 12, 24, 48]), "X") for i in range(n)]


def random_distance_matrix(k, rng):
    points = {"Depot": (50.0, 50.0)}
    points.update({f"S{i}": (rng.uniform(0, 100), rng.uniform(0, 100)) for i in range(k)})
    return {a: {b: math.dist(pa, pb) for b, pb in points.items()} for a, pa in points.items()}


def log(message):
    print(message, flush=True)


# --------------------------------------------------------------------------
# Individual benchmarks
# --------------------------------------------------------------------------
def bench_sorting(rng):
    sizes = [10, 100, 500, 1000, 2000, 5000, 10000]
    rows = []
    for n in sizes:
        parcels = random_parcels(n, rng)
        row = {"n": n,
               "Merge Sort": measure(merge_sort, parcels, priority_key),
               "Quick Sort": measure(quick_sort, parcels, priority_key),
               "Quick Sort (middle pivot)": measure(quick_sort_middle_pivot, parcels, priority_key, max_repeats=5),
               "Built-in sorted()": measure(lambda p: sorted(p, key=priority_key), parcels)}
        # Insertion sort is O(n^2): stop at 2000 to keep the run short.
        row["Insertion Sort"] = measure(insertion_sort, parcels, priority_key, min_repeats=3, max_repeats=3) if n <= 2000 else None
        # Best case for insertion sort: already-sorted input is O(n).
        already_sorted = sorted(parcels, key=priority_key)
        row["Insertion Sort (pre-sorted input)"] = measure(insertion_sort, already_sorted, priority_key)
        rows.append(row)
        log(f"  sorting n={n:>6}: merge {row['Merge Sort']*1000:8.2f} ms")
    return rows


def bench_knapsack(rng):
    by_n, by_w = [], []
    capacity = 500
    for n in [10, 50, 100, 250, 500, 1000]:
        w = [rng.randint(1, 15) for _ in range(n)]
        v = [rng.randint(10, 74) for _ in range(n)]
        by_n.append({"n": n, "W": capacity,
                     "Full DP table": measure(knapsack_01, w, v, capacity, max_repeats=5),
                     "1-D DP (value only)": measure(knapsack_max_value_1d, w, v, capacity, max_repeats=5)})
        log(f"  knapsack n={n:>5} W={capacity}: {by_n[-1]['Full DP table']*1000:9.2f} ms")
    n = 200
    w = [rng.randint(1, 15) for _ in range(n)]
    v = [rng.randint(10, 74) for _ in range(n)]
    for capacity in [50, 100, 250, 500, 1000, 2000]:
        by_w.append({"n": n, "W": capacity,
                     "Full DP table": measure(knapsack_01, w, v, capacity, max_repeats=5),
                     "1-D DP (value only)": measure(knapsack_max_value_1d, w, v, capacity, max_repeats=5)})
        log(f"  knapsack n={n} W={capacity:>5}: {by_w[-1]['Full DP table']*1000:9.2f} ms")
    return {"vary_n": by_n, "vary_W": by_w}


def bench_dijkstra(rng):
    rows = []
    for v in [10, 50, 100, 250, 500, 1000, 2000]:
        graph = build_graph(make_graph(v, rng))
        rows.append({"V": v, "E": graph.edge_count,
                     "Dijkstra (one source)": measure(dijkstra, graph.adjacency, graph.depot)})
        log(f"  dijkstra V={v:>5} E={graph.edge_count:>5}: {rows[-1]['Dijkstra (one source)']*1000:8.3f} ms")
    return rows


def bench_tsp(rng):
    scaling = []
    for k in [5, 10, 25, 50, 100, 200, 400]:
        dist = random_distance_matrix(k, rng)
        stops = [s for s in dist if s != "Depot"]
        scaling.append({"stops": k, "Nearest Neighbour": measure(nearest_neighbor_tsp, dist, "Depot", stops)})
        log(f"  tsp NN k={k:>4}: {scaling[-1]['Nearest Neighbour']*1000:8.3f} ms")

    quality = []
    for k in range(3, 10):
        nn_times, bf_times, ratios = [], [], []
        trials = 20 if k <= 7 else 5
        for _ in range(trials):
            dist = random_distance_matrix(k, rng)
            stops = [s for s in dist if s != "Depot"]
            t = time.perf_counter()
            _, nn_len = nearest_neighbor_tsp(dist, "Depot", stops)
            nn_times.append(time.perf_counter() - t)
            t = time.perf_counter()
            _, opt_len = brute_force_tsp(dist, "Depot", stops)
            bf_times.append(time.perf_counter() - t)
            ratios.append(nn_len / opt_len)
        quality.append({"stops": k, "trials": trials,
                        "Nearest Neighbour": statistics.median(nn_times),
                        "Brute force (exact)": statistics.median(bf_times),
                        "mean_ratio": statistics.mean(ratios), "worst_ratio": max(ratios),
                        "optimal_found_pct": 100 * sum(r < 1 + 1e-9 for r in ratios) / trials})
        log(f"  tsp NN vs exact k={k}: avg NN/opt = {quality[-1]['mean_ratio']:.3f}")
    return {"scaling": scaling, "quality": quality}


def bench_end_to_end():
    folder = os.path.join(PROJECT_ROOT, "data", "test_datasets")
    rows = []
    for size in ["small", "medium", "large"]:
        parcels, capacity = load_parcel_file(os.path.join(folder, f"{size}_parcels.json"))
        graph = load_graph_file(os.path.join(folder, f"{size}_graph.json"))
        runs = [CourierPlanner(parcels, capacity, graph).run(keep_dp_table=False) for _ in range(5)]
        steps = runs[0].timings.keys()
        timings = {step: min(r.timings[step] for r in runs) for step in steps}
        last = runs[-1]
        rows.append({"dataset": size, "parcels": len(parcels), "locations": len(graph.adjacency),
                     "roads": graph.edge_count, "capacity": capacity,
                     "selected": len(last.selected), "selected_weight": last.knapsack.total_weight,
                     "stops": len(last.stops), "route_km": round(last.route.total_distance, 2),
                     "timings": timings})
        log(f"  end-to-end {size:<6}: total {timings['Total']*1000:9.2f} ms, "
            f"{len(last.selected)} parcels, {len(last.stops)} stops, {last.route.total_distance:.1f} km")
    return rows


# --------------------------------------------------------------------------
# Tables
# --------------------------------------------------------------------------
def ms(seconds):
    return "-" if seconds is None else f"{seconds * 1000:.3f}"


def write_tables(results):
    lines = ["# Runtime measurement tables",
             "",
             f"Generated {results['meta']['date']} on {results['meta']['machine']}, "
             f"Python {results['meta']['python']}. All times are the **minimum of 3-15 repeats, in milliseconds**, "
             "measured with `time.perf_counter()`.", ""]

    lines += ["## 1. Sorting (parcels by deadline, priority, id)", "",
              "| n | Merge Sort | Quick Sort (random pivot) | Quick Sort (middle pivot) | Insertion Sort | Insertion Sort (pre-sorted) | Built-in sorted() |",
              "|---:|---:|---:|---:|---:|---:|---:|"]
    for r in results["sorting"]:
        lines.append(f"| {r['n']} | {ms(r['Merge Sort'])} | {ms(r['Quick Sort'])} | {ms(r['Quick Sort (middle pivot)'])} | {ms(r['Insertion Sort'])} | "
                     f"{ms(r['Insertion Sort (pre-sorted input)'])} | {ms(r['Built-in sorted()'])} |")
    lines.append("\n`-` = not run (O(n^2) would take too long).\n")

    for key, title in (("vary_n", "## 2a. 0/1 Knapsack - growing n (W = 500 kg)"),
                       ("vary_W", "## 2b. 0/1 Knapsack - growing capacity W (n = 200)")):
        lines += [title, "", "| n | W | DP cells n*W | Full DP table | 1-D DP (value only) |",
                  "|---:|---:|---:|---:|---:|"]
        for r in results["knapsack"][key]:
            lines.append(f"| {r['n']} | {r['W']} | {r['n'] * r['W']:,} | {ms(r['Full DP table'])} | "
                         f"{ms(r['1-D DP (value only)'])} |")
        lines.append("")

    lines += ["## 3. Dijkstra (single source, binary heap)", "", "| V | E | time |", "|---:|---:|---:|"]
    for r in results["dijkstra"]:
        lines.append(f"| {r['V']} | {r['E']} | {ms(r['Dijkstra (one source)'])} |")

    lines += ["", "## 4a. Nearest Neighbour TSP - scaling", "", "| stops | time |", "|---:|---:|"]
    for r in results["tsp"]["scaling"]:
        lines.append(f"| {r['stops']} | {ms(r['Nearest Neighbour'])} |")
    lines += ["", "## 4b. Nearest Neighbour vs exact brute force", "",
              "| stops | trials | NN time | brute-force time | mean NN/optimal | worst NN/optimal | NN optimal in |",
              "|---:|---:|---:|---:|---:|---:|---:|"]
    for r in results["tsp"]["quality"]:
        lines.append(f"| {r['stops']} | {r['trials']} | {ms(r['Nearest Neighbour'])} | "
                     f"{ms(r['Brute force (exact)'])} | {r['mean_ratio']:.3f} | {r['worst_ratio']:.3f} | "
                     f"{r['optimal_found_pct']:.0f}% |")

    steps = list(results["end_to_end"][0]["timings"].keys())
    lines += ["", "## 5. Complete planner on the test datasets", "",
              "| dataset | parcels | locations | roads | capacity | selected | stops | route km | "
              + " | ".join(steps) + " |",
              "|---|" + "---:|" * (7 + len(steps))]
    for r in results["end_to_end"]:
        lines.append(f"| {r['dataset']} | {r['parcels']} | {r['locations']} | {r['roads']} | {r['capacity']} | "
                     f"{r['selected']} | {r['stops']} | {r['route_km']} | "
                     + " | ".join(ms(r["timings"][s]) for s in steps) + " |")
    path = os.path.join(RESULTS_DIR, "runtime_tables.md")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    return path


# --------------------------------------------------------------------------
# Charts
# --------------------------------------------------------------------------
def _style(ax, title, xlabel, ylabel):
    ax.set_title(title, color=INK, fontsize=12, loc="left", pad=10)
    ax.set_xlabel(xlabel, color=INK_2)
    ax.set_ylabel(ylabel, color=INK_2)
    ax.set_facecolor(SURFACE)
    ax.grid(color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#b9b8b3")
    ax.tick_params(colors=INK_2)


def _line(ax, xs, ys, label, color_index):
    pts = [(x, y * 1000) for x, y in zip(xs, ys) if y is not None]
    ax.plot([p[0] for p in pts], [p[1] for p in pts], color=COLORS[color_index], lw=2,
            marker="o", markersize=6, markeredgecolor=SURFACE, markeredgewidth=1.5, label=label)
    # Direct label at the line end (identity never by colour alone).
    ax.annotate(label, pts[-1], xytext=(6, 0), textcoords="offset points", va="center",
                fontsize=8.5, color=INK_2)


def draw_charts(results):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(CHARTS_DIR, exist_ok=True)
    plt.rcParams.update({"font.size": 10, "figure.facecolor": "white"})
    saved = []

    def save(fig, name):
        path = os.path.join(CHARTS_DIR, name)
        fig.tight_layout()
        fig.savefig(path, dpi=130)
        plt.close(fig)
        saved.append(path)

    # 1. Sorting comparison (log-log so every size range is readable).
    fig, ax = plt.subplots(figsize=(9, 5.5))
    rows = results["sorting"]
    xs = [r["n"] for r in rows]
    for i, name in enumerate(["Merge Sort", "Quick Sort", "Insertion Sort",
                              "Insertion Sort (pre-sorted input)", "Built-in sorted()",
                              "Quick Sort (middle pivot)"]):
        _line(ax, xs, [r[name] for r in rows], name, i)
    ax.set_xscale("log")
    ax.set_yscale("log")
    _style(ax, "Sorting runtime vs number of parcels (log-log)", "number of parcels n", "time (ms)")
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    ax.set_xlim(right=max(xs) * 6)
    save(fig, "sorting_comparison.png")

    # 2. Knapsack: two panels, growing n and growing W (same unit, separate axes per panel).
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, key, xkey, title in ((axes[0], "vary_n", "n", "Knapsack vs number of parcels n (W = 500)"),
                                 (axes[1], "vary_W", "W", "Knapsack vs capacity W (n = 200)")):
        rows = results["knapsack"][key]
        xs = [r[xkey] for r in rows]
        _line(ax, xs, [r["Full DP table"] for r in rows], "Full DP table", 0)
        _line(ax, xs, [r["1-D DP (value only)"] for r in rows], "1-D DP (value only)", 1)
        _style(ax, title, "n (parcels)" if xkey == "n" else "W (capacity, kg)", "time (ms)")
        ax.set_xlim(left=0, right=max(xs) * 1.35)
        ax.set_ylim(bottom=0)
        ax.legend(frameon=False, fontsize=9, loc="upper left")
    save(fig, "knapsack_scaling.png")

    # 3. Dijkstra scaling.
    fig, ax = plt.subplots(figsize=(8, 5))
    rows = results["dijkstra"]
    _line(ax, [r["V"] for r in rows], [r["Dijkstra (one source)"] for r in rows], "Dijkstra (one source)", 0)
    _style(ax, "Dijkstra runtime vs number of locations V (sparse road graphs)", "locations V", "time (ms)")
    ax.set_xlim(left=0, right=rows[-1]["V"] * 1.3)
    ax.set_ylim(bottom=0)
    save(fig, "dijkstra_scaling.png")

    # 4. TSP: NN scaling | NN vs brute force time | NN tour quality.
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
    rows = results["tsp"]["scaling"]
    _line(axes[0], [r["stops"] for r in rows], [r["Nearest Neighbour"] for r in rows], "Nearest Neighbour", 0)
    _style(axes[0], "NN TSP runtime vs stops", "stops k", "time (ms)")
    axes[0].set_xlim(left=0, right=rows[-1]["stops"] * 1.4)
    axes[0].set_ylim(bottom=0)
    q = results["tsp"]["quality"]
    ks = [r["stops"] for r in q]
    _line(axes[1], ks, [r["Nearest Neighbour"] for r in q], "Nearest Neighbour", 0)
    _line(axes[1], ks, [r["Brute force (exact)"] for r in q], "Brute force (exact)", 1)
    axes[1].set_yscale("log")
    axes[1].set_xlim(right=max(ks) + 2.5)
    _style(axes[1], "NN O(n^2) vs brute force O(n!)", "stops k", "time (ms, log scale)")
    axes[1].legend(frameon=False, fontsize=9, loc="upper left")
    axes[2].bar(ks, [(r["mean_ratio"] - 1) * 100 for r in q], color=COLORS[0], width=0.6, label="mean")
    axes[2].scatter(ks, [(r["worst_ratio"] - 1) * 100 for r in q], color=COLORS[1], s=40, zorder=3,
                    label="worst case")
    for k, r in zip(ks, q):
        axes[2].annotate(f"{(r['mean_ratio'] - 1) * 100:.1f}%", (k, (r["mean_ratio"] - 1) * 100),
                         xytext=(0, 3), textcoords="offset points", ha="center", fontsize=8, color=INK_2)
    _style(axes[2], "How much longer NN tour is than optimal", "stops k", "extra distance (%)")
    axes[2].legend(frameon=False, fontsize=9, loc="upper left")
    save(fig, "tsp_comparison.png")

    # 5. End-to-end stacked bars by step (one bar per dataset, log scale not used
    #    for stacks - show per-step share instead with a second panel of totals).
    e2e = results["end_to_end"]
    steps = [s for s in e2e[0]["timings"] if s != "Total"]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    labels = [f"{r['dataset']}\n{r['parcels']} parcels\n{r['locations']} locations" for r in e2e]
    bottoms = [0.0] * len(e2e)
    for i, step in enumerate(steps):
        shares = [r["timings"][step] / sum(r["timings"][s] for s in steps) * 100 for r in e2e]
        axes[0].bar(labels, shares, bottom=bottoms, color=COLORS[i], width=0.55, label=step,
                    edgecolor=SURFACE, linewidth=2)
        bottoms = [b + s for b, s in zip(bottoms, shares)]
    _style(axes[0], "Share of total planner time by step", "dataset", "% of total time")
    axes[0].legend(frameon=False, fontsize=8.5, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    totals = [r["timings"]["Total"] * 1000 for r in e2e]
    axes[1].bar(labels, totals, color=COLORS[0], width=0.55)
    for x, t in zip(labels, totals):
        axes[1].annotate(f"{t:.1f} ms", (x, t), xytext=(0, 3), textcoords="offset points",
                         ha="center", fontsize=9, color=INK_2)
    axes[1].set_yscale("log")
    _style(axes[1], "Total planner time (log scale)", "dataset", "time (ms)")
    save(fig, "end_to_end_breakdown.png")
    return saved


# --------------------------------------------------------------------------
# Entry points
# --------------------------------------------------------------------------
def run_all(make_charts=True):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    rng = random.Random(42)
    log("Running benchmarks (this takes about a minute)...")
    results = {
        "meta": {"date": time.strftime("%Y-%m-%d %H:%M"), "python": platform.python_version(),
                 "machine": f"{platform.system()} {platform.release()} / {platform.processor() or platform.machine()}"},
    }
    log("[1/5] Sorting");      results["sorting"] = bench_sorting(rng)
    log("[2/5] Knapsack");     results["knapsack"] = bench_knapsack(rng)
    log("[3/5] Dijkstra");     results["dijkstra"] = bench_dijkstra(rng)
    log("[4/5] TSP");          results["tsp"] = bench_tsp(rng)
    log("[5/5] End-to-end");   results["end_to_end"] = bench_end_to_end()
    with open(RESULTS_FILE, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=1)
    table_path = write_tables(results)
    log(f"\nRaw results : {os.path.relpath(RESULTS_FILE, PROJECT_ROOT)}")
    log(f"Tables      : {os.path.relpath(table_path, PROJECT_ROOT)}")
    if make_charts:
        for path in draw_charts(results):
            log(f"Chart       : {os.path.relpath(path, PROJECT_ROOT)}")
    return results


def charts_from_saved_results():
    if not os.path.exists(RESULTS_FILE):
        print("No saved benchmark results yet - running the benchmark first.")
        run_all(make_charts=True)
        return
    with open(RESULTS_FILE, encoding="utf-8") as handle:
        results = json.load(handle)
    for path in draw_charts(results):
        print(f"Chart saved: {os.path.relpath(path, PROJECT_ROOT)}")


if __name__ == "__main__":
    run_all()
