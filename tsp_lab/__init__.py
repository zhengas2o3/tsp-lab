"""tsp-lab: a small laboratory for TSP heuristics (pure standard library)."""

from .instance import Instance, builtin_instance, random_instance, load_instance, save_instance
from .evaluate import tour_length, is_valid_tour, brute_force_optimal
from . import solvers

__version__ = "0.1.0"

__all__ = [
    "Instance",
    "builtin_instance",
    "random_instance",
    "load_instance",
    "save_instance",
    "tour_length",
    "is_valid_tour",
    "brute_force_optimal",
    "solvers",
    "__version__",
]
