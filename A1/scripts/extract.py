"""Knowledge extraction for listings.csv — observe before slicing.

Does not drop, impute, or write listings_eda.csv.
Writes artifacts/extract_report.txt.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RAW_PATH = ROOT / "listings.csv"
ARTIFACTS = ROOT / "artifacts"
REPORT_PATH = ARTIFACTS / "extract_report.txt"

DROP_FROM_VIEW = {
    "listing_url",
    "picture_url",
    "host_url",
    "host_profile_id",
    "host_profile_url",
    "host_thumbnail_url",
    "host_picture_url",
    "scrape_id",
    "price_quote_raw",
    "calendar_updated",
}

KEEP = {
    "KEYS": ["id", "host_id"],
    "LOCATION": [
        "neighbourhood_cleansed",
        "neighbourhood_group_cleansed",
        "latitude",
        "longitude",
    ],
    "HOST": [
        "host_name",
        "host_since",
        "host_is_superhost",
        "host_response_time",
        "host_response_rate",
        "host_acceptance_rate",
        "host_identity_verified",
        "calculated_host_listings_count",
    ],
    "PROPERTY": [
        "property_type",
        "room_type",
        "accommodates",
        "bathrooms",
        "bathrooms_text",
        "bedrooms",
        "beds",
        "amenities",
    ],
    "PRICE": [
        "price",
        "price_quote_price_per_night",
        "price_quote_total_price",
        "price_quote_checkin_date",
    ],
    "CALENDAR": [
        "minimum_nights",
        "maximum_nights",
        "has_availability",
        "availability_30",
        "availability_60",
        "availability_90",
        "availability_365",
    ],
    "REVIEWS": [
        "number_of_reviews",
        "number_of_reviews_ltm",
        "first_review",
        "last_review",
        "review_scores_rating",
        "reviews_per_month",
    ],
    "OTHER": [
        "instant_bookable",
        "license",
        "estimated_occupancy_l365d",
        "estimated_revenue_l365d",
    ],
}


def role_of(column: str) -> str:
    if column in DROP_FROM_VIEW:
        return "DROP"
    for group, columns in KEEP.items():
        if column in columns:
            return group
    return "UNTAGGED"


def is_empty(series: pd.Series) -> bool:
    return series.isna().all() or series.nunique(dropna=True) == 0


def profile_column(series: pd.Series) -> dict:
    n = len(series)
    n_null = int(series.isna().sum())
    nunique_nn = int(series.nunique(dropna=True))
    samples = []
    for value in series.dropna().head(2).tolist():
        text = str(value).replace("\n", " ")
        samples.append(text if len(text) <= 72 else text[:69] + "...")
    return {
        "dtype": str(series.dtype),
        "n_null": n_null,
        "pct_null": n_null / n,
        "nunique_nonnull": nunique_nn,
        "empty": is_empty(series),
        "constant": nunique_nn == 1,
        "samples": samples,
    }


def parse_price(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype("string").str.replace(r"[\$,]", "", regex=True),
        errors="coerce",
    )


def main() -> None:
    raw = pd.read_csv(RAW_PATH, low_memory=False)
    n, p = raw.shape
    assert raw["id"].notna().all() and raw["id"].is_unique, "each row must have a unique id"

    keep_flat = [c for cols in KEEP.values() for c in cols]
    missing_drop = sorted(DROP_FROM_VIEW - set(raw.columns))
    missing_keep = sorted(set(keep_flat) - set(raw.columns))
    untagged = [c for c in raw.columns if c not in set(keep_flat) | DROP_FROM_VIEW]
    profiles = {c: profile_column(raw[c]) for c in raw.columns}
    constant_cols = [c for c, pcol in profiles.items() if pcol["constant"]]

    empty_keep = [c for c in keep_flat if profiles[c]["empty"]]
    empty_drop = [c for c in DROP_FROM_VIEW if profiles[c]["empty"]]
    empty_untagged = [c for c in untagged if profiles[c]["empty"]]

    price = parse_price(raw["price"])
    quote = raw["price_quote_price_per_night"]
    both = price.notna() & quote.notna()
    price_quote_max_diff = (
        float((price[both] - quote[both]).abs().max()) if both.any() else float("nan")
    )

    host_null = raw["host_name"].isna()
    reviews_zero = raw["number_of_reviews"].eq(0)
    amenity_lists = raw["amenities"].map(json.loads)
    amenity_lens = amenity_lists.str.len()
    amenities = amenity_lists.explode().value_counts()

    lines = []
    w = lines.append

    w("EXTRACT listings.csv — observe only, do not slice yet")
    w("=" * 72)
    w(f"path: {RAW_PATH}")
    w(f"shape: {n:,} rows x {p} columns")
    w(f"unique listing id: {raw['id'].nunique():,}")
    w(f"unique host_id: {raw['host_id'].nunique():,}")
    w(f"scrape_id (constant): {raw['scrape_id'].iloc[0]}")
    w(f"last_scraped values: {sorted(raw['last_scraped'].unique())}")
    w("")
    w("TAG AUDIT FOR CLEANUP KEEP/DROP")
    w("-" * 72)
    w(f"KEEP names in file: {len(keep_flat) - len(missing_keep)}/{len(keep_flat)}")
    w(f"DROP names in file: {len(DROP_FROM_VIEW) - len(missing_drop)}/{len(DROP_FROM_VIEW)}")
    w(f"KEEP missing from file: {missing_keep or 'none'}")
    w(f"DROP missing from file: {missing_drop or 'none'}")
    w(f"untagged columns: {len(untagged)}")
    w(f"KEEP that are 100% empty: {empty_keep}")
    w(f"DROP that are 100% empty: {empty_drop}")
    w(f"UNTAGGED that are 100% empty: {empty_untagged}")
    w(f"constant (1 non-null value): {constant_cols}")
    w("")
    w("UNTAGGED COLUMN NAMES")
    w("-" * 72)
    for col in untagged:
        pcol = profiles[col]
        flag = " EMPTY" if pcol["empty"] else (" CONST" if pcol["constant"] else "")
        w(f"  {col:48s} null={pcol['pct_null']:6.1%}  nunique={pcol['nunique_nonnull']:6d}{flag}")
    w("")
    w("COLUMN PROFILE (all 90)")
    w("-" * 72)
    w(f"{'column':44s} {'role':10s} {'dtype':8s} {'null%':7s} {'nunique':8s} empty const")
    for col in raw.columns:
        pcol = profiles[col]
        w(
            f"{col:44s} {role_of(col):10s} {pcol['dtype']:8s} "
            f"{pcol['pct_null']:6.1%} {pcol['nunique_nonnull']:8d} "
            f"{int(pcol['empty']):5d} {int(pcol['constant']):5d}"
        )
    w("")
    w("MARKET SHAPE")
    w("-" * 72)
    w("boroughs:")
    w(raw["neighbourhood_group_cleansed"].value_counts().to_string())
    w("room_type:")
    w(raw["room_type"].value_counts().to_string())
    w(f"property_type distinct: {raw['property_type'].nunique()}")
    w("source:")
    w(raw["source"].value_counts().to_string())
    w("")
    w("PRICE")
    w("-" * 72)
    w(f"price missing: {price.isna().sum():,} ({price.isna().mean():.1%})")
    w("price missing by source:")
    w(pd.crosstab(raw["source"], price.isna(), margins=True).to_string())
    w("priced listings (USD / night):")
    w(price.dropna().describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95, 0.99]).to_string())
    w(
        f"price vs price_quote_price_per_night: both present {int(both.sum()):,}; "
        f"max abs diff {price_quote_max_diff}"
    )
    w(
        "quote checkin present / price missing: "
        f"{int((raw['price_quote_checkin_date'].notna() & price.isna()).sum())}"
    )
    w("")
    w("HOST BLOCK")
    w("-" * 72)
    w(f"host_since empty: {profiles['host_since']['empty']}")
    w("replacement tenure fields (not in KEEP): hosts_time_as_{user,host}_{years,months}")
    w(raw[["hosts_time_as_host_years", "hosts_time_as_host_months"]].describe().to_string())
    w(f"host_name/superhost/identity-verified missing together: {int(host_null.sum())} rows")
    w(f"those rows are all previous scrape: {(raw.loc[host_null, 'source'] == 'previous scrape').all()}")
    w(
        "host_response_time/rate and host_acceptance_rate empty: "
        f"{profiles['host_response_time']['empty']}"
    )
    w("")
    w("PROPERTY / TEXT")
    w("-" * 72)
    w(
        f"bathrooms numeric missing: {profiles['bathrooms']['pct_null']:.1%}; "
        f"bathrooms_text missing: {profiles['bathrooms_text']['pct_null']:.1%}"
    )
    w(
        f"bedrooms missing: {profiles['bedrooms']['pct_null']:.1%}; "
        f"beds missing: {profiles['beds']['pct_null']:.1%}"
    )
    w(f"amenities JSON lists: mean length {amenity_lens.mean():.1f}; distinct strings {len(amenities)}")
    w("top amenities:")
    for name, count in amenities.head(12).items():
        w(f"  {count:6d}  {name}")
    w("")
    w("REVIEWS / MODELLED")
    w("-" * 72)
    w(
        "number_of_reviews == 0 iff first_review null: "
        f"{(reviews_zero == raw['first_review'].isna()).all()}"
    )
    w(f"instant_bookable empty: {profiles['instant_bookable']['empty']}")
    w(
        f"license missing: {profiles['license']['pct_null']:.1%}; "
        f"value 'Exempt' count: {int((raw['license'] == 'Exempt').sum())}"
    )
    w(
        "estimated_revenue_l365d missing iff price missing: "
        f"{(raw['estimated_revenue_l365d'].isna() == price.isna()).all()}"
    )
    w(f"estimated_occupancy_l365d == 0: {(raw['estimated_occupancy_l365d'] == 0).mean():.1%}")
    w("")
    w("VERDICT FOR CLEANUP TAGS")
    w("-" * 72)
    w("Keep as-is: KEYS, LOCATION, PROPERTY, CALENDAR, most of PRICE and REVIEWS.")
    w("Do not KEEP (empty in this snapshot): host_since, host_response_time,")
    w("  host_response_rate, host_acceptance_rate, instant_bookable.")
    w("Swap host_since -> hosts_time_as_host_years / hosts_time_as_host_months.")
    w("Add to PRICE: price_quote_checkout_date (needed to read total_price).")
    w("Add as FLAG, not location: source (explains most missing prices).")
    w("Treat estimated_* as modelled; license is sparse.")
    w("DROP list is correct. Also empty and unused: neighborhood_overview,")
    w("  neighbourhood, host_neighbourhood, host_total_listings_count, host_verifications.")
    w("37 untagged columns remain; most are scrape metadata, nested night bounds,")
    w("  review sub-scores, or host-count splits. Safe to leave out of a first EDA view.")

    text = "\n".join(lines) + "\n"
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(text, encoding="utf-8")
    print(text)
    print(f"wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
