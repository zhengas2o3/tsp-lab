"""TSP heuristics with a uniform interface.

Every solver takes a distance matrix (list of lists of floats) and returns
``(tour, length)`` where ``tour`` is a permutation of ``range(n)`` and
``length`` is the closed-tour length. Stochastic solvers accept a ``seed``
keyword so results are reproducible.
"""

from __future__ import annotations

import math
import random

from .evaluate import tour_length


# ---------------------------------------------------------------------------
# Construction heuristics
# ---------------------------------------------------------------------------

def nearest_neighbor(dist, start=0, seed=0):
    """Greedy tour: always move to the closest unvisited city."""
    n = len(dist)
    unvisited = set(range(n))
    unvisited.remove(start)
    tour = [start]
    current = start
    while unvisited:
        nxt = min(unvisited, key=lambda j: (dist[current][j], j))
        tour.append(nxt)
        unvisited.remove(nxt)
        current = nxt
    return tour, tour_length(dist, tour)


def greedy_edges(dist, seed=0):
    """Kruskal-style tour: add shortest edges that keep a single path cover.

    Edges are considered in increasing length order and accepted unless they
    would give a city degree > 2 or close a cycle before all cities are in.
    """
    n = len(dist)
    edges = sorted(
        (dist[i][j], i, j) for i in range(n) for j in range(i + 1, n)
    )
    degree = [0] * n
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    adjacency = [[] for _ in range(n)]
    chosen = 0
    for _w, i, j in edges:
        if degree[i] >= 2 or degree[j] >= 2:
            continue
        ri, rj = find(i), find(j)
        if ri == rj and chosen < n - 1:
            continue  # would close a premature cycle
        parent[ri] = rj
        degree[i] += 1
        degree[j] += 1
        adjacency[i].append(j)
        adjacency[j].append(i)
        chosen += 1
        if chosen == n:
            break

    # Walk the resulting Hamiltonian cycle.
    tour = [0]
    prev, current = -1, 0
    while len(tour) < n:
        nxt = adjacency[current][0] if adjacency[current][1] == prev else adjacency[current][1]
        tour.append(nxt)
        prev, current = current, nxt
    return tour, tour_length(dist, tour)


# ---------------------------------------------------------------------------
# 2-opt local search
# ---------------------------------------------------------------------------

def _two_opt_improve(dist, tour):
    """Improve ``tour`` in place with 2-opt moves until locally optimal."""
    n = len(tour)
    improved = True
    while improved:
        improved = False
        for i in range(n - 1):
            for j in range(i + 2, n):
                if i == 0 and j == n - 1:
                    continue  # reversing the whole tour changes nothing
                a, b = tour[i], tour[i + 1]
                c, d = tour[j], tour[(j + 1) % n]
                delta = dist[a][c] + dist[b][d] - dist[a][b] - dist[c][d]
                if delta < -1e-9:
                    tour[i + 1:j + 1] = reversed(tour[i + 1:j + 1])
                    improved = True
    return tour


def two_opt(dist, tour=None, seed=0):
    """2-opt improvement, starting from the nearest-neighbour tour by default."""
    if tour is None:
        tour, _ = nearest_neighbor(dist)
    else:
        tour = list(tour)
    tour = _two_opt_improve(dist, tour)
    return tour, tour_length(dist, tour)


# ---------------------------------------------------------------------------
# Simulated annealing
# ---------------------------------------------------------------------------

def simulated_annealing(dist, seed=0, iterations=20000, initial_temp=None,
                        final_temp=1e-3):
    """Simulated annealing with segment-reversal (2-opt style) moves."""
    n = len(dist)
    rng = random.Random(seed)
    tour, current_len = nearest_neighbor(dist)
    if initial_temp is None:
        total = sum(dist[i][j] for i in range(n) for j in range(n) if i != j)
        initial_temp = max(total / (n * (n - 1)), 1e-9)  # average edge length
    best_tour, best_len = list(tour), current_len
    ratio = final_temp / initial_temp
    for step in range(iterations):
        temp = initial_temp * ratio ** (step / max(iterations - 1, 1))
        i, j = sorted(rng.sample(range(n), 2))
        if i == 0 and j == n - 1:
            continue
        a, b = tour[i], tour[(i + 1) % n]
        c, d = tour[j], tour[(j + 1) % n]
        delta = dist[a][c] + dist[b][d] - dist[a][b] - dist[c][d]
        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            tour[i + 1:j + 1] = reversed(tour[i + 1:j + 1])
            current_len += delta
            if current_len < best_len:
                best_len = current_len
                best_tour = list(tour)
    return best_tour, tour_length(dist, best_tour)


# ---------------------------------------------------------------------------
# Genetic algorithm (order crossover OX + swap mutation)
# ---------------------------------------------------------------------------

def _order_crossover(parent1, parent2, rng):
    """Order crossover (OX): keep a slice of parent1, fill the rest in
    parent2's relative order."""
    n = len(parent1)
    a, b = sorted(rng.sample(range(n), 2))
    child = [None] * n
    child[a:b + 1] = parent1[a:b + 1]
    inherited = set(parent1[a:b + 1])
    fill = [city for city in parent2 if city not in inherited]
    positions = list(range(b + 1, n)) + list(range(0, a))
    for pos, city in zip(positions, fill):
        child[pos] = city
    return child


def genetic_algorithm(dist, seed=0, population_size=60, generations=300,
                      mutation_rate=0.25, tournament_size=3, elite=2):
    """Genetic algorithm over permutations with OX crossover and swap mutation."""
    n = len(dist)
    rng = random.Random(seed)
    nn_tour, _ = nearest_neighbor(dist)
    population = [list(nn_tour)]
    while len(population) < population_size:
        perm = list(range(n))
        rng.shuffle(perm)
        population.append(perm)

    def evaluate(pop):
        return [tour_length(dist, t) for t in pop]

    lengths = evaluate(population)
    best_idx = min(range(len(population)), key=lambda k: lengths[k])
    best_tour, best_len = list(population[best_idx]), lengths[best_idx]

    for _gen in range(generations):
        order = sorted(range(len(population)), key=lambda k: lengths[k])
        population = [population[k] for k in order]
        lengths = [lengths[k] for k in order]
        if lengths[0] < best_len:
            best_tour, best_len = list(population[0]), lengths[0]

        def select():
            contenders = rng.sample(range(len(population)), tournament_size)
            return population[min(contenders, key=lambda k: lengths[k])]

        children = [list(t) for t in population[:elite]]
        while len(children) < population_size:
            child = _order_crossover(select(), select(), rng)
            if rng.random() < mutation_rate:
                i, j = rng.sample(range(n), 2)
                child[i], child[j] = child[j], child[i]
            children.append(child)
        population = children
        lengths = evaluate(population)

    best_idx = min(range(len(population)), key=lambda k: lengths[k])
    if lengths[best_idx] < best_len:
        best_tour, best_len = list(population[best_idx]), lengths[best_idx]
    return best_tour, tour_length(dist, best_tour)


# Registry: short CLI name -> (solver function, display name)
SOLVERS = {
    "nn": (nearest_neighbor, "Nearest Neighbor"),
    "greedy": (greedy_edges, "Greedy Edges"),
    "2opt": (two_opt, "2-opt (from NN)"),
    "sa": (simulated_annealing, "Simulated Annealing"),
    "ga": (genetic_algorithm, "Genetic Algorithm"),
}
