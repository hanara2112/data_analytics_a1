"""Count groups meeting minimum support without dataframe grouping or SQL.

Category codes are nonnegative int32 values; -1 means ALL. Result keys always
follow the original dimension order. The disk memory allowance covers encoded
records and algorithm workspace, not the entire Python process.
"""

import csv
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

ALL = -1
DTYPE = np.dtype("<i4")


@dataclass
class Stats:
    """Counts and estimated memory use for one BUC run."""

    cells: int = 0
    partitions: int = 0
    pruned: int = 0
    spills: int = 0
    budget_bytes: int = 0
    peak_accounted_bytes: int = 0


def encode_frame(frame, dimensions):
    """Encode categories once; retain labels for interpreting the result."""
    # Sorted labels give the same codes to the memory and disk versions.
    labels = {name: sorted(frame[name].astype(str).unique()) for name in dimensions}
    codes = np.empty((len(frame), len(dimensions)), dtype=DTYPE)
    for index, name in enumerate(dimensions):
        lookup = {label: code for code, label in enumerate(labels[name])}
        codes[:, index] = frame[name].astype(str).map(lookup).to_numpy()
    return codes, labels


def encode_csv(csv_path, output_path, dimensions, labels):
    """Encode the CSV one row at a time using the supplied category labels."""
    lookups = {
        name: {label: code for code, label in enumerate(labels[name])}
        for name in dimensions
    }
    row = np.empty(len(dimensions), dtype=DTYPE)
    with open(csv_path, newline="") as source, open(output_path, "wb") as target:
        for record in csv.DictReader(source):
            for index, name in enumerate(dimensions):
                value = record[name].strip()
                # Match the missing-value handling in aoi.load_data.
                if value in {"", "?", "NA"}:
                    value = "Unknown"
                row[index] = lookups[name][value]
            target.write(row.tobytes())


def _validate(dimensions, cardinalities, minsup, measure, order):
    """Check cube settings and return the dimension traversal order."""
    if measure != "count":
        raise ValueError("This implementation supports measure='count' (COUNT(*)).")
    if not isinstance(minsup, (int, np.integer)) or minsup < 1:
        raise ValueError("minsup must be a positive integer record count.")
    if not dimensions or len(set(dimensions)) != len(dimensions):
        raise ValueError("Provide a nonempty list of distinct dimensions.")
    if len(cardinalities) != len(dimensions) or any(c < 1 for c in cardinalities):
        raise ValueError("Each dimension needs a positive codebook cardinality.")
    # Reordering changes traversal, not the dimension positions in result keys.
    if order is None:
        order = list(range(len(dimensions)))
    if sorted(order) != list(range(len(dimensions))):
        raise ValueError("order must be a permutation of dimension indices.")
    return list(order)


def dimension_order(cardinalities):
    """Try dimensions with more distinct values first to form small groups earlier."""
    return sorted(range(len(cardinalities)), key=lambda i: (-cardinalities[i], i))


def _check_codes(rows, cardinalities):
    """Check the array shape, storage type and category-code ranges."""
    if rows.ndim != 2 or rows.shape[1] != len(cardinalities) or rows.dtype != DTYPE:
        raise ValueError("Expected a two-dimensional little-endian int32 array.")
    if len(rows) and any(rows[:, i].min() < 0 or rows[:, i].max() >= card
                         for i, card in enumerate(cardinalities)):
        raise ValueError("Category code outside its codebook.")


def _visit(rows, start, key, order, cards, minsup, emit, stats):
    """Count the current group, then recursively split it by remaining dimensions."""
    # Adding conditions cannot increase a group's count.
    if len(rows) < minsup:
        stats.pruned += 1
        return
    emit(tuple(key), len(rows))
    stats.cells += 1

    # Only use later dimensions so each combination is visited once.
    for position in range(start, len(order)):
        axis = order[position]
        counts = np.bincount(rows[:, axis], minlength=cards[axis])
        stats.partitions += int(np.count_nonzero(counts))
        if not np.any(counts >= minsup):
            stats.pruned += int(np.count_nonzero(counts))
            continue
        # Sort equal values together, then pass slices without copying each child.
        rows[:] = rows[np.argsort(rows[:, axis], kind="quicksort")]
        offset = 0
        for value, count in enumerate(counts):
            count = int(count)
            if count >= minsup:
                key[axis] = value
                _visit(rows[offset:offset + count], position + 1, key,
                       order, cards, minsup, emit, stats)
            elif count:
                stats.pruned += 1
            offset += count
        # Remove this condition before trying the next dimension.
        key[axis] = ALL


