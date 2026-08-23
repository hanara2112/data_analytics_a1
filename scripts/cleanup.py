"""Typed viewing table for listings.csv. Same rows, no imputation.

Reads the snapshot extract already explained: empty schema fields stay out of
the view; missing price is mostly `previous scrape`. Output is for plots, not
models. Import `clean` if you want the same transforms on another frame.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ARTIFACTS = ROOT / "artifacts"
EXPECTED_ROWS = 30_259  # this listings.csv; pass expected_rows=None to skip

KEEP = [
    "id",
    "host_id",
    "source",
    "neighbourhood_cleansed",
    "neighbourhood_group_cleansed",
    "latitude",
    "longitude",
    "host_name",
    "hosts_time_as_host_years",
    "hosts_time_as_host_months",
    "host_is_superhost",
    "host_identity_verified",
    "calculated_host_listings_count",
    "property_type",
    "room_type",
    "accommodates",
    "bathrooms",
    "bathrooms_text",
    "bedrooms",
    "beds",
    "amenities",
    "price",
    "price_quote_price_per_night",
    "price_quote_total_price",
    "price_quote_checkin_date",
    "price_quote_checkout_date",
    "minimum_nights",
    "maximum_nights",
    "has_availability",
    "availability_30",
    "availability_60",
    "availability_90",
    "availability_365",
    "number_of_reviews",
    "number_of_reviews_ltm",
    "first_review",
    "last_review",
    "review_scores_rating",
    "reviews_per_month",
    "license",
    "estimated_occupancy_l365d",
    "estimated_revenue_l365d",
]

BOOL_TF = (
    "host_is_superhost",
    "host_identity_verified",
    "has_availability",
)
DATES = (
    "first_review",
    "last_review",
    "price_quote_checkin_date",
    "price_quote_checkout_date",
)
NUMBERS = (
    "latitude",
    "longitude",
    "hosts_time_as_host_years",
    "hosts_time_as_host_months",
    "calculated_host_listings_count",
    "accommodates",
    "bathrooms",
    "bedrooms",
    "beds",
    "price_quote_price_per_night",
    "price_quote_total_price",
    "minimum_nights",
    "maximum_nights",
    "availability_30",
    "availability_60",
    "availability_90",
    "availability_365",
    "number_of_reviews",
    "number_of_reviews_ltm",
    "review_scores_rating",
    "reviews_per_month",
    "estimated_occupancy_l365d",
    "estimated_revenue_l365d",
)

NYC_LAT = (40.4, 41.0)
NYC_LON = (-74.3, -73.6)
LONG_STAY_MIN_NIGHTS = 30
# Viewing marks from this extract (99th pct ≈ $1,714). Not row filters.
PRICE_FLAG_LO, PRICE_FLAG_HI = 20.0, 2000.0
BLANK = {"", "none", "n/a", "na", "null"}
FLAGS = (
    "has_price",
    "has_reviews",
    "has_review_score",
    "is_previous_scrape",
    "is_long_stay_only",
    "is_multi_listing_host",
    "flag_geo_outside_nyc",
    "flag_price_extreme",
    "flag_zero_accommodates",
    "flag_quote_without_price",
    "flag_score_without_reviews",
)


def parse_money(series: pd.Series) -> pd.Series:
    stripped = series.astype("string").str.replace(r"[\$,]", "", regex=True)
    return pd.to_numeric(stripped, errors="coerce").astype("float64")


def flag_bool(series: pd.Series) -> pd.Series:
    """Comparisons on NA must be False for EDA flags, not a third state."""
    return series.fillna(False).astype(bool)


def tf_to_bool(series: pd.Series) -> pd.Series:
    """t/f → nullable boolean. Unmapped values, including NA, stay NA."""
    mapped = series.astype("string").str.strip().str.lower().map({"t": True, "f": False})
    return mapped.astype("boolean")


def count_amenities(series: pd.Series) -> pd.Series:
    def n(raw: object) -> int:
        if raw is None or (isinstance(raw, float) and pd.isna(raw)):
            return 0
        try:
            parsed = json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            return 0
        return len(parsed) if isinstance(parsed, list) else 0

    return series.map(n).astype("int64")


def blank_to_na(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.select_dtypes(include=["object", "string"]):
        as_str = out[col].astype("string").str.strip()
        out[col] = as_str.mask(as_str.str.lower().isin(BLANK), pd.NA)
    return out


def add_flags(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    priced = flag_bool(out["price_usd"].gt(0))
    in_nyc = flag_bool(
        out["latitude"].between(*NYC_LAT) & out["longitude"].between(*NYC_LON)
    )

    out["has_price"] = priced
    out["has_reviews"] = flag_bool(out["number_of_reviews"].gt(0))
    out["has_review_score"] = out["review_scores_rating"].notna()
    out["is_previous_scrape"] = out["source"].eq("previous scrape")
    out["is_long_stay_only"] = flag_bool(out["minimum_nights"].ge(LONG_STAY_MIN_NIGHTS))
    out["is_multi_listing_host"] = flag_bool(
        out["calculated_host_listings_count"].gt(1)
    )
    out["flag_geo_outside_nyc"] = ~in_nyc
    out["flag_price_extreme"] = priced & (
        out["price_usd"].lt(PRICE_FLAG_LO) | out["price_usd"].gt(PRICE_FLAG_HI)
    )
    out["flag_zero_accommodates"] = flag_bool(out["accommodates"].eq(0))
    out["flag_quote_without_price"] = out["price_quote_checkin_date"].notna() & ~priced
    out["flag_score_without_reviews"] = out["has_review_score"] & ~out["has_reviews"]
    return out


def clean(raw: pd.DataFrame, *, expected_rows: int | None = EXPECTED_ROWS) -> pd.DataFrame:
    if "id" not in raw.columns:
        raise KeyError("listings.csv needs an id column")
    if raw["id"].isna().any() or raw["id"].duplicated().any():
        raise ValueError("each row needs a unique id")
    if expected_rows is not None and len(raw) != expected_rows:
        raise ValueError(f"expected {expected_rows:,} rows, got {len(raw):,}")

    missing = [c for c in KEEP if c not in raw.columns]
    if missing:
        raise KeyError(f"missing columns: {missing}")

    df = blank_to_na(raw.loc[:, KEEP])
    for col in BOOL_TF:
        df[col] = tf_to_bool(df[col])
    for col in DATES:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in NUMBERS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["price_usd"] = parse_money(df.pop("price"))
    df["amenity_count"] = count_amenities(df["amenities"])
    df = add_flags(df)
    return df.rename(
        columns={
            "neighbourhood_group_cleansed": "borough",
            "neighbourhood_cleansed": "neighborhood",
        }
    )


def snapshot_log(df: pd.DataFrame, n_raw: int) -> str:
    priced = df.loc[df["has_price"], "price_usd"]
    lines = [
        f"cleanup {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"rows in/out: {n_raw:,} / {len(df):,}",
        f"columns: {df.shape[1]}",
        f"unique hosts: {df['host_id'].nunique():,}",
        "",
        "source × has_price",
        pd.crosstab(df["source"], df["has_price"], margins=True).to_string(),
        "",
        f"price_usd among has_price: n={len(priced):,}  "
        f"median={priced.median():.2f}  min={priced.min():.2f}  max={priced.max():.2f}",
        "host_is_superhost: "
        f"{int(df['host_is_superhost'].eq(True).sum())} true, "
        f"{int(df['host_is_superhost'].eq(False).sum())} false, "
        f"{int(df['host_is_superhost'].isna().sum())} NA",
        "",
        "flags",
    ]
    for col in FLAGS:
        lines.append(f"  {col:32s} {int(df[col].sum()):6d}")
    lines += [
        "",
        "do not treat estimated_occupancy / estimated_revenue as observed earnings",
        "amenities stays JSON text; amenity_count is the list length, not one-hot",
        "price_usd is a scrape quote (often a monthly-window nightly), not a booking",
        "previous scrape is a different population, not 'cheap'",
    ]
    return "\n".join(lines) + "\n"


def main(
    src: Path = ROOT / "listings.csv",
    dst: Path = ARTIFACTS / "listings_eda.csv",
    log_path: Path = ARTIFACTS / "cleanup_log.txt",
) -> None:
    raw = pd.read_csv(src, low_memory=False)
    view = clean(raw)
    if len(view) != len(raw):
        raise RuntimeError("cleanup must not drop rows")
    dst.parent.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    view.to_csv(dst, index=False)
    text = snapshot_log(view, len(raw))
    log_path.write_text(text, encoding="utf-8")
    print(text, end="")
    print(f"wrote {dst}")
    print(f"wrote {log_path}")


if __name__ == "__main__":
    main()
