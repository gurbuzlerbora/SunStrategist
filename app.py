"""
Dostum  app.py  projenin menusudur diyebilriz.
Streamlit kullanarak o  kodların hepsini bir web sitesine çevirdim.
Artık main.py içinden elle rakam değiştirmekle uğraşmıyorsun; yan tarafa slider'lar, butonlar falan koydum.
Şehri seçiyorsun, çatı kaç metrekare yazıyorsun, 'Analizi Çalıştır' diyince her şey saniyeler içinde önünde bitecek.
Grafiklere bakıp en son PDF raporunuda indirebiliyorsun. Kodu hiç bilmeyen biri bile rahatça kullanabilir.

"""

import streamlit as st
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.factory import Factory
from models.battery import Battery
from engines.weather_api import WeatherAPI
from engines.solar_engine import SolarEngine
from engines.finance_engine import FinancialModel
from engines.sensitivity import SensitivityAnalyzer
from outputs.charts import generate_all_charts
from outputs.report_generator import ReportGenerator

# =============================================================================
# Page Configuration
# =============================================================================

st.set_page_config(
    page_title="SunStrategist",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# Custom CSS
# =============================================================================

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 800;
        color: #1E90FF;
        text-align: center;
        padding: 1rem 0 0.2rem 0;
    }
    .sub-header {
        font-size: 1rem;
        color: #888;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        border: 1px solid #1E90FF33;
    }
    .stButton > button {
        width: 100%;
        background-color: #1E90FF;
        color: white;
        font-size: 1.1rem;
        font-weight: 700;
        padding: 0.75rem;
        border-radius: 8px;
        border: none;
    }
    .stButton > button:hover {
        background-color: #1565C0;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# Header
# =============================================================================

st.markdown('<div class="main-header">SunStrategist</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Industrial Solar Optimizer & 20-Year Financial Forecaster</div>', unsafe_allow_html=True)

st.divider()

# =============================================================================
# Sidebar -- User Inputs
# =============================================================================

with st.sidebar:
    st.header("Factory Configuration")

    st.subheader("Location")
    city = st.selectbox(
        "Select City",
        options=[
            "Berlin, Germany",
            "Munich, Germany",
            "Hamburg, Germany",
            "Madrid, Spain",
            "Barcelona, Spain",
            "Paris, France",
            "Amsterdam, Netherlands",
            "Vienna, Austria",
            "Rome, Italy",
            "Milan, Italy",
            "Warsaw, Poland",
            "Istanbul, Turkey",
            "Schweinfurt, Germany",
            "Altınoluk, Turkey",
            "Bodrum, Turkey",
            "Manavgat, Turkey",
            "Custom Location",
        ],
        index=0,
    )

    # City coordinates lookup
    CITY_COORDS = {
        "Berlin, Germany"       : (52.52,  13.405, 34),
        "Munich, Germany"       : (48.14,  11.58,  519),
        "Hamburg, Germany"      : (53.55,   9.99,  14),
        "Madrid, Spain"         : (40.42,  -3.70,  657),
        "Barcelona, Spain"      : (41.39,   2.15,  12),
        "Paris, France"         : (48.86,   2.35,  35),
        "Amsterdam, Netherlands": (52.37,   4.90,   2),
        "Vienna, Austria"       : (48.21,  16.37, 180),
        "Rome, Italy"           : (41.90,  12.50,  21),
        "Milan, Italy"          : (45.46,   9.19, 122),
        "Warsaw, Poland"        : (52.23,  21.01, 100),
        "Istanbul, Turkey"      : (41.01,  28.97,  40),
        "Schweinfurt, Germany"  : (50.05,  10.23, 229),
        "Altinoluk, Turkey"     : (39.57,  26.73,  10),
        "Bodrum, Turkey"        : (37.03,  27.43,  10),
        "Manavgat, Turkey"      : (36.78,  31.44,  45),

    }

    if city == "Custom Location":
        lat = st.number_input("Latitude",  value=52.52, format="%.4f")
        lon = st.number_input("Longitude", value=13.405, format="%.4f")
        alt = st.number_input("Altitude (m)", value=34)
    else:
        lat, lon, alt = CITY_COORDS[city]
        st.caption(f"Lat: {lat} | Lon: {lon} | Alt: {alt}m")

    st.divider()

    st.subheader("Factory & Roof")
    factory_name = st.text_input("Factory Name", value="Industrial Factory A")
    roof_area    = st.slider("Roof Area (m2)", min_value=500, max_value=20000,
                              value=5000, step=100)

    st.divider()

    st.subheader("Panel Type")
    panel_type = st.selectbox(
        "Select Panel",
        options=[
            "550W Industrial (21% eff.)",
            "450W Standard (19% eff.)",
            "650W Premium (23% eff.)",
        ],
        index=0,
    )

    PANEL_SPECS = {
        "550W Industrial (21% eff.)": {"power": 550, "efficiency": 0.21, "cost": 180},
        "450W Standard (19% eff.)"  : {"power": 450, "efficiency": 0.19, "cost": 130},
        "650W Premium (23% eff.)"   : {"power": 650, "efficiency": 0.23, "cost": 240},
    }
    selected_panel = PANEL_SPECS[panel_type]

    st.divider()

    st.subheader("Battery Storage (BESS)")
    include_battery  = st.toggle("Include Battery", value=True)
    battery_capacity = st.slider("Battery Capacity (kWh)",
                                  min_value=50, max_value=500,
                                  value=100, step=50,
                                  disabled=not include_battery)

    st.divider()

    st.subheader("Financial Parameters")
    tariff_day   = st.number_input("Day Tariff (EUR/kWh)",   value=0.28, format="%.3f")
    tariff_night = st.number_input("Night Tariff (EUR/kWh)", value=0.16, format="%.3f")
    discount_rate = st.slider("Discount Rate (%)", min_value=1, max_value=20,
                               value=7, step=1)

    st.divider()
    run_button = st.button("Run Analysis")

# =============================================================================
# Main Analysis
# =============================================================================

if run_button:

    # --- Override config values with user inputs ----------------------------
    import config
    config.PANEL_RATED_POWER_W   = selected_panel["power"]
    config.PANEL_EFFICIENCY      = selected_panel["efficiency"]
    config.PANEL_COST_USD        = selected_panel["cost"]
    config.TARIFF_DAY_EUR_PER_KWH   = tariff_day
    config.TARIFF_NIGHT_EUR_PER_KWH = tariff_night
    config.DISCOUNT_RATE         = discount_rate / 100
    config.BATTERY_CAPACITY_KWH  = battery_capacity

    with st.spinner("Fetching real solar data from PVGIS API..."):

        # Step 1 -- Factory
        factory = Factory(
            name         = factory_name,
            roof_area_m2 = roof_area,
            latitude     = lat,
            longitude    = lon,
            altitude_m   = alt,
        )
        factory.install_panels()
        battery = Battery(capacity_kwh=battery_capacity) if include_battery else None

        # Step 2 -- Weather
        api          = WeatherAPI(latitude=lat, longitude=lon, altitude=alt)
        weather_data = api.fetch()

        # Step 3 -- Solar Engine
        engine = SolarEngine(factory)
        engine.apply_optimal_angles()
        weather_data    = api.fetch(tilt_deg=factory.optimal_tilt_deg, azimuth_deg=0.0)
        energy_forecast = engine.calc_lifetime_energy_forecast(weather_data)
        monthly_data    = engine.calc_monthly_output_kwh(weather_data, year=1)

        # Step 4 -- Financial
        finance        = FinancialModel(factory, battery)
        cashflow_table = finance.calc_cashflow_table(energy_forecast)
        metrics        = finance.get_summary_metrics()

        # Step 5 -- Sensitivity
        analyzer         = SensitivityAnalyzer(factory, battery)
        analyzer.run_all(energy_forecast)
        comparison_table = analyzer.get_comparison_table()

        # Step 6 -- Charts
        degradation_summary = battery.get_lifetime_degradation_summary() \
            if battery else None
        chart_paths = generate_all_charts(
            energy_forecast     = energy_forecast,
            monthly_data        = monthly_data,
            cashflow_table      = cashflow_table,
            comparison_table    = comparison_table,
            degradation_summary = degradation_summary,
        )

    st.success("Analysis complete!")

    # =========================================================================
    # Results Section
    # =========================================================================

    st.header("Executive Summary")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total CAPEX",    f"EUR {metrics['total_capex_eur']:,.0f}")
        st.metric("Panels",         f"{len(factory.panels):,}")
    with col2:
        st.metric("20-Yr NPV",      f"EUR {metrics['npv_eur']:,.0f}")
        st.metric("Capacity",       f"{factory.get_total_capacity_kw():,.1f} kWp")
    with col3:
        st.metric("IRR",            f"{metrics['irr_pct']}%")
        st.metric("Optimal Tilt",   f"{factory.optimal_tilt_deg}")
    with col4:
        st.metric("Payback Period", f"{metrics['payback_years']:.0f} years")
        st.metric("Daily PSH",      f"{weather_data['peak_sun_hours_daily']} h/day")

    st.divider()

    # -------------------------------------------------------------------------
    # Charts
    # -------------------------------------------------------------------------

    st.header("Energy Production")
    col1, col2 = st.columns(2)
    with col1:
        if "energy_forecast" in chart_paths:
            st.image(chart_paths["energy_forecast"],
                     caption="20-Year Energy Forecast", use_container_width=True)
    with col2:
        if "monthly_output" in chart_paths:
            st.image(chart_paths["monthly_output"],
                     caption="Monthly Output & Peak Sun Hours", use_container_width=True)

    st.header("Financial Analysis")
    col1, col2 = st.columns(2)
    with col1:
        if "cashflow" in chart_paths:
            st.image(chart_paths["cashflow"],
                     caption="20-Year Cash Flow", use_container_width=True)
    with col2:
        if "revenue_breakdown" in chart_paths:
            st.image(chart_paths["revenue_breakdown"],
                     caption="Revenue Stream Breakdown", use_container_width=True)

    st.header("Sensitivity Analysis")
    if "sensitivity" in chart_paths:
        st.image(chart_paths["sensitivity"],
                 caption="Scenario Comparison", use_container_width=True)

    # Scenario table
    col1, col2, col3 = st.columns(3)
    for col, row in zip([col1, col2, col3], comparison_table):
        with col:
            st.subheader(row["scenario"].capitalize())
            st.metric("NPV",     f"EUR {row['npv_eur']:,.0f}")
            st.metric("IRR",     f"{row['irr_pct']}%")
            st.metric("ROI",     f"{row['roi_pct']}%")
            st.metric("Payback", f"{row['payback_years']:.0f} yrs")

    if include_battery:
        st.header("Battery (BESS) Analysis")
        if "battery_degradation" in chart_paths:
            st.image(chart_paths["battery_degradation"],
                     caption="Battery Capacity Degradation", use_container_width=True)

    # -------------------------------------------------------------------------
    # PDF Download
    # -------------------------------------------------------------------------

    st.divider()
    st.header("Download Report")

    with st.spinner("Generating PDF report..."):
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

    with open(report_path, "rb") as f:
        st.download_button(
            label="Download PDF Report",
            data=f,
            file_name="sunstrategist_report.pdf",
            mime="application/pdf",
        )

else:
    # -------------------------------------------------------------------------
    # Welcome Screen
    # -------------------------------------------------------------------------
    st.info("Configure your factory settings in the sidebar and click 'Run Analysis' to start.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Solar Physics Engine")
        st.write("Calculates optimal tilt and azimuth angles based on your exact coordinates using real PVGIS satellite data.")
    with col2:
        st.subheader("20-Year Financial Model")
        st.write("Full NPV, IRR, ROI and payback analysis with EU carbon credit calculations and BESS peak-shifting.")
    with col3:
        st.subheader("Sensitivity Analysis")
        st.write("Stress-tests your investment across optimistic, realistic and pessimistic scenarios automatically.")