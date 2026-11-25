"""Tour evaluation: length computation and exact optima for tiny instances."""

from __future__ import annotations

import itertools


def tour_length(dist, tour):
    """Total length of a closed tour (returns to the start city)."""
    n = len(tour)
    if n == 0:
        return 0.0
    total = 0.0
    for k in range(n):
        total += dist[tour[k]][tour[(k + 1) % n]]
    return total


def is_valid_tour(tour, n):
    """True when ``tour`` visits each of the ``n`` cities exactly once."""
    return len(tour) == n and sorted(tour) == list(range(n))


def brute_force_optimal(dist):
    """Exact optimum by exhaustive search. Only feasible for n <= 10.

    Returns (tour, length). City 0 is fixed as the start to remove the
    rotational symmetry of the tour.
    """
    n = len(dist)
    if n > 10:
        raise ValueError("brute force is limited to n <= 10 (got %d)" % n)
    best_tour = None
    best_len = float("inf")
    for perm in itertools.permutations(range(1, n)):
        tour = (0,) + perm
        length = tour_length(dist, tour)
        if length < best_len:
            best_len = length
            best_tour = list(tour)
    return best_tour, best_len
