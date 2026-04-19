# ☀ SunStrategist — Industrial Solar Optimizer

A professional-grade Python simulation tool for industrial 
rooftop solar installations. Calculates optimal panel angles, 
forecasts 20-year energy production, and generates full 
financial analysis reports.

## Features
- Real solar irradiance data via PVGIS API (no key required)
- Optimal tilt/azimuth calculation based on coordinates
- 20-year degradation-adjusted energy forecast
- NPV, IRR, ROI & payback period analysis
- Battery Energy Storage (BESS) simulation
- Carbon credit income calculation (EU ETS)
- Sensitivity analysis (Optimistic / Realistic / Pessimistic)
- Auto-generated professional PDF report with charts

## Project Structure

```text
SunStrategist/
├── main.py
├── config.py
├── models/
│   ├── panel.py
│   ├── factory.py
│   └── battery.py
├── engines/
│   ├── solar_engine.py
│   ├── finance_engine.py
│   ├── weather_api.py
│   └── sensitivity.py
└── outputs/
    ├── charts.py
    └── report_generator.py
```
    
## Installation
```bash
pip install -r requirements.txt
python main.py
```

## Configuration
Edit the constants at the top of `main.py`:
```python
FACTORY_NAME    = "Berlin Industrial Factory A"
ROOF_AREA_M2    = 5000
INCLUDE_BATTERY = True
```

## Tech Stack
Python · PVGIS API · Matplotlib · FPDF2 · Requests