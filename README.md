# tsp-lab

A small laboratory for experimenting with Traveling Salesman Problem (TSP) heuristics — pure Python standard library, no third-party dependencies.

tsp-lab gives five classic heuristics a single uniform interface (distance matrix in, tour + length out), ships small built-in and random instances, and can check heuristic results against the exact optimum on tiny instances (n ≤ 10) by brute force.

## Algorithms

| CLI name | Algorithm | Notes |
|----------|-----------|-------|
| `nn` | Nearest Neighbor | Greedy construction: always visit the closest unvisited city |
| `greedy` | Greedy Edges | Kruskal-style: add shortest edges that keep a valid path cover |
| `2opt` | 2-opt | Local search with segment reversals, starting from the NN tour |
| `sa` | Simulated Annealing | Segment-reversal moves, geometric cooling, seeded |
| `ga` | Genetic Algorithm | Permutation encoding, order crossover (OX) + swap mutation, seeded |

## Installation

Requires Python ≥ 3.9. From a clone of this repository:

```bash
pip install .
```

This installs the `tsp-lab` command. Without installing, run it as a module from the repository root:

```bash
PYTHONPATH=. python -m tsp_lab.cli --help
```

## Usage

### Compare all algorithms on one instance

```bash
$ tsp-lab compare --instance ten --seed 0
Instance: ten (10 cities), seed 0
Algorithm                        Length Gap vs optimal
------------------------------------------------------
Nearest Neighbor                 115.35         22.06%
Greedy Edges                     101.27          7.17%
2-opt (from NN)                  101.27          7.17%
Simulated Annealing               94.50          0.00%
Genetic Algorithm                 94.50          0.00%
Optimal (brute force)             94.50          0.00%
```

For instances with n ≤ 10 the table includes the exact optimum (brute force over all permutations) and gaps are measured against it; for larger instances gaps are measured against the best heuristic result.

### Run a single algorithm

```bash
$ tsp-lab run --algo ga --instance ten --seed 0
Instance : ten (10 cities)
Algorithm: Genetic Algorithm
Tour     : 3 -> 4 -> 9 -> 5 -> 6 -> 0 -> 7 -> 1 -> 2 -> 8 -> 3
Length   : 94.50
Optimal  : 94.50 (gap 0.00%)
```

Instances can also come from a file (`--file path.tsp` / `--file path.json`) or be generated on the fly (`--random 20 --seed 1`).

### Generate a random instance

```bash
$ tsp-lab gen --n 15 --seed 42 --out random15.tsp
Saved random15 (15 cities, seed 42) to random15.tsp
```

The output format is TSPLIB-like text for `.tsp` and JSON for `.json`; both can be loaded back with `--file`.

An example instance file is included at `examples/cities10.json`:

```bash
$ tsp-lab run --algo 2opt --file examples/cities10.json
Instance : cities10 (10 cities)
Algorithm: 2-opt (from NN)
Tour     : 0 -> 6 -> 5 -> 4 -> 9 -> 7 -> 1 -> 8 -> 3 -> 2 -> 0
Length   : 101.27
Optimal  : 94.50 (gap 7.17%)
```

### Library use

```python
from tsp_lab import builtin_instance, brute_force_optimal
from tsp_lab.solvers import two_opt, genetic_algorithm

dist = builtin_instance("ten").distance_matrix()
tour, length = genetic_algorithm(dist, seed=0)
opt_tour, opt_len = brute_force_optimal(dist)  # n <= 10 only
print(length, opt_len)
```

## Project structure

```
tsp-lab/
├── pyproject.toml
├── README.md
├── LICENSE
├── examples/
│   └── cities10.json        # example instance file
├── tsp_lab/
│   ├── __init__.py
│   ├── instance.py          # built-in / random instances, load & save (.tsp / .json)
│   ├── solvers.py           # nn, greedy, 2-opt, simulated annealing, genetic algorithm
│   ├── evaluate.py          # tour length, validity check, brute-force optimum
│   └── cli.py               # argparse CLI: run / compare / gen
└── tests/
    └── test_tsp_lab.py      # unittest suite (14 tests)
```

## Tests

```bash
python -m unittest discover -s tests
```

## License

MIT — see [LICENSE](LICENSE). Copyright (c) 2026 Ruizhao Zheng.
