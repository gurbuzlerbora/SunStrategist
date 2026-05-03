# SunStrategist -- Industrial Solar Optimizer & Financial Forecaster

A professional-grade Python simulation platform for industrial rooftop solar
installations. Started in October 2025 and continuously developed across three
major versions, combining real-world API data, advanced financial modelling,
and an interactive multi-page web interface.

---

## Overview

SunStrategist enables factory owners, energy consultants, and engineers to
simulate rooftop solar installations for any location in the world. The platform
calculates optimal panel angles using solar physics, forecasts 20-year energy
production with degradation modelling, and delivers a full financial analysis
including NPV, IRR, ROI, payback period, carbon credit income, and Monte Carlo
risk simulation -- all through a clean, interactive web interface.

---

## Features

### Solar Physics Engine
- Real solar irradiance data via PVGIS API (European Commission -- free, no key required)
- Optimal tilt and azimuth angle calculation based on GPS coordinates
- 20-year degradation-adjusted energy production forecast (0.5% annual loss)
- Monthly and annual energy breakdown with seasonal variation analysis

### Financial Modelling
- NPV, IRR, ROI and payback period analysis
- Day / night / peak electricity tariff modelling with annual escalation
- Carbon credit income calculation (EU ETS -- EUR 65/ton CO2)
- Battery Energy Storage System (BESS) peak-shifting savings
- Full 20-year cash flow table with discounted cash flow (DCF)

### Risk & Scenario Analysis
- Sensitivity analysis -- Optimistic, Realistic, Pessimistic scenarios
- Monte Carlo simulation (up to 10,000 runs) with configurable volatility
- P10 / P50 / P90 NPV distribution and investment risk rating
- Tornado chart showing which variable drives the most risk

### Interactive Web Interface
- Multi-page Streamlit architecture (7 dedicated analysis pages)
- Global city search via Nominatim / OpenStreetMap geocoding
- Automatic electricity tariff loading for 100+ countries
- Plotly interactive charts with zoom, hover and filter
- Folium map with factory location, solar performance rating and benchmark comparison
- PDF report generation with one-click download

---

## Versions

| Version | Date | Highlights |
|---------|------|------------|
| v1.0.0 | Nov 2025 | CLI pipeline, PVGIS API, PDF report generation |
| v2.0.0 | Apr 2026 | Streamlit web interface, city selector, interactive charts |
| v3.0.0 | May 2026 | Multi-page architecture, global city search, Plotly, Folium map, Monte Carlo risk simulation, 100-country tariff database |

---

## Project Structure

```text
SunStrategist/
├── app.py                      # Main entry point & shared sidebar (v3.0)
├── main.py                     # CLI entry point (v1.0)
├── config.py                   # Global constants and parameters
├── requirements.txt
├── data/
│   └── electricity_tariffs.json  # 100+ country tariff database
├── models/
│   ├── panels.py               # SolarPanel class
│   ├── factory.py              # Factory class
│   └── battery.py              # Battery (BESS) class
├── engines/
│   ├── solar_engine.py         # Solar physics and energy calculations
│   ├── finance_engine.py       # NPV, IRR, ROI, cash flow modelling
│   ├── weather_api.py          # PVGIS API integration
│   └── sensitivity.py          # Scenario analysis engine
├── outputs/
│   ├── charts.py               # Matplotlib chart generator (PDF)
│   └── report_generator.py     # FPDF2 PDF report builder
└── pages/
    ├── 1_Home.py               # Entry redirect
    ├── 2_Energy_Analysis.py    # 20-year forecast + monthly charts
    ├── 3_Financial_Analysis.py # Cash flow + revenue breakdown + PDF
    ├── 4_Scenario_Comparison.py # Sensitivity analysis + scenario cards
    ├── 5_BESS_Analysis.py      # Battery degradation + daily simulation
    ├── 6_Map_View.py           # Folium map + benchmark comparison
    └── 7_Risk_Analysis.py      # Monte Carlo simulation + tornado chart
```

---

## Installation

```bash
git clone https://github.com/gurbuzlerbora/SunStrategist.git
cd SunStrategist
pip install -r requirements.txt
```

---

## Usage

**Web Interface (recommended):**
```bash
streamlit run app.py
```

**Command Line (PDF report only):**
```bash
python main.py
```

---

## How It Works

1. Search any city in the world -- coordinates load automatically
2. Configure factory roof area, panel type and battery capacity
3. Financial parameters auto-load based on country electricity tariffs
4. Click **Run Analysis** -- PVGIS API fetches real solar irradiance data
5. Navigate through 7 analysis pages to explore results
6. Run Monte Carlo simulation to assess investment risk
7. Download the professional PDF report

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11 |
| Web Interface | Streamlit |
| Charts | Plotly, Matplotlib |
| Maps | Folium, streamlit-folium |
| Geocoding | Geopy / Nominatim (OpenStreetMap) |
| Solar Data | PVGIS API (European Commission) |
| PDF Reports | FPDF2 |
| Risk Modelling | NumPy (Monte Carlo) |
| HTTP Requests | Requests |

---

## Development

| Milestone | Date |
|-----------|------|
| Project Started | October 2025 |
| v1.0.0 Completed | November 2025 |
| v2.0.0 Completed | April 2026 |
| v3.0.0 Completed | May 2026 |



