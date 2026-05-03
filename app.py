# =============================================================================
# app.py -- SunStrategist v3.0 | Multi-Page Web Interface
# =============================================================================

import streamlit as st
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
    [data-testid="stSidebar"] {
        background-color: #0d1117;
    }
    .main-header {
        font-size: 2.8rem;
        font-weight: 900;
        color: #1E90FF;
        text-align: center;
        padding: 1.5rem 0 0.3rem 0;
        letter-spacing: -1px;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        text-align: center;
        margin-bottom: 1rem;
    }
    .version-badge {
        text-align: center;
        color: #1E90FF;
        font-size: 0.85rem;
        font-weight: 600;
        letter-spacing: 2px;
        margin-bottom: 2rem;
    }
    .feature-card {
        background: linear-gradient(135deg, #0d1117, #161b22);
        border: 1px solid #1E90FF33;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: border-color 0.3s;
    }
    .feature-title {
        color: #1E90FF;
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .feature-desc {
        color: #888;
        font-size: 0.9rem;
        line-height: 1.5;
    }
    .stat-number {
        font-size: 2rem;
        font-weight: 800;
        color: #1E90FF;
    }
    .stat-label {
        font-size: 0.8rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #1E90FF, #0066CC);
        color: white;
        font-size: 1rem;
        font-weight: 700;
        padding: 0.75rem;
        border-radius: 8px;
        border: none;
        transition: opacity 0.2s;
    }
    .stButton > button:hover {
        opacity: 0.9;
    }
    .city-info-box {
        background: #0d1117;
        border: 1px solid #1E90FF33;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-top: 0.5rem;
        font-size: 0.85rem;
        color: #888;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# Shared State Helpers
# =============================================================================

def load_tariffs() -> dict:
    """Loads the electricity tariff database from JSON."""
    tariff_path = os.path.join(os.path.dirname(__file__), "data", "electricity_tariffs.json")
    with open(tariff_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_tariff_for_country(country: str, tariffs: dict) -> dict:
    """Returns tariff data for a given country, with fallback."""
    return tariffs.get(country, {
        "day": 0.15, "night": 0.09, "peak": 0.20,
        "currency": "USD", "source": "estimate"
    })


def geocode_city(city_name: str) -> dict:
    """
    Uses Nominatim (OpenStreetMap) to geocode a city name.
    Returns lat, lon, altitude, display_name, country.
    """
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut

    geolocator = Nominatim(user_agent="sunstrategist_v3")
    try:
        location = geolocator.geocode(city_name, language="en", timeout=10)
        if location:
            # Extract country from address
            address_parts = location.address.split(",")
            country = address_parts[-1].strip()

            return {
                "found"       : True,
                "lat"         : round(location.latitude, 4),
                "lon"         : round(location.longitude, 4),
                "alt"         : 50,   # Default altitude, PVGIS handles this
                "display_name": location.address,
                "country"     : country,
            }
    except GeocoderTimedOut:
        pass

    return {"found": False}


# =============================================================================
# Sidebar -- Shared Configuration
# =============================================================================

def render_sidebar():
    """Renders the shared sidebar configuration panel."""

    tariffs = load_tariffs()

    with st.sidebar:
        st.markdown("### SunStrategist")
        st.markdown("**v3.0** | Industrial Solar Optimizer")
        st.divider()

        # ---- Location -------------------------------------------------------
        st.subheader("Location")

        city_input = st.text_input(
            "Search City",
            placeholder="e.g. Berlin, Tokyo, Dubai...",
            help="Type any city in the world and press Enter"
        )

        location_data = None

        if city_input:
            with st.spinner("Finding location..."):
                location_data = geocode_city(city_input)

            if location_data["found"]:
                st.success(f"Found: {location_data['display_name'][:60]}...")
                st.markdown(f"""<div class="city-info-box">
                    Lat: {location_data['lat']} | Lon: {location_data['lon']}<br>
                    Country: {location_data['country']}
                </div>""", unsafe_allow_html=True)

                lat     = location_data["lat"]
                lon     = location_data["lon"]
                alt     = location_data["alt"]
                country = location_data["country"]
            else:
                st.error("City not found. Try a different spelling.")
                lat, lon, alt, country = 52.52, 13.405, 34, "Germany"
        else:
            st.caption("Default: Berlin, Germany")
            lat, lon, alt, country = 52.52, 13.405, 34, "Germany"

        # ---- Factory --------------------------------------------------------
        st.divider()
        st.subheader("Factory")
        factory_name = st.text_input("Factory Name", value="Industrial Factory A")
        roof_area    = st.slider("Roof Area (m2)", 500, 20000, 5000, 100)

        # ---- Panel Type -----------------------------------------------------
        st.divider()
        st.subheader("Panel Type")
        panel_type = st.selectbox(
            "Select Panel",
            options=[
                "550W Industrial (21% eff.)",
                "450W Standard (19% eff.)",
                "650W Premium (23% eff.)",
            ],
        )
        PANEL_SPECS = {
            "550W Industrial (21% eff.)": {"power": 550, "efficiency": 0.21, "cost": 180},
            "450W Standard (19% eff.)"  : {"power": 450, "efficiency": 0.19, "cost": 130},
            "650W Premium (23% eff.)"   : {"power": 650, "efficiency": 0.23, "cost": 240},
        }
        selected_panel = PANEL_SPECS[panel_type]

        # ---- Battery --------------------------------------------------------
        st.divider()
        st.subheader("Battery (BESS)")
        include_battery  = st.toggle("Include Battery", value=True)
        battery_capacity = st.slider(
            "Capacity (kWh)", 50, 500, 100, 50,
            disabled=not include_battery
        )

        # ---- Tariffs --------------------------------------------------------
        st.divider()
        st.subheader("Electricity Tariffs")

        country_tariff = get_tariff_for_country(country, tariffs)

        st.caption(f"Auto-loaded for {country} | Source: {country_tariff['source']}")

        tariff_day   = st.number_input(
            "Day Tariff (EUR/kWh)",
            value=float(country_tariff["day"]),
            format="%.3f"
        )
        tariff_night = st.number_input(
            "Night Tariff (EUR/kWh)",
            value=float(country_tariff["night"]),
            format="%.3f"
        )
        tariff_peak  = st.number_input(
            "Peak Tariff (EUR/kWh)",
            value=float(country_tariff["peak"]),
            format="%.3f"
        )

        # ---- Financial ------------------------------------------------------
        st.divider()
        st.subheader("Financial")
        discount_rate = st.slider("Discount Rate (%)", 1, 20, 7)

        st.divider()
        run_button = st.button("Run Analysis")

    return {
        "factory_name"   : factory_name,
        "roof_area"      : roof_area,
        "lat"            : lat,
        "lon"            : lon,
        "alt"            : alt,
        "country"        : country,
        "selected_panel" : selected_panel,
        "include_battery": include_battery,
        "battery_capacity": battery_capacity,
        "tariff_day"     : tariff_day,
        "tariff_night"   : tariff_night,
        "tariff_peak"    : tariff_peak,
        "discount_rate"  : discount_rate,
        "run_button"     : run_button,
    }


# =============================================================================
# Main Analysis Runner
# =============================================================================

def run_analysis(cfg: dict) -> dict:
    """
    Runs the full SunStrategist pipeline and returns all results.
    Called from any page when run_button is pressed.
    """
    from models.factory import Factory
    from models.battery import Battery
    from engines.weather_api import WeatherAPI
    from engines.solar_engine import SolarEngine
    from engines.finance_engine import FinancialModel
    from engines.sensitivity import SensitivityAnalyzer
    from outputs.charts import generate_all_charts
    import config

    # Override config
    config.PANEL_RATED_POWER_W      = cfg["selected_panel"]["power"]
    config.PANEL_EFFICIENCY         = cfg["selected_panel"]["efficiency"]
    config.PANEL_COST_USD           = cfg["selected_panel"]["cost"]
    config.TARIFF_DAY_EUR_PER_KWH   = cfg["tariff_day"]
    config.TARIFF_NIGHT_EUR_PER_KWH = cfg["tariff_night"]
    config.TARIFF_PEAK_EUR_PER_KWH  = cfg["tariff_peak"]
    config.DISCOUNT_RATE            = cfg["discount_rate"] / 100
    config.BATTERY_CAPACITY_KWH     = cfg["battery_capacity"]

    factory = Factory(
        name         = cfg["factory_name"],
        roof_area_m2 = cfg["roof_area"],
        latitude     = cfg["lat"],
        longitude    = cfg["lon"],
        altitude_m   = cfg["alt"],
    )
    factory.install_panels()

    battery = Battery(capacity_kwh=cfg["battery_capacity"]) \
        if cfg["include_battery"] else None

    api          = WeatherAPI(cfg["lat"], cfg["lon"], cfg["alt"])
    weather_data = api.fetch()

    engine = SolarEngine(factory)
    engine.apply_optimal_angles()
    weather_data    = api.fetch(tilt_deg=factory.optimal_tilt_deg, azimuth_deg=0.0)
    energy_forecast = engine.calc_lifetime_energy_forecast(weather_data)
    monthly_data    = engine.calc_monthly_output_kwh(weather_data, year=1)

    finance        = FinancialModel(factory, battery)
    cashflow_table = finance.calc_cashflow_table(energy_forecast)
    metrics        = finance.get_summary_metrics()

    analyzer         = SensitivityAnalyzer(factory, battery)
    analyzer.run_all(energy_forecast)
    comparison_table = analyzer.get_comparison_table()

    degradation_summary = battery.get_lifetime_degradation_summary() \
        if battery else None

    chart_paths = generate_all_charts(
        energy_forecast     = energy_forecast,
        monthly_data        = monthly_data,
        cashflow_table      = cashflow_table,
        comparison_table    = comparison_table,
        degradation_summary = degradation_summary,
    )

    return {
        "factory"           : factory,
        "battery"           : battery,
        "weather_data"      : weather_data,
        "energy_forecast"   : energy_forecast,
        "monthly_data"      : monthly_data,
        "cashflow_table"    : cashflow_table,
        "metrics"           : metrics,
        "comparison_table"  : comparison_table,
        "degradation_summary": degradation_summary,
        "chart_paths"       : chart_paths,
    }


# =============================================================================
# Home Page
# =============================================================================

def page_home(cfg: dict):
    """Renders the home / welcome page."""

    st.markdown('<div class="main-header">SunStrategist</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Industrial Solar Optimizer & 20-Year Financial Forecaster</div>', unsafe_allow_html=True)
    st.markdown('<div class="version-badge">VERSION 3.0</div>', unsafe_allow_html=True)

    if cfg["run_button"]:
        with st.spinner("Running full analysis..."):
            results = run_analysis(cfg)
        st.session_state["results"] = results
        st.session_state["cfg"]     = cfg
        st.success("Analysis complete! Navigate to any tab to see results.")
        _render_kpi_cards(results["metrics"], results["factory"])
        return

    if "results" in st.session_state:
        st.info("Showing previous analysis results. Press 'Run Analysis' to refresh.")
        _render_kpi_cards(
            st.session_state["results"]["metrics"],
            st.session_state["results"]["factory"]
        )
        return

    # Welcome screen
    st.divider()
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""<div class="feature-card">
            <div class="feature-title">Solar Physics Engine</div>
            <div class="feature-desc">Calculates optimal tilt and azimuth angles
            based on exact GPS coordinates using real PVGIS satellite data.</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("""<div class="feature-card">
            <div class="feature-title">Global City Search</div>
            <div class="feature-desc">Search any city in the world. Coordinates
            and electricity tariffs load automatically.</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown("""<div class="feature-card">
            <div class="feature-title">20-Year Financial Model</div>
            <div class="feature-desc">Full NPV, IRR, ROI and payback analysis
            with EU carbon credit calculations and BESS peak-shifting.</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("""<div class="feature-card">
            <div class="feature-title">Battery Storage (BESS)</div>
            <div class="feature-desc">Simulates battery charge/discharge cycles,
            peak-shifting savings and 20-year capacity degradation.</div>
        </div>""", unsafe_allow_html=True)

    with col3:
        st.markdown("""<div class="feature-card">
            <div class="feature-title">Sensitivity Analysis</div>
            <div class="feature-desc">Stress-tests your investment across
            optimistic, realistic and pessimistic scenarios automatically.</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("""<div class="feature-card">
            <div class="feature-title">PDF Report</div>
            <div class="feature-desc">Auto-generates a professional multi-page
            PDF report with all charts and financial tables included.</div>
        </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("### How to use")
    st.markdown("""
    1. Search your city in the sidebar
    2. Configure factory roof area and panel type
    3. Adjust financial parameters if needed
    4. Click **Run Analysis**
    5. Navigate through the tabs to explore results
    6. Download your PDF report
    """)


def _render_kpi_cards(metrics: dict, factory):
    """Renders the 8 KPI metric cards."""
    st.divider()
    st.subheader("Executive Summary")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total CAPEX",    f"EUR {metrics['total_capex_eur']:,.0f}")
        st.metric("Panels",         f"{len(factory.panels):,}")
    with col2:
        st.metric("20-Yr NPV",      f"EUR {metrics['npv_eur']:,.0f}")
        st.metric("Capacity",       f"{factory.get_total_capacity_kw():,.1f} kWp")
    with col3:
        st.metric("IRR",            f"{metrics['irr_pct']}%")
        st.metric("ROI",            f"{metrics['roi_pct']}%")
    with col4:
        st.metric("Payback Period", f"{metrics['payback_years']:.0f} years")
        st.metric("Lifetime Revenue", f"EUR {metrics['lifetime_revenue_eur']:,.0f}")


# =============================================================================
# Entry Point
# =============================================================================

cfg = render_sidebar()
page_home(cfg)