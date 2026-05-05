# =============================================================================
# pages/8_City_Comparison.py -- Two City Solar Comparison
# =============================================================================

import streamlit as st
import plotly.graph_objects as go
import requests
import json
import os

st.set_page_config(page_title="City Comparison | SunStrategist", layout="wide")

st.title("City vs City Solar Comparison")
st.caption("Compare solar potential and financial returns for two locations side by side.")

# =============================================================================
# Helpers
# =============================================================================

def geocode_city(city_name: str) -> dict:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut
    geolocator = Nominatim(user_agent="sunstrategist_comparison")
    try:
        location = geolocator.geocode(city_name, language="en", timeout=10)
        if location:
            country = location.address.split(",")[-1].strip()
            return {
                "found": True,
                "lat": round(location.latitude, 4),
                "lon": round(location.longitude, 4),
                "display_name": location.address,
                "country": country,
            }
    except GeocoderTimedOut:
        pass
    return {"found": False}


def fetch_pvgis(lat: float, lon: float, tilt: float = 35.0) -> dict:
    """Fetches PVGIS data for a given location."""
    params = {
        "lat": lat, "lon": lon,
        "raddatabase": "PVGIS-ERA5",
        "peakpower": 1, "loss": 14.0,
        "mountingplace": "building",
        "angle": tilt, "aspect": 0.0,
        "outputformat": "json", "browser": 0,
    }
    try:
        r = requests.get(
            "https://re.jrc.ec.europa.eu/api/v5_2/PVcalc",
            params=params, timeout=30
        )
        r.raise_for_status()
        raw = r.json()
        totals  = raw["outputs"]["totals"]["fixed"]
        monthly = raw["outputs"]["monthly"]["fixed"]

        month_names = ["Jan","Feb","Mar","Apr","May","Jun",
                       "Jul","Aug","Sep","Oct","Nov","Dec"]

        return {
            "found": True,
            "annual_irradiance": round(totals["H(i)_y"], 2),
            "annual_yield_kwp" : round(totals["E_y"], 2),
            "psh_daily"        : round(totals["H(i)_y"] / 365, 2),
            "monthly_irr"      : [round(m["H(i)_m"], 1) for m in monthly],
            "month_names"      : month_names,
        }
    except Exception:
        return {"found": False}


def calc_optimal_tilt(lat: float) -> float:
    lat = abs(lat)
    if lat < 25:
        return round(0.70 * lat + 2.5, 1)
    elif lat <= 65:
        return round(0.87 * lat + 3.1, 1)
    else:
        return round(0.90 * lat + 2.0, 1)


def load_tariffs() -> dict:
    path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data", "electricity_tariffs.json"
    )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_country_info() -> dict:
    path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data", "country_info.json"
    )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def estimate_npv(annual_yield_kwp: float, capacity_kwp: float,
                 tariff_day: float, capex: float) -> dict:
    """Simple 20-year NPV estimate for comparison purposes."""
    discount_rate  = 0.07
    degradation    = 0.005
    tariff_growth  = 0.04
    annual_revenue = 0.0
    cumulative     = -capex
    npv            = -capex

    for year in range(1, 21):
        output  = capacity_kwp * annual_yield_kwp * ((1 - degradation) ** year)
        tariff  = tariff_day * ((1 + tariff_growth) ** year)
        revenue = output * tariff
        opex    = capex * 0.01
        net_cf  = revenue - opex
        cumulative += net_cf
        npv += net_cf / ((1 + discount_rate) ** year)
        annual_revenue += net_cf

    payback = -1
    cum = -capex
    for year in range(1, 21):
        output  = capacity_kwp * annual_yield_kwp * ((1 - degradation) ** year)
        tariff  = tariff_day * ((1 + tariff_growth) ** year)
        revenue = output * tariff
        opex    = capex * 0.01
        cum    += revenue - opex
        if cum >= 0 and payback == -1:
            payback = year

    return {
        "npv"           : round(npv, 0),
        "total_revenue" : round(annual_revenue, 0),
        "payback"       : payback,
        "cumulative_20" : round(cumulative, 0),
    }


# =============================================================================
# City Input
# =============================================================================

tariffs    = load_tariffs()
country_db = load_country_info()

col1, col2 = st.columns(2)

