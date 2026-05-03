# =============================================================================
# pages/6_Map_View.py -- Factory Location & Map View
# =============================================================================

import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import os

st.set_page_config(page_title="Map View | SunStrategist", layout="wide")

st.title("Factory Location & Solar Map")

if "results" not in st.session_state:
    st.warning("No analysis results found. Please run the analysis from the Home page first.")
    st.stop()

results      = st.session_state["results"]
factory      = results["factory"]
weather_data = results["weather_data"]
metrics      = results["metrics"]
cfg          = st.session_state.get("cfg", {})

lat = factory.latitude
lon = factory.longitude

# =============================================================================
# Location Summary
# =============================================================================

st.subheader("Location Overview")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Latitude",          f"{lat}°")
with col2:
    st.metric("Longitude",         f"{lon}°")
with col3:
    st.metric("Annual Irradiance", f"{weather_data['annual_irradiance_kwh_m2']} kWh/m2")
with col4:
    st.metric("Daily PSH",         f"{weather_data['peak_sun_hours_daily']} h/day")

st.divider()

# =============================================================================
# Main Factory Map
# =============================================================================

st.subheader("Factory Location")

# Build folium map
m = folium.Map(
    location=[lat, lon],
    zoom_start=13,
    tiles="CartoDB dark_matter",
)

# Factory marker
popup_html = f"""
<div style="font-family: Arial; min-width: 220px;">
    <h4 style="color: #1E90FF; margin-bottom: 8px;">{factory.name}</h4>
    <hr style="border-color: #1E90FF33;">
    <b>Capacity:</b> {factory.get_total_capacity_kw():,.1f} kWp<br>
    <b>Panels:</b> {len(factory.panels):,}<br>
    <b>Roof Area:</b> {factory.roof_area_m2:,} m2<br>
    <b>Optimal Tilt:</b> {factory.optimal_tilt_deg}°<br>
    <hr style="border-color: #1E90FF33;">
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

# Solar irradiance circle -- size based on PSH
folium.CircleMarker(
    location=[lat, lon],
    radius=60,
    color="#1E90FF",
    fill=True,
    fill_color="#1E90FF",
    fill_opacity=0.08,
    tooltip=f"Daily PSH: {weather_data['peak_sun_hours_daily']} h/day",
).add_to(m)

st_folium(m, width=None, height=480, returned_objects=[])

# =============================================================================
# Solar Irradiance Heatmap Context
# =============================================================================

st.divider()
st.subheader("Global Solar Context")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Location Solar Performance")

    psh = weather_data["peak_sun_hours_daily"]

    if psh >= 5.0:
        rating = "Excellent"
        color  = "#2ecc71"
        desc   = "Outstanding solar resource. Top-tier investment location."
    elif psh >= 4.0:
        rating = "Very Good"
        color  = "#3498db"
        desc   = "Strong solar resource. Highly favorable for investment."
    elif psh >= 3.0:
        rating = "Good"
        color  = "#f39c12"
        desc   = "Adequate solar resource. Investment is viable."
    elif psh >= 2.0:
        rating = "Moderate"
        color  = "#e67e22"
        desc   = "Below average solar resource. Careful financial planning needed."
    else:
        rating = "Low"
        color  = "#e74c3c"
        desc   = "Limited solar resource. Extended payback period expected."

    st.markdown(f"""
    <div style="
        background: #0d1117;
        border: 2px solid {color};
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
    ">
        <div style="color: {color}; font-size: 1.8rem; font-weight: 800;">
            {rating}
        </div>
        <div style="color: #888; font-size: 0.9rem; margin: 0.5rem 0;">
            Solar Resource Rating
        </div>
        <div style="color: white; font-size: 2.2rem; font-weight: 700;">
            {psh} h/day
        </div>
        <div style="color: #888; font-size: 0.8rem;">
            Daily Peak Sun Hours
        </div>
        <hr style="border-color: {color}33; margin: 1rem 0;">
        <div style="color: #aaa; font-size: 0.85rem;">
            {desc}
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("#### Benchmark Comparison")

    benchmarks = [
        ("Dubai, UAE",        6.1, "#f39c12"),
        ("Madrid, Spain",     5.3, "#e67e22"),
        ("Rome, Italy",       4.8, "#e67e22"),
        ("Paris, France",     3.5, "#3498db"),
        ("This Location",     psh, "#1E90FF"),
        ("Berlin, Germany",   3.6, "#3498db"),
        ("Warsaw, Poland",    3.4, "#3498db"),
        ("Helsinki, Finland", 2.8, "#9b59b6"),
    ]

    # Sort by PSH descending
    benchmarks_sorted = sorted(benchmarks, key=lambda x: x[1], reverse=True)
    max_psh = benchmarks_sorted[0][1]

    for name, val, color in benchmarks_sorted:
        is_current = name == "This Location"
        border = "2px solid #1E90FF" if is_current else "none"
        bg     = "#0d1117" if is_current else "transparent"

        bar_width = int((val / max_psh) * 100)

        st.markdown(f"""
        <div style="
            background: {bg};
            border: {border};
            border-radius: 6px;
            padding: 0.4rem 0.8rem;
            margin-bottom: 0.4rem;
        ">
            <div style="display: flex; justify-content: space-between;
                        align-items: center; margin-bottom: 3px;">
                <span style="color: {'white' if is_current else '#aaa'};
                             font-size: 0.85rem; font-weight: {'700' if is_current else '400'};">
                    {'>> ' if is_current else ''}{name}
                </span>
                <span style="color: {color}; font-size: 0.85rem; font-weight: 600;">
                    {val} h/day
                </span>
            </div>
            <div style="background: #1a1a2e; border-radius: 3px; height: 6px;">
                <div style="background: {color}; width: {bar_width}%;
                            height: 6px; border-radius: 3px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# =============================================================================
# Monthly Irradiance Map Data
# =============================================================================

st.divider()
st.subheader("Monthly Irradiance Breakdown")

monthly = weather_data.get("monthly", [])

if monthly:
    cols = st.columns(6)
    for i, month in enumerate(monthly):
        col = cols[i % 6]
        irr = month["irradiance_kwh_m2"]
        max_irr = max(m["irradiance_kwh_m2"] for m in monthly)
        intensity = irr / max_irr

        r = int(30 + intensity * 30)
        g = int(100 + intensity * 100)
        b = int(255 - intensity * 180)
        color = f"rgb({r},{g},{b})"

        with col:
            st.markdown(f"""
            <div style="
                background: #0d1117;
                border: 1px solid {color};
                border-radius: 8px;
                padding: 0.6rem;
                text-align: center;
                margin-bottom: 0.5rem;
            ">
                <div style="color: #888; font-size: 0.75rem;">
                    {month['month'][:3]}
                </div>
                <div style="color: {color}; font-size: 1rem; font-weight: 700;">
                    {irr:.0f}
                </div>
                <div style="color: #555; font-size: 0.7rem;">kWh/m2</div>
            </div>
            """, unsafe_allow_html=True)