"""
data_cleaning.py
----------------
Run ONCE to clean the raw Superstore CSV → saves a fast parquet file.

    python data_cleaning.py

Works on Python 3.8 – 3.14. Uses explicit format strings for all date
parsing to avoid pandas/Cython cache bugs on newer Python versions.
"""

import sys
import pandas as pd
from pathlib import Path

RAW_PATH   = Path("data/superstore.csv")
CLEAN_PATH = Path("data/superstore_clean.parquet")


def load_raw(path: Path) -> pd.DataFrame:
    """Try multiple encodings — Superstore CSVs vary by source."""
    for enc in ("latin-1", "utf-8", "cp1252", "iso-8859-1"):
        try:
            df = pd.read_csv(path, encoding=enc)
            print(f"  Encoding used: {enc}")
            return df
        except (UnicodeDecodeError, Exception):
            continue
    raise ValueError(f"Could not read {path} with any common encoding.")


def _parse_dates(series: pd.Series) -> pd.Series:
    """
    Parse date strings safely on all Python / pandas versions.
    Tries explicit formats first, then falls back to infer_datetime_format=False.
    Never uses the cache path that crashes on Python 3.14.
    """
    sample = series.dropna().iloc[0] if len(series.dropna()) else ""

    # Detect separator and try matching formats
    for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d", "%m-%d-%Y", "%d-%m-%Y"):
        try:
            result = pd.to_datetime(series, format=fmt, errors="raise")
            return result
        except (ValueError, TypeError):
            continue

    # Last resort: let pandas infer without caching
    return pd.to_datetime(series, infer_datetime_format=False,
                          errors="coerce", cache=False)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    # ── 1. Normalise column names ─────────────────────────────────────────
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(r"[\s\-]+", "_", regex=True)
    )

    # ── 2. Parse dates (no cache — avoids Python 3.14 numpy bug) ─────────
    df["order_date"] = _parse_dates(df["order_date"])
    df["ship_date"]  = _parse_dates(df["ship_date"])

    # ── 3. Drop duplicates & nulls ────────────────────────────────────────
    key_cols = [c for c in ["order_id", "product_id"] if c in df.columns]
    if key_cols:
        df = df.drop_duplicates(subset=key_cols)
    df = df.dropna(subset=["sales", "profit", "quantity"])

    # ── 4. Derived columns ────────────────────────────────────────────────
    df["days_to_ship"]     = (df["ship_date"] - df["order_date"]).dt.days
    df["profit_margin"]    = (df["profit"] / df["sales"].replace(0, float("nan"))) * 100
    df["year"]             = df["order_date"].dt.year
    df["month"]            = df["order_date"].dt.month
    df["year_month"]       = df["order_date"].dt.to_period("M").astype(str)
    df["revenue_per_unit"] = df["sales"] / df["quantity"].replace(0, float("nan"))

    # ── 5. Categorical columns ────────────────────────────────────────────
    cat_cols = ["category", "sub_category", "region", "segment",
                "ship_mode", "state", "country"]
    for col in cat_cols:
        if col in df.columns:
            df[col] = df[col].astype("category")

    # ── 6. Remove extreme margin outliers ─────────────────────────────────
    df = df[df["profit_margin"].between(-300, 300, inclusive="both")]

    return df.reset_index(drop=True)


def main():
    print(f"Python  {sys.version}")
    print(f"Pandas  {pd.__version__}")
    print()

    if not RAW_PATH.exists():
        print(f"ERROR: {RAW_PATH} not found.")
        print("Download from: kaggle.com/datasets/vivek468/superstore-dataset-final")
        print("Then save it as:  data/superstore.csv")
        sys.exit(1)

    print(f"Loading  → {RAW_PATH}")
    raw = load_raw(RAW_PATH)
    print(f"  Rows loaded  : {len(raw):,}")
    print(f"  Columns      : {list(raw.columns)[:6]} …")

    cleaned = clean(raw)
    print(f"  Rows cleaned : {len(cleaned):,}")

    CLEAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_parquet(CLEAN_PATH, index=False)
    print(f"\nSaved  → {CLEAN_PATH}")
    print("\nColumn dtypes:")
    print(cleaned.dtypes.to_string())
    print("\n✅ Done! You can now run:  streamlit run app.py")


if __name__ == "__main__":
    main()
