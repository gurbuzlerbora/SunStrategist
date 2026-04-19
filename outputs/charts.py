"""
Visual Analytics & Reporting Suite
----------------------------------
This module transforms raw simulation data into high-impact visual charts.
It uses Matplotlib with a specialized 'Agg' backend to ensure charts are
rendered efficiently as static files (PNG) for PDF reporting.

Visual Strategy:
1. Energy Forecast: Visualizes the long-term decline in production due to
   panel aging (degradation) using a dual-axis bar and line chart.
2. Monthly Dynamics: Highlights the extreme seasonal variance in Berlin
   by comparing monthly yield against daily Peak Sun Hours (PSH).
3. Financial Trajectory: Tracks the 'Break-Even' point through a 20-year
   cumulative cash flow line, clearly distinguishing the profit zone.
4. Sensitivity Analysis: Provides a side-by-side comparison of Optimistic,
   Realistic, and Pessimistic scenarios to evaluate investment risk.
5. Battery Health: Tracks capacity fade over 20 years, showing the gap
   between nominal storage and usable energy due to SoC limits.
6. Revenue Breakdown: A stacked bar chart that reveals exactly where the
   money is coming from (Grid savings vs. Carbon credits vs. Battery shifting).
"""

import os
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for file saving
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from typing import List
from config import (
    OUTPUT_DIR,
    CHART_DPI,
    CHART_STYLE,
    PROJECT_LIFETIME,
)

# Apply global chart style
try:
    plt.style.use(CHART_STYLE)
except OSError:
    plt.style.use("seaborn-v0_8-darkgrid")

# Color palette for scenarios
SCENARIO_COLORS = {
    "optimistic" : "#2ecc71",
    "realistic"  : "#3498db",
    "pessimistic": "#e74c3c",
}

CHART_DIR = os.path.join(OUTPUT_DIR, "charts")


def _ensure_dirs() -> None:
    """Creates output chart directory if it does not exist."""
    os.makedirs(CHART_DIR, exist_ok=True)


def _save(fig: plt.Figure, filename: str) -> str:
    """
    Saves a matplotlib figure to the chart directory.

    Args:
        fig      : Matplotlib Figure object.
        filename : Output filename (without path).

    Returns:
        Full path to the saved file.
    """
    _ensure_dirs()
    path = os.path.join(CHART_DIR, filename)
    fig.savefig(path, dpi=CHART_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"[Charts] Saved → {path}")
    return path


# =============================================================================
# Chart 1 — 20-Year Energy Production Forecast
# Shows the 20-year lifecycle of the solar array.
# The blue bars represent the total energy generated, while the orange line tracks the unavoidable efficiency drop.
# It proves that even at Year 20, the factory is still a production powerhouse.
# =============================================================================

def chart_energy_forecast(energy_forecast: List[dict]) -> str:
    """
    Bar chart showing annual energy output (kWh) over 20 years,
    with a degradation trend line overlaid.

    Args:
        energy_forecast: Output of SolarEngine.calc_lifetime_energy_forecast()

    Returns:
        Path to saved chart image.
    """
    years  = [e["year"] for e in energy_forecast if e["year"] > 0]
    output = [e["annual_output_kwh"] for e in energy_forecast if e["year"] > 0]
    deg    = [e["degradation_factor"] * 100 for e in energy_forecast if e["year"] > 0]

    fig, ax1 = plt.subplots(figsize=(12, 5))

    # Bar chart — energy output
    bars = ax1.bar(years, output, color="#3498db", alpha=0.75, label="Annual Output (kWh)")
    ax1.set_xlabel("Project Year", fontsize=11)
    ax1.set_ylabel("Energy Output (kWh)", fontsize=11)
    ax1.set_title("20-Year Solar Energy Production Forecast", fontsize=13, fontweight="bold")
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    # Secondary axis — degradation %
    ax2 = ax1.twinx()
    ax2.plot(years, deg, color="#e67e22", linewidth=2,
             marker="o", markersize=3, label="Panel Efficiency (%)")
    ax2.set_ylabel("Panel Efficiency (%)", fontsize=11)
    ax2.set_ylim(85, 102)

    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=9)

    fig.tight_layout()
    return _save(fig, "01_energy_forecast.png")


