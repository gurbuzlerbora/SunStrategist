# =============================================================================
# pages/6_Map_View.py -- Factory Location & Map View
# =============================================================================

import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import os
import math

st.set_page_config(page_title="Map View | SunStrategist", layout="wide")

st.title("Factory Location & Solar Map")

if "results" not in st.session_state:
    st.warning("No analysis results found. Please run the analysis from the Home page first.")
    st.stop()

results      = st.session_state["results"]
factory      = results["factory"]
weather_data = results["weather_data"]
metrics      = results["metrics"]

lat = factory.latitude
lon = factory.longitude
psh = weather_data["peak_sun_hours_daily"]

# =============================================================================
# World Solar City Database -- PSH rankings
# =============================================================================

WORLD_CITIES = [
    ("Dubai, UAE", 6.1), ("Riyadh, Saudi Arabia", 6.0), ("Cairo, Egypt", 5.9),
    ("Phoenix, USA", 5.8), ("Mumbai, India", 5.7), ("Karachi, Pakistan", 5.6),
    ("Bangkok, Thailand", 5.5), ("Mexico City, Mexico", 5.4), ("Lagos, Nigeria", 5.3),
    ("Nairobi, Kenya", 5.2), ("Delhi, India", 5.1), ("Lima, Peru", 5.0),
    ("Johannesburg, South Africa", 4.9), ("Madrid, Spain", 4.8),
    ("Athens, Greece", 4.7), ("Rome, Italy", 4.6), ("Istanbul, Turkey", 4.5),
    ("Buenos Aires, Argentina", 4.4), ("Beijing, China", 4.3),
    ("Tokyo, Japan", 4.2), ("Sydney, Australia", 4.1), ("Seoul, South Korea", 4.0),
    ("São Paulo, Brazil", 3.9), ("Barcelona, Spain", 3.8), ("Lisbon, Portugal", 3.7),
    ("Paris, France", 3.5), ("Berlin, Germany", 3.6), ("Vienna, Austria", 3.4),
    ("Warsaw, Poland", 3.3), ("Amsterdam, Netherlands", 3.2),
    ("Brussels, Belgium", 3.1), ("London, UK", 2.9), ("Dublin, Ireland", 2.8),
    ("Stockholm, Sweden", 2.7), ("Oslo, Norway", 2.5),
    ("Helsinki, Finland", 2.4), ("Reykjavik, Iceland", 1.8),
]

def get_city_rank(psh_value: float) -> dict:
    """
    Calculates world rank of the selected location based on PSH.
    Returns rank, total cities, percentile and tier.
    """
    sorted_cities = sorted(WORLD_CITIES, key=lambda x: x[1], reverse=True)
    rank = 1
    for _, city_psh in sorted_cities:
        if psh_value < city_psh:
            rank += 1

    total      = len(sorted_cities) + 1
    percentile = round((1 - rank / total) * 100, 1)

    if percentile >= 80:
        tier  = "Elite"
        color = "#f39c12"
    elif percentile >= 60:
        tier  = "Strong"
        color = "#2ecc71"
    elif percentile >= 40:
        tier  = "Good"
        color = "#3498db"
    elif percentile >= 20:
        tier  = "Moderate"
        color = "#9b59b6"
    else:
        tier  = "Low"
        color = "#e74c3c"

    return {
        "rank"       : rank,
        "total"      : total,
        "percentile" : percentile,
        "tier"       : tier,
        "color"      : color,
    }

# =============================================================================
# Location Summary
# =============================================================================

st.subheader("Location Overview")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Latitude",          f"{lat}")
with col2:
    st.metric("Longitude",         f"{lon}")
with col3:
    st.metric("Annual Irradiance", f"{weather_data['annual_irradiance_kwh_m2']} kWh/m2")
with col4:
    st.metric("Daily PSH",         f"{psh} h/day")

st.divider()

# =============================================================================
# World Ranking Card
# =============================================================================

st.subheader("World Solar Potential Ranking")

