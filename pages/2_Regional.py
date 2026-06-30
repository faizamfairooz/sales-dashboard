"""pages/2_Regional.py — Regional breakdown & US map"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import load_data
from utils.charts import region_donut, state_choropleth, PALETTE, LAYOUT_DEFAULTS

st.set_page_config(page_title="Regional", page_icon="🗺️", layout="wide")
st.title("🗺️ Regional analysis")

df = st.session_state.get("filtered_df", load_data())
if df.empty:
    st.warning("No data for current filters.")
    st.stop()

col1, col2 = st.columns([1, 2])
with col1:
    st.subheader("Revenue by region")
    st.plotly_chart(region_donut(df), use_container_width=True)
with col2:
    st.subheader("Revenue by US state")
    st.plotly_chart(state_choropleth(df), use_container_width=True)

st.divider()
st.subheader("Profit margin heatmap — region × category")
heat = (
    df.groupby(["region", "category"], observed=True)["profit_margin"]
    .mean().reset_index()
    .pivot(index="region", columns="category", values="profit_margin")
)
fig_heat = go.Figure(go.Heatmap(
    z=heat.values, x=heat.columns.tolist(), y=heat.index.tolist(),
    colorscale=[[0,"#D85A30"],[0.5,"#FFFFFF"],[1,"#1D9E75"]], zmid=0,
    text=[[f"{v:.1f}%" for v in row] for row in heat.values],
    texttemplate="%{text}",
    hovertemplate="Region:%{y}<br>Category:%{x}<br>Margin:%{z:.1f}%<extra></extra>",
    colorbar=dict(title="Avg margin (%)", ticksuffix="%"),
))
fig_heat.update_layout(**LAYOUT_DEFAULTS, height=300)
st.plotly_chart(fig_heat, use_container_width=True)

st.divider()
st.subheader("Revenue trend by region")
trend = (
    df.groupby(["year_month", "region"], observed=True)["sales"]
    .sum().reset_index()
    .rename(columns={"sales":"Revenue","year_month":"Month","region":"Region"})
)
fig_t = px.line(trend, x="Month", y="Revenue", color="Region",
                color_discrete_sequence=PALETTE)
fig_t.update_layout(**LAYOUT_DEFAULTS, yaxis_tickprefix="$", yaxis_tickformat=",.0f")
st.plotly_chart(fig_t, use_container_width=True)

st.divider()
st.subheader("Region detail table")
tbl = (
    df.groupby("region", observed=True)
    .agg(Revenue=("sales","sum"), Profit=("profit","sum"),
         Orders=("order_id","nunique"),
         Avg_Margin=("profit_margin","mean"),
         Avg_Ship_Days=("days_to_ship","mean"))
    .reset_index()
    .rename(columns={"region":"Region","Avg_Margin":"Avg margin (%)","Avg_Ship_Days":"Avg days to ship"})
    .sort_values("Revenue", ascending=False)
)
tbl["Revenue"]          = tbl["Revenue"].map("${:,.0f}".format)
tbl["Profit"]           = tbl["Profit"].map("${:,.0f}".format)
tbl["Avg margin (%)"]   = tbl["Avg margin (%)"].map("{:.1f}%".format)
tbl["Avg days to ship"] = tbl["Avg days to ship"].map("{:.1f}".format)
st.dataframe(tbl, use_container_width=True, hide_index=True)