# =============================================================================
# Chart 2 — Monthly Energy Output (Year 1)
# A reality check for Berlin’s weather. It contrasts the high-yield summer months against the darker winters.
# The horizontal bar design makes it easy to spot the "Golden Months" for energy production.
# =============================================================================

def chart_monthly_output(monthly_data: List[dict]) -> str:
    """
    Horizontal bar chart showing month-by-month energy output for Year 1.
    Clearly illustrates Berlin's seasonal solar variation.

    Args:
        monthly_data: Output of SolarEngine.calc_monthly_output_kwh()

    Returns:
        Path to saved chart image.
    """
    months = [m["month"][:3] for m in monthly_data]
    energy = [m["energy_kwh"] for m in monthly_data]
    psh    = [m["peak_sun_hours"] for m in monthly_data]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Left — monthly energy bars
    colors = ["#f39c12" if e == max(energy) else "#3498db" for e in energy]
    ax1.barh(months, energy, color=colors, alpha=0.85)
    ax1.set_xlabel("Energy Output (kWh)", fontsize=11)
    ax1.set_title("Monthly Energy Output — Year 1", fontsize=12, fontweight="bold")
    ax1.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    for i, v in enumerate(energy):
        ax1.text(v + max(energy) * 0.01, i, f"{v:,.0f}", va="center", fontsize=8)

    # Right — daily peak sun hours
    ax2.plot(months, psh, color="#e67e22", marker="o",
             linewidth=2, markersize=6, label="Daily PSH")
    ax2.fill_between(range(len(months)), psh, alpha=0.15, color="#e67e22")
    ax2.set_ylabel("Peak Sun Hours / Day", fontsize=11)
    ax2.set_title("Daily Peak Sun Hours by Month", fontsize=12, fontweight="bold")
    ax2.set_xticks(range(len(months)))
    ax2.set_xticklabels(months)
    ax2.legend(fontsize=9)

    fig.tight_layout()
    return _save(fig, "02_monthly_output.png")


# =============================================================================
# Chart 3 — 20-Year Cumulative Cash Flow
# The most important chart for investors.
# It shows the initial dip (the investment cost) and the steady climb back to zero (Payback).
# Once it crosses the dashed line, everything in green is pure profit.
# =============================================================================

def chart_cashflow(cashflow_table: List[dict]) -> str:
    """
    Line chart showing cumulative cash flow over 20 years.
    Highlights the payback point where cumulative CF crosses zero.

    Args:
        cashflow_table: Output of FinancialModel.calc_cashflow_table()

    Returns:
        Path to saved chart image.
    """
    years      = [r["year"] for r in cashflow_table]
    cumulative = [r["cumulative_cashflow_eur"] for r in cashflow_table]
    net_cf     = [r["net_cashflow_eur"] for r in cashflow_table]

    fig, ax = plt.subplots(figsize=(12, 5))

    # Cumulative cash flow line
    ax.plot(years, cumulative, color="#2ecc71", linewidth=2.5,
            marker="o", markersize=4, label="Cumulative Cash Flow")

    # Annual net cash flow bars
    bar_colors = ["#3498db" if v >= 0 else "#e74c3c" for v in net_cf]
    ax.bar(years, net_cf, color=bar_colors, alpha=0.35, label="Annual Net Cash Flow")

    # Zero line — payback reference
    ax.axhline(y=0, color="white", linewidth=1.2, linestyle="--", alpha=0.7)

    # Shade negative zone
    ax.fill_between(years, cumulative, 0,
                    where=[c < 0 for c in cumulative],
                    alpha=0.15, color="#e74c3c", label="Pre-payback Zone")

    # Shade positive zone
    ax.fill_between(years, cumulative, 0,
                    where=[c >= 0 for c in cumulative],
                    alpha=0.15, color="#2ecc71", label="Profit Zone")

    ax.set_xlabel("Project Year", fontsize=11)
    ax.set_ylabel("EUR", fontsize=11)
    ax.set_title("20-Year Cumulative Cash Flow Analysis", fontsize=13, fontweight="bold")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"€{x:,.0f}"))
    ax.legend(fontsize=9)

    fig.tight_layout()
    return _save(fig, "03_cashflow.png")


