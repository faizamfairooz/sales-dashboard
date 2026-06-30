"""
pages/4_Forecast.py  —  90-day revenue forecast
Tries Prophet first. Falls back to statsmodels ARIMA automatically
if Prophet isn't installed or fails to import.
"""

import streamlit as st
import pandas as pd
from io import StringIO
import plotly.graph_objects as go
from utils.data_loader import load_data
from utils.charts import BRAND_GREEN, LAYOUT_DEFAULTS

st.set_page_config(page_title="Forecast", page_icon="🔮", layout="wide")
st.title("🔮 90-day revenue forecast")

df = st.session_state.get("filtered_df", load_data())

if df.empty:
    st.warning("No data matches the current filters.")
    st.stop()

# ── Detect which forecasting backend actually works ────────────────────────
try:
    from prophet import Prophet
    _test_model = Prophet()  # forces Stan backend to load — catches broken installs
    del _test_model
    BACKEND = "prophet"
except Exception:
    BACKEND = "arima"
    st.info(
        "ℹ️ Prophet's Stan backend isn't available on this machine — using "
        "statsmodels ARIMA instead. Results are still solid! To fix Prophet, try: "
        "`pip uninstall prophet cmdstanpy -y && pip install prophet --no-cache-dir`"
    )

st.caption(f"Backend: **{'Facebook Prophet' if BACKEND == 'prophet' else 'statsmodels ARIMA'}**")

with st.sidebar:
    st.markdown("---")
    st.subheader("Forecast settings")
    horizon = st.slider("Forecast horizon (days)", 30, 180, 90, step=30)
    if BACKEND == "prophet":
        show_components = st.checkbox("Show seasonality components", value=False)


@st.cache_data(show_spinner="Preparing data…")
def make_daily(df_json: str) -> pd.DataFrame:
    daily = (
        pd.read_json(StringIO(df_json))
        .rename(columns={"order_date": "ds", "sales": "y"})
        [["ds", "y"]]
    )
    daily["ds"] = pd.to_datetime(daily["ds"])
    return daily.groupby("ds")["y"].sum().reset_index()


df_slim = df[["order_date", "sales"]].copy()
df_slim["order_date"] = df_slim["order_date"].astype(str)
daily = make_daily(df_slim.to_json())


