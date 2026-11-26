"""Parcel data: loading, validation, prioritisation and packing (Phase 2).

Parcel attributes
    id            unique text id, e.g. "P01"
    weight        integer kg (> 0)        - integer so the knapsack DP works
    priority      1 (critical) ... 5 (low)
    deadline      hours from dispatch (> 0); smaller = more urgent
    destination   name of a node in the delivery graph

Priority order used for sorting (most urgent first)
    1. earlier deadline
    2. then higher priority (smaller priority number)
    3. then parcel id (makes the order fully deterministic)

Knapsack value ("delivery importance") of a parcel
    value = (6 - priority) * 10 + max(0, 24 - deadline)
  * priority 1 -> 50 points ... priority 5 -> 10 points
  * up to 24 extra urgency points for parcels due within 24 hours
  This rewards urgent, high-priority parcels while still letting the DP
  trade them off against their weight.
"""

import json
from dataclasses import asdict, dataclass
from typing import Dict, Iterable, List, Sequence, Tuple

from algorithms.knapsack import KnapsackResult, knapsack_01
from algorithms.sorting import SORTING_ALGORITHMS, merge_sort

PRIORITY_LABELS = {1: "Critical", 2: "High", 3: "Medium", 4: "Normal", 5: "Low"}


class DataError(ValueError):
    """Raised when an input file contains invalid parcel or graph data."""


@dataclass(frozen=True)
class Parcel:
    id: str
    weight: int
    priority: int
    deadline: int
    destination: str

    @property
    def value(self) -> int:
        """Delivery importance used as the knapsack value."""
        return (6 - self.priority) * 10 + max(0, 24 - self.deadline)

    @property
    def priority_label(self) -> str:
        return PRIORITY_LABELS.get(self.priority, str(self.priority))

    def to_dict(self) -> Dict:
        return asdict(self)


def priority_key(parcel: Parcel) -> Tuple[int, int, str]:
    """Sort key: deadline first, then priority, then id (all ascending)."""
    return (parcel.deadline, parcel.priority, parcel.id)


# --------------------------------------------------------------------------
# Loading and validation
# --------------------------------------------------------------------------
def _is_int(x) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def parse_parcels(raw_parcels: Iterable[Dict]) -> List[Parcel]:
    """Validate raw dictionaries and convert them to Parcel objects."""
    parcels, seen_ids = [], set()
    for position, raw in enumerate(raw_parcels, start=1):
        if not isinstance(raw, dict):
            raise DataError(f"parcel #{position} is not an object")
        missing = {"id", "weight", "priority", "deadline", "destination"} - raw.keys()
        if missing:
            raise DataError(f"parcel #{position} is missing field(s): {', '.join(sorted(missing))}")
        pid = str(raw["id"]).strip()
        if not pid:
            raise DataError(f"parcel #{position} has an empty id")
        if pid in seen_ids:
            raise DataError(f"duplicate parcel id {pid!r}")
        if not _is_int(raw["weight"]) or raw["weight"] <= 0:
            raise DataError(f"parcel {pid}: weight must be a positive integer (kg)")
        if not _is_int(raw["priority"]) or not 1 <= raw["priority"] <= 5:
            raise DataError(f"parcel {pid}: priority must be an integer from 1 to 5")
        if not _is_int(raw["deadline"]) or raw["deadline"] <= 0:
            raise DataError(f"parcel {pid}: deadline must be a positive integer (hours)")
        destination = str(raw["destination"]).strip()
        if not destination:
            raise DataError(f"parcel {pid}: destination is empty")
        seen_ids.add(pid)
        parcels.append(Parcel(pid, raw["weight"], raw["priority"], raw["deadline"], destination))
    return parcels


def load_parcel_file(path: str) -> Tuple[List[Parcel], int]:
    """Load parcels.json -> (parcels, vehicle capacity in kg)."""
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        raise DataError(f"parcel file not found: {path}") from None
    except json.JSONDecodeError as error:
        raise DataError(f"parcel file is not valid JSON: {error}") from None
    if not isinstance(data, dict) or "parcels" not in data:
        raise DataError("parcel file must be an object with a 'parcels' list")
    capacity = data.get("vehicle_capacity_kg", 0)
    if not _is_int(capacity) or capacity < 0:
        raise DataError("vehicle_capacity_kg must be a non-negative integer")
    return parse_parcels(data["parcels"]), capacity


# --------------------------------------------------------------------------
# Prioritisation (sorting) and packing (knapsack)
# --------------------------------------------------------------------------
def sort_parcels(parcels: Sequence[Parcel], algorithm: str = "Merge Sort") -> List[Parcel]:
    """Return parcels in priority order using the chosen sorting algorithm."""
    if algorithm not in SORTING_ALGORITHMS:
        raise ValueError(f"unknown sorting algorithm {algorithm!r}")
    return SORTING_ALGORITHMS[algorithm](list(parcels), key=priority_key)


def select_parcels(sorted_parcels: Sequence[Parcel], capacity: int,
                   keep_table: bool = True) -> Tuple[List[Parcel], KnapsackResult]:
    """Run 0/1 knapsack on the (sorted) parcels and return the chosen ones.

    The chosen parcels are returned in the same priority order as the input.
    """
    weights = [p.weight for p in sorted_parcels]
    values = [p.value for p in sorted_parcels]
    result = knapsack_01(weights, values, capacity, keep_table=keep_table)
    chosen = [sorted_parcels[i] for i in result.selected_indices]
    return chosen, result


# --------------------------------------------------------------------------
# Display helpers
# --------------------------------------------------------------------------
def format_parcel_table(parcels: Sequence[Parcel], title: str = "") -> str:
    if not parcels:
        return (title + "\n" if title else "") + "  (no parcels)"
    header = f"{'#':>3}  {'ID':<6}{'Weight':>7}  {'Priority':<12}{'Deadline':>9}  {'Value':>5}  Destination"
    lines = [title] if title else []
    lines += [header, "-" * len(header)]
    for n, p in enumerate(parcels, start=1):
        lines.append(f"{n:>3}  {p.id:<6}{p.weight:>5}kg  {p.priority} {p.priority_label:<10}"
                     f"{p.deadline:>7} h  {p.value:>5}  {p.destination}")
    total_w = sum(p.weight for p in parcels)
    total_v = sum(p.value for p in parcels)
    lines.append("-" * len(header))
    lines.append(f"     Total: {len(parcels)} parcels, {total_w} kg, value {total_v}")
    return "\n".join(lines)
