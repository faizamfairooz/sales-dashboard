"""pages/3_Products.py — Product-level analysis"""

import streamlit as st
import plotly.express as px
from utils.data_loader import load_data
from utils.charts import top_bottom_products, discount_profit_scatter, PALETTE, LAYOUT_DEFAULTS

st.set_page_config(page_title="Products", page_icon="📦", layout="wide")
st.title("📦 Product analysis")

df = st.session_state.get("filtered_df", load_data())
if df.empty:
    st.warning("No data for current filters.")
    st.stop()

st.subheader("Top & bottom products by profit margin")
n = st.slider("Products per side", 5, 20, 10, step=5)
st.plotly_chart(top_bottom_products(df, n), use_container_width=True)

st.divider()
st.subheader("Does discounting hurt profit?")
st.caption("Dashed line = break-even (0% margin).")
st.plotly_chart(discount_profit_scatter(df), use_container_width=True)

st.divider()
st.subheader("Revenue treemap — category → sub-category")
tree = (
    df.groupby(["category","sub_category"], observed=True)[["sales","profit"]]
    .sum().reset_index()
    .rename(columns={"sales":"Revenue","profit":"Profit","category":"Category","sub_category":"Sub-category"})
)
tree["Margin (%)"] = (tree["Profit"] / tree["Revenue"] * 100).round(1)
fig_tree = px.treemap(tree, path=["Category","Sub-category"], values="Revenue",
                      color="Margin (%)",
                      color_continuous_scale=[[0,"#D85A30"],[0.5,"#FFFFFF"],[1,"#1D9E75"]],
                      color_continuous_midpoint=0,
                      hover_data={"Revenue":":$,.0f","Margin (%)":":.1f"})
fig_tree.update_layout(**LAYOUT_DEFAULTS, height=480,
                       coloraxis_colorbar=dict(title="Margin (%)"))
st.plotly_chart(fig_tree, use_container_width=True)

st.divider()
st.subheader("Revenue & profit by segment")
seg = (
    df.groupby("segment", observed=True)[["sales","profit"]]
    .sum().reset_index()
    .rename(columns={"sales":"Revenue","profit":"Profit","segment":"Segment"})
)
import plotly.graph_objects as go
fig_seg = go.Figure()
fig_seg.add_trace(go.Bar(x=seg["Segment"], y=seg["Revenue"], name="Revenue", marker_color=PALETTE[0]))
fig_seg.add_trace(go.Bar(x=seg["Segment"], y=seg["Profit"],  name="Profit",  marker_color=PALETTE[1]))
fig_seg.update_layout(**LAYOUT_DEFAULTS, barmode="group",
                      yaxis_tickprefix="$", yaxis_tickformat=",.0f")
st.plotly_chart(fig_seg, use_container_width=True)

st.divider()
st.subheader("🔍 Product search")
search = st.text_input("Search product name", placeholder="e.g. Chair")
prod = (
    df.groupby("product_name", observed=True)
    .agg(Category=("category","first"), Sub=("sub_category","first"),
         Revenue=("sales","sum"), Profit=("profit","sum"),
         Orders=("order_id","nunique"), Margin=("profit_margin","mean"))
    .reset_index()
    .rename(columns={"product_name":"Product","Sub":"Sub-category","Margin":"Avg margin (%)"})
    .sort_values("Revenue", ascending=False)
)
if search:
    prod = prod[prod["Product"].str.contains(search, case=False, na=False)]
prod["Revenue"]        = prod["Revenue"].map("${:,.0f}".format)
prod["Profit"]         = prod["Profit"].map("${:,.0f}".format)
prod["Avg margin (%)"] = prod["Avg margin (%)"].map("{:.1f}%".format)
st.dataframe(prod, use_container_width=True, height=400, hide_index=True)