# =============================================================================
# Chart 4 — Sensitivity Analysis Comparison
# This is the ´Stress Test´ view. It plots the 3 scenarios side-by-side.
# It answers the question: ´Even if everything goes wrong (Pessimistic), is this still a good idea?´
# =============================================================================

def chart_sensitivity(comparison_table: List[dict]) -> str:
    """
    Grouped bar chart comparing NPV, ROI, and payback period
    across optimistic, realistic, and pessimistic scenarios.

    Args:
        comparison_table: Output of SensitivityAnalyzer.get_comparison_table()

    Returns:
        Path to saved chart image.
    """
    scenarios = [r["scenario"].capitalize() for r in comparison_table]
    npv       = [r["npv_eur"] for r in comparison_table]
    roi       = [r["roi_pct"] for r in comparison_table]
    payback   = [r["payback_years"] for r in comparison_table]
    colors    = [SCENARIO_COLORS[r["scenario"]] for r in comparison_table]

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("Sensitivity Analysis — Scenario Comparison",
                 fontsize=13, fontweight="bold")

    # NPV
    bars = ax1.bar(scenarios, npv, color=colors, alpha=0.85, edgecolor="white")
    ax1.set_title("Net Present Value (NPV)", fontsize=11)
    ax1.set_ylabel("EUR", fontsize=10)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"€{x:,.0f}"))
    ax1.axhline(y=0, color="white", linewidth=1, linestyle="--", alpha=0.5)
    for bar, val in zip(bars, npv):
        ax1.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + max(abs(v) for v in npv) * 0.01,
                 f"€{val:,.0f}", ha="center", fontsize=8)

    # ROI
    bars2 = ax2.bar(scenarios, roi, color=colors, alpha=0.85, edgecolor="white")
    ax2.set_title("Return on Investment (ROI %)", fontsize=11)
    ax2.set_ylabel("ROI (%)", fontsize=10)
    for bar, val in zip(bars2, roi):
        ax2.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 0.5,
                 f"{val:.1f}%", ha="center", fontsize=8)

    # Payback Period
    bars3 = ax3.bar(scenarios, payback, color=colors, alpha=0.85, edgecolor="white")
    ax3.set_title("Payback Period (Years)", fontsize=11)
    ax3.set_ylabel("Years", fontsize=10)
    for bar, val in zip(bars3, payback):
        ax3.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 0.1,
                 f"{val:.0f} yrs", ha="center", fontsize=8)

    fig.tight_layout()
    return _save(fig, "04_sensitivity.png")


# =============================================================================
# Chart 5 — Battery Degradation Over 20 Years
# Tracks the health of our BESS (Battery System).
# It visualizes how the battery gets ´tired´ over two decades,
# helping the factory plan for future maintenance or replacement.
# =============================================================================

