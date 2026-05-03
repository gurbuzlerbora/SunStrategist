# =============================================================================
# pages/5_BESS_Analysis.py -- Battery Energy Storage System Analysis
# =============================================================================

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="BESS Analysis | SunStrategist", layout="wide")

st.title("Battery Energy Storage System (BESS) Analysis")

if "results" not in st.session_state:
    st.warning("No analysis results found. Please run the analysis from the Home page first.")
    st.stop()

results = st.session_state["results"]
battery = results["battery"]

if battery is None:
    st.info("Battery storage was not included in this analysis. Enable BESS in the sidebar and run again.")
    st.stop()

degradation_summary = results["degradation_summary"]
cashflow_table      = results["cashflow_table"]

# =============================================================================
# Battery Specs
# =============================================================================

st.subheader("Battery Specifications")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Nominal Capacity",    f"{battery.capacity_kwh} kWh")
    st.metric("Total BESS Cost",     f"EUR {battery.get_total_cost_usd():,.0f}")
with col2:
    st.metric("Usable Capacity",     f"{battery.get_usable_capacity_at_year(0):.1f} kWh")
    st.metric("Annual Degradation",  f"{battery.degradation_rate * 100:.1f}%")
with col3:
    st.metric("Round-Trip Efficiency", f"{battery.efficiency * 100:.0f}%")
    st.metric("Max SoC",             f"{battery.max_soc * 100:.0f}%")
with col4:
    st.metric("Min SoC",             f"{battery.min_soc * 100:.0f}%")
    st.metric("Year 20 Capacity",
              f"{battery.get_capacity_at_year(20):.1f} kWh")

st.divider()

# =============================================================================
# Chart 1 -- Capacity Degradation (Plotly)
# =============================================================================

st.subheader("Capacity Degradation Over 20 Years")

years   = [d["year"] for d in degradation_summary]
nominal = [d["capacity_kwh"] for d in degradation_summary]
usable  = [d["usable_kwh"] for d in degradation_summary]
buffer  = [n - u for n, u in zip(nominal, usable)]

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=years,
    y=nominal,
    name="Nominal Capacity",
    line=dict(color="#9b59b6", width=3),
    mode="lines+markers",
    marker=dict(size=5),
    hovertemplate="Year %{x}<br>Nominal: %{y:.2f} kWh<extra></extra>",
))

fig.add_trace(go.Scatter(
    x=years,
    y=usable,
    name="Usable Capacity",
    line=dict(color="#3498db", width=3, dash="dash"),
    mode="lines+markers",
    marker=dict(size=5, symbol="square"),
    hovertemplate="Year %{x}<br>Usable: %{y:.2f} kWh<extra></extra>",
))

# Fill between nominal and usable
fig.add_trace(go.Scatter(
    x=years + years[::-1],
    y=nominal + usable[::-1],
    fill="toself",
    fillcolor="rgba(155,89,182,0.12)",
    line=dict(color="rgba(0,0,0,0)"),
    name="Unusable Buffer (SoC limits)",
    hoverinfo="skip",
))

fig.update_layout(
    yaxis=dict(title="Capacity (kWh)"),
    xaxis=dict(title="Project Year"),
    hovermode="x unified",
    height=420,
    margin=dict(t=20, b=40),
    legend=dict(x=0.01, y=0.99),
)

st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# Chart 2 -- BESS Annual Savings Contribution
# =============================================================================

st.subheader("Annual BESS Peak-Shift Savings")

data        = [r for r in cashflow_table if r["year"] > 0]
years2      = [r["year"] for r in data]
bess_savings = [r["battery_savings_eur"] for r in data]
total_rev   = [r["total_revenue_eur"] for r in data]
bess_pct    = [
    (b / t * 100) if t > 0 else 0
    for b, t in zip(bess_savings, total_rev)
]

fig2 = go.Figure()

fig2.add_trace(go.Bar(
    x=years2,
    y=bess_savings,
    name="BESS Savings (EUR)",
    marker_color="#9b59b6",
    opacity=0.85,
    hovertemplate="Year %{x}<br>Savings: EUR %{y:,.0f}<extra></extra>",
))

