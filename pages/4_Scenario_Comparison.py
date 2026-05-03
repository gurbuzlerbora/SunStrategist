# =============================================================================
# pages/4_Scenario_Comparison.py -- Sensitivity & Scenario Analysis
# =============================================================================

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Scenario Comparison | SunStrategist", layout="wide")

st.title("Sensitivity & Scenario Analysis")

if "results" not in st.session_state:
    st.warning("No analysis results found. Please run the analysis from the Home page first.")
    st.stop()

results          = st.session_state["results"]
comparison_table = results["comparison_table"]
cashflow_table   = results["cashflow_table"]
metrics          = results["metrics"]

SCENARIO_COLORS = {
    "optimistic" : "#2ecc71",
    "realistic"  : "#3498db",
    "pessimistic": "#e74c3c",
}

# =============================================================================
# Scenario Overview Cards
# =============================================================================

st.subheader("Scenario Overview")

col1, col2, col3 = st.columns(3)
cols = [col1, col2, col3]

for col, row in zip(cols, comparison_table):
    color = SCENARIO_COLORS[row["scenario"]]
    with col:
        st.markdown(f"""
        <div style="
            background: #0d1117;
            border: 2px solid {color};
            border-radius: 12px;
            padding: 1.2rem;
            text-align: center;
        ">
            <div style="color: {color}; font-size: 1.2rem; font-weight: 800;
                        text-transform: uppercase; letter-spacing: 2px;">
                {row['scenario']}
            </div>
            <hr style="border-color: {color}33; margin: 0.8rem 0;">
            <div style="color: white; font-size: 1.4rem; font-weight: 700;">
                EUR {row['npv_eur']:,.0f}
            </div>
            <div style="color: #888; font-size: 0.8rem;">Net Present Value</div>
            <br>
            <div style="color: white; font-size: 1.1rem; font-weight: 600;">
                {row['irr_pct']}%
            </div>
            <div style="color: #888; font-size: 0.8rem;">IRR</div>
            <br>
            <div style="color: white; font-size: 1.1rem; font-weight: 600;">
                {row['payback_years']:.0f} years
            </div>
            <div style="color: #888; font-size: 0.8rem;">Payback Period</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# =============================================================================
# Chart 1 -- NPV Comparison (Plotly)
# =============================================================================

st.subheader("Metric Comparison Across Scenarios")

tab1, tab2, tab3, tab4 = st.tabs(["NPV", "ROI", "Payback Period", "Lifetime Revenue"])

scenarios = [r["scenario"].capitalize() for r in comparison_table]
colors    = [SCENARIO_COLORS[r["scenario"]] for r in comparison_table]

with tab1:
    npv = [r["npv_eur"] for r in comparison_table]
    fig = go.Figure(go.Bar(
        x=scenarios,
        y=npv,
        marker_color=colors,
        text=[f"EUR {v:,.0f}" for v in npv],
        textposition="outside",
        hovertemplate="%{x}<br>NPV: EUR %{y:,.0f}<extra></extra>",
    ))
    fig.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.4)
    fig.update_layout(
        yaxis=dict(title="EUR", tickformat=",.0f"),
        height=400,
        margin=dict(t=40, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    roi = [r["roi_pct"] for r in comparison_table]
    fig2 = go.Figure(go.Bar(
        x=scenarios,
        y=roi,
        marker_color=colors,
        text=[f"{v:.1f}%" for v in roi],
        textposition="outside",
        hovertemplate="%{x}<br>ROI: %{y:.1f}%<extra></extra>",
    ))
    fig2.update_layout(
        yaxis=dict(title="ROI (%)"),
        height=400,
        margin=dict(t=40, b=40),
    )
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    payback = [r["payback_years"] for r in comparison_table]
    fig3 = go.Figure(go.Bar(
        x=scenarios,
        y=payback,
        marker_color=colors,
        text=[f"{v:.0f} yrs" for v in payback],
        textposition="outside",
        hovertemplate="%{x}<br>Payback: %{y:.0f} years<extra></extra>",
    ))
    fig3.update_layout(
        yaxis=dict(title="Years"),
        height=400,
        margin=dict(t=40, b=40),
    )
    st.plotly_chart(fig3, use_container_width=True)

with tab4:
    revenue = [r["lifetime_revenue_eur"] for r in comparison_table]
    fig4 = go.Figure(go.Bar(
        x=scenarios,
        y=revenue,
        marker_color=colors,
        text=[f"EUR {v:,.0f}" for v in revenue],
        textposition="outside",
        hovertemplate="%{x}<br>Revenue: EUR %{y:,.0f}<extra></extra>",
    ))
    fig4.update_layout(
        yaxis=dict(title="EUR", tickformat=",.0f"),
        height=400,
        margin=dict(t=40, b=40),
    )
    st.plotly_chart(fig4, use_container_width=True)

# =============================================================================
# Chart 2 -- Cumulative Cash Flow All Scenarios
# =============================================================================

st.subheader("Cumulative Cash Flow -- All Scenarios")
st.caption("Realistic scenario is the base case. Optimistic and Pessimistic apply multipliers to irradiance, tariff and cost.")

years      = [r["year"] for r in cashflow_table]
cumulative = [r["cumulative_cashflow_eur"] for r in cashflow_table]

fig5 = go.Figure()

# Realistic line from actual results
fig5.add_trace(go.Scatter(
    x=years,
    y=cumulative,
    name="Realistic",
    line=dict(color="#3498db", width=3),
    mode="lines",
    hovertemplate="Year %{x}<br>Realistic: EUR %{y:,.0f}<extra></extra>",
))

# Optimistic -- scale realistic by 1.3
opt = [v * 1.30 for v in cumulative]
fig5.add_trace(go.Scatter(
    x=years,
    y=opt,
    name="Optimistic",
    line=dict(color="#2ecc71", width=2, dash="dot"),
    mode="lines",
    hovertemplate="Year %{x}<br>Optimistic: EUR %{y:,.0f}<extra></extra>",
))

# Pessimistic -- scale realistic by 0.70
pes = [v * 0.70 for v in cumulative]
fig5.add_trace(go.Scatter(
    x=years,
    y=pes,
    name="Pessimistic",
    line=dict(color="#e74c3c", width=2, dash="dot"),
    mode="lines",
    hovertemplate="Year %{x}<br>Pessimistic: EUR %{y:,.0f}<extra></extra>",
))

# Fill between optimistic and pessimistic
fig5.add_trace(go.Scatter(
    x=years + years[::-1],
    y=opt + pes[::-1],
    fill="toself",
    fillcolor="rgba(52,152,219,0.08)",
    line=dict(color="rgba(0,0,0,0)"),
    name="Uncertainty Range",
    hoverinfo="skip",
))

fig5.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.4)

fig5.update_layout(
    yaxis=dict(title="EUR", tickformat=",.0f"),
    xaxis=dict(title="Project Year"),
    hovermode="x unified",
    height=420,
    margin=dict(t=20, b=40),
    legend=dict(x=0.01, y=0.99),
)

st.plotly_chart(fig5, use_container_width=True)

# =============================================================================
# Multipliers Table
# =============================================================================

st.subheader("Scenario Assumptions")

df = pd.DataFrame([
    {
        "Scenario"         : r["scenario"].capitalize(),
        "Irradiance Mult." : f"x{r['irradiance_mult']}",
        "Tariff Mult."     : f"x{r['tariff_mult']}",
        "Cost Mult."       : f"x{r['cost_mult']}",
        "NPV (EUR)"        : f"{r['npv_eur']:,.0f}",
        "IRR (%)"          : f"{r['irr_pct']}%",
        "ROI (%)"          : f"{r['roi_pct']}%",
        "Payback (yrs)"    : f"{r['payback_years']:.0f}",
        "Lifetime Rev (EUR)": f"{r['lifetime_revenue_eur']:,.0f}",
    }
    for r in comparison_table
])

st.dataframe(df, use_container_width=True)