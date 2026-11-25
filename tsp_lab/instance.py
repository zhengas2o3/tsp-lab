"""TSP instances: built-in examples, random generation, loading and saving.

An instance is a named set of 2-D city coordinates. Distances are Euclidean
and computed on demand as a full matrix.
"""

from __future__ import annotations

import json
import math
import os
import random

# Hand-made small instances (name -> list of (x, y) coordinates).
BUILTIN_INSTANCES = {
    "ten": [
        (0, 0), (10, 5), (20, 0), (25, 12), (15, 20),
        (5, 18), (-5, 10), (8, 8), (18, 9), (12, 14),
    ],
    "fifteen": [
        (0, 0), (10, 5), (20, 0), (25, 12), (15, 20),
        (5, 18), (-5, 10), (8, 8), (18, 9), (12, 14),
        (30, 20), (22, 28), (3, 27), (-8, 20), (14, 3),
    ],
}


class Instance:
    """A TSP instance: a name plus a list of (x, y) city coordinates."""

    def __init__(self, name, coords):
        coords = [(float(x), float(y)) for x, y in coords]
        if len(coords) < 3:
            raise ValueError("a TSP instance needs at least 3 cities")
        self.name = str(name)
        self.coords = coords

    @property
    def size(self):
        return len(self.coords)

    def distance_matrix(self):
        """Return the full symmetric Euclidean distance matrix."""
        n = self.size
        dist = [[0.0] * n for _ in range(n)]
        for i in range(n):
            xi, yi = self.coords[i]
            for j in range(i + 1, n):
                xj, yj = self.coords[j]
                d = math.hypot(xi - xj, yi - yj)
                dist[i][j] = d
                dist[j][i] = d
        return dist

    def to_dict(self):
        return {"name": self.name, "coords": [list(c) for c in self.coords]}

    @classmethod
    def from_dict(cls, data):
        return cls(data.get("name", "instance"), data["coords"])

    def __repr__(self):
        return "Instance(name=%r, size=%d)" % (self.name, self.size)


def builtin_instance(name):
    """Return one of the built-in instances by name."""
    try:
        coords = BUILTIN_INSTANCES[name]
    except KeyError:
        raise ValueError(
            "unknown built-in instance %r (available: %s)"
            % (name, ", ".join(sorted(BUILTIN_INSTANCES)))
        )
    return Instance(name, coords)


def random_instance(n, seed=0, name=None, width=100.0, height=100.0):
    """Generate a random instance with ``n`` cities in a width x height box.

    The same seed always produces the same instance.
    """
    if n < 3:
        raise ValueError("n must be at least 3")
    rng = random.Random(seed)
    coords = [(rng.uniform(0, width), rng.uniform(0, height)) for _ in range(n)]
    return Instance(name or "random%d" % n, coords)


def to_tsp_text(instance):
    """Serialize an instance in a TSPLIB-like text format."""
    lines = [
        "NAME: %s" % instance.name,
        "TYPE: TSP",
        "DIMENSION: %d" % instance.size,
        "EDGE_WEIGHT_TYPE: EUC_2D",
        "NODE_COORD_SECTION",
    ]
    for idx, (x, y) in enumerate(instance.coords, start=1):
        lines.append("%d %s %s" % (idx, _fmt(x), _fmt(y)))
    lines.append("EOF")
    return "\n".join(lines) + "\n"


def _fmt(value):
    if float(value).is_integer():
        return str(int(value))
    return repr(float(value))


def parse_tsp_text(text, name_fallback="instance"):
    """Parse a TSPLIB-like text (NAME / DIMENSION / NODE_COORD_SECTION)."""
    name = name_fallback
    coords = []
    in_section = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        upper = line.upper()
        if upper.startswith("NAME"):
            name = line.split(":", 1)[-1].strip() or name
            continue
        if upper.startswith("NODE_COORD_SECTION"):
            in_section = True
            continue
        if upper == "EOF":
            break
        if in_section:
            parts = line.split()
            if len(parts) >= 3:
                coords.append((float(parts[1]), float(parts[2])))
    if not coords:
        raise ValueError("no NODE_COORD_SECTION coordinates found")
    return Instance(name, coords)


def save_instance(instance, path):
    """Save an instance to ``path`` (.json -> JSON, anything else -> TSP text)."""
    if str(path).lower().endswith(".json"):
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(instance.to_dict(), fh, indent=2)
            fh.write("\n")
    else:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(to_tsp_text(instance))


def load_instance(path):
    """Load an instance from a .json file or a TSPLIB-like .tsp text file."""
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    if str(path).lower().endswith(".json"):
        return Instance.from_dict(json.loads(text))
    fallback = os.path.splitext(os.path.basename(str(path)))[0]
    return parse_tsp_text(text, name_fallback=fallback)