fig2.add_trace(go.Scatter(
    x=years2,
    y=bess_pct,
    name="% of Total Revenue",
    yaxis="y2",
    line=dict(color="#f39c12", width=2),
    mode="lines+markers",
    marker=dict(size=4),
    hovertemplate="Year %{x}<br>Share: %{y:.1f}%<extra></extra>",
))

fig2.update_layout(
    yaxis=dict(title="EUR", tickformat=",.0f"),
    yaxis2=dict(
        title="% of Total Revenue",
        overlaying="y",
        side="right",
        ticksuffix="%",
    ),
    hovermode="x unified",
    height=380,
    margin=dict(t=20, b=40),
    legend=dict(x=0.01, y=0.99),
)

st.plotly_chart(fig2, use_container_width=True)

# =============================================================================
# Chart 3 -- SoC Simulation (Single Day Example)
# =============================================================================

st.subheader("Daily Charge / Discharge Simulation (Example Day)")
st.caption("Illustrative simulation of a typical summer day showing solar generation, factory demand and battery SoC.")

hours          = list(range(24))
solar_gen      = [0,0,0,0,0,0.5,2,4,6,7,7.5,8,8,7.5,7,6,4,2,0.5,0,0,0,0,0]
factory_demand = [3,2.5,2.5,2.5,3,3.5,5,6,7,7,7,7,6.5,6.5,6.5,6,5,4.5,4,3.5,3.5,3,3,3]

soc      = [0.5]
charged  = []
discharged = []

for h in range(24):
    gen    = solar_gen[h]
    demand = factory_demand[h]
    net    = gen - demand
    current_soc = soc[-1]

    if net > 0:
        energy_in = min(net * battery.efficiency,
                        (battery.max_soc - current_soc) * battery.capacity_kwh)
        new_soc = current_soc + energy_in / battery.capacity_kwh
        charged.append(energy_in)
        discharged.append(0)
    else:
        energy_out = min(abs(net),
                         (current_soc - battery.min_soc) * battery.capacity_kwh)
        new_soc = current_soc - energy_out / battery.capacity_kwh
        charged.append(0)
        discharged.append(energy_out)

    soc.append(min(battery.max_soc, max(battery.min_soc, new_soc)))

soc = soc[1:]

fig3 = go.Figure()

fig3.add_trace(go.Scatter(
    x=hours, y=solar_gen,
    name="Solar Generation (kW)",
    line=dict(color="#f39c12", width=2.5),
    fill="tozeroy",
    fillcolor="rgba(243,156,18,0.15)",
    hovertemplate="Hour %{x}:00<br>Solar: %{y:.1f} kW<extra></extra>",
))

fig3.add_trace(go.Scatter(
    x=hours, y=factory_demand,
    name="Factory Demand (kW)",
    line=dict(color="#e74c3c", width=2.5),
    hovertemplate="Hour %{x}:00<br>Demand: %{y:.1f} kW<extra></extra>",
))

fig3.add_trace(go.Scatter(
    x=hours, y=[s * 100 for s in soc],
    name="Battery SoC (%)",
    yaxis="y2",
    line=dict(color="#9b59b6", width=2, dash="dot"),
    hovertemplate="Hour %{x}:00<br>SoC: %{y:.1f}%<extra></extra>",
))

fig3.update_layout(
    xaxis=dict(title="Hour of Day", tickmode="linear", dtick=2),
    yaxis=dict(title="Power (kW)"),
    yaxis2=dict(
        title="Battery SoC (%)",
        overlaying="y",
        side="right",
        range=[0, 110],
    ),
    hovermode="x unified",
    height=400,
    margin=dict(t=20, b=40),
    legend=dict(x=0.01, y=0.99),
)

st.plotly_chart(fig3, use_container_width=True)

# =============================================================================
# Degradation Table
# =============================================================================

with st.expander("View Full Degradation Data"):
    df = pd.DataFrame([
        {
            "Year"              : d["year"],
            "Nominal Cap. (kWh)": d["capacity_kwh"],
            "Usable Cap. (kWh)" : d["usable_kwh"],
            "Lost to SoC (kWh)" : round(d["capacity_kwh"] - d["usable_kwh"], 2),
            "Remaining (%)"     : round(d["capacity_kwh"] / battery.capacity_kwh * 100, 1),
        }
        for d in degradation_summary
    ])
    st.dataframe(df, use_container_width=True)