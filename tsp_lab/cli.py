"""Command line interface for tsp-lab.

Subcommands:
  run      run one algorithm on one instance
  compare  run every algorithm on one instance and print a table
  gen      generate a random instance and save it (.tsp text or .json)
"""

from __future__ import annotations

import argparse
import sys

from .evaluate import brute_force_optimal, tour_length
from .instance import (
    BUILTIN_INSTANCES,
    builtin_instance,
    load_instance,
    random_instance,
    save_instance,
)
from .solvers import SOLVERS


def _add_instance_args(parser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--instance",
        choices=sorted(BUILTIN_INSTANCES),
        default=None,
        help="built-in instance name (default: ten)",
    )
    group.add_argument("--file", default=None, help="load instance from a .tsp/.json file")
    group.add_argument(
        "--random", type=int, default=None, metavar="N",
        help="use a random instance with N cities",
    )
    parser.add_argument("--seed", type=int, default=0, help="random seed (default: 0)")


def _resolve_instance(args):
    if getattr(args, "file", None):
        return load_instance(args.file)
    if getattr(args, "random", None):
        return random_instance(args.random, seed=args.seed)
    return builtin_instance(args.instance or "ten")


def _gap_pct(length, reference):
    if not reference:
        return 0.0
    gap = (length - reference) / reference * 100
    # Differences below display precision come from float summation order.
    return 0.0 if abs(gap) < 0.005 else gap


def _format_tour(tour):
    return " -> ".join(str(c) for c in tour) + " -> " + str(tour[0])


def cmd_run(args):
    instance = _resolve_instance(args)
    dist = instance.distance_matrix()
    solver, display = SOLVERS[args.algo]
    tour, length = solver(dist, seed=args.seed)
    print("Instance : %s (%d cities)" % (instance.name, instance.size))
    print("Algorithm: %s" % display)
    print("Tour     : %s" % _format_tour(tour))
    print("Length   : %.2f" % length)
    if instance.size <= 10:
        _opt_tour, opt_len = brute_force_optimal(dist)
        print("Optimal  : %.2f (gap %.2f%%)" % (opt_len, _gap_pct(length, opt_len)))
    return 0


def cmd_compare(args):
    instance = _resolve_instance(args)
    dist = instance.distance_matrix()
    rows = []
    for key in ("nn", "greedy", "2opt", "sa", "ga"):
        solver, display = SOLVERS[key]
        _tour, length = solver(dist, seed=args.seed)
        rows.append((display, length))
    reference = None
    reference_label = "best"
    if instance.size <= 10:
        _opt_tour, opt_len = brute_force_optimal(dist)
        rows.append(("Optimal (brute force)", opt_len))
        reference = opt_len
        reference_label = "optimal"
    if reference is None:
        reference = min(length for _name, length in rows)

    print("Instance: %s (%d cities), seed %d" % (instance.name, instance.size, args.seed))
    print("%-26s %12s %14s" % ("Algorithm", "Length", "Gap vs " + reference_label))
    print("-" * 54)
    for name, length in rows:
        print("%-26s %12.2f %13.2f%%" % (name, length, _gap_pct(length, reference)))
    return 0


def cmd_gen(args):
    instance = random_instance(args.n, seed=args.seed, name=args.name)
    save_instance(instance, args.out)
    print("Saved %s (%d cities, seed %d) to %s"
          % (instance.name, instance.size, args.seed, args.out))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="tsp-lab",
        description="A small laboratory for TSP heuristics (pure standard library).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="run one algorithm on one instance")
    p_run.add_argument("--algo", choices=sorted(SOLVERS), required=True,
                       help="algorithm to run")
    _add_instance_args(p_run)
    p_run.set_defaults(func=cmd_run)

    p_cmp = sub.add_parser("compare", help="compare all algorithms on one instance")
    _add_instance_args(p_cmp)
    p_cmp.set_defaults(func=cmd_compare)

    p_gen = sub.add_parser("gen", help="generate a random instance and save it")
    p_gen.add_argument("--n", type=int, required=True, help="number of cities")
    p_gen.add_argument("--seed", type=int, default=0, help="random seed (default: 0)")
    p_gen.add_argument("--name", default=None, help="instance name")
    p_gen.add_argument("--out", required=True,
                       help="output file (.tsp for TSPLIB-like text, .json for JSON)")
    p_gen.set_defaults(func=cmd_gen)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
