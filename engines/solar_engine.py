"""
Solar Physics & Energy Engine
-----------------------------
This is the 'math brain' of the project. It calculates the best
angle for the panels to face the sun based on our location.
It also predicts how much electricity the factory will produce
over the next 20 years, making sure to account for the panels
getting a bit older and weaker each year.
"""

import math
from typing import List
from config import (
    PANEL_DEGRADATION_RATE,
    PROJECT_LIFETIME,
)
from models.panels import SolarPanel
from models.factory import Factory


class SolarEngine:
    """
    Handles all solar physics calculations including:
    - Optimal tilt and azimuth angle estimation
    - Annual and monthly energy output for the full panel array
    - 20-year degradation-adjusted energy forecast
    """

    def __init__(self, factory: Factory):
        """
        Args:
            factory: Factory instance with installed panels and location data.
        """
        self.factory  = factory
        self.latitude = factory.latitude

        # Results cache — populated after run()
        self.optimal_tilt_deg    = None
        self.optimal_azimuth_deg = 180.0   # true south for northern hemisphere
        self.weather_data        = None
        self._annual_output_cache = {}

    # -------------------------------------------------------------------------
    # Optimal Angle Calculation
    # -------------------------------------------------------------------------

    def calc_optimal_tilt(self) -> float:
        """
        Estimates the optimal fixed tilt angle for maximum annual yield.
        Uses the latitude-based empirical formula widely adopted in PV literature.

        Formula:
            tilt = 0.87 * |latitude| + 3.1   (for latitudes 25° - 65°)

            Rationale:
        This formula follows the empirical 'best-fit' model established in
        core PV literature (e.g., Lunde, Duffie & Beckman).

        - 0.87 Multiplier: Adjusts for the longer atmospheric path (Air Mass)
          and the lower sun elevation typical of high latitudes.

        - +3.1 Constant: An offset to optimize the capture of diffuse radiation
          (scattering from clouds), maximizing total annual yield rather than
          just peak summer performance.

        For Berlin (lat=52.52°): tilt ≈ 48.8°

        Returns:
            Optimal tilt angle in degrees (float).
        """
        lat = abs(self.latitude)

        if lat < 25:
            # Tropical regions — low tilt favours diffuse radiation capture
            tilt = 0.70 * lat + 2.5
        elif lat <= 65:
            # Mid-latitude formula (covers all of Europe)
            tilt = 0.87 * lat + 3.1
        else:
            # High latitude — steeper tilt to catch low sun angles
            tilt = 0.90 * lat + 2.0

        self.optimal_tilt_deg = round(tilt, 1)
        return self.optimal_tilt_deg

    def calc_optimal_azimuth(self) -> float:
        """
        Determines the optimal azimuth angle based on hemisphere.

        Northern hemisphere (lat > 0): face south  → 180°
        Southern hemisphere (lat < 0): face north  →   0°

        Returns:
            Optimal azimuth angle in degrees (float).
        """
        self.optimal_azimuth_deg = 180.0 if self.latitude >= 0 else 0.0
        return self.optimal_azimuth_deg

    def apply_optimal_angles(self) -> None:
        """
        Calculates optimal angles and applies them to all panels in the factory.
        Also updates the factory's stored optimal angle attributes.
        """
        tilt    = self.calc_optimal_tilt()
        azimuth = self.calc_optimal_azimuth()

        for panel in self.factory.panels:
            panel.tilt_deg    = tilt
            panel.azimuth_deg = azimuth

        self.factory.optimal_tilt_deg    = tilt
        self.factory.optimal_azimuth_deg = azimuth

        print(f"[SolarEngine] Optimal angles applied — "
              f"Tilt: {tilt}°, Azimuth: {azimuth}°")

    # -------------------------------------------------------------------------
    # Energy Output Calculations
    # -------------------------------------------------------------------------

    def calc_annual_output_kwh(
        self,
        weather_data: dict,
        year: int = 0,
    ) -> float:
        """
        Calculates total annual energy output of the entire panel array.

        Formula:
            E = total_capacity_kwp * annual_yield_per_kwp * degradation_factor

        Args:
            weather_data : Parsed dict returned by WeatherAPI.fetch().
            year         : Project year for degradation adjustment.

        Returns:
            Total annual energy output in kWh.
        """
        self.weather_data = weather_data

        annual_yield_per_kwp = weather_data["annual_energy_kwh_per_kwp"]
        total_kwp            = self.factory.get_total_capacity_kwp()
        degradation_factor   = (1 - PANEL_DEGRADATION_RATE) ** year

        output_kwh = total_kwp * annual_yield_per_kwp * degradation_factor
        self._annual_output_cache[year] = round(output_kwh, 2)

        return round(output_kwh, 2)

    def calc_monthly_output_kwh(
        self,
        weather_data: dict,
        year: int = 0,
    ) -> List[dict]:
        """
        Calculates energy output broken down by month for a given project year.

        Args:
            weather_data : Parsed dict returned by WeatherAPI.fetch().
            year         : Project year for degradation adjustment.

        Returns:
            List of 12 dicts:
            [{"month": str, "energy_kwh": float, "peak_sun_hours": float}, ...]
        """
        total_kwp          = self.factory.get_total_capacity_kwp()
        degradation_factor = (1 - PANEL_DEGRADATION_RATE) ** year
        monthly_output     = []

        for month in weather_data["monthly"]:
            energy = (
                total_kwp
                * month["energy_kwh_per_kwp"]
                * degradation_factor
            )
            monthly_output.append({
                "month"           : month["month"],
                "energy_kwh"      : round(energy, 2),
                "peak_sun_hours"  : month["peak_sun_hours_daily"],
                "irradiance_kwh_m2": month["irradiance_kwh_m2"],
            })

        return monthly_output

    # -------------------------------------------------------------------------
    # 20-Year Forecast
    # -------------------------------------------------------------------------

    def calc_lifetime_energy_forecast(
        self,
        weather_data: dict,
    ) -> List[dict]:
        """
        Generates a year-by-year energy production forecast over the full
        project lifetime, accounting for panel degradation each year.

        Args:
            weather_data: Parsed dict returned by WeatherAPI.fetch().

        Returns:
            List of dicts, one per year:
            [
                {
                    "year"              : int,
                    "annual_output_kwh" : float,
                    "degradation_factor": float,
                    "efficiency_pct"    : float,
                },
                ...
            ]
        """
        forecast = []

        for year in range(PROJECT_LIFETIME + 1):
            degradation_factor = (1 - PANEL_DEGRADATION_RATE) ** year
            annual_output      = self.calc_annual_output_kwh(weather_data, year)
            avg_efficiency     = (
                self.factory.panels[0].get_efficiency_at_year(year)
                if self.factory.panels else 0.0
            )

            forecast.append({
                "year"              : year,
                "annual_output_kwh" : annual_output,
                "degradation_factor": round(degradation_factor, 4),
                "efficiency_pct"    : round(avg_efficiency * 100, 2),
            })

        total_lifetime = sum(f["annual_output_kwh"] for f in forecast)
        print(f"[SolarEngine] 20-year total output forecast: "
              f"{total_lifetime:,.0f} kWh")

        return forecast

    # -------------------------------------------------------------------------
    # Solar Geometry Helpers
    # -------------------------------------------------------------------------

    def calc_solar_declination(self, day_of_year: int) -> float:
        """
        Calculates solar declination angle for a given day.
        Declination varies from -23.45° (winter) to +23.45° (summer).

        Formula: δ = 23.45 * sin(360/365 * (284 + N))

        Args:
            day_of_year: Day number (1 = Jan 1, 365 = Dec 31).

        Returns:
            Declination angle in degrees.
        """
        return 23.45 * math.sin(
            math.radians((360 / 365) * (284 + day_of_year))
        )

    def calc_peak_sun_hours_theoretical(self, day_of_year: int) -> float:
        """
        Estimates theoretical daily peak sun hours based on
        latitude and solar declination (clear-sky approximation).

        Args:
            day_of_year: Day number (1-365).

        Returns:
            Estimated peak sun hours for that day.
        """
        declination  = self.calc_solar_declination(day_of_year)
        lat_rad      = math.radians(self.latitude)
        dec_rad      = math.radians(declination)

        # Hour angle at sunset
        cos_hour_angle = (
            -math.tan(lat_rad) * math.tan(dec_rad)
        )
        # Clamp to valid range to avoid domain errors at extreme latitudes
        cos_hour_angle = max(-1.0, min(1.0, cos_hour_angle))
        hour_angle_deg = math.degrees(math.acos(cos_hour_angle))

        # Daylight hours and PSH approximation
        daylight_hours = (2 / 15) * hour_angle_deg
        psh            = daylight_hours * 0.45   # ~45% efficiency factor

        return round(psh, 2)

    # -------------------------------------------------------------------------
    # Representation
    # -------------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"SolarEngine(factory='{self.factory.name}', "
            f"lat={self.latitude}, "
            f"optimal_tilt={self.optimal_tilt_deg}°)"
        )