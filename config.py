"""
SunStrategist Global Configuration
----------------------------------
This module serves as the 'Single Source of Truth' for the entire project.
It contains global constants including geographical coordinates (Berlin),
industrial solar panel specifications, local electricity tariffs (Germany),
and financial assumptions (inflation, discount rates, carbon credits).
"""

# --- Project Identity --------------------------------------------------------
PROJECT_NAME = "SunStrategist"
VERSION      = "1.0.0"

# --- Project Identity --------------------------------------------------------
PROJECT_NAME = "SunStrategist"
VERSION      = "1.0.0"

# --- Default Factory Location (Berlin, Germany) ------------------------------
DEFAULT_LATITUDE  = 52.5200   # Berlin
DEFAULT_LONGITUDE = 13.4050
DEFAULT_ALTITUDE  = 34        # metres above sea level

# --- Solar Panel Defaults ----------------------------------------------------
PANEL_RATED_POWER_W    = 550    # Watt peak (modern industrial panel)
PANEL_EFFICIENCY       = 0.21   # 21% efficiency
PANEL_AREA_M2          = 2.65   # m² per panel
PANEL_DEGRADATION_RATE = 0.005  # 0.5% annual efficiency loss
PANEL_LIFESPAN_YEARS   = 20
PANEL_COST_USD         = 180    # cost per panel (USD)

# --- Installation Costs ------------------------------------------------------
INSTALLATION_COST_USD_PER_KW  = 250   # installation cost (USD/kW)
INVERTER_COST_USD_PER_KW      = 80    # inverter cost (USD/kW)
MAINTENANCE_COST_RATIO        = 0.01  # 1% of total system cost per year

# --- Battery Storage (BESS) Defaults -----------------------------------------
BATTERY_CAPACITY_KWH     = 100   # kWh
BATTERY_COST_USD_PER_KWH = 280   # cost per kWh of storage
BATTERY_EFFICIENCY       = 0.92  # round-trip efficiency
BATTERY_MAX_SOC          = 0.95  # maximum state of charge
BATTERY_MIN_SOC          = 0.10  # minimum state of charge (protection)
BATTERY_DEGRADATION_RATE = 0.02  # 2% annual capacity loss

# --- Electricity Tariffs (German industrial, EUR/kWh) ------------------------
TARIFF_DAY_EUR_PER_KWH   = 0.28  # 06:00 - 22:00
TARIFF_NIGHT_EUR_PER_KWH = 0.16  # 22:00 - 06:00
TARIFF_PEAK_EUR_PER_KWH  = 0.38  # peak hours (08:00 - 12:00)
DAY_HOURS   = list(range(6, 22))
NIGHT_HOURS = list(range(0, 6)) + list(range(22, 24))
PEAK_HOURS  = list(range(8, 12))

# Annual tariff increase rate assumption
TARIFF_ANNUAL_INCREASE_RATE = 0.04  # 4% per year (EU energy market estimate)

# --- Carbon & Incentives -----------------------------------------------------
CARBON_EMISSION_FACTOR_KG_PER_KWH = 0.366  # German grid emission factor (2024)
CARBON_CREDIT_EUR_PER_TON         = 65.0   # EU ETS carbon price (EUR/ton CO2)

# --- Financial Parameters ----------------------------------------------------
DISCOUNT_RATE    = 0.07  # 7% discount rate for NPV calculations
INFLATION_RATE   = 0.03  # 3% annual inflation (EU average)
EUR_TO_USD       = 1.08  # 1 EUR = 1.08 USD (update as needed)
PROJECT_LIFETIME = 20    # years

# --- Sensitivity Analysis Multipliers ----------------------------------------
SCENARIOS = {
    "optimistic":  {"irradiance": 1.10, "tariff": 1.20, "cost": 0.90},
    "realistic":   {"irradiance": 1.00, "tariff": 1.00, "cost": 1.00},
    "pessimistic": {"irradiance": 0.90, "tariff": 0.85, "cost": 1.15},
}

# --- Weather API (PVGIS — free, no registration required) --------------------
PVGIS_API_URL     = "https://re.jrc.ec.europa.eu/api/v5_2/PVcalc"
PVGIS_TIMEOUT_SEC = 30

# --- Output ------------------------------------------------------------------
OUTPUT_DIR      = "outputs/reports"
REPORT_FILENAME = "sunstrategist_report.pdf"
CHART_DPI       = 150
CHART_STYLE     = "seaborn-v0_8-darkgrid"