with col1:
    st.markdown("### City A")
    city_a_input = st.text_input("Search City A", value="Berlin", key="city_a")
    roof_a       = st.slider("Roof Area A (m2)", 500, 20000, 5000, 100, key="roof_a")

with col2:
    st.markdown("### City B")
    city_b_input = st.text_input("Search City B", value="Dubai", key="city_b")
    roof_b       = st.slider("Roof Area B (m2)", 500, 20000, 5000, 100, key="roof_b")

panel_power = st.select_slider(
    "Panel Power (W)",
    options=[400, 450, 500, 550, 600, 650],
    value=550,
)

compare_btn = st.button("Compare Cities", type="primary")

# =============================================================================
# Comparison Engine
# =============================================================================

if compare_btn:

    with st.spinner("Fetching solar data for both cities..."):
        loc_a = geocode_city(city_a_input)
        loc_b = geocode_city(city_b_input)

    if not loc_a["found"]:
        st.error(f"City A not found: {city_a_input}")
        st.stop()
    if not loc_b["found"]:
        st.error(f"City B not found: {city_b_input}")
        st.stop()

    tilt_a = calc_optimal_tilt(loc_a["lat"])
    tilt_b = calc_optimal_tilt(loc_b["lat"])

    with st.spinner("Calculating solar irradiance from PVGIS..."):
        solar_a = fetch_pvgis(loc_a["lat"], loc_a["lon"], tilt_a)
        solar_b = fetch_pvgis(loc_b["lat"], loc_b["lon"], tilt_b)

    if not solar_a["found"]:
        st.error(f"Could not fetch solar data for {city_a_input}.")
        st.stop()
    if not solar_b["found"]:
        st.error(f"Could not fetch solar data for {city_b_input}.")
        st.stop()

    # Capacity calculation
    panel_area    = 2.65
    usable_ratio  = 0.75 * 0.85
    cap_a = (roof_a * usable_ratio / panel_area) * (panel_power / 1000)
    cap_b = (roof_b * usable_ratio / panel_area) * (panel_power / 1000)

    # Tariffs
    tar_a = tariffs.get(loc_a["country"], {}).get("day", 0.15)
    tar_b = tariffs.get(loc_b["country"], {}).get("day", 0.15)

    # CAPEX
    capex_a = cap_a * (180 + 250 + 80)
    capex_b = cap_b * (180 + 250 + 80)

    # Financial estimates
    fin_a = estimate_npv(solar_a["annual_yield_kwp"], cap_a, tar_a, capex_a)
    fin_b = estimate_npv(solar_b["annual_yield_kwp"], cap_b, tar_b, capex_b)

    c_a = country_db.get(loc_a["country"], {"flag": "🌍"})
    c_b = country_db.get(loc_b["country"], {"flag": "🌍"})

    st.divider()
    st.subheader("Comparison Results")

    # =========================================================================
    # Header Cards
    # =========================================================================

    col1, col2 = st.columns(2)

    def city_header(col, name, loc, solar, cap, capex, fin, c_info, tilt, tar):
        winner_npv = fin_a["npv"] > fin_b["npv"]
        with col:
            border = "#2ecc71" if (name == city_a_input and winner_npv) or \
                                  (name == city_b_input and not winner_npv) else "#1E90FF"
            st.markdown(f"""
            <div style="background:#0d1117;border:2px solid {border};
                        border-radius:16px;padding:1.5rem;text-align:center;
                        margin-bottom:1rem;">
                <div style="font-size:2rem;">{c_info.get('flag','🌍')}</div>
                <div style="color:white;font-size:1.4rem;font-weight:800;">{name.title()}</div>
                <div style="color:#888;font-size:0.85rem;">{loc['country']}</div>
                <hr style="border-color:{border}33;margin:0.8rem 0;">
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.8rem;text-align:center;">
                    <div>
                        <div style="color:#888;font-size:0.7rem;text-transform:uppercase;">Daily PSH</div>
                        <div style="color:{border};font-size:1.3rem;font-weight:700;">{solar['psh_daily']} h</div>
                    </div>
                    <div>
                        <div style="color:#888;font-size:0.7rem;text-transform:uppercase;">Capacity</div>
                        <div style="color:{border};font-size:1.3rem;font-weight:700;">{cap:,.0f} kWp</div>
                    </div>
                    <div>
                        <div style="color:#888;font-size:0.7rem;text-transform:uppercase;">20-Yr NPV</div>
                        <div style="color:{border};font-size:1.3rem;font-weight:700;">EUR {fin['npv']:,.0f}</div>
                    </div>
                    <div>
                        <div style="color:#888;font-size:0.7rem;text-transform:uppercase;">Payback</div>
                        <div style="color:{border};font-size:1.3rem;font-weight:700;">{fin['payback']} yrs</div>
                    </div>
                    <div>
                        <div style="color:#888;font-size:0.7rem;text-transform:uppercase;">Tariff</div>
                        <div style="color:{border};font-size:1.3rem;font-weight:700;">EUR {tar:.3f}</div>
                    </div>
                    <div>
                        <div style="color:#888;font-size:0.7rem;text-transform:uppercase;">Opt. Tilt</div>
                        <div style="color:{border};font-size:1.3rem;font-weight:700;">{tilt}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    city_header(col1, city_a_input, loc_a, solar_a, cap_a, capex_a, fin_a, c_a, tilt_a, tar_a)
    city_header(col2, city_b_input, loc_b, solar_b, cap_b, capex_b, fin_b, c_b, tilt_b, tar_b)

    # Winner banner
    if fin_a["npv"] > fin_b["npv"]:
        winner = city_a_input.title()
        diff   = fin_a["npv"] - fin_b["npv"]
    else:
        winner = city_b_input.title()
        diff   = fin_b["npv"] - fin_a["npv"]

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0a2e1a,#0d4a28);
                border:2px solid #2ecc71;border-radius:12px;
                padding:1rem 2rem;text-align:center;margin:1rem 0;">
        <div style="color:#2ecc71;font-size:1.2rem;font-weight:800;">
            {winner} wins by EUR {diff:,.0f} in 20-year NPV
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # =========================================================================
    # Chart 1 -- PSH Monthly Comparison
    # =========================================================================

    st.subheader("Monthly Solar Irradiance Comparison")

    months = solar_a["month_names"]

    fig1 = go.Figure()
    fig1.add_trace(go.Bar(
        x=months, y=solar_a["monthly_irr"],
        name=city_a_input.title(),
        marker_color="#1E90FF", opacity=0.85,
        hovertemplate="%{x}: %{y} kWh/m2<extra></extra>",
    ))
    fig1.add_trace(go.Bar(
        x=months, y=solar_b["monthly_irr"],
        name=city_b_input.title(),
        marker_color="#2ecc71", opacity=0.85,
        hovertemplate="%{x}: %{y} kWh/m2<extra></extra>",
    ))
    fig1.update_layout(
        barmode="group",
        yaxis=dict(title="Irradiance (kWh/m2)"),
        height=380,
        margin=dict(t=20, b=40),
        legend=dict(x=0.01, y=0.99),
        hovermode="x unified",
    )
    st.plotly_chart(fig1, use_container_width=True)

    # =========================================================================
    # Chart 2 -- Financial Comparison
    # =========================================================================

    st.subheader("Financial Comparison")

    col1, col2 = st.columns(2)

    with col1:
        metrics_labels = ["20-Yr NPV", "Total Revenue", "CAPEX"]
        vals_a = [fin_a["npv"], fin_a["total_revenue"], capex_a]
        vals_b = [fin_b["npv"], fin_b["total_revenue"], capex_b]

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            y=metrics_labels, x=vals_a,
            name=city_a_input.title(),
            orientation="h",
            marker_color="#1E90FF", opacity=0.85,
            hovertemplate="%{y}: EUR %{x:,.0f}<extra></extra>",
        ))
        fig2.add_trace(go.Bar(
            y=metrics_labels, x=vals_b,
            name=city_b_input.title(),
            orientation="h",
            marker_color="#2ecc71", opacity=0.85,
            hovertemplate="%{y}: EUR %{x:,.0f}<extra></extra>",
        ))
        fig2.update_layout(
            barmode="group",
            xaxis=dict(title="EUR", tickformat=",.0f"),
            height=300,
            margin=dict(t=20, b=40),
            legend=dict(x=0.01, y=0.99),
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        # Radar chart
        categories = ["Solar PSH", "NPV Score", "Payback Score",
                      "Irradiance", "Tariff Score"]

        max_psh  = max(solar_a["psh_daily"], solar_b["psh_daily"])
        max_npv  = max(abs(fin_a["npv"]), abs(fin_b["npv"]))
        max_irr  = max(solar_a["annual_irradiance"], solar_b["annual_irradiance"])
        max_tar  = max(tar_a, tar_b)

        def norm(val, max_val):
            return round((val / max_val) * 10, 1) if max_val > 0 else 0

        pay_score_a = round((1 - (fin_a["payback"] / 20)) * 10, 1) if fin_a["payback"] > 0 else 0
        pay_score_b = round((1 - (fin_b["payback"] / 20)) * 10, 1) if fin_b["payback"] > 0 else 0

        scores_a = [
            norm(solar_a["psh_daily"], max_psh),
            norm(fin_a["npv"], max_npv),
            pay_score_a,
            norm(solar_a["annual_irradiance"], max_irr),
            norm(tar_a, max_tar),
        ]
        scores_b = [
            norm(solar_b["psh_daily"], max_psh),
            norm(fin_b["npv"], max_npv),
            pay_score_b,
            norm(solar_b["annual_irradiance"], max_irr),
            norm(tar_b, max_tar),
        ]

        fig3 = go.Figure()
        fig3.add_trace(go.Scatterpolar(
            r=scores_a + [scores_a[0]],
            theta=categories + [categories[0]],
            fill="toself",
            name=city_a_input.title(),
            line_color="#1E90FF",
            fillcolor="rgba(30,144,255,0.2)",
        ))
        fig3.add_trace(go.Scatterpolar(
            r=scores_b + [scores_b[0]],
            theta=categories + [categories[0]],
            fill="toself",
            name=city_b_input.title(),
            line_color="#2ecc71",
            fillcolor="rgba(46,204,113,0.2)",
        ))
        fig3.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
            height=300,
            margin=dict(t=20, b=20),
            legend=dict(x=0.01, y=0.99),
        )
        st.plotly_chart(fig3, use_container_width=True)

    # =========================================================================
    # Summary Table
    # =========================================================================

    st.subheader("Full Comparison Table")

    import pandas as pd
    df = pd.DataFrame({
        "Metric": [
            "Country", "Latitude", "Longitude",
            "Daily PSH (h/day)", "Annual Irradiance (kWh/m2)",
            "Optimal Tilt", "Capacity (kWp)", "CAPEX (EUR)",
            "Day Tariff (EUR/kWh)", "20-Yr NPV (EUR)",
            "Total Revenue (EUR)", "Payback (years)",
        ],
        city_a_input.title(): [
            loc_a["country"], loc_a["lat"], loc_a["lon"],
            solar_a["psh_daily"], solar_a["annual_irradiance"],
            f"{tilt_a}", f"{cap_a:,.0f}", f"{capex_a:,.0f}",
            f"{tar_a:.3f}", f"{fin_a['npv']:,.0f}",
            f"{fin_a['total_revenue']:,.0f}", fin_a["payback"],
        ],
        city_b_input.title(): [
            loc_b["country"], loc_b["lat"], loc_b["lon"],
            solar_b["psh_daily"], solar_b["annual_irradiance"],
            f"{tilt_b}", f"{cap_b:,.0f}", f"{capex_b:,.0f}",
            f"{tar_b:.3f}", f"{fin_b['npv']:,.0f}",
            f"{fin_b['total_revenue']:,.0f}", fin_b["payback"],
        ],
    })
    st.dataframe(df, use_container_width=True)

else:
    st.info("Enter two cities above and click 'Compare Cities' to start the analysis.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        **What does this compare?**
        Real PVGIS satellite data for both locations,
        optimal tilt angles, 20-year financial projections
        and side-by-side NPV analysis.
        """)
    with col2:
        st.markdown("""
        **Example comparisons**
        - Berlin vs Dubai
        - Istanbul vs Stockholm
        - Tokyo vs Madrid
        - London vs Nairobi
        """)
    with col3:
        st.markdown("""
        **What you get**
        - Monthly irradiance chart
        - Financial bar comparison
        - Radar performance chart
        - Full metrics table
        - Winner announcement
        """)