def buc_memory(rows, dimensions, cardinalities, minsup, measure="count", *,
               order=None, emit=None):
    """Return a count cube and statistics, leaving input rows unchanged.

    With emit supplied, send each (key, count) to it and return None as the cube.
    """
    order = _validate(dimensions, cardinalities, minsup, measure, order)
    _check_codes(rows, cardinalities)

    # Collect results by default; a supplied callback can write them elsewhere.
    result = {} if emit is None else None
    if emit is None:
        def emit(key, count):
            result[key] = count

    stats = Stats()
    # Recursion sorts its input, so work on a copy.
    working = rows.copy()
    _visit(working, 0, [ALL] * len(dimensions), order, cardinalities,
           minsup, emit, stats)
    return result, stats


def buc_disk(input_path, dimensions, cardinalities, minsup, memory_mb,
             measure="count", *, order=None, emit, temp_dir=None):
    """Count a cube from an encoded file, spilling groups that exceed the allowance.

    Input is a headerless int32 file in the original dimension order. Results go
    through emit; any memory used by that callback is outside the allowance.
    """
    order = _validate(dimensions, cardinalities, minsup, measure, order)
    width = len(dimensions)
    row_bytes = width * DTYPE.itemsize
    budget = int(memory_mb * 1024**2)
    # Leave room for recursion, file paths, group counts and an output row.
    reserve = 65536 + 4096 * width + 64 * sum(cardinalities)
    # Estimate space for records, sorting and temporary NumPy arrays.
    workspace_per_row = 3 * row_bytes + 32
    capacity = (budget - reserve) // workspace_per_row
    if capacity < 1:
        raise ValueError(f"Budget too small; require more than {reserve + workspace_per_row} bytes.")

    # Each file must contain a whole number of fixed-width records.
    size = Path(input_path).stat().st_size
    if size % row_bytes:
        raise ValueError("Truncated encoded input file.")
    stats = Stats(budget_bytes=budget, peak_accounted_bytes=reserve)
    key = [ALL] * width

    def pages(path):
        """Read at most capacity records at a time."""
        with open(path, "rb", buffering=0) as source:
            while True:
                block = np.fromfile(source, dtype=DTYPE, count=capacity * width)
                if not block.size:
                    break
                block = block.reshape(-1, width)
                _check_codes(block, cardinalities)
                stats.peak_accounted_bytes = max(
                    stats.peak_accounted_bytes,
                    reserve + len(block) * workspace_per_row)
                yield block
                # Free this page before allocating its successor.
                del block

    with TemporaryDirectory(prefix="buc-", dir=temp_dir) as root:
        serial = 0

        def visit_file(path, count, start):
            nonlocal serial
            if count < minsup:
                stats.pruned += 1
                return

            # A fitting group can use the same in-memory recursion.
            if count <= capacity:
                block = np.fromfile(path, dtype=DTYPE).reshape(-1, width)
                _check_codes(block, cardinalities)
                stats.peak_accounted_bytes = max(
                    stats.peak_accounted_bytes, reserve + count * workspace_per_row)
                _visit(block, start, key, order, cardinalities, minsup, emit, stats)
                return

            # Count an oversized group without loading it all at once.
            emit(tuple(key), count)
            stats.cells += 1
            for position in range(start, width):
                axis = order[position]
                counts = np.zeros(cardinalities[axis], dtype=np.int64)
                # First pass: find child groups that meet minimum support.
                for block in pages(path):
                    counts += np.bincount(block[:, axis], minlength=len(counts))
                    del block
                stats.partitions += int(np.count_nonzero(counts))
                stats.pruned += int(np.count_nonzero((counts > 0) & (counts < minsup)))
                children = {}
                for value in np.flatnonzero(counts >= minsup):
                    serial += 1
                    children[int(value)] = Path(root) / f"{serial}.bin"
                if not children:
                    continue

                # Second pass: write only those children to separate files.
                for block in pages(path):
                    for value, child_path in children.items():
                        selected = block[block[:, axis] == value]
                        if len(selected):
                            with open(child_path, "ab", buffering=0) as target:
                                selected.tofile(target)
                        del selected
                    del block
                stats.spills += len(children)
                # Free each child's file after processing; no parent pages stay in memory.
                for value, child_path in children.items():
                    key[axis] = value
                    visit_file(child_path, int(counts[value]), position + 1)
                    child_path.unlink()
                key[axis] = ALL

        visit_file(Path(input_path), size // row_bytes, 0)
    # TemporaryDirectory removes any remaining files, including after an error.
    assert stats.peak_accounted_bytes <= stats.budget_bytes
    return stats
