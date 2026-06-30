"""
app.py  —  Homepage & shared sidebar
Run with:  streamlit run app.py
"""

import streamlit as st
import pandas as pd
from utils.data_loader import load_data, apply_filters, get_kpis

st.set_page_config(
    page_title="Sales Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
[data-testid="stMetricValue"] { font-size: 1.6rem; font-weight: 600; }
.block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# ── Load ──────────────────────────────────────────────────────────────────
df = load_data()

# ── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📊 Sales Dashboard")
    st.markdown("---")

    min_date = df["order_date"].min().date()
    max_date = df["order_date"].max().date()
    date_range = st.date_input(
        "Order date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    regions    = st.multiselect("Region",   sorted(df["region"].unique()),   default=sorted(df["region"].unique()))
    categories = st.multiselect("Category", sorted(df["category"].unique()), default=sorted(df["category"].unique()))
    segments   = st.multiselect("Segment",  sorted(df["segment"].unique()),  default=sorted(df["segment"].unique()))

    st.markdown("---")
    st.caption("Superstore dataset · statsmodels · Streamlit")

# ── Filter ────────────────────────────────────────────────────────────────
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    filtered = apply_filters(df, date_range, regions, categories, segments)
else:
    filtered = df.copy()

st.session_state["filtered_df"] = filtered

# ── Homepage ──────────────────────────────────────────────────────────────
st.title("📊 Superstore Sales Dashboard")
st.markdown(
    "Interactive analytics dashboard — **Streamlit · Pandas · Plotly · statsmodels**. "
    "Use the sidebar to filter by date, region, category, and segment."
)
st.divider()

# ── KPIs ──────────────────────────────────────────────────────────────────
kpis = get_kpis(filtered)
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("💰 Revenue",       f"${kpis['total_revenue']:,.0f}")
c2.metric("📈 Profit",        f"${kpis['total_profit']:,.0f}")
c3.metric("🎯 Margin",        f"{kpis['profit_margin']:.1f}%")
c4.metric("🛒 Orders",        f"{kpis['total_orders']:,}")
c5.metric("🧾 Avg order",     f"${kpis['avg_order_value']:,.0f}")
c6.metric("👥 Customers",     f"{kpis['total_customers']:,}")

st.divider()

# ── Category summary ──────────────────────────────────────────────────────
st.subheader("Revenue & profit by category")
cat_summary = (
    filtered.groupby("category", observed=True)
    .agg(Revenue=("sales","sum"), Profit=("profit","sum"),
         Orders=("order_id","nunique"), Avg_Margin=("profit_margin","mean"))
    .reset_index()
    .rename(columns={"category":"Category","Avg_Margin":"Avg margin (%)"})
    .sort_values("Revenue", ascending=False)
)
cat_summary["Revenue"]       = cat_summary["Revenue"].map("${:,.0f}".format)
cat_summary["Profit"]        = cat_summary["Profit"].map("${:,.0f}".format)
cat_summary["Avg margin (%)"] = cat_summary["Avg margin (%)"].map("{:.1f}%".format)
st.dataframe(cat_summary, use_container_width=True, hide_index=True)

st.divider()

# ── Raw data ──────────────────────────────────────────────────────────────
with st.expander("🔍 Raw filtered data"):
    st.dataframe(filtered.sort_values("order_date", ascending=False),
                 use_container_width=True, height=400)
    st.download_button("⬇️ Download CSV",
                       data=filtered.to_csv(index=False).encode(),
                       file_name="superstore_filtered.csv", mime="text/csv")
