"""Draw the Phase 1 workflow diagram as a PNG (documentation/images/workflow_diagram.png).

Run:  python tools/draw_workflow.py
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt                       # noqa: E402
from matplotlib.patches import FancyBboxPatch         # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "documentation", "images", "workflow_diagram.png")

# (title, detail, algorithm colour or None)
STEPS = [
    ("1. Load & validate", "parcels.json + delivery_graph.json", None),
    ("2. Display parcels", "id, weight, priority, deadline, destination", None),
    ("3. Merge Sort", "key = (deadline, priority, id)  O(n log n)", "#2a78d6"),
    ("4. Reachability check", "Dijkstra from depot; drop unknown/unreachable", "#eda100"),
    ("5. 0/1 Knapsack DP", "max value within capacity W  O(nW)", "#1baf7a"),
    ("6. Delivery stops", "distinct destinations of selected parcels", None),
    ("7. Dijkstra from every stop", "exact stop-to-stop distance matrix", "#eda100"),
    ("8. Nearest Neighbour TSP", "visiting order (approximate)  O(k^2)", "#eb6834"),
    ("9. Distance, ETA, summary", "total km, deadline check, route map", None),
    ("10. Benchmark & charts", "small / medium / large, Matplotlib", None),
]


def main():
    fig, ax = plt.subplots(figsize=(7.2, 10))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, len(STEPS) * 1.2 + 0.4)
    ax.axis("off")
    box_w, box_h, x0 = 7.6, 0.8, 1.2
    for i, (title, detail, color) in enumerate(STEPS):
        y = (len(STEPS) - 1 - i) * 1.2 + 0.5
        face = color or "#f0efec"
        ink = "white" if color else "#0b0b0b"
        ax.add_patch(FancyBboxPatch((x0, y), box_w, box_h, boxstyle="round,pad=0.02,rounding_size=0.15",
                                    facecolor=face, edgecolor="#52514e" if not color else face, linewidth=1))
        ax.text(x0 + box_w / 2, y + box_h * 0.64, title, ha="center", va="center",
                fontsize=11, fontweight="bold", color=ink)
        ax.text(x0 + box_w / 2, y + box_h * 0.27, detail, ha="center", va="center", fontsize=8.5, color=ink)
        if i < len(STEPS) - 1:
            ax.annotate("", xy=(x0 + box_w / 2, y - 0.4 + 0.02), xytext=(x0 + box_w / 2, y - 0.02),
                        arrowprops=dict(arrowstyle="-|>", color="#52514e", lw=1.4))
    ax.text(5, len(STEPS) * 1.2 + 0.15, "Mini-Courier Planner - workflow", ha="center",
            fontsize=13, fontweight="bold", color="#0b0b0b")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT, dpi=150, facecolor="white")
    plt.close(fig)
    print(f"saved {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
