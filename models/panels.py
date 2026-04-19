"""
Solar Panel Model
-----------------
This is the 'ID card' for each individual panel. It holds all
the technical specs, like how much power it makes and its size.
It also tracks how each panel loses a tiny bit of its
efficiency every year as it gets older.
"""

from config import (
    PANEL_RATED_POWER_W,
    PANEL_EFFICIENCY,
    PANEL_AREA_M2,
    PANEL_DEGRADATION_RATE,
    PANEL_LIFESPAN_YEARS,
    PANEL_COST_USD,
)


class SolarPanel:
    """
    Represents a single industrial solar panel unit.
    Stores physical specifications and calculates degraded efficiency over time.
    """

    def __init__(
        self,
        panel_id: int,
        rated_power_w: float = PANEL_RATED_POWER_W,
        efficiency: float = PANEL_EFFICIENCY,
        area_m2: float = PANEL_AREA_M2,
        degradation_rate: float = PANEL_DEGRADATION_RATE,
        cost_usd: float = PANEL_COST_USD,
        tilt_deg: float = 35.0,
        azimuth_deg: float = 180.0,
    ):
        """
        Args:
            panel_id       : Unique identifier for this panel.
            rated_power_w  : Rated peak power in Watts (STC conditions).
            efficiency     : Initial conversion efficiency (0.0 - 1.0).
            area_m2        : Physical surface area in square metres.
            degradation_rate: Annual efficiency loss as a decimal (e.g. 0.005).
            cost_usd       : Purchase cost in USD.
            tilt_deg       : Tilt angle from horizontal in degrees.
            azimuth_deg    : Azimuth angle in degrees (180 = true south).
        """
        self.panel_id        = panel_id
        self.rated_power_w   = rated_power_w
        self.efficiency      = efficiency
        self.area_m2         = area_m2
        self.degradation_rate = degradation_rate
        self.cost_usd        = cost_usd
        self.tilt_deg        = tilt_deg
        self.azimuth_deg     = azimuth_deg

        # Computed on initialisation
        self.rated_power_kw  = rated_power_w / 1000.0

    # -------------------------------------------------------------------------
    # Core Methods
    # -------------------------------------------------------------------------

    def get_efficiency_at_year(self, year: int) -> float:
        """
        Returns the degraded efficiency at a given project year.
        Uses compound degradation: eff * (1 - rate) ^ year

        Args:
            year: Project year (0 = installation year, no degradation yet).

        Returns:
            Degraded efficiency as a float between 0 and 1.
        """
        if year < 0:
            raise ValueError(f"Year must be >= 0, got {year}")
        return self.efficiency * ((1 - self.degradation_rate) ** year)

    def get_power_at_year(self, year: int) -> float:
        """
        Returns the effective rated power (Watts) after degradation.

        Args:
            year: Project year.

        Returns:
            Degraded power output in Watts.
        """
        return self.rated_power_w * ((1 - self.degradation_rate) ** year)

    def get_annual_energy_kwh(self, peak_sun_hours: float, year: int) -> float:
        """
        Estimates annual energy output for this single panel.

        Formula:
            E = P_rated(kW) * PSH * 365 * degradation_factor

        Args:
            peak_sun_hours: Average daily peak sun hours for the location.
            year          : Project year (for degradation).

        Returns:
            Estimated annual energy output in kWh.
        """
        degradation_factor = (1 - self.degradation_rate) ** year
        return self.rated_power_kw * peak_sun_hours * 365 * degradation_factor

    # -------------------------------------------------------------------------
    # Representation
    # -------------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"SolarPanel(id={self.panel_id}, "
            f"power={self.rated_power_w}W, "
            f"efficiency={self.efficiency:.1%}, "
            f"tilt={self.tilt_deg}°, "
            f"azimuth={self.azimuth_deg}°)"
        )

    def summary(self) -> dict:
        """
        Returns a dictionary snapshot of this panel's key specifications.
        Useful for report generation and logging.
        """
        return {
            "panel_id"        : self.panel_id,
            "rated_power_w"   : self.rated_power_w,
            "efficiency_pct"  : round(self.efficiency * 100, 2),
            "area_m2"         : self.area_m2,
            "tilt_deg"        : self.tilt_deg,
            "azimuth_deg"     : self.azimuth_deg,
            "cost_usd"        : self.cost_usd,
            "degradation_rate": self.degradation_rate,
        }