"""Load the census data and form AOI rules using stored hierarchies."""

import json
from pathlib import Path

import pandas as pd

UNKNOWN = "Unknown"


def load_data(path):
    """Load all records and standardize missing values."""
    # Keep literal missing labels so pandas does not decide their meaning.
    data = pd.read_csv(path, keep_default_na=False)
    # Leave 'Not in universe' and repeated records unchanged.
    for column in data.select_dtypes(include="object"):
        data[column] = data[column].str.strip().replace(
            {"?": UNKNOWN, "NA": UNKNOWN, "": UNKNOWN}
        )
    return data


def load_hierarchies(path):
    """Read the grouping rules from JSON."""
    return json.loads(Path(path).read_text())


def generalize(series, hierarchy, level):
    """Apply hierarchy levels in order; reject values with no mapping."""
    if not 0 <= level <= len(hierarchy["levels"]):
        raise ValueError("Generalization level outside the hierarchy.")
    # JSON category keys are strings; level 0 keeps the original values.
    result = series.astype(str)
    for specification in hierarchy["levels"][:level]:
        if specification["kind"] == "all":
            result = pd.Series("ALL", index=series.index)
        elif specification["kind"] == "mapping":
            # Check coverage before mapping, so no records silently become missing.
            unseen = set(result.unique()) - set(specification["parents"])
            if unseen:
                raise ValueError(f"Unmapped values for {series.name}: {sorted(unseen)}")
            result = result.map(specification["parents"])
        elif specification["kind"] == "intervals":
            # Assign numeric values to inclusive bands, keeping Unknown separate.
            numeric = pd.to_numeric(result, errors="coerce")
            grouped = pd.Series(pd.NA, index=series.index, dtype="object")
            for interval in specification["intervals"]:
                mask = numeric.between(interval["minimum"], interval["maximum"], inclusive="both")
                if grouped[mask].notna().any():
                    raise ValueError("Overlapping hierarchy intervals.")
                grouped.loc[mask] = interval["parent"]
            grouped.loc[result.eq(UNKNOWN)] = UNKNOWN
            if grouped.isna().any():
                raise ValueError(f"Values outside hierarchy intervals for {series.name}")
            result = grouped
        else:
            raise ValueError(f"Unknown hierarchy kind: {specification['kind']}")
    return result


def check_hierarchies(data, hierarchies):
    """Check supplied summary columns and report values with multiple summaries."""
    reports = []
    for source, specification in hierarchies["attributes"].items():
        summary = specification.get("check_against")
        if summary is None:
            continue

        # Find detailed values that do not have a single summary.
        predicted = generalize(data[source], specification, 1)
        counts = data.groupby(source, dropna=False)[summary].nunique(dropna=False)
        ambiguous = set(counts[counts > 1].index.astype(str))
        declared = set(specification.get("ambiguous_values", {}))
        if ambiguous != declared:
            raise AssertionError(f"Ambiguity metadata disagrees for {source}")

        # Only unambiguous mappings can reproduce the supplied summary exactly.
        reliable = ~data[source].astype(str).isin(ambiguous)
        mismatches = int(predicted[reliable].ne(data.loc[reliable, summary].astype(str)).sum())
        if mismatches:
            raise AssertionError(f"Hierarchy reconstruction failed for {source}")
        reports.append({
            "source": source,
            "summary": summary,
            "source_values": len(counts),
            "ambiguous_values": len(ambiguous),
            "ambiguous_rows": int((~reliable).sum()),
            "checked_rows": int(reliable.sum()),
            "mismatches": mismatches,
        })
    return pd.DataFrame(reports)
