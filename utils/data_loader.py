"""
utils/data_loader.py
--------------------
Cached data loading and filtering shared across all pages.
"""

from pathlib import Path
import pandas as pd
import streamlit as st

CLEAN_PATH = Path("data/superstore_clean.parquet")


@st.cache_data(show_spinner="Loading data…")
def load_data() -> pd.DataFrame:
    if not CLEAN_PATH.exists():
        st.error(
            "**Clean data not found.**  \n"
            "Please run `python data_cleaning.py` first, then refresh."
        )
        st.stop()
    return pd.read_parquet(CLEAN_PATH)


def apply_filters(df, date_range, regions, categories, segments) -> pd.DataFrame:
    start = pd.Timestamp(date_range[0])
    end   = pd.Timestamp(date_range[1])
    mask  = (df["order_date"] >= start) & (df["order_date"] <= end)
    if regions:
        mask &= df["region"].isin(regions)
    if categories:
        mask &= df["category"].isin(categories)
    if segments:
        mask &= df["segment"].isin(segments)
    return df[mask].copy()


def get_kpis(df: pd.DataFrame) -> dict:
    total_sales  = df["sales"].sum()
    total_profit = df["profit"].sum()
    return {
        "total_revenue":   total_sales,
        "total_profit":    total_profit,
        "profit_margin":   (total_profit / total_sales * 100) if total_sales else 0,
        "total_orders":    df["order_id"].nunique(),
        "avg_order_value": df.groupby("order_id")["sales"].sum().mean(),
        "total_customers": df["customer_id"].nunique() if "customer_id" in df.columns else 0,
    }
