# =============================================================================
# pages/7_Risk_Analysis.py -- Monte Carlo Risk Analysis
# =============================================================================

import streamlit as st
import plotly.graph_objects as go
import plotly.figure_factory as ff
import numpy as np
import pandas as pd

st.set_page_config(page_title="Risk Analysis | SunStrategist", layout="wide")

st.title("Weather & Financial Risk Analysis")
st.caption("Monte Carlo simulation -- models uncertainty in solar irradiance, electricity tariffs and installation costs.")

if "results" not in st.session_state:
    st.warning("No analysis results found. Please run the analysis from the Home page first.")
    st.stop()

results        = st.session_state["results"]
metrics        = results["metrics"]
cashflow_table = results["cashflow_table"]
factory        = results["factory"]
weather_data   = results["weather_data"]

# =============================================================================
# Monte Carlo Configuration
# =============================================================================

st.subheader("Simulation Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    n_simulations = st.select_slider(
        "Number of Simulations",
        options=[500, 1000, 2000, 5000, 10000],
        value=2000,
    )

with col2:
    irr_volatility = st.slider(
        "Irradiance Volatility (%)",
        min_value=5, max_value=30, value=15,
        help="Standard deviation of annual solar irradiance variation"
    )

with col3:
    tariff_volatility = st.slider(
        "Tariff Volatility (%)",
        min_value=5, max_value=30, value=10,
        help="Standard deviation of electricity tariff variation"
    )

cost_volatility = st.slider(
    "Installation Cost Volatility (%)",
    min_value=5, max_value=25, value=10,
    help="Standard deviation of CAPEX uncertainty"
)

run_mc = st.button("Run Monte Carlo Simulation", type="primary")

# =============================================================================
# Monte Carlo Engine
# =============================================================================

def run_monte_carlo(
    base_metrics: dict,
    cashflow_table: list,
    n_sims: int,
    irr_vol: float,
    tariff_vol: float,
    cost_vol: float,
) -> dict:
    """
    Runs Monte Carlo simulation by sampling from normal distributions
    around the base case values for irradiance, tariff and cost.

    Returns distribution of NPV, IRR, ROI and payback period.
    """
    np.random.seed(42)

    base_npv     = base_metrics["npv_eur"]
    base_irr     = base_metrics["irr_pct"]
    base_roi     = base_metrics["roi_pct"]
    base_payback = base_metrics["payback_years"]
    base_capex   = base_metrics["total_capex_eur"]
    base_revenue = base_metrics["lifetime_revenue_eur"]

    # Sample multipliers from normal distributions
    irr_mult    = np.random.normal(1.0, irr_vol / 100,  n_sims)
    tariff_mult = np.random.normal(1.0, tariff_vol / 100, n_sims)
    cost_mult   = np.random.normal(1.0, cost_vol / 100, n_sims)

    # Clip to realistic bounds
    irr_mult    = np.clip(irr_mult,    0.50, 1.50)
    tariff_mult = np.clip(tariff_mult, 0.50, 1.80)
    cost_mult   = np.clip(cost_mult,   0.70, 1.50)

    # Revenue scales with irradiance and tariff
    revenue_mult = irr_mult * tariff_mult
    capex_sim    = base_capex * cost_mult
    revenue_sim  = base_revenue * revenue_mult

    # Simulated NPV
    npv_sim = revenue_sim - capex_sim

    # Simulated ROI
    roi_sim = ((revenue_sim - capex_sim) / capex_sim) * 100

    # Simulated payback -- approximate inverse relationship
    payback_sim = base_payback / (revenue_mult / cost_mult)
    payback_sim = np.clip(payback_sim, 1, 20)

    # Simulated IRR -- approximate scaling
    irr_sim = base_irr * (revenue_mult / cost_mult)
    irr_sim = np.clip(irr_sim, 0, 200)

    return {
        "npv"         : npv_sim,
        "roi"         : roi_sim,
        "payback"     : payback_sim,
        "irr"         : irr_sim,
        "irr_mult"    : irr_mult,
        "tariff_mult" : tariff_mult,
        "cost_mult"   : cost_mult,
    }