# ══════════════════════════════════════════════════════════════════════════
#  PROPHET PATH
# ══════════════════════════════════════════════════════════════════════════
if BACKEND == "prophet":

    @st.cache_data(show_spinner="Training Prophet model…")
    def run_prophet(data_hash: str, daily_json: str, periods: int):
        d = pd.read_json(StringIO(daily_json))
        d["ds"] = pd.to_datetime(d["ds"])
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            changepoint_prior_scale=0.05,
        )
        model.fit(d)
        future = model.make_future_dataframe(periods=periods, freq="D")
        forecast = model.predict(future)
        return d, forecast

    data_hash = str(len(daily)) + str(daily["ds"].max())
    daily_data, forecast = run_prophet(data_hash, daily.to_json(), horizon)
    cutoff = daily_data["ds"].max()
    hist_fc = forecast[forecast["ds"] <= cutoff]
    future_fc = forecast[forecast["ds"] > cutoff]

    st.subheader(f"Daily revenue — actuals + {horizon}-day Prophet forecast")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=pd.concat([hist_fc["ds"], hist_fc["ds"].iloc[::-1]]),
        y=pd.concat([hist_fc["yhat_upper"], hist_fc["yhat_lower"].iloc[::-1]]),
        fill="toself", fillcolor="rgba(29,158,117,0.12)",
        line=dict(color="rgba(0,0,0,0)"), name="CI (historical)",
    ))
    fig.add_trace(go.Scatter(
        x=pd.concat([future_fc["ds"], future_fc["ds"].iloc[::-1]]),
        y=pd.concat([future_fc["yhat_upper"], future_fc["yhat_lower"].iloc[::-1]]),
        fill="toself", fillcolor="rgba(55,138,221,0.15)",
        line=dict(color="rgba(0,0,0,0)"), name="CI (forecast)",
    ))
    fig.add_trace(go.Scatter(
        x=daily_data["ds"], y=daily_data["y"],
        mode="markers", name="Actual",
        marker=dict(color="#444441", size=3, opacity=0.5),
    ))
    fig.add_trace(go.Scatter(
        x=hist_fc["ds"], y=hist_fc["yhat"],
        mode="lines", name="Fitted",
        line=dict(color=BRAND_GREEN, width=2),
    ))
    fig.add_trace(go.Scatter(
        x=future_fc["ds"], y=future_fc["yhat"],
        mode="lines", name="Forecast",
        line=dict(color="#378ADD", width=2.5, dash="dot"),
    ))
    fig.add_vline(
        x=cutoff.timestamp() * 1000,
        line_dash="dash", line_color="#999", line_width=1,
        annotation_text="Forecast start", annotation_position="top right",
    )
    fig.update_layout(**LAYOUT_DEFAULTS, title=None,
                      yaxis_tickprefix="$", yaxis_tickformat=",.0f", height=420)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Forecast summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"Projected revenue ({horizon}d)", f"${future_fc['yhat'].sum():,.0f}")
    c2.metric("Upper bound", f"${future_fc['yhat_upper'].sum():,.0f}")
    c3.metric("Lower bound", f"${future_fc['yhat_lower'].sum():,.0f}")
    c4.metric("Avg daily", f"${future_fc['yhat'].mean():,.0f}")

    if show_components:
        st.divider()
        st.subheader("Seasonality components")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Yearly seasonality**")
            yr = forecast[["ds", "yearly"]].drop_duplicates("ds").sort_values("ds")
            fig_y = go.Figure(go.Scatter(x=yr["ds"], y=yr["yearly"],
                              mode="lines", line=dict(color=BRAND_GREEN, width=2)))
            fig_y.update_layout(**LAYOUT_DEFAULTS, title=None, height=280)
            st.plotly_chart(fig_y, use_container_width=True)
        with col2:
            st.markdown("**Weekly seasonality**")
            wk = forecast[["ds", "weekly"]].copy()
            wk["dow"] = wk["ds"].dt.day_name()
            wk_avg = wk.groupby("dow")["weekly"].mean().reindex(
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            )
            fig_w = go.Figure(go.Bar(x=wk_avg.index, y=wk_avg.values,
                                     marker_color=BRAND_GREEN))
            fig_w.update_layout(**LAYOUT_DEFAULTS, title=None, height=280)
            st.plotly_chart(fig_w, use_container_width=True)

    st.divider()
    with st.expander("📋 View forecast table"):
        tbl = future_fc[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
        tbl.columns = ["Date", "Forecast ($)", "Lower ($)", "Upper ($)"]
        tbl["Date"] = tbl["Date"].dt.date
        for c in ["Forecast ($)", "Lower ($)", "Upper ($)"]:
            tbl[c] = tbl[c].map("${:,.0f}".format)
        st.dataframe(tbl, use_container_width=True, height=350, hide_index=True)
        csv = future_fc[["ds", "yhat", "yhat_lower", "yhat_upper"]].to_csv(index=False).encode()
        st.download_button("⬇️ Download forecast CSV", data=csv,
                           file_name="forecast.csv", mime="text/csv")


# ══════════════════════════════════════════════════════════════════════════
#  ARIMA (statsmodels) FALLBACK PATH
# ══════════════════════════════════════════════════════════════════════════
else:
    import warnings
    warnings.filterwarnings("ignore")
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    @st.cache_data(show_spinner="Training ARIMA model…")
    def run_arima(data_hash: str, daily_json: str, periods: int):
        d = pd.read_json(StringIO(daily_json))
        d["ds"] = pd.to_datetime(d["ds"])
        d = d.sort_values("ds").set_index("ds")
        d = d.asfreq("D").ffill()

        model = SARIMAX(d["y"], order=(1, 1, 1), seasonal_order=(1, 1, 0, 7),
                        enforce_stationarity=False, enforce_invertibility=False)
        result = model.fit(disp=False)

        fc = result.get_forecast(steps=periods)
        fc_mean = fc.predicted_mean
        fc_ci = fc.conf_int(alpha=0.20)

        future_dates = pd.date_range(d.index[-1] + pd.Timedelta(days=1), periods=periods, freq="D")
        future_fc = pd.DataFrame({
            "ds": future_dates,
            "yhat": fc_mean.values,
            "yhat_lower": fc_ci.iloc[:, 0].values,
            "yhat_upper": fc_ci.iloc[:, 1].values,
        })

        fitted = result.fittedvalues.reset_index()
        fitted.columns = ["ds", "yhat"]
        return d.reset_index(), fitted, future_fc

    data_hash = str(len(daily)) + str(daily["ds"].max())
    daily_data, fitted, future_fc = run_arima(data_hash, daily.to_json(), horizon)
    cutoff = daily_data["ds"].max()

    st.subheader(f"Daily revenue — actuals + {horizon}-day ARIMA forecast")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=pd.concat([future_fc["ds"], future_fc["ds"].iloc[::-1]]),
        y=pd.concat([future_fc["yhat_upper"], future_fc["yhat_lower"].iloc[::-1]]),
        fill="toself", fillcolor="rgba(55,138,221,0.15)",
        line=dict(color="rgba(0,0,0,0)"), name="80% confidence interval",
    ))
    fig.add_trace(go.Scatter(
        x=daily_data["ds"], y=daily_data["y"],
        mode="markers", name="Actual daily revenue",
        marker=dict(color="#444441", size=3, opacity=0.5),
    ))
    fig.add_trace(go.Scatter(
        x=fitted["ds"], y=fitted["yhat"],
        mode="lines", name="Fitted",
        line=dict(color=BRAND_GREEN, width=1.5, dash="dot"),
    ))
    fig.add_trace(go.Scatter(
        x=future_fc["ds"], y=future_fc["yhat"],
        mode="lines", name="Forecast",
        line=dict(color="#378ADD", width=2.5),
    ))
    fig.add_vline(
        x=cutoff.timestamp() * 1000,
        line_dash="dash", line_color="#999", line_width=1,
        annotation_text="Forecast start", annotation_position="top right",
    )
    fig.update_layout(**LAYOUT_DEFAULTS, title=None,
                      yaxis_tickprefix="$", yaxis_tickformat=",.0f", height=420)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Forecast summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"Projected revenue ({horizon}d)", f"${future_fc['yhat'].sum():,.0f}")
    c2.metric("Upper bound (80%)", f"${future_fc['yhat_upper'].sum():,.0f}")
    c3.metric("Lower bound (80%)", f"${future_fc['yhat_lower'].sum():,.0f}")
    c4.metric("Avg daily revenue", f"${future_fc['yhat'].mean():,.0f}")

    st.divider()
    with st.expander("📋 View forecast table"):
        tbl = future_fc.copy()
        tbl.columns = ["Date", "Forecast ($)", "Lower ($)", "Upper ($)"]
        tbl["Date"] = tbl["Date"].dt.date
        for c in ["Forecast ($)", "Lower ($)", "Upper ($)"]:
            tbl[c] = tbl[c].map("${:,.0f}".format)
        st.dataframe(tbl, use_container_width=True, height=350, hide_index=True)
        csv = future_fc.to_csv(index=False).encode()
        st.download_button("⬇️ Download forecast CSV", data=csv,
                           file_name="forecast.csv", mime="text/csv")
