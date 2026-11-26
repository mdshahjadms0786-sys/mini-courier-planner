"""Sorting algorithms used for parcel prioritisation (Phase 2).

The planner uses MERGE SORT as its main sorting algorithm because:
  * it is O(n log n) in the best, average AND worst case (no bad inputs),
  * it is STABLE: parcels with equal keys keep their original order, which
    makes the output predictable and fair (first-come, first-served on ties),
  * it works naturally with a composite key (deadline, then priority, ...).

Quick Sort and Insertion Sort are also implemented so that Phase 4 can
compare their running times against Merge Sort on the same data.

All functions take a list and an optional ``key`` function and return a NEW
sorted list (the input list is never modified).
"""

import random
from typing import Callable, List, Optional, TypeVar

T = TypeVar("T")
_pivot_rng = random.Random(2026)   # seeded: identical timings run to run


def _identity(item):
    return item


# --------------------------------------------------------------------------
# Merge Sort  -  O(n log n) time, O(n) extra space, stable
# --------------------------------------------------------------------------
def merge_sort(items: List[T], key: Optional[Callable[[T], object]] = None) -> List[T]:
    """Return a new list containing ``items`` sorted by ``key`` (stable)."""
    key = key or _identity
    # Decorate each item with its key once, so the key function is not
    # called O(n log n) times.
    decorated = [(key(item), item) for item in items]
    sorted_decorated = _merge_sort_decorated(decorated)
    return [item for _, item in sorted_decorated]


def _merge_sort_decorated(pairs):
    """Recursive merge sort on (key, item) pairs."""
    if len(pairs) <= 1:
        return list(pairs)
    middle = len(pairs) // 2
    left = _merge_sort_decorated(pairs[:middle])
    right = _merge_sort_decorated(pairs[middle:])
    return _merge(left, right)


def _merge(left, right):
    """Merge two sorted lists of (key, item) pairs into one sorted list."""
    merged = []
    i = j = 0
    while i < len(left) and j < len(right):
        # "<=" (not "<") keeps the sort STABLE: on equal keys the element
        # from the left half (which came first originally) is taken first.
        if left[i][0] <= right[j][0]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged


# --------------------------------------------------------------------------
# Quick Sort  -  O(n log n) expected, O(n^2) worst case
# (this 3-way partition version is stable because it builds new lists)
#
# Pivot choice matters: an earlier version used the MIDDLE element and on
# our partly-ordered parcel data the recursion went 286 levels deep for
# n = 10,000 (ideal ~14), making it ~5x slower than Merge Sort. A RANDOM
# pivot makes such bad splits extremely unlikely for any input order.
# --------------------------------------------------------------------------
def quick_sort(items: List[T], key: Optional[Callable[[T], object]] = None) -> List[T]:
    """Return a new list sorted with Quick Sort (random pivot, 3-way partition)."""
    key = key or _identity
    decorated = [(key(item), item) for item in items]
    return [item for _, item in _quick_sort_decorated(decorated)]


def _quick_sort_decorated(pairs):
    if len(pairs) <= 1:
        return list(pairs)
    pivot_key = _pivot_rng.choice(pairs)[0]
    less = [p for p in pairs if p[0] < pivot_key]
    equal = [p for p in pairs if p[0] == pivot_key]
    greater = [p for p in pairs if p[0] > pivot_key]
    return _quick_sort_decorated(less) + equal + _quick_sort_decorated(greater)


def quick_sort_middle_pivot(items: List[T], key: Optional[Callable[[T], object]] = None) -> List[T]:
    """Quick Sort with a fixed MIDDLE pivot - kept only for the Phase 4
    benchmark, to show how a poor pivot rule degrades towards O(n^2)."""
    key = key or _identity
    decorated = [(key(item), item) for item in items]

    def recurse(pairs):
        if len(pairs) <= 1:
            return list(pairs)
        pivot_key = pairs[len(pairs) // 2][0]
        less = [p for p in pairs if p[0] < pivot_key]
        equal = [p for p in pairs if p[0] == pivot_key]
        greater = [p for p in pairs if p[0] > pivot_key]
        return recurse(less) + equal + recurse(greater)

    return [item for _, item in recurse(decorated)]


# --------------------------------------------------------------------------
# Insertion Sort  -  O(n^2) worst/average, O(n) best (already sorted), stable
# --------------------------------------------------------------------------
def insertion_sort(items: List[T], key: Optional[Callable[[T], object]] = None) -> List[T]:
    """Return a new list sorted with Insertion Sort (good only for small n)."""
    key = key or _identity
    result = [(key(item), item) for item in items]
    for i in range(1, len(result)):
        current = result[i]
        j = i - 1
        # Shift larger elements one position right ("<" keeps it stable).
        while j >= 0 and current[0] < result[j][0]:
            result[j + 1] = result[j]
            j -= 1
        result[j + 1] = current
    return [item for _, item in result]


SORTING_ALGORITHMS = {
    "Merge Sort": merge_sort,
    "Quick Sort": quick_sort,
    "Insertion Sort": insertion_sort,
}
