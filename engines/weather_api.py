"""
PVGIS Weather Data Engine
-------------------------
This is our connection to the real world. It talks to the European
Commission's database (PVGIS) to get actual solar data for our
specific location. Instead of guessing how much the sun shines,
we use this to get scientific, satellite-based numbers for our simulation.
"""

import requests
from config import (
    PVGIS_API_URL,
    PVGIS_TIMEOUT_SEC,
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
    DEFAULT_ALTITUDE,
)


class WeatherAPI:
    """
    Fetches real-world solar irradiance and climate data from the
    PVGIS (Photovoltaic Geographical Information System) API.
    Provided by the European Commission — free, no API key required.

    API Docs: https://re.jrc.ec.europa.eu/api/v5_2/
    """

    def __init__(
        self,
        latitude: float = DEFAULT_LATITUDE,
        longitude: float = DEFAULT_LONGITUDE,
        altitude: float = DEFAULT_ALTITUDE,
    ):
        """
        Args:
            latitude  : Location latitude in decimal degrees.
            longitude : Location longitude in decimal degrees.
            altitude  : Altitude above sea level in metres.
        """
        self.latitude  = latitude
        self.longitude = longitude
        self.altitude  = altitude

        # Cached raw API response
        self._raw_data: dict = {}

    # -------------------------------------------------------------------------
    # API Request
    # -------------------------------------------------------------------------

    def fetch(
        self,
        panel_efficiency: float = 0.21,
        tilt_deg: float = 35.0,
        azimuth_deg: float = 0.0,
        system_loss_pct: float = 14.0,
    ) -> dict:
        """
        Sends a request to the PVGIS PVcalc endpoint and returns parsed data.

        Args:
            panel_efficiency : Panel efficiency as decimal (e.g. 0.21).
            tilt_deg         : Panel tilt angle in degrees.
            azimuth_deg      : Azimuth angle in degrees.
                               PVGIS convention: 0 = south, -90 = east, 90 = west.
            system_loss_pct  : Total system losses in percent (default 14%).

        Returns:
            Dictionary with monthly and annual irradiance + energy data.

        Raises:
            ConnectionError : If the API request fails.
            ValueError      : If the API returns unexpected data.
        """
        # Convert panel efficiency to peak power percentage for PVGIS
        # PVGIS expects peak power in kWp — we use 1 kWp as reference unit
        params = {
            "lat"       : self.latitude,
            "lon"       : self.longitude,
            "userhorizon": "",
            "raddatabase": "PVGIS-SARAH2",   # best dataset for Europe
            "peakpower" : 1,                  # 1 kWp reference system
            "loss"      : system_loss_pct,
            "mountingplace": "building",
            "angle"     : tilt_deg,
            "aspect"    : azimuth_deg,
            "outputformat": "json",
            "browser"   : 0,
        }

        print(f"[WeatherAPI] Fetching PVGIS data for "
              f"lat={self.latitude}, lon={self.longitude} ...")

        try:
            response = requests.get(
                PVGIS_API_URL,
                params=params,
                timeout=PVGIS_TIMEOUT_SEC,
            )
            response.raise_for_status()
        except requests.exceptions.Timeout:
            raise ConnectionError(
                "[WeatherAPI] Request timed out. Check your internet connection."
            )
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"[WeatherAPI] API request failed: {e}")

        raw = response.json()
        self._raw_data = raw

        return self._parse_response(raw)

    # -------------------------------------------------------------------------
    # Response Parser
    # -------------------------------------------------------------------------

    def _parse_response(self, raw: dict) -> dict:
        """
        Parses the raw PVGIS JSON response into a clean, usable dictionary.

        Args:
            raw: Raw JSON response from PVGIS API.

        Returns:
            Parsed dictionary with the following keys:
                - annual_irradiance_kwh_m2 : Total annual irradiance (kWh/m²)
                - annual_energy_kwh_per_kwp: Annual yield per kWp installed
                - peak_sun_hours_daily     : Average daily peak sun hours
                - monthly                  : List of 12 monthly dicts
                - system_loss_pct          : System losses used in calculation
        """
        try:
            totals  = raw["outputs"]["totals"]["fixed"]
            monthly = raw["outputs"]["monthly"]["fixed"]
        except KeyError as e:
            raise ValueError(f"[WeatherAPI] Unexpected API response structure: {e}")

        # Annual values
        annual_irradiance      = totals["H(i)_y"]   # kWh/m² per year
        annual_energy_per_kwp  = totals["E_y"]       # kWh/kWp per year
        peak_sun_hours_daily   = annual_irradiance / 365.0

        # Monthly breakdown
        month_names = [
            "January", "February", "March", "April",
            "May", "June", "July", "August",
            "September", "October", "November", "December"
        ]

        monthly_data = []
        for i, month in enumerate(monthly):
            monthly_data.append({
                "month"              : month_names[i],
                "irradiance_kwh_m2"  : round(month["H(i)_m"], 2),
                "energy_kwh_per_kwp" : round(month["E_m"], 2),
                "peak_sun_hours_daily": round(month["H(i)_m"] / 30.0, 2),
            })

        result = {
            "annual_irradiance_kwh_m2" : round(annual_irradiance, 2),
            "annual_energy_kwh_per_kwp": round(annual_energy_per_kwp, 2),
            "peak_sun_hours_daily"     : round(peak_sun_hours_daily, 2),
            "monthly"                  : monthly_data,
            "system_loss_pct"          : raw["inputs"].get("system_losses", {}).get("system_loss", 14.0),
            "location"                 : {
                "latitude" : self.latitude,
                "longitude": self.longitude,
                "altitude" : self.altitude,
            }
        }

        print(f"[WeatherAPI] Success — "
              f"Annual irradiance: {result['annual_irradiance_kwh_m2']} kWh/m², "
              f"Daily PSH: {result['peak_sun_hours_daily']:.2f} h/day")

        return result

    # -------------------------------------------------------------------------
    # Cached Data Access
    # -------------------------------------------------------------------------

    def get_monthly_peak_sun_hours(self) -> list:
        """
        Returns a list of 12 average daily peak sun hours, one per month.
        Requires fetch() to have been called first.

        Returns:
            List of 12 floats representing daily PSH per month.
        """
        if not self._raw_data:
            raise RuntimeError(
                "[WeatherAPI] No data available. Call fetch() first."
            )
        parsed = self._parse_response(self._raw_data)
        return [m["peak_sun_hours_daily"] for m in parsed["monthly"]]

    # -------------------------------------------------------------------------
    # Representation
    # -------------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"WeatherAPI(lat={self.latitude}, "
            f"lon={self.longitude}, "
            f"alt={self.altitude}m)"
        )