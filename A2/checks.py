"""Check BUC counts on small inputs with known answers.

DuckDB is only a reference here. Neither BUC implementation uses it.
Run from assignments/A2 with: python checks.py
"""

from collections import Counter
from itertools import combinations, product
from pathlib import Path
from tempfile import TemporaryDirectory

import duckdb
import numpy as np
import pandas as pd

from aoi import generalize, load_hierarchies
from buc import ALL, DTYPE, buc_memory, buc_disk, dimension_order, encode_frame


def brute_force_cube(rows, minsup):
    """Count every dimension subset directly; only suitable for small inputs."""
    result = {}
    width = rows.shape[1]
    # Include the empty subset for the unrestricted total.
    for size in range(width + 1):
        for axes in combinations(range(width), size):
            counts = Counter(tuple(int(row[i]) for i in axes) for row in rows)
            for values, count in counts.items():
                if count >= minsup:
                    # Put selected values back in the original dimension positions.
                    key = [ALL] * width
                    for axis, value in zip(axes, values):
                        key[axis] = value
                    result[tuple(key)] = count
    return result


def duckdb_cube(rows, dimensions, minsup, batch_width=8):
    """Return reference counts from DuckDB CUBE, splitting large queries into batches."""
    frame = pd.DataFrame(rows, columns=dimensions)
    split = max(0, len(dimensions) - batch_width)
    # For 12 dimensions, 16 subsets of the first four × CUBE(last eight)
    # covers all 4,096 subsets. Smaller cubes need only one query.
    leading = dimensions[:split]
    trailing = dimensions[split:]
    result = {}
    with TemporaryDirectory(prefix="duckdb-") as sql_temp:
        config = {
            "memory_limit": "1500MB",
            "threads": "1",
            "temp_directory": sql_temp,
            "preserve_insertion_order": "false",
        }
        with duckdb.connect(config=config) as connection:
            connection.register("records", frame)
            for mask in product([False, True], repeat=split):
                # Fix one subset of leading dimensions; CUBE varies the rest.
                fixed = [name for name, include in zip(leading, mask) if include]
                select = [f'"{name}"' if include else f'NULL AS "{name}"'
                          for name, include in zip(leading, mask)]
                select += [f'"{name}"' for name in trailing]
                grouping = [f'"{name}"' for name in fixed]
                grouping.append("CUBE (" + ", ".join(f'"{name}"' for name in trailing) + ")")
                query = (
                    f"SELECT {', '.join(select)}, COUNT(*) AS support "
                    f"FROM records GROUP BY {', '.join(grouping)} "
                    f"HAVING COUNT(*) >= {int(minsup)}"
                )
                # SQL uses NULL for an unrestricted dimension; BUC uses ALL.
                for record in connection.execute(query).fetchall():
                    key = tuple(ALL if value is None else int(value) for value in record[:-1])
                    assert key not in result, "Grouping sets must be disjoint."
                    result[key] = int(record[-1])
    return result


def run_checks():
    """Check both BUC versions, hierarchy errors and invalid inputs."""
    # Cover support boundaries, empty input and repeated records.
    rng = np.random.default_rng(42)
    random_rows = np.column_stack([
        rng.integers(0, count, 500) for count in [2, 4, 3, 5]
    ]).astype(DTYPE)
    cases = [(f"random, support={support}", random_rows, [2, 4, 3, 5], support)
             for support in [1, 20, 100, 501]]
    cases += [
        ("empty", np.empty((0, 2), dtype=DTYPE), [2, 2], 1),
        ("one record", np.array([[1, 0]], dtype=DTYPE), [2, 2], 1),
        ("identical records", np.zeros((1000, 4), dtype=DTYPE), [1] * 4, 1000),
    ]
    unknown, _ = encode_frame(pd.DataFrame({
        "A": ["Unknown", "x", "x"], "B": ["y", "y", "z"]
    }), ["A", "B"])
    cases.append(("Unknown is different from ALL", unknown, [2, 2], 1))

    # Compare complete results with two independent counting methods.
    results = []
    with TemporaryDirectory() as directory:
        path = Path(directory) / "input.bin"
        for name, rows, cards, support in cases:
            dimensions = [f"d{i}" for i in range(len(cards))]
            expected = brute_force_cube(rows, support)
            assert expected == duckdb_cube(rows, dimensions, support)
            rows.tofile(path)
            # Both traversal orders must return the same keys and counts.
            for order in [None, dimension_order(cards)]:
                memory_cube, _ = buc_memory(rows, dimensions, cards, support, order=order)
                assert memory_cube == expected
                disk_cube = {}

                def collect(key, count):
                    assert key not in disk_cube
                    disk_cube[key] = count

                # A small allowance forces disk use in the larger test cases.
                stats = buc_disk(
                    path, dimensions, cards, support, 0.10,
                    order=order, emit=collect,
                )
                assert disk_cube == expected
                assert stats.peak_accounted_bytes <= stats.budget_bytes
            results.append({
                "case": name,
                "counts": len(expected),
                "disk_spills": stats.spills,
                "passed": True,
            })
    assert any(row["disk_spills"] > 0 for row in results)

    # Missing hierarchy mappings must fail instead of dropping values.
    hierarchies = load_hierarchies(Path(__file__).with_name("hierarchies.json"))
    for values, attribute in [(["unmapped qualification"], "education"), ([91], "age")]:
        try:
            generalize(pd.Series(values, name=attribute), hierarchies["attributes"][attribute], 1)
        except ValueError:
            pass
        else:
            raise AssertionError("A missing hierarchy mapping must raise an error.")
    # Minimum support is a positive record count.
    for support in [0, -1, 1.5]:
        try:
            buc_memory(random_rows, list("ABCD"), [2, 4, 3, 5], support)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid minimum support was accepted.")
    return pd.DataFrame(results)


if __name__ == "__main__":
    print(run_checks().to_string(index=False))
