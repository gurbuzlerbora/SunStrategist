# =============================================================================
# pages/2_Energy_Analysis.py -- Energy Production Analysis
# =============================================================================

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Energy Analysis | SunStrategist", layout="wide")

st.title("Energy Production Analysis")

if "results" not in st.session_state:
    st.warning("No analysis results found. Please run the analysis from the Home page first.")
    st.stop()

results = st.session_state["results"]
energy_forecast = results["energy_forecast"]
monthly_data    = results["monthly_data"]
factory         = results["factory"]
weather_data    = results["weather_data"]

# =============================================================================
# Summary Metrics
# =============================================================================

st.subheader("System Overview")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Capacity", f"{factory.get_total_capacity_kw():,.1f} kWp")
with col2:
    st.metric("Panels Installed", f"{len(factory.panels):,}")
with col3:
    st.metric("Optimal Tilt", f"{factory.optimal_tilt_deg}°")
with col4:
    st.metric("Daily PSH", f"{weather_data['peak_sun_hours_daily']} h/day")

st.divider()

# =============================================================================
# Chart 1 -- 20-Year Energy Forecast (Plotly)
# =============================================================================

st.subheader("20-Year Energy Production Forecast")

years  = [e["year"] for e in energy_forecast if e["year"] > 0]
output = [e["annual_output_kwh"] for e in energy_forecast if e["year"] > 0]
eff    = [e["efficiency_pct"] for e in energy_forecast if e["year"] > 0]

fig = go.Figure()

fig.add_trace(go.Bar(
    x=years,
    y=output,
    name="Annual Output (kWh)",
    marker_color="#3498db",
    opacity=0.8,
    hovertemplate="Year %{x}<br>Output: %{y:,.0f} kWh<extra></extra>",
))

fig.add_trace(go.Scatter(
    x=years,
    y=eff,
    name="Panel Efficiency (%)",
    yaxis="y2",
    line=dict(color="#e67e22", width=2.5),
    mode="lines+markers",
    marker=dict(size=4),
    hovertemplate="Year %{x}<br>Efficiency: %{y:.2f}%<extra></extra>",
))

fig.update_layout(
    yaxis=dict(title="Energy Output (kWh)", tickformat=",.0f"),
    yaxis2=dict(title="Panel Efficiency (%)", overlaying="y", side="right",
                range=[85, 102]),
    legend=dict(x=0.01, y=0.99),
    hovermode="x unified",
    height=420,
    margin=dict(t=20, b=40),
)

st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# Chart 2 -- Monthly Output (Plotly)
# =============================================================================

st.subheader("Monthly Energy Output & Peak Sun Hours")

months = [m["month"][:3] for m in monthly_data]
energy = [m["energy_kwh"] for m in monthly_data]
psh    = [m["peak_sun_hours"] for m in monthly_data]

col1, col2 = st.columns(2)

with col1:
    colors = ["#f39c12" if e == max(energy) else "#3498db" for e in energy]
    fig2 = go.Figure(go.Bar(
        x=energy,
        y=months,
        orientation="h",
        marker_color=colors,
        hovertemplate="%{y}: %{x:,.0f} kWh<extra></extra>",
    ))
    fig2.update_layout(
        title="Monthly Energy Output -- Year 1",
        xaxis=dict(title="Energy (kWh)", tickformat=",.0f"),
        height=400,
        margin=dict(t=40, b=40),
    )
    st.plotly_chart(fig2, use_container_width=True)

with col2:
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=months,
        y=psh,
        mode="lines+markers",
        line=dict(color="#e67e22", width=2.5),
        marker=dict(size=8),
        fill="tozeroy",
        fillcolor="rgba(230,126,34,0.15)",
        hovertemplate="%{x}: %{y:.2f} h/day<extra></extra>",
    ))
    fig3.update_layout(
        title="Daily Peak Sun Hours by Month",
        yaxis=dict(title="Peak Sun Hours / Day"),
        height=400,
        margin=dict(t=40, b=40),
    )
    st.plotly_chart(fig3, use_container_width=True)

# =============================================================================
# Raw Data Table
# =============================================================================

with st.expander("View Raw Energy Forecast Data"):
    import pandas as pd
    df = pd.DataFrame([
        {
            "Year": e["year"],
            "Annual Output (kWh)": f"{e['annual_output_kwh']:,.0f}",
            "Efficiency (%)": e["efficiency_pct"],
            "Degradation Factor": e["degradation_factor"],
        }
        for e in energy_forecast if e["year"] > 0
    ])
    st.dataframe(df, use_container_width=True)