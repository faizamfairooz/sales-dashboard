"""
utils/charts.py
---------------
Reusable Plotly chart functions. Each returns a plotly Figure.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

BRAND_GREEN = "#1D9E75"
PALETTE = ["#1D9E75", "#378ADD", "#EF9F27", "#D85A30", "#7F77DD", "#D4537E"]

LAYOUT_DEFAULTS = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_family="sans-serif",
    font_color="#444441",
    margin=dict(l=16, r=16, t=40, b=16),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)


def monthly_trend(df: pd.DataFrame) -> go.Figure:
    monthly = (
        df.groupby("year_month", observed=True)[["sales", "profit"]]
        .sum()
        .reset_index()
        .rename(columns={"sales": "Revenue", "profit": "Profit"})
    )
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly["year_month"], y=monthly["Revenue"],
        name="Revenue", mode="lines+markers",
        line=dict(color=BRAND_GREEN, width=2), marker=dict(size=4),
    ))
    fig.add_trace(go.Scatter(
        x=monthly["year_month"], y=monthly["Profit"],
        name="Profit", mode="lines+markers",
        line=dict(color="#378ADD", width=2, dash="dot"), marker=dict(size=4),
    ))
    fig.update_layout(**LAYOUT_DEFAULTS, title="Monthly revenue & profit",
                      yaxis_tickprefix="$", yaxis_tickformat=",.0f")
    return fig


def category_bar(df: pd.DataFrame, metric: str = "sales") -> go.Figure:
    data = (
        df.groupby(["category", "sub_category"], observed=True)[metric]
        .sum().reset_index().sort_values(metric, ascending=False)
    )
    fig = px.bar(data, x="sub_category", y=metric, color="category",
                 color_discrete_sequence=PALETTE,
                 labels={"sub_category": "Sub-category", metric: metric.title()},
                 title=f"{metric.title()} by sub-category")
    fig.update_layout(**LAYOUT_DEFAULTS, xaxis_tickangle=-35)
    fig.update_yaxes(tickprefix="$", tickformat=",.0f")
    return fig


def region_donut(df: pd.DataFrame, metric: str = "sales") -> go.Figure:
    data = df.groupby("region", observed=True)[metric].sum().reset_index()
    fig = go.Figure(go.Pie(
        labels=data["region"], values=data[metric],
        hole=0.55, marker_colors=PALETTE,
        textinfo="label+percent",
        hovertemplate="%{label}: $%{value:,.0f}<extra></extra>",
    ))
    fig.update_layout(**LAYOUT_DEFAULTS, title="Revenue by region", showlegend=False)
    return fig


def top_bottom_products(df: pd.DataFrame, n: int = 10) -> go.Figure:
    prod = (
        df.groupby("product_name", observed=True)
        .agg(profit_margin=("profit_margin", "mean"), revenue=("sales", "sum"))
        .reset_index().dropna(subset=["profit_margin"])
    )
    combined = pd.concat([prod.nlargest(n, "profit_margin"),
                          prod.nsmallest(n, "profit_margin")]).drop_duplicates()
    combined["color"] = combined["profit_margin"].apply(
        lambda x: BRAND_GREEN if x >= 0 else "#D85A30"
    )
    fig = go.Figure(go.Bar(
        x=combined["profit_margin"], y=combined["product_name"],
        orientation="h", marker_color=combined["color"],
        hovertemplate="<b>%{y}</b><br>Margin: %{x:.1f}%<extra></extra>",
    ))
    layout = {**LAYOUT_DEFAULTS, "margin": dict(l=260, r=16, t=40, b=16)}
    fig.update_layout(**layout,
                      title=f"Top & bottom {n} products by profit margin",
                      xaxis_title="Avg profit margin (%)", yaxis_title=None,
                      height=600)
    return fig


def state_choropleth(df: pd.DataFrame, metric: str = "sales") -> go.Figure:
    # Use state abbreviations if available, else full names
    state_col = "state"
    state_data = df.groupby(state_col, observed=True)[metric].sum().reset_index()
    fig = px.choropleth(
        state_data, locations=state_col, locationmode="USA-states",
        color=metric, scope="usa",
        color_continuous_scale=[[0, "#E1F5EE"], [0.5, BRAND_GREEN], [1, "#04342C"]],
        labels={metric: metric.title()},
        hover_name=state_col, hover_data={metric: ":$,.0f"},
        title=f"{metric.title()} by state",
    )
    fig.update_layout(**LAYOUT_DEFAULTS)
    return fig


def discount_profit_scatter(df: pd.DataFrame) -> go.Figure:
    sample = df.sample(min(len(df), 2000), random_state=42)
    fig = px.scatter(
        sample, x="discount", y="profit_margin", color="category",
        color_discrete_sequence=PALETTE, opacity=0.55,
        labels={"discount": "Discount rate", "profit_margin": "Profit margin (%)"},
        title="Discount rate vs profit margin",
        hover_data=["product_name", "sales"],
    )
    fig.add_hline(y=0, line_dash="dash", line_color="#999", line_width=1)
    fig.update_layout(**LAYOUT_DEFAULTS)
    return fig


def ship_mode_bar(df: pd.DataFrame) -> go.Figure:
    data = (
        df.groupby("ship_mode", observed=True)
        .agg(orders=("order_id", "nunique"), avg_days=("days_to_ship", "mean"))
        .reset_index().sort_values("orders", ascending=False)
    )
    fig = go.Figure()
    fig.add_trace(go.Bar(x=data["ship_mode"], y=data["orders"],
                         name="Orders", marker_color=BRAND_GREEN))
    fig.add_trace(go.Scatter(
        x=data["ship_mode"], y=data["avg_days"],
        name="Avg days to ship", mode="markers",
        marker=dict(color="#EF9F27", size=12, symbol="diamond"), yaxis="y2",
    ))
    fig.update_layout(
        **LAYOUT_DEFAULTS, title="Shipping mode — orders & avg days to ship",
        yaxis=dict(title="Orders"),
        yaxis2=dict(title="Avg days", overlaying="y", side="right", showgrid=False),
    )
    return fig