def chart_battery_degradation(degradation_summary: List[dict]) -> str:
    """
    Dual-line chart showing nominal vs usable battery capacity
    degradation over the project lifetime.

    Args:
        degradation_summary: Output of Battery.get_lifetime_degradation_summary()

    Returns:
        Path to saved chart image.
    """
    years    = [d["year"] for d in degradation_summary]
    nominal  = [d["capacity_kwh"] for d in degradation_summary]
    usable   = [d["usable_kwh"] for d in degradation_summary]

    fig, ax = plt.subplots(figsize=(10, 4))

    ax.plot(years, nominal, color="#9b59b6", linewidth=2.5,
            marker="o", markersize=4, label="Nominal Capacity (kWh)")
    ax.plot(years, usable, color="#3498db", linewidth=2.5,
            linestyle="--", marker="s", markersize=4, label="Usable Capacity (kWh)")
    ax.fill_between(years, usable, nominal, alpha=0.12, color="#9b59b6",
                    label="Unusable Buffer (SoC limits)")

    ax.set_xlabel("Project Year", fontsize=11)
    ax.set_ylabel("Capacity (kWh)", fontsize=11)
    ax.set_title("Battery (BESS) Capacity Degradation — 20 Years",
                 fontsize=13, fontweight="bold")
    ax.legend(fontsize=9)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.1f} kWh"))

    fig.tight_layout()
    return _save(fig, "05_battery_degradation.png")


# =============================================================================
# Chart 6 — Revenue Stream Breakdown (Stacked Bar)
# Breaks down the income sources.
# It shows that we aren't just saving on electricity;
# we are also making money through carbon neutrality and smart peak-shifting with the battery.
# =============================================================================

def chart_revenue_breakdown(cashflow_table: List[dict]) -> str:
    """
    Stacked bar chart showing annual revenue split across
    energy savings, carbon credits, and battery savings.

    Args:
        cashflow_table: Output of FinancialModel.calc_cashflow_table()

    Returns:
        Path to saved chart image.
    """
    data   = [r for r in cashflow_table if r["year"] > 0]
    years  = [r["year"] for r in data]
    energy = [r["energy_revenue_eur"] for r in data]
    carbon = [r["carbon_income_eur"] for r in data]
    bess   = [r["battery_savings_eur"] for r in data]

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.bar(years, energy, label="Energy Savings",   color="#3498db", alpha=0.85)
    ax.bar(years, carbon, label="Carbon Credits",   color="#2ecc71", alpha=0.85,
           bottom=energy)
    ax.bar(years, bess,   label="BESS Peak-Shift",  color="#9b59b6", alpha=0.85,
           bottom=[e + c for e, c in zip(energy, carbon)])

    ax.set_xlabel("Project Year", fontsize=11)
    ax.set_ylabel("Revenue (EUR)", fontsize=11)
    ax.set_title("Annual Revenue Stream Breakdown", fontsize=13, fontweight="bold")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"€{x:,.0f}"))
    ax.legend(fontsize=9, loc="upper left")

    fig.tight_layout()
    return _save(fig, "06_revenue_breakdown.png")


# =============================================================================
# Master Runner — Generate All Charts
# =============================================================================

def generate_all_charts(
    energy_forecast   : List[dict],
    monthly_data      : List[dict],
    cashflow_table    : List[dict],
    comparison_table  : List[dict],
    degradation_summary: List[dict] = None,
) -> dict:
    """
    Generates and saves all charts. Returns a dict of chart paths
    keyed by chart name for use by ReportGenerator.

    Args:
        energy_forecast    : From SolarEngine.calc_lifetime_energy_forecast()
        monthly_data       : From SolarEngine.calc_monthly_output_kwh()
        cashflow_table     : From FinancialModel.calc_cashflow_table()
        comparison_table   : From SensitivityAnalyzer.get_comparison_table()
        degradation_summary: From Battery.get_lifetime_degradation_summary()

    Returns:
        Dict mapping chart names to file paths.
    """
    print("[Charts] Generating all charts ...\n")
    paths = {}

    paths["energy_forecast"]   = chart_energy_forecast(energy_forecast)
    paths["monthly_output"]    = chart_monthly_output(monthly_data)
    paths["cashflow"]          = chart_cashflow(cashflow_table)
    paths["sensitivity"]       = chart_sensitivity(comparison_table)
    paths["revenue_breakdown"] = chart_revenue_breakdown(cashflow_table)

    if degradation_summary:
        paths["battery_degradation"] = chart_battery_degradation(degradation_summary)

    print(f"\n[Charts] Done — {len(paths)} charts saved to '{CHART_DIR}'")
    return paths