def percentile_summary(data: np.ndarray, name: str, unit: str = "") -> dict:
    """Returns key percentile statistics for a distribution."""
    return {
        "metric" : name,
        "p5"     : np.percentile(data, 5),
        "p25"    : np.percentile(data, 25),
        "p50"    : np.percentile(data, 50),
        "p75"    : np.percentile(data, 75),
        "p95"    : np.percentile(data, 95),
        "mean"   : np.mean(data),
        "std"    : np.std(data),
        "unit"   : unit,
    }


# =============================================================================
# Run Simulation
# =============================================================================

if run_mc or "mc_results" in st.session_state:

    if run_mc:
        with st.spinner(f"Running {n_simulations:,} simulations..."):
            mc = run_monte_carlo(
                metrics,
                cashflow_table,
                n_simulations,
                irr_volatility,
                tariff_volatility,
                cost_volatility,
            )
            st.session_state["mc_results"] = mc
    else:
        mc = st.session_state["mc_results"]

    st.success(f"Simulation complete -- {n_simulations:,} scenarios analyzed.")
    st.divider()

    # =========================================================================
    # Key Risk Metrics
    # =========================================================================

    st.subheader("Risk-Adjusted Key Metrics")

    npv_p10 = np.percentile(mc["npv"], 10)
    npv_p50 = np.percentile(mc["npv"], 50)
    npv_p90 = np.percentile(mc["npv"], 90)
    prob_positive = (mc["npv"] > 0).mean() * 100
    prob_payback_under_10 = (mc["payback"] <= 10).mean() * 100

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric(
            "NPV (10th Pct.)",
            f"EUR {npv_p10:,.0f}",
            help="Worst-case realistic NPV (90% of outcomes are better)"
        )
    with col2:
        st.metric(
            "NPV (Median)",
            f"EUR {npv_p50:,.0f}",
            help="50th percentile -- most likely outcome"
        )
    with col3:
        st.metric(
            "NPV (90th Pct.)",
            f"EUR {npv_p90:,.0f}",
            help="Best-case realistic NPV"
        )
    with col4:
        st.metric(
            "Prob. Positive NPV",
            f"{prob_positive:.1f}%",
            help="Probability that the investment is profitable"
        )
    with col5:
        st.metric(
            "Prob. Payback < 10yr",
            f"{prob_payback_under_10:.1f}%",
            help="Probability of recovering investment within 10 years"
        )

    st.divider()

    # =========================================================================
    # Chart 1 -- NPV Distribution
    # =========================================================================

    st.subheader("NPV Distribution")

    fig1 = go.Figure()

    fig1.add_trace(go.Histogram(
        x=mc["npv"],
        nbinsx=80,
        name="NPV Distribution",
        marker_color="#3498db",
        opacity=0.75,
        hovertemplate="NPV: EUR %{x:,.0f}<br>Count: %{y}<extra></extra>",
    ))

    # Base case line
    fig1.add_vline(
        x=metrics["npv_eur"],
        line_dash="dash",
        line_color="#f39c12",
        annotation_text=f"Base Case: EUR {metrics['npv_eur']:,.0f}",
        annotation_font_color="#f39c12",
    )

    # P10 line
    fig1.add_vline(
        x=npv_p10,
        line_dash="dot",
        line_color="#e74c3c",
        annotation_text=f"P10: EUR {npv_p10:,.0f}",
        annotation_font_color="#e74c3c",
        annotation_position="bottom right",
    )

    # P90 line
    fig1.add_vline(
        x=npv_p90,
        line_dash="dot",
        line_color="#2ecc71",
        annotation_text=f"P90: EUR {npv_p90:,.0f}",
        annotation_font_color="#2ecc71",
    )

    # Zero line
    fig1.add_vline(x=0, line_color="white", opacity=0.3, line_width=1)

    fig1.update_layout(
        xaxis=dict(title="Net Present Value (EUR)", tickformat=",.0f"),
        yaxis=dict(title="Frequency"),
        height=400,
        margin=dict(t=20, b=40),
        showlegend=False,
    )

    st.plotly_chart(fig1, use_container_width=True)

    # =========================================================================
    # Chart 2 -- Payback Period Distribution
    # =========================================================================

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Payback Period Distribution")

        fig2 = go.Figure()
        fig2.add_trace(go.Histogram(
            x=mc["payback"],
            nbinsx=40,
            marker_color="#9b59b6",
            opacity=0.80,
            hovertemplate="Payback: %{x:.1f} yrs<br>Count: %{y}<extra></extra>",
        ))
        fig2.add_vline(
            x=metrics["payback_years"],
            line_dash="dash",
            line_color="#f39c12",
            annotation_text=f"Base: {metrics['payback_years']:.0f} yrs",
            annotation_font_color="#f39c12",
        )
        fig2.update_layout(
            xaxis=dict(title="Payback Period (Years)"),
            yaxis=dict(title="Frequency"),
            height=340,
            margin=dict(t=20, b=40),
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.subheader("IRR Distribution")

        fig3 = go.Figure()
        fig3.add_trace(go.Histogram(
            x=mc["irr"],
            nbinsx=40,
            marker_color="#2ecc71",
            opacity=0.80,
            hovertemplate="IRR: %{x:.1f}%<br>Count: %{y}<extra></extra>",
        ))
        fig3.add_vline(
            x=metrics["irr_pct"],
            line_dash="dash",
            line_color="#f39c12",
            annotation_text=f"Base: {metrics['irr_pct']}%",
            annotation_font_color="#f39c12",
        )
        fig3.update_layout(
            xaxis=dict(title="Internal Rate of Return (%)"),
            yaxis=dict(title="Frequency"),
            height=340,
            margin=dict(t=20, b=40),
        )
        st.plotly_chart(fig3, use_container_width=True)

    # =========================================================================
    # Chart 3 -- Sensitivity Tornado
    # =========================================================================

    st.subheader("Sensitivity Tornado Chart")
    st.caption("Shows which input variable has the most impact on NPV.")

    base_npv = metrics["npv_eur"]

    # Calculate impact of each variable independently
    np.random.seed(42)
    n_test = 2000

    def npv_from_mults(irr_m, tar_m, cost_m):
        rev  = metrics["lifetime_revenue_eur"] * irr_m * tar_m
        capex = metrics["total_capex_eur"] * cost_m
        return rev - capex

    # Irradiance impact
    irr_low  = npv_from_mults(1 - irr_volatility/100, 1, 1)
    irr_high = npv_from_mults(1 + irr_volatility/100, 1, 1)

    # Tariff impact
    tar_low  = npv_from_mults(1, 1 - tariff_volatility/100, 1)
    tar_high = npv_from_mults(1, 1 + tariff_volatility/100, 1)

    # Cost impact
    cost_low  = npv_from_mults(1, 1, 1 - cost_volatility/100)
    cost_high = npv_from_mults(1, 1, 1 + cost_volatility/100)

    variables = ["Solar Irradiance", "Electricity Tariff", "Installation Cost"]
    lows      = [irr_low - base_npv, tar_low - base_npv, cost_low - base_npv]
    highs     = [irr_high - base_npv, tar_high - base_npv, cost_high - base_npv]

    fig4 = go.Figure()

    fig4.add_trace(go.Bar(
        y=variables,
        x=[abs(l) for l in lows],
        orientation="h",
        name="Downside Risk",
        marker_color="#e74c3c",
        base=[min(l, 0) for l in lows],
        hovertemplate="%{y}<br>Downside: EUR %{x:,.0f}<extra></extra>",
    ))

    fig4.add_trace(go.Bar(
        y=variables,
        x=highs,
        orientation="h",
        name="Upside Potential",
        marker_color="#2ecc71",
        hovertemplate="%{y}<br>Upside: EUR %{x:,.0f}<extra></extra>",
    ))

    fig4.add_vline(x=0, line_color="white", opacity=0.5, line_width=1.5)

    fig4.update_layout(
        barmode="overlay",
        xaxis=dict(title="NPV Change from Base Case (EUR)", tickformat=",.0f"),
        height=300,
        margin=dict(t=20, b=40),
        legend=dict(x=0.01, y=0.99),
    )

    st.plotly_chart(fig4, use_container_width=True)

    # =========================================================================
    # Percentile Summary Table
    # =========================================================================

    st.subheader("Full Percentile Summary")

    summaries = [
        percentile_summary(mc["npv"],     "NPV",            "EUR"),
        percentile_summary(mc["irr"],     "IRR",            "%"),
        percentile_summary(mc["roi"],     "ROI",            "%"),
        percentile_summary(mc["payback"], "Payback Period", "yrs"),
    ]

    rows = []
    for s in summaries:
        fmt = "{:,.0f}" if s["unit"] == "EUR" else "{:.1f}"
        rows.append({
            "Metric"  : s["metric"],
            "Unit"    : s["unit"],
            "P5"      : fmt.format(s["p5"]),
            "P25"     : fmt.format(s["p25"]),
            "P50 (Median)": fmt.format(s["p50"]),
            "Mean"    : fmt.format(s["mean"]),
            "P75"     : fmt.format(s["p75"]),
            "P95"     : fmt.format(s["p95"]),
            "Std Dev" : fmt.format(s["std"]),
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    # =========================================================================
    # Risk Assessment
    # =========================================================================

    st.divider()
    st.subheader("Investment Risk Assessment")

    if prob_positive >= 95:
        risk_level = "Very Low Risk"
        risk_color = "#2ecc71"
        risk_desc  = "The investment is profitable in over 95% of simulated scenarios. Proceed with high confidence."
    elif prob_positive >= 85:
        risk_level = "Low Risk"
        risk_color = "#3498db"
        risk_desc  = "Strong probability of positive returns. Minor sensitivity to market conditions."
    elif prob_positive >= 70:
        risk_level = "Moderate Risk"
        risk_color = "#f39c12"
        risk_desc  = "Investment is generally viable but sensitive to irradiance and tariff assumptions."
    elif prob_positive >= 50:
        risk_level = "High Risk"
        risk_color = "#e67e22"
        risk_desc  = "Uncertain outcome. Significant sensitivity to market and weather conditions."
    else:
        risk_level = "Very High Risk"
        risk_color = "#e74c3c"
        risk_desc  = "Majority of scenarios result in negative NPV. Investment not recommended at current parameters."

    st.markdown(f"""
    <div style="
        background: #0d1117;
        border: 2px solid {risk_color};
        border-radius: 12px;
        padding: 1.5rem 2rem;
        display: flex;
        align-items: center;
        gap: 2rem;
    ">
        <div style="text-align: center; min-width: 160px;">
            <div style="color: {risk_color}; font-size: 1.4rem; font-weight: 800;">
                {risk_level}
            </div>
            <div style="color: #888; font-size: 0.8rem; margin-top: 4px;">
                Investment Rating
            </div>
        </div>
        <div style="border-left: 1px solid {risk_color}33; padding-left: 2rem;">
            <div style="color: white; font-size: 1rem; line-height: 1.6;">
                {risk_desc}
            </div>
            <div style="color: #888; font-size: 0.85rem; margin-top: 0.5rem;">
                Based on {n_simulations:,} Monte Carlo simulations with
                {irr_volatility}% irradiance volatility,
                {tariff_volatility}% tariff volatility,
                {cost_volatility}% cost volatility.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    st.info("Configure simulation parameters above and click 'Run Monte Carlo Simulation' to start.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        **What is Monte Carlo?**

        Instead of assuming one fixed future, we simulate thousands of
        possible futures by randomly varying key inputs within realistic ranges.
        """)
    with col2:
        st.markdown("""
        **What does it model?**

        - Annual solar irradiance variation (cloud cover, weather patterns)
        - Electricity tariff fluctuations
        - Installation and maintenance cost uncertainty
        """)
    with col3:
        st.markdown("""
        **What does it tell us?**

        - Probability of positive NPV
        - NPV range (P10 to P90)
        - Which variable creates the most risk
        - Investment risk rating
        """)