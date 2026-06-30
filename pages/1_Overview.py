"""pages/1_Overview.py — Revenue & profit trends"""

import streamlit as st
import plotly.express as px
from utils.data_loader import load_data
from utils.charts import monthly_trend, category_bar, ship_mode_bar, PALETTE, LAYOUT_DEFAULTS

st.set_page_config(page_title="Overview", page_icon="📈", layout="wide")
st.title("📈 Overview — Trends & performance")

df = st.session_state.get("filtered_df", load_data())
if df.empty:
    st.warning("No data for current filters.")
    st.stop()

st.subheader("Monthly revenue & profit")
st.plotly_chart(monthly_trend(df), use_container_width=True)

st.divider()
col1, col2 = st.columns(2)
with col1:
    st.subheader("Revenue by sub-category")
    st.plotly_chart(category_bar(df, "sales"), use_container_width=True)
with col2:
    st.subheader("Profit by sub-category")
    st.plotly_chart(category_bar(df, "profit"), use_container_width=True)

st.divider()
st.subheader("Shipping mode performance")
st.plotly_chart(ship_mode_bar(df), use_container_width=True)

st.divider()
st.subheader("Year-on-year revenue by category")
yoy = (
    df.groupby(["year", "category"], observed=True)["sales"]
    .sum().reset_index()
    .rename(columns={"sales":"Revenue","year":"Year","category":"Category"})
)
fig = px.bar(yoy, x="Year", y="Revenue", color="Category", barmode="group",
             color_discrete_sequence=PALETTE)
fig.update_layout(**LAYOUT_DEFAULTS, yaxis_tickprefix="$", yaxis_tickformat=",.0f")
st.plotly_chart(fig, use_container_width=True)