rank_data = get_city_rank(psh)

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown(f"""
    <div style="
        background: #0d1117;
        border: 2px solid {rank_data['color']};
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
    ">
        <div style="color: {rank_data['color']}; font-size: 0.85rem;
                    letter-spacing: 2px; text-transform: uppercase; font-weight: 600;">
            World Ranking
        </div>
        <div style="color: white; font-size: 4rem; font-weight: 900; margin: 0.5rem 0;
                    line-height: 1;">
            #{rank_data['rank']}
        </div>
        <div style="color: #888; font-size: 0.9rem;">
            out of {rank_data['total']} major cities
        </div>
        <hr style="border-color: {rank_data['color']}33; margin: 1rem 0;">
        <div style="color: {rank_data['color']}; font-size: 1.4rem; font-weight: 700;">
            {rank_data['tier']} Tier
        </div>
        <div style="color: #888; font-size: 0.85rem; margin-top: 0.3rem;">
            Top {100 - rank_data['percentile']:.0f}% globally
        </div>
        <hr style="border-color: {rank_data['color']}33; margin: 1rem 0;">
        <div style="color: white; font-size: 1.8rem; font-weight: 800;">
            {psh} h/day
        </div>
        <div style="color: #888; font-size: 0.8rem;">Daily Peak Sun Hours</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("#### Global City Benchmark")

    sorted_cities = sorted(WORLD_CITIES, key=lambda x: x[1], reverse=True)
    max_psh = sorted_cities[0][1]

    # Insert current location
    all_cities = list(sorted_cities)
    all_cities.append((">> This Location", psh))
    all_cities = sorted(all_cities, key=lambda x: x[1], reverse=True)

    for name, val in all_cities:
        is_current = name == ">> This Location"
        bar_width  = int((val / max_psh) * 100)

        if val >= 5.0:
            bar_color = "#f39c12"
        elif val >= 4.0:
            bar_color = "#e67e22"
        elif val >= 3.0:
            bar_color = "#3498db"
        else:
            bar_color = "#9b59b6"

        if is_current:
            bar_color = "#1E90FF"

        border = "2px solid #1E90FF" if is_current else "1px solid #1a1a2e"
        bg     = "#0a1628" if is_current else "transparent"
        fw     = "700" if is_current else "400"
        fc     = "white" if is_current else "#aaa"

        st.markdown(f"""
        <div style="background:{bg};border:{border};border-radius:6px;
                    padding:0.35rem 0.8rem;margin-bottom:0.3rem;">
            <div style="display:flex;justify-content:space-between;
                        align-items:center;margin-bottom:3px;">
                <span style="color:{fc};font-size:0.82rem;font-weight:{fw};">
                    {name}
                </span>
                <span style="color:{bar_color};font-size:0.82rem;font-weight:600;">
                    {val} h/day
                </span>
            </div>
            <div style="background:#1a1a2e;border-radius:3px;height:5px;">
                <div style="background:{bar_color};width:{bar_width}%;
                            height:5px;border-radius:3px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# =============================================================================
# Factory Map
# =============================================================================

st.subheader("Factory Location")

m = folium.Map(
    location=[lat, lon],
    zoom_start=13,
    tiles="CartoDB dark_matter",
)

popup_html = f"""
<div style="font-family:Arial;min-width:220px;">
    <h4 style="color:#1E90FF;margin-bottom:8px;">{factory.name}</h4>
    <hr style="border-color:#1E90FF33;">
    <b>Capacity:</b> {factory.get_total_capacity_kw():,.1f} kWp<br>
    <b>Panels:</b> {len(factory.panels):,}<br>
    <b>Roof Area:</b> {factory.roof_area_m2:,} m2<br>
    <b>Optimal Tilt:</b> {factory.optimal_tilt_deg}<br>
    <hr style="border-color:#1E90FF33;">
    <b>NPV:</b> EUR {metrics['npv_eur']:,.0f}<br>
    <b>Payback:</b> {metrics['payback_years']:.0f} years<br>
    <b>IRR:</b> {metrics['irr_pct']}%
</div>
"""

folium.Marker(
    location=[lat, lon],
    popup=folium.Popup(popup_html, max_width=280),
    tooltip=f"{factory.name} -- Click for details",
    icon=folium.Icon(color="blue", icon="sun-o", prefix="fa"),
).add_to(m)

folium.CircleMarker(
    location=[lat, lon],
    radius=60,
    color="#1E90FF",
    fill=True,
    fill_color="#1E90FF",
    fill_opacity=0.08,
).add_to(m)

st_folium(m, width=None, height=460, returned_objects=[])

# =============================================================================
# Solar Performance Rating
# =============================================================================

st.divider()
st.subheader("Solar Performance Rating")

if psh >= 5.0:
    rating = "Excellent"
    color  = "#2ecc71"
    desc   = "Outstanding solar resource. Top-tier investment location worldwide."
elif psh >= 4.0:
    rating = "Very Good"
    color  = "#3498db"
    desc   = "Strong solar resource. Highly favorable conditions for investment."
elif psh >= 3.0:
    rating = "Good"
    color  = "#f39c12"
    desc   = "Adequate solar resource. Investment is viable with good returns."
elif psh >= 2.0:
    rating = "Moderate"
    color  = "#e67e22"
    desc   = "Below average solar resource. Careful financial planning needed."
else:
    rating = "Low"
    color  = "#e74c3c"
    desc   = "Limited solar resource. Extended payback period expected."

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    <div style="background:#0d1117;border:2px solid {color};
                border-radius:12px;padding:1.5rem;text-align:center;">
        <div style="color:{color};font-size:1.8rem;font-weight:800;">{rating}</div>
        <div style="color:#888;font-size:0.8rem;margin:0.3rem 0;">Solar Resource Rating</div>
        <div style="color:white;font-size:2rem;font-weight:700;">{psh} h/day</div>
        <hr style="border-color:{color}33;margin:0.8rem 0;">
        <div style="color:#aaa;font-size:0.85rem;">{desc}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("#### Monthly Irradiance")
    monthly = weather_data.get("monthly", [])
    if monthly:
        cols = st.columns(6)
        for i, month in enumerate(monthly):
            irr     = month["irradiance_kwh_m2"]
            max_irr = max(m["irradiance_kwh_m2"] for m in monthly)
            intensity = irr / max_irr
            r = int(30 + intensity * 30)
            g = int(100 + intensity * 100)
            b = int(255 - intensity * 180)
            color_m = f"rgb({r},{g},{b})"
            with cols[i % 6]:
                st.markdown(f"""
                <div style="background:#0d1117;border:1px solid {color_m};
                            border-radius:8px;padding:0.5rem;text-align:center;
                            margin-bottom:0.4rem;">
                    <div style="color:#888;font-size:0.7rem;">{month['month'][:3]}</div>
                    <div style="color:{color_m};font-size:0.95rem;font-weight:700;">{irr:.0f}</div>
                    <div style="color:#555;font-size:0.65rem;">kWh/m2</div>
                </div>
                """, unsafe_allow_html=True)