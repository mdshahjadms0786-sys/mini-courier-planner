"""Capture REAL program output as evidence for the report.

Run:  python tools/capture_evidence.py

For each scenario below the program is actually executed (as a subprocess),
its console output is saved to screenshots/<name>.txt, and the same text is
rendered as a terminal-style PNG image (screenshots/<name>.png) for the
report. Nothing is typed in by hand - every line comes from a real run.
"""

import os
import shutil
import subprocess
import sys
import textwrap

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "screenshots")
PY = sys.executable
TEST = os.path.join("data", "test_datasets")

SCENARIOS = [
    ("01_complete_plan_sample", "Complete courier plan - sample data (python main.py --demo)",
     [PY, "main.py", "--demo"], None),
    ("02_menu_session", "Interactive menu: options 1, 2, 4, an invalid choice, then 10 (exit)",
     [PY, "main.py"], "1\n\n2\n\n4\n\nabc\n10\n"),
    ("03_menu_dijkstra_tsp", "Interactive menu: option 5 (Dijkstra) and option 6 (TSP route)",
     [PY, "main.py"], "5\n\n6\n\n10\n"),
    ("04_unit_tests", "Automated tests (python -m unittest discover -s tests -v)",
     [PY, "-m", "unittest", "discover", "-s", "tests", "-v"], None),
    ("05_medium_dataset_plan", "Unseen dataset: medium (100 parcels, 60 locations)",
     [PY, "main.py", "--parcels", os.path.join(TEST, "medium_parcels.json"),
      "--graph", os.path.join(TEST, "medium_graph.json"), "--demo"], None),
    ("06_capacity_override", "Same sample data with capacity changed to 35 kg (--capacity 35)",
     [PY, "main.py", "--capacity", "35", "--demo"], None),
    ("07_zero_capacity", "Edge case: zero capacity (--capacity 0)",
     [PY, "main.py", "--capacity", "0", "--demo"], None),
    ("08_invalid_inputs", "Edge cases: missing file, then invalid capacity typed in the menu",
     None, None),
    ("09_benchmark_run", "Performance benchmark (python main.py --benchmark)",
     [PY, "main.py", "--benchmark"], None),
]


def run(cmd, stdin_text=None):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    result = subprocess.run(cmd, cwd=ROOT, input=stdin_text, capture_output=True,
                            text=True, encoding="utf-8", env=env)
    return result.stdout + result.stderr


def show_cmd(cmd):
    return " ".join("python" if part == PY else part for part in cmd)


def render_png(text, title, path, max_lines=150):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    lines = []
    for line in text.splitlines():
        lines.extend(textwrap.wrap(line, 150, drop_whitespace=False) or [""])
    if len(lines) > max_lines:
        hidden = len(lines) - max_lines
        lines = lines[:max_lines] + [f"... ({hidden} more lines in the .txt file)"]
    width = max(80, max(len(line) for line in lines))
    fig_w = min(22, 0.072 * width + 0.6)
    fig_h = 0.17 * (len(lines) + 3) + 0.4
    fig = plt.figure(figsize=(fig_w, fig_h))
    fig.patch.set_facecolor("#1e1e1e")
    fig.text(0.01, 1 - 0.12 / fig_h, title, color="#9cdcfe", family="monospace",
             fontsize=9.5, va="top", fontweight="bold")
    fig.text(0.01, 1 - 0.45 / fig_h, "\n".join(lines), color="#e8e8e8", family="monospace",
             fontsize=8.5, va="top", linespacing=1.25)
    fig.savefig(path, dpi=110, facecolor=fig.get_facecolor())
    plt.close(fig)


def invalid_input_scenario():
    parts = []
    cmd = [PY, "main.py", "--parcels", "data/missing.json"]
    parts.append(f"$ {show_cmd(cmd)}\n{run(cmd)}")
    # Option 0 -> keep files -> type an invalid capacity; then option 11 (invalid) and exit.
    cmd = [PY, "main.py"]
    parts.append(f"$ {show_cmd(cmd)}   (typed: 0, Enter, Enter, -5, Enter, 11, 10)\n"
                 + run(cmd, "0\n\n\n-5\n\n11\n10\n"))
    bad = os.path.join(OUT, "_bad_parcels.json")
    with open(bad, "w", encoding="utf-8") as handle:
        handle.write('{"vehicle_capacity_kg": 10, "parcels": [{"id": "X", "weight": -2, '
                     '"priority": 1, "deadline": 3, "destination": "Mall"}]}')
    cmd = [PY, "main.py", "--parcels", os.path.relpath(bad, ROOT)]
    parts.append(f"$ {show_cmd(cmd)}   (file has weight -2)\n{run(cmd)}")
    os.remove(bad)
    return "\n".join(parts)


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, title, cmd, stdin_text in SCENARIOS:
        print(f"running {name} ...", flush=True)
        if cmd is None:
            text = invalid_input_scenario()
        else:
            text = f"$ {show_cmd(cmd)}\n" + run(cmd, stdin_text)
        with open(os.path.join(OUT, f"{name}.txt"), "w", encoding="utf-8") as handle:
            handle.write(text)
        render_png(text, title, os.path.join(OUT, f"{name}.png"))
        # Keep a copy of the route map produced by the medium-dataset run.
        if name == "05_medium_dataset_plan":
            shutil.copy(os.path.join(OUT, "route_map.png"), os.path.join(OUT, "route_map_medium.png"))
    # Finish with the sample-data route map as screenshots/route_map.png.
    run([PY, "main.py", "--demo"])
    print("Evidence saved in screenshots/")


if __name__ == "__main__":
    main()
