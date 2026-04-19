# SunStrategist -- Industrial Solar Optimizer

A professional-grade Python simulation tool for industrial rooftop solar
installations. Started in the previous academic semester and completed in
April 2026 with a full interactive web interface.

## Overview

SunStrategist calculates optimal panel angles, forecasts 20-year energy
production, and generates full financial analysis reports -- either via
a Streamlit web interface or a command-line pipeline.

## Features

- Real solar irradiance data via PVGIS API (no API key required)
- Optimal tilt/azimuth calculation based on GPS coordinates
- 20-year degradation-adjusted energy production forecast
- NPV, IRR, ROI and payback period analysis
- Battery Energy Storage System (BESS) simulation
- Carbon credit income calculation (EU ETS)
- Sensitivity analysis (Optimistic / Realistic / Pessimistic scenarios)
- Auto-generated professional PDF report with Matplotlib charts
- Interactive web interface with city selector and live results (v2.0.0)

## Versions

- v1.0.0 (Nov 2025) -- CLI pipeline with PDF report generation
- v2.0.0 (20.04.2026) -- Streamlit interactive web interface added

## Project Structure

```text
SunStrategist/
├── app.py                  # Streamlit web interface (v2.0.0)
├── main.py                 # CLI entry point (v1.0.0)
├── config.py               # Global constants and parameters
├── requirements.txt
├── models/
│   ├── panel.py            # SolarPanel class
│   ├── factory.py          # Factory class
│   └── battery.py          # Battery (BESS) class
├── engines/
│   ├── solar_engine.py     # Solar physics and energy calculations
│   ├── finance_engine.py   # NPV, IRR, ROI, cash flow modelling
│   ├── weather_api.py      # PVGIS API integration
│   └── sensitivity.py      # Scenario analysis engine
└── outputs/
├── charts.py           # Matplotlib chart generator
└── report_generator.py # FPDF2 PDF report builder
```
    
## Installation

```bash
pip install -r requirements.txt
```

## Usage

**Web Interface (recommended):**
```bash
streamlit run app.py
```

**Command Line:**
```bash
python main.py
```

## Configuration

Edit the constants at the top of `main.py` for CLI usage, or use the
sidebar controls in the Streamlit interface to configure city, roof area,
panel type, battery capacity, and financial parameters interactively.

## Tech Stack

Python -- PVGIS API -- Streamlit -- Matplotlib -- FPDF2 -- Requests

## Development

Started: October 2025

Version 1 Completed: November 2025

Version 2 Completed: April 2026