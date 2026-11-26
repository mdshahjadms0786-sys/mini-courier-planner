"""0/1 Knapsack using Dynamic Programming (Phase 2 - "Box Filling").

Problem: the delivery box (vehicle) can carry at most ``capacity`` kg.
Each parcel i has an integer weight w[i] and a value v[i] (its delivery
importance). Each parcel is either taken whole or left behind (0/1).
Choose the subset with maximum total value whose total weight <= capacity.

DP definition
    dp[i][c] = best total value using only the first i parcels
               with a box of capacity c.

Recurrence
    dp[0][c] = 0                                     (no parcels)
    dp[i][c] = dp[i-1][c]                            if w[i] > c
    dp[i][c] = max(dp[i-1][c],                       (skip parcel i)
                   dp[i-1][c - w[i]] + v[i])         (take parcel i)

Answer: dp[n][capacity]. The chosen parcels are recovered by walking the
table backwards: if dp[i][c] != dp[i-1][c] then parcel i was taken.

Complexity: O(n * W) time and O(n * W) space for the full table
(W = capacity). ``knapsack_max_value_1d`` shows the O(W)-space optimisation.
"""

from dataclasses import dataclass, field
from typing import List, Sequence


@dataclass
class KnapsackResult:
    max_value: int
    selected_indices: List[int]          # indices into the input lists
    total_weight: int
    dp_table: List[List[int]] = field(repr=False, default_factory=list)


def _validate(weights: Sequence[int], values: Sequence[int], capacity: int) -> None:
    if len(weights) != len(values):
        raise ValueError("weights and values must have the same length")
    if not isinstance(capacity, int) or isinstance(capacity, bool):
        raise TypeError("capacity must be an integer")
    if capacity < 0:
        raise ValueError("capacity cannot be negative")
    for w in weights:
        if not isinstance(w, int) or isinstance(w, bool) or w < 0:
            raise ValueError(f"weights must be non-negative integers, got {w!r}")
    for v in values:
        if not isinstance(v, (int, float)) or v < 0:
            raise ValueError(f"values must be non-negative numbers, got {v!r}")


def knapsack_01(weights: Sequence[int], values: Sequence[int], capacity: int,
                keep_table: bool = True) -> KnapsackResult:
    """Solve 0/1 knapsack bottom-up and reconstruct the chosen items.

    Returns a KnapsackResult with the max value, the selected item indices
    (in input order), their total weight and (optionally) the full DP table.
    """
    _validate(weights, values, capacity)
    n = len(weights)

    # (n+1) x (capacity+1) table, row 0 / column 0 are the base cases (= 0).
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        w, v = weights[i - 1], values[i - 1]
        previous_row, current_row = dp[i - 1], dp[i]
        for c in range(capacity + 1):
            skip = previous_row[c]
            if w <= c:
                take = previous_row[c - w] + v
                current_row[c] = take if take > skip else skip
            else:
                current_row[c] = skip

    # Backtrack to find which items were taken.
    selected = []
    c = capacity
    for i in range(n, 0, -1):
        if dp[i][c] != dp[i - 1][c]:
            selected.append(i - 1)
            c -= weights[i - 1]
    selected.reverse()

    total_weight = sum(weights[i] for i in selected)
    return KnapsackResult(
        max_value=dp[n][capacity],
        selected_indices=selected,
        total_weight=total_weight,
        dp_table=dp if keep_table else [],
    )


def knapsack_max_value_1d(weights: Sequence[int], values: Sequence[int], capacity: int) -> int:
    """Space-optimised knapsack: O(n*W) time but only O(W) memory.

    Iterating capacity from high to low ensures each item is used at most
    once. It returns only the best value (item reconstruction needs the
    full table or extra bookkeeping) - used in Phase 4 as an optimisation.
    """
    _validate(weights, values, capacity)
    best = [0] * (capacity + 1)
    for w, v in zip(weights, values):
        for c in range(capacity, w - 1, -1):
            candidate = best[c - w] + v
            if candidate > best[c]:
                best[c] = candidate
    return best[capacity]


def format_dp_table(dp: List[List[int]], row_labels: Sequence[str],
                    max_columns: int = 16) -> str:
    """Return the DP table as printable text.

    Large tables are shown with only every k-th capacity column so that the
    table still fits on a screen; the last column (full capacity) is always
    shown because it holds the answer.
    """
    if not dp:
        return "(empty DP table)"
    capacity = len(dp[0]) - 1
    if capacity + 1 <= max_columns:
        columns = list(range(capacity + 1))
    else:
        step = max(1, capacity // (max_columns - 1))
        columns = list(range(0, capacity + 1, step))
        if columns[-1] != capacity:
            columns.append(capacity)

    label_width = max(8, max(len(label) for label in row_labels) + 1)
    cell_width = max(4, len(str(dp[-1][-1])) + 1)
    lines = ["Item".ljust(label_width) + "".join(f"c={c}".rjust(cell_width + 2) for c in columns)]
    for label, row in zip(row_labels, dp):
        lines.append(label.ljust(label_width) + "".join(str(row[c]).rjust(cell_width + 2) for c in columns))
    if len(columns) < capacity + 1:
        lines.append(f"(showing {len(columns)} of {capacity + 1} capacity columns)")
    return "\n".join(lines)
