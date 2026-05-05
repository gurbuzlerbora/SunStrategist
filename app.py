# =============================================================================
# app.py -- SunStrategist v3.0 | Multi-Page Web Interface
# =============================================================================

import streamlit as st
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="SunStrategist",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #0d1117; }
    .main-header {
        font-size: 2.8rem; font-weight: 900; color: #1E90FF;
        text-align: center; padding: 1.5rem 0 0.3rem 0; letter-spacing: -1px;
    }
    .sub-header {
        font-size: 1.1rem; color: #666;
        text-align: center; margin-bottom: 1rem;
    }
    .version-badge {
        text-align: center; color: #1E90FF; font-size: 0.85rem;
        font-weight: 600; letter-spacing: 2px; margin-bottom: 2rem;
    }
    .feature-card {
        background: linear-gradient(135deg, #0d1117, #161b22);
        border: 1px solid #1E90FF33; border-radius: 12px;
        padding: 1.5rem; margin-bottom: 1rem;
    }
    .feature-title { color: #1E90FF; font-size: 1.1rem; font-weight: 700; margin-bottom: 0.5rem; }
    .feature-desc { color: #888; font-size: 0.9rem; line-height: 1.5; }
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #1E90FF, #0066CC);
        color: white; font-size: 1rem; font-weight: 700;
        padding: 0.75rem; border-radius: 8px; border: none;
    }
    .city-info-box {
        background: #0d1117; border: 1px solid #1E90FF33;
        border-radius: 8px; padding: 0.75rem 1rem;
        margin-top: 0.5rem; font-size: 0.85rem; color: #888; line-height: 1.8;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# Helpers
# =============================================================================

def load_tariffs() -> dict:
    path = os.path.join(os.path.dirname(__file__), "data", "electricity_tariffs.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_country_info() -> dict:
    path = os.path.join(os.path.dirname(__file__), "data", "country_info.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_tariff_for_country(country: str, tariffs: dict) -> dict:
    return tariffs.get(country, {
        "day": 0.15, "night": 0.09, "peak": 0.20,
        "currency": "USD", "source": "estimate"
    })


def get_country_info(country: str, info: dict) -> dict:
    return info.get(country, {
        "flag": "🌍", "currency": "USD",
        "carbon_target": "NDC 2030", "carbon_price": 0, "grid_factor": 0.45,
    })


def geocode_city(city_name: str) -> dict:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut
    geolocator = Nominatim(user_agent="sunstrategist_v3")
    try:
        location = geolocator.geocode(city_name, language="en", timeout=10)
        if location:
            country = location.address.split(",")[-1].strip()
            return {
                "found": True,
                "lat": round(location.latitude, 4),
                "lon": round(location.longitude, 4),
                "alt": 50,
                "display_name": location.address,
                "country": country,
            }
    except GeocoderTimedOut:
        pass
    return {"found": False}


# =============================================================================
# Sidebar
# =============================================================================

def render_sidebar():
    tariffs    = load_tariffs()
    country_db = load_country_info()

    with st.sidebar:
        st.markdown("### SunStrategist")
        st.markdown("**v3.0** | Industrial Solar Optimizer")
        st.divider()

        st.subheader("Location")
        city_input = st.text_input(
            "Search City",
            placeholder="e.g. Berlin, Tokyo, Dubai...",
        )

        lat, lon, alt, country = 52.52, 13.405, 34, "Germany"

        if city_input:
            with st.spinner("Finding location..."):
                loc = geocode_city(city_input)
            if loc["found"]:
                lat, lon, alt, country = loc["lat"], loc["lon"], loc["alt"], loc["country"]
                c = get_country_info(country, country_db)
                st.success(f"Found: {loc['display_name'][:55]}...")
                st.markdown(f"""<div class="city-info-box">
                    {c['flag']} <b>{country}</b> | {c['currency']}<br>
                    Lat: {lat} | Lon: {lon}<br>
                    Carbon Target: {c['carbon_target']}<br>
                    Carbon Price: EUR {c['carbon_price']}/ton CO2<br>
                    Grid Emission: {c['grid_factor']} kg CO2/kWh
                </div>""", unsafe_allow_html=True)
            else:
                st.error("City not found. Try a different spelling.")
        else:
            c = get_country_info(country, country_db)
            st.caption(f"{c['flag']} Default: Berlin, Germany")

        st.divider()
        st.subheader("Factory")
        factory_name = st.text_input("Factory Name", value="Industrial Factory A")
        roof_area    = st.slider("Roof Area (m2)", 500, 20000, 5000, 100)

        st.divider()
        st.subheader("Panel Type")
        panel_type = st.selectbox("Select Panel", options=[
            "550W Industrial (21% eff.)",
            "450W Standard (19% eff.)",
            "650W Premium (23% eff.)",
        ])
        PANEL_SPECS = {
            "550W Industrial (21% eff.)": {"power": 550, "efficiency": 0.21, "cost": 180},
            "450W Standard (19% eff.)":   {"power": 450, "efficiency": 0.19, "cost": 130},
            "650W Premium (23% eff.)":    {"power": 650, "efficiency": 0.23, "cost": 240},
        }
        selected_panel = PANEL_SPECS[panel_type]

        st.divider()
        st.subheader("Battery (BESS)")
        include_battery  = st.toggle("Include Battery", value=True)
        battery_capacity = st.slider("Capacity (kWh)", 50, 500, 100, 50,
                                     disabled=not include_battery)

        st.divider()
        st.subheader("Electricity Tariffs")
        t = get_tariff_for_country(country, tariffs)
        st.caption(f"Auto-loaded for {country} | Source: {t['source']}")
        tariff_day   = st.number_input("Day Tariff (EUR/kWh)",   value=float(t["day"]),   format="%.3f")
        tariff_night = st.number_input("Night Tariff (EUR/kWh)", value=float(t["night"]), format="%.3f")
        tariff_peak  = st.number_input("Peak Tariff (EUR/kWh)",  value=float(t["peak"]),  format="%.3f")

        st.divider()
        st.subheader("Financial")
        discount_rate = st.slider("Discount Rate (%)", 1, 20, 7)

        st.divider()
        run_button = st.button("Run Analysis")

    return {
        "factory_name":    factory_name,
        "roof_area":       roof_area,
        "lat":             lat,
        "lon":             lon,
        "alt":             alt,
        "country":         country,
        "selected_panel":  selected_panel,
        "include_battery": include_battery,
        "battery_capacity":battery_capacity,
        "tariff_day":      tariff_day,
        "tariff_night":    tariff_night,
        "tariff_peak":     tariff_peak,
        "discount_rate":   discount_rate,
        "run_button":      run_button,
    }


# =============================================================================
# Analysis Runner
# =============================================================================

def run_analysis(cfg: dict) -> dict:
    from models.factory import Factory
    from models.battery import Battery
    from engines.weather_api import WeatherAPI
    from engines.solar_engine import SolarEngine
    from engines.finance_engine import FinancialModel
    from engines.sensitivity import SensitivityAnalyzer
    from outputs.charts import generate_all_charts
    import config

    config.PANEL_RATED_POWER_W      = cfg["selected_panel"]["power"]
    config.PANEL_EFFICIENCY         = cfg["selected_panel"]["efficiency"]
    config.PANEL_COST_USD           = cfg["selected_panel"]["cost"]
    config.TARIFF_DAY_EUR_PER_KWH   = cfg["tariff_day"]
    config.TARIFF_NIGHT_EUR_PER_KWH = cfg["tariff_night"]
    config.TARIFF_PEAK_EUR_PER_KWH  = cfg["tariff_peak"]
    config.DISCOUNT_RATE            = cfg["discount_rate"] / 100
    config.BATTERY_CAPACITY_KWH     = cfg["battery_capacity"]

    factory = Factory(
        name=cfg["factory_name"], roof_area_m2=cfg["roof_area"],
        latitude=cfg["lat"], longitude=cfg["lon"], altitude_m=cfg["alt"],
    )
    factory.install_panels()
    battery = Battery(capacity_kwh=cfg["battery_capacity"]) if cfg["include_battery"] else None

    api          = WeatherAPI(cfg["lat"], cfg["lon"], cfg["alt"])
    weather_data = api.fetch()
    engine       = SolarEngine(factory)
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

    degradation_summary = battery.get_lifetime_degradation_summary() if battery else None
    chart_paths = generate_all_charts(
        energy_forecast=energy_forecast, monthly_data=monthly_data,
        cashflow_table=cashflow_table, comparison_table=comparison_table,
        degradation_summary=degradation_summary,
    )

    return {
        "factory": factory, "battery": battery,
        "weather_data": weather_data, "energy_forecast": energy_forecast,
        "monthly_data": monthly_data, "cashflow_table": cashflow_table,
        "metrics": metrics, "comparison_table": comparison_table,
        "degradation_summary": degradation_summary, "chart_paths": chart_paths,
    }


# =============================================================================
# KPI Cards
# =============================================================================

def _render_kpi_cards(metrics: dict, factory):
    st.divider()
    st.subheader("Executive Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);
            border:1px solid #1E90FF55;border-radius:12px;padding:1.2rem;
            text-align:center;margin-bottom:1rem;">
            <div style="color:#888;font-size:0.75rem;letter-spacing:1px;text-transform:uppercase;">Total CAPEX</div>
            <div style="color:white;font-size:1.6rem;font-weight:800;margin:0.3rem 0;">EUR {metrics['total_capex_eur']:,.0f}</div>
        </div>
        <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);
            border:1px solid #9b59b655;border-radius:12px;padding:1.2rem;text-align:center;">
            <div style="color:#888;font-size:0.75rem;letter-spacing:1px;text-transform:uppercase;">ROI</div>
            <div style="color:#9b59b6;font-size:1.6rem;font-weight:800;margin:0.3rem 0;">{metrics['roi_pct']}%</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#0a2a4a,#0d3b6e);
            border:1px solid #1E90FF;border-radius:12px;padding:1.2rem;
            text-align:center;margin-bottom:1rem;">
            <div style="color:#88aaff;font-size:0.75rem;letter-spacing:1px;text-transform:uppercase;">20-Year NPV</div>
            <div style="color:#1E90FF;font-size:1.6rem;font-weight:800;margin:0.3rem 0;">EUR {metrics['npv_eur']:,.0f}</div>
        </div>
        <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);
            border:1px solid #3498db55;border-radius:12px;padding:1.2rem;text-align:center;">
            <div style="color:#888;font-size:0.75rem;letter-spacing:1px;text-transform:uppercase;">Panels Installed</div>
            <div style="color:#3498db;font-size:1.6rem;font-weight:800;margin:0.3rem 0;">{len(factory.panels):,}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#0a2e1a,#0d4a28);
            border:1px solid #2ecc71;border-radius:12px;padding:1.2rem;
            text-align:center;margin-bottom:1rem;">
            <div style="color:#88ffaa;font-size:0.75rem;letter-spacing:1px;text-transform:uppercase;">IRR</div>
            <div style="color:#2ecc71;font-size:1.6rem;font-weight:800;margin:0.3rem 0;">{metrics['irr_pct']}%</div>
        </div>
        <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);
            border:1px solid #2ecc7155;border-radius:12px;padding:1.2rem;text-align:center;">
            <div style="color:#888;font-size:0.75rem;letter-spacing:1px;text-transform:uppercase;">Carbon Income</div>
            <div style="color:#2ecc71;font-size:1.6rem;font-weight:800;margin:0.3rem 0;">EUR {metrics['lifetime_carbon_income_eur']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#2e1a0a,#4a280d);
            border:1px solid #f39c12;border-radius:12px;padding:1.2rem;
            text-align:center;margin-bottom:1rem;">
            <div style="color:#ffcc88;font-size:0.75rem;letter-spacing:1px;text-transform:uppercase;">Payback Period</div>
            <div style="color:#f39c12;font-size:1.6rem;font-weight:800;margin:0.3rem 0;">{metrics['payback_years']:.0f} years</div>
        </div>
        <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);
            border:1px solid #f39c1255;border-radius:12px;padding:1.2rem;text-align:center;">
            <div style="color:#888;font-size:0.75rem;letter-spacing:1px;text-transform:uppercase;">Lifetime Revenue</div>
            <div style="color:#f39c12;font-size:1.6rem;font-weight:800;margin:0.3rem 0;">EUR {metrics['lifetime_revenue_eur']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# Home Page
# =============================================================================

def page_home(cfg: dict):
    st.markdown('<div class="main-header">SunStrategist</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Industrial Solar Optimizer & 20-Year Financial Forecaster</div>', unsafe_allow_html=True)
    st.markdown('<div class="version-badge">VERSION 3.0</div>', unsafe_allow_html=True)

    if cfg["run_button"]:
        import time
        steps = [
            "Connecting to PVGIS satellite database...",
            "Fetching real solar irradiance data...",
            "Calculating optimal tilt and azimuth angles...",
            "Running 20-year energy production forecast...",
            "Computing NPV, IRR and payback period...",
            "Running sensitivity analysis...",
            "Generating charts and PDF report...",
        ]
        bar  = st.progress(0)
        text = st.empty()
        for i, step in enumerate(steps):
            bar.progress((i + 1) / len(steps))
            text.markdown(f"**{step}**")
            time.sleep(0.3)

        results = run_analysis(cfg)
        bar.empty()
        text.empty()

        st.session_state["results"] = results
        st.session_state["cfg"]     = cfg
        st.success("Analysis complete! Navigate to any tab to explore results.")
        _render_kpi_cards(results["metrics"], results["factory"])
        return

    if "results" in st.session_state:
        st.info("Showing previous analysis results. Press 'Run Analysis' to refresh.")
        _render_kpi_cards(
            st.session_state["results"]["metrics"],
            st.session_state["results"]["factory"],
        )
        return

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
            <div class="feature-desc">Search any city in the world. Coordinates,
            tariffs and country carbon data load automatically.</div>
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
            <div class="feature-title">Monte Carlo Risk Analysis</div>
            <div class="feature-desc">Runs up to 10,000 simulations to model
            weather uncertainty and deliver P10/P50/P90 NPV ranges.</div>
        </div>""", unsafe_allow_html=True)
        st.markdown("""<div class="feature-card">
            <div class="feature-title">Interactive Maps & Charts</div>
            <div class="feature-desc">Plotly interactive charts, Folium factory
            map with solar benchmark comparison across global cities.</div>
        </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("### How to use")
    st.markdown("""
    1. Search your city in the sidebar
    2. Configure factory roof area and panel type
    3. Click **Run Analysis**
    4. Navigate through the 7 analysis pages
    5. Run Monte Carlo simulation for risk assessment
    6. Download the PDF report
    """)


# =============================================================================
# Entry Point
# =============================================================================

cfg = render_sidebar()
page_home(cfg)