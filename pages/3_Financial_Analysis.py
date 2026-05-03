# =============================================================================
# pages/3_Financial_Analysis.py -- Financial Analysis
# =============================================================================

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="Financial Analysis | SunStrategist", layout="wide")

st.title("20-Year Financial Analysis")

if "results" not in st.session_state:
    st.warning("No analysis results found. Please run the analysis from the Home page first.")
    st.stop()

results        = st.session_state["results"]
cashflow_table = results["cashflow_table"]
metrics        = results["metrics"]
factory        = results["factory"]

# =============================================================================
# KPI Metrics
# =============================================================================

st.subheader("Key Financial Metrics")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total CAPEX",     f"EUR {metrics['total_capex_eur']:,.0f}")
    st.metric("Annual OPEX",     f"EUR {factory.get_annual_opex_usd():,.0f}")
with col2:
    st.metric("20-Yr NPV",       f"EUR {metrics['npv_eur']:,.0f}")
    st.metric("Lifetime Revenue",f"EUR {metrics['lifetime_revenue_eur']:,.0f}")
with col3:
    st.metric("IRR",             f"{metrics['irr_pct']}%")
    st.metric("ROI",             f"{metrics['roi_pct']}%")
with col4:
    st.metric("Payback Period",  f"{metrics['payback_years']:.0f} years")
    st.metric("Carbon Income",   f"EUR {metrics['lifetime_carbon_income_eur']:,.0f}")

st.divider()

# =============================================================================
# Chart 1 -- Cumulative Cash Flow (Plotly)
# =============================================================================

st.subheader("20-Year Cumulative Cash Flow")

years      = [r["year"] for r in cashflow_table]
cumulative = [r["cumulative_cashflow_eur"] for r in cashflow_table]
net_cf     = [r["net_cashflow_eur"] for r in cashflow_table]

fig = go.Figure()

# Annual net cash flow bars
bar_colors = ["#3498db" if v >= 0 else "#e74c3c" for v in net_cf]
fig.add_trace(go.Bar(
    x=years,
    y=net_cf,
    name="Annual Net Cash Flow",
    marker_color=bar_colors,
    opacity=0.4,
    hovertemplate="Year %{x}<br>Net CF: EUR %{y:,.0f}<extra></extra>",
))

# Cumulative line
fig.add_trace(go.Scatter(
    x=years,
    y=cumulative,
    name="Cumulative Cash Flow",
    line=dict(color="#2ecc71", width=3),
    mode="lines+markers",
    marker=dict(size=5),
    hovertemplate="Year %{x}<br>Cumulative: EUR %{y:,.0f}<extra></extra>",
))

# Zero reference line
fig.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.5)

# Payback annotation
payback_year = int(metrics["payback_years"])
if payback_year > 0 and payback_year <= 20:
    fig.add_vline(
        x=payback_year,
        line_dash="dot",
        line_color="#f39c12",
        annotation_text=f"Payback: Year {payback_year}",
        annotation_position="top right",
        annotation_font_color="#f39c12",
    )

fig.update_layout(
    yaxis=dict(title="EUR", tickformat=",.0f"),
    xaxis=dict(title="Project Year"),
    hovermode="x unified",
    height=430,
    margin=dict(t=20, b=40),
    legend=dict(x=0.01, y=0.99),
)

st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# Chart 2 -- Revenue Stream Breakdown (Plotly)
# =============================================================================

st.subheader("Annual Revenue Stream Breakdown")

data   = [r for r in cashflow_table if r["year"] > 0]
years2 = [r["year"] for r in data]
energy = [r["energy_revenue_eur"] for r in data]
carbon = [r["carbon_income_eur"] for r in data]
bess   = [r["battery_savings_eur"] for r in data]
opex   = [r["opex_eur"] for r in data]

fig2 = go.Figure()

fig2.add_trace(go.Bar(
    x=years2, y=energy,
    name="Energy Savings",
    marker_color="#3498db",
    hovertemplate="Year %{x}<br>Energy: EUR %{y:,.0f}<extra></extra>",
))
fig2.add_trace(go.Bar(
    x=years2, y=carbon,
    name="Carbon Credits",
    marker_color="#2ecc71",
    hovertemplate="Year %{x}<br>Carbon: EUR %{y:,.0f}<extra></extra>",
))
fig2.add_trace(go.Bar(
    x=years2, y=bess,
    name="BESS Peak-Shift",
    marker_color="#9b59b6",
    hovertemplate="Year %{x}<br>BESS: EUR %{y:,.0f}<extra></extra>",
))
fig2.add_trace(go.Bar(
    x=years2, y=[-o for o in opex],
    name="OPEX (Cost)",
    marker_color="#e74c3c",
    hovertemplate="Year %{x}<br>OPEX: EUR %{y:,.0f}<extra></extra>",
))

fig2.update_layout(
    barmode="relative",
    yaxis=dict(title="EUR", tickformat=",.0f"),
    xaxis=dict(title="Project Year"),
    hovermode="x unified",
    height=400,
    margin=dict(t=20, b=40),
    legend=dict(x=0.01, y=0.99),
)

st.plotly_chart(fig2, use_container_width=True)

# =============================================================================
# Cash Flow Table
# =============================================================================

st.subheader("Full Cash Flow Table")

tab1, tab2 = st.tabs(["Years 1-10", "Years 11-20"])

def build_cf_df(rows):
    return pd.DataFrame([
        {
            "Year"              : r["year"],
            "Output (kWh)"      : f"{r['annual_output_kwh']:,.0f}",
            "Energy Rev (EUR)"  : f"{r['energy_revenue_eur']:,.0f}",
            "Carbon (EUR)"      : f"{r['carbon_income_eur']:,.0f}",
            "BESS (EUR)"        : f"{r['battery_savings_eur']:,.0f}",
            "OPEX (EUR)"        : f"{r['opex_eur']:,.0f}",
            "Net CF (EUR)"      : f"{r['net_cashflow_eur']:,.0f}",
            "Cumulative (EUR)"  : f"{r['cumulative_cashflow_eur']:,.0f}",
            "NPV Cumul. (EUR)"  : f"{r['npv_cumulative_eur']:,.0f}",
        }
        for r in rows if r["year"] > 0
    ])

with tab1:
    st.dataframe(build_cf_df(cashflow_table[:11]), use_container_width=True)

with tab2:
    st.dataframe(build_cf_df(cashflow_table[11:]), use_container_width=True)

# =============================================================================
# PDF Download
# =============================================================================

st.divider()
st.subheader("Download Report")

if st.button("Generate PDF Report"):
    from outputs.report_generator import ReportGenerator
    from outputs.charts import generate_all_charts

    cfg     = st.session_state.get("cfg", {})
    results = st.session_state["results"]

    with st.spinner("Generating PDF..."):
        report = ReportGenerator(
            factory_summary  = results["factory"].summary(),
            weather_data     = results["weather_data"],
            energy_forecast  = results["energy_forecast"],
            monthly_data     = results["monthly_data"],
            cashflow_table   = results["cashflow_table"],
            metrics          = results["metrics"],
            comparison_table = results["comparison_table"],
            chart_paths      = results["chart_paths"],
            battery_summary  = results["battery"].summary()
                               if results["battery"] else None,
        )
        report_path = report.build()

    with open(report_path, "rb") as f:
        st.download_button(
            label     = "Download PDF Report",
            data      = f,
            file_name = "sunstrategist_report.pdf",
            mime      = "application/pdf",
        )