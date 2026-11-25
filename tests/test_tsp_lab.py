"""Unit tests for tsp-lab. Stochastic solvers are tested with fixed seeds."""

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from tsp_lab import (
    Instance,
    brute_force_optimal,
    builtin_instance,
    is_valid_tour,
    load_instance,
    random_instance,
    save_instance,
    tour_length,
)
from tsp_lab import solvers
from tsp_lab.cli import main as cli_main

ALL_SOLVERS = [
    solvers.nearest_neighbor,
    solvers.greedy_edges,
    solvers.two_opt,
    solvers.simulated_annealing,
    solvers.genetic_algorithm,
]


class TestInstance(unittest.TestCase):
    def test_distance_matrix_symmetric_zero_diagonal(self):
        inst = builtin_instance("ten")
        dist = inst.distance_matrix()
        n = inst.size
        for i in range(n):
            self.assertEqual(dist[i][i], 0.0)
            for j in range(n):
                self.assertAlmostEqual(dist[i][j], dist[j][i])

    def test_distance_matrix_known_values(self):
        inst = Instance("triangle", [(0, 0), (3, 0), (0, 4)])
        dist = inst.distance_matrix()
        self.assertAlmostEqual(dist[0][1], 3.0)
        self.assertAlmostEqual(dist[0][2], 4.0)
        self.assertAlmostEqual(dist[1][2], 5.0)

    def test_random_instance_reproducible_with_seed(self):
        a = random_instance(12, seed=42)
        b = random_instance(12, seed=42)
        self.assertEqual(a.coords, b.coords)
        c = random_instance(12, seed=43)
        self.assertNotEqual(a.coords, c.coords)

    def test_save_load_roundtrip_json_and_tsp(self):
        inst = random_instance(8, seed=7, name="roundtrip")
        with tempfile.TemporaryDirectory() as tmp:
            for fname in ("inst.json", "inst.tsp"):
                path = os.path.join(tmp, fname)
                save_instance(inst, path)
                loaded = load_instance(path)
                self.assertEqual(loaded.size, inst.size)
                for (x1, y1), (x2, y2) in zip(loaded.coords, inst.coords):
                    self.assertAlmostEqual(x1, x2)
                    self.assertAlmostEqual(y1, y2)


class TestEvaluate(unittest.TestCase):
    def test_tour_length_unit_square(self):
        inst = Instance("square", [(0, 0), (1, 0), (1, 1), (0, 1)])
        dist = inst.distance_matrix()
        self.assertAlmostEqual(tour_length(dist, [0, 1, 2, 3]), 4.0)

    def test_brute_force_unit_square(self):
        inst = Instance("square", [(0, 0), (1, 0), (1, 1), (0, 1)])
        dist = inst.distance_matrix()
        tour, length = brute_force_optimal(dist)
        self.assertTrue(is_valid_tour(tour, 4))
        self.assertAlmostEqual(length, 4.0)

    def test_brute_force_rejects_large_instances(self):
        dist = random_instance(11, seed=1).distance_matrix()
        with self.assertRaises(ValueError):
            brute_force_optimal(dist)


class TestSolvers(unittest.TestCase):
    def setUp(self):
        self.dist10 = builtin_instance("ten").distance_matrix()
        self.dist_small = random_instance(8, seed=3).distance_matrix()

    def test_each_solver_returns_valid_tour(self):
        for solver in ALL_SOLVERS:
            with self.subTest(solver=solver.__name__):
                tour, length = solver(self.dist10, seed=0)
                self.assertTrue(is_valid_tour(tour, 10))
                self.assertAlmostEqual(length, tour_length(self.dist10, tour))

    def test_two_opt_not_worse_than_nearest_neighbor(self):
        _nn_tour, nn_len = solvers.nearest_neighbor(self.dist10)
        _opt_tour, opt_len = solvers.two_opt(self.dist10)
        self.assertLessEqual(opt_len, nn_len + 1e-9)

    def test_two_opt_improves_a_bad_tour(self):
        bad_tour = list(range(9, -1, -1))
        bad_len = tour_length(self.dist10, bad_tour)
        _tour, improved_len = solvers.two_opt(self.dist10, tour=bad_tour)
        self.assertLessEqual(improved_len, bad_len + 1e-9)

    def test_brute_force_optimal_not_worse_than_heuristics(self):
        _tour, opt_len = brute_force_optimal(self.dist_small)
        for solver in ALL_SOLVERS:
            with self.subTest(solver=solver.__name__):
                _t, length = solver(self.dist_small, seed=0)
                self.assertLessEqual(opt_len, length + 1e-9)

    def test_stochastic_solvers_reproducible_with_seed(self):
        for solver in (solvers.simulated_annealing, solvers.genetic_algorithm):
            with self.subTest(solver=solver.__name__):
                tour1, len1 = solver(self.dist10, seed=123)
                tour2, len2 = solver(self.dist10, seed=123)
                self.assertEqual(tour1, tour2)
                self.assertAlmostEqual(len1, len2)


class TestCli(unittest.TestCase):
    def test_cli_compare_runs(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli_main(["compare", "--instance", "ten", "--seed", "0"])
        self.assertEqual(rc, 0)
        out = buf.getvalue()
        self.assertIn("Nearest Neighbor", out)
        self.assertIn("Genetic Algorithm", out)
        self.assertIn("Optimal (brute force)", out)

    def test_cli_run_and_gen(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli_main(["run", "--algo", "2opt", "--instance", "ten"])
        self.assertEqual(rc, 0)
        self.assertIn("Length", buf.getvalue())

        with tempfile.TemporaryDirectory() as tmp:
            out_path = os.path.join(tmp, "gen.json")
            with redirect_stdout(io.StringIO()):
                rc = cli_main(["gen", "--n", "12", "--seed", "5", "--out", out_path])
            self.assertEqual(rc, 0)
            with open(out_path, encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(len(data["coords"]), 12)


if __name__ == "__main__":
    unittest.main()
