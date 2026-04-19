"""
SunStrategist - Main execution script.
This file connects the entire logic: building the factory, fetching real-time
solar data from the PVGIS API, and calculating the 20-year financial outlook.

Workflow:
1. Initialize infrastructure (Factory & BESS models).
2. Fetch solar data for the specific coordinates.
3. Optimize tilt/azimuth and forecast energy yields.
4. Run NPV, IRR, and payback calculations.
5. Stress-test the investment (Sensitivity Analysis).
6. Generate visual charts and export the final PDF report.

Change the constants at ´Configuration´ to simulate different scenarios.
"""

from models.factory import Factory
from models.battery import Battery
from engines.weather_api import WeatherAPI
from engines.solar_engine import SolarEngine
from engines.finance_engine import FinancialModel
from engines.sensitivity import SensitivityAnalyzer
from outputs.charts import generate_all_charts
from outputs.report_generator import ReportGenerator


# =============================================================================
# Configuration — Edit These Values For Your Factory
# =============================================================================

FACTORY_NAME      = "Berlin Industrial Factory A"
ROOF_AREA_M2      = 5000        # total roof area in square metres
INCLUDE_BATTERY   = True        # set False to exclude BESS


# =============================================================================
# Pipeline
# =============================================================================

def run() -> None:
    """
    Executes the full SunStrategist analysis pipeline:
        1. Build factory & install panels
        2. Fetch real weather data from PVGIS
        3. Calculate optimal angles & energy forecast
        4. Run financial model
        5. Run sensitivity analysis
        6. Generate charts
        7. Build PDF report
    """

    print("=" * 60)
    print(f"  {' ' * 10}*** SunStrategist ***")
    print(f"  {'Industrial Solar Optimizer':^40}")
    print("=" * 60)
    print()

    # -------------------------------------------------------------------------
    # Step 1 — Build Factory & Install Panels
    # -------------------------------------------------------------------------
    print("[Step 1/7] Building factory and installing panels ...")

    factory = Factory(
        name         = FACTORY_NAME,
        roof_area_m2 = ROOF_AREA_M2,
    )

    battery = Battery() if INCLUDE_BATTERY else None

    # Temporarily install with default angles — will be updated in Step 3
    factory.install_panels()

    print(f"           Capacity : {factory.get_total_capacity_kw():,.1f} kWp")
    print(f"           Panels   : {len(factory.panels):,}")
    print(f"           CAPEX    : €{factory.get_total_capex_usd():,.0f}")
    print()

    # -------------------------------------------------------------------------
    # Step 2 — Fetch Real Weather Data (PVGIS API)
    # -------------------------------------------------------------------------
    print("[Step 2/7] Fetching solar irradiance data from PVGIS ...")

    api          = WeatherAPI(
        latitude  = factory.latitude,
        longitude = factory.longitude,
        altitude  = factory.altitude_m,
    )
    weather_data = api.fetch()

    print(f"           Irradiance : {weather_data['annual_irradiance_kwh_m2']} kWh/m²/yr")
    print(f"           Daily PSH  : {weather_data['peak_sun_hours_daily']} h/day")
    print()

    # -------------------------------------------------------------------------
    # Step 3 — Optimal Angles & Energy Forecast
    # -------------------------------------------------------------------------
    print("[Step 3/7] Calculating optimal angles and energy forecast ...")

    engine = SolarEngine(factory)
    engine.apply_optimal_angles()

    # Re-fetch with optimal tilt for more accurate irradiance
    weather_data = api.fetch(
        tilt_deg    = factory.optimal_tilt_deg,
        azimuth_deg = 0.0,   # PVGIS: 0 = south
    )

    energy_forecast = engine.calc_lifetime_energy_forecast(weather_data)
    monthly_data    = engine.calc_monthly_output_kwh(weather_data, year=1)

    year1_output = energy_forecast[1]["annual_output_kwh"]
    print(f"           Optimal Tilt    : {factory.optimal_tilt_deg}°")
    print(f"           Optimal Azimuth : {factory.optimal_azimuth_deg}°")
    print(f"           Year 1 Output   : {year1_output:,.0f} kWh")
    print()

    # -------------------------------------------------------------------------
    # Step 4 — Financial Model
    # -------------------------------------------------------------------------
    print("[Step 4/7] Running financial model ...")

    finance        = FinancialModel(factory, battery)
    cashflow_table = finance.calc_cashflow_table(energy_forecast)
    metrics        = finance.get_summary_metrics()

    print(f"           NPV         : €{metrics['npv_eur']:,.0f}")
    print(f"           IRR         : {metrics['irr_pct']}%")
    print(f"           ROI         : {metrics['roi_pct']}%")
    print(f"           Payback     : {metrics['payback_years']:.0f} years")
    print()

    # -------------------------------------------------------------------------
    # Step 5 — Sensitivity Analysis
    # -------------------------------------------------------------------------
    print("[Step 5/7] Running sensitivity analysis ...")

    analyzer         = SensitivityAnalyzer(factory, battery)
    analyzer.run_all(energy_forecast)
    comparison_table = analyzer.get_comparison_table()
    print()

    # -------------------------------------------------------------------------
    # Step 6 — Generate Charts
    # -------------------------------------------------------------------------
    print("[Step 6/7] Generating charts ...")

    degradation_summary = battery.get_lifetime_degradation_summary() \
        if battery else None

    chart_paths = generate_all_charts(
        energy_forecast    = energy_forecast,
        monthly_data       = monthly_data,
        cashflow_table     = cashflow_table,
        comparison_table   = comparison_table,
        degradation_summary= degradation_summary,
    )
    print()

    # -------------------------------------------------------------------------
    # Step 7 — Build PDF Report
    # -------------------------------------------------------------------------
    print("[Step 7/7] Building PDF report ...")

    report = ReportGenerator(
        factory_summary  = factory.summary(),
        weather_data     = weather_data,
        energy_forecast  = energy_forecast,
        monthly_data     = monthly_data,
        cashflow_table   = cashflow_table,
        metrics          = metrics,
        comparison_table = comparison_table,
        chart_paths      = chart_paths,
        battery_summary  = battery.summary() if battery else None,
    )

    report_path = report.build()

    # -------------------------------------------------------------------------
    # Done
    # -------------------------------------------------------------------------
    print()
    print("=" * 60)
    print("  [OK] SunStrategist Analysis Complete!")
    print("=" * 60)
    print(f"  Factory  : {FACTORY_NAME}")
    print(f"  Capacity : {factory.get_total_capacity_kw():,.1f} kWp")
    print(f"  NPV      : €{metrics['npv_eur']:,.0f}")
    print(f"  IRR      : {metrics['irr_pct']}%")
    print(f"  Payback  : {metrics['payback_years']:.0f} years")
    print(f"  Report   : {report_path}")
    print("=" * 60)


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    run()