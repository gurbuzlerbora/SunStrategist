"""
Factory Rooftop & Infrastructure Model
--------------------------------------
This represents the actual building. It looks at the roof size
and figures out exactly how many panels we can fit up there.
It also handles the math for the total cost to build the system
and keep it running every year.
"""

import math
from typing import List
from config import (
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
    DEFAULT_ALTITUDE,
    PANEL_AREA_M2,
    PANEL_COST_USD,
    INSTALLATION_COST_USD_PER_KW,
    INVERTER_COST_USD_PER_KW,
    MAINTENANCE_COST_RATIO,
)
from models.panels import SolarPanel


class Factory:
    """
    Represents an industrial factory with a rooftop solar installation.
    Manages the panel array, roof geometry, and total system cost calculations.
    """

    def __init__(
        self,
        name: str,
        roof_area_m2: float,
        latitude: float = DEFAULT_LATITUDE,
        longitude: float = DEFAULT_LONGITUDE,
        altitude_m: float = DEFAULT_ALTITUDE,
        usable_roof_ratio: float = 0.75,
        panel_spacing_ratio: float = 0.85,
    ):
        """
        Args:
            name               : Factory name (used in reports).
            roof_area_m2       : Total flat roof area in square metres.
            latitude           : Geographic latitude in decimal degrees.
            longitude          : Geographic longitude in decimal degrees.
            altitude_m         : Altitude above sea level in metres.
            usable_roof_ratio  : Fraction of roof usable for panels (default 75%).
            panel_spacing_ratio: Fraction of usable area covered by panels
                                 after spacing/shading gaps (default 85%).
        """
        self.name                = name
        self.roof_area_m2        = roof_area_m2
        self.latitude            = latitude
        self.longitude           = longitude
        self.altitude_m          = altitude_m
        self.usable_roof_ratio   = usable_roof_ratio
        self.panel_spacing_ratio = panel_spacing_ratio

        # Panel array — populated by install_panels()
        self.panels: List[SolarPanel] = []

        # Optimal angles — set by SolarEngine later
        self.optimal_tilt_deg    = None
        self.optimal_azimuth_deg = None

    # -------------------------------------------------------------------------
    # Panel Installation
    # -------------------------------------------------------------------------

    def calculate_max_panels(self) -> int:
        """
        Calculates the maximum number of panels that fit on the roof.

        Formula:
            usable_area = roof_area * usable_roof_ratio * panel_spacing_ratio
            max_panels  = floor(usable_area / panel_area)

        Returns:
            Maximum number of panels as an integer.
        """
        usable_area = (
            self.roof_area_m2
            * self.usable_roof_ratio
            * self.panel_spacing_ratio
        )
        return math.floor(usable_area / PANEL_AREA_M2)

    def install_panels(
        self,
        tilt_deg: float = 35.0,
        azimuth_deg: float = 180.0,
        num_panels: int = None,
    ) -> None:
        """
        Instantiates and registers SolarPanel objects on this factory.

        Args:
            tilt_deg    : Tilt angle applied to all panels (degrees).
            azimuth_deg : Azimuth angle applied to all panels (degrees).
            num_panels  : Number of panels to install. If None, uses maximum
                          possible based on roof area.
        """
        if num_panels is None:
            num_panels = self.calculate_max_panels()

        self.panels = [
            SolarPanel(
                panel_id=i + 1,
                tilt_deg=tilt_deg,
                azimuth_deg=azimuth_deg,
            )
            for i in range(num_panels)
        ]

        print(
            f"[Factory] '{self.name}' — {num_panels} panels installed "
            f"(tilt={tilt_deg}°, azimuth={azimuth_deg}°)"
        )

    # -------------------------------------------------------------------------
    # System Capacity
    # -------------------------------------------------------------------------

    def get_total_capacity_kw(self) -> float:
        """
        Returns total installed capacity of the panel array in kilowatts.
        """
        return sum(p.rated_power_kw for p in self.panels)

    def get_total_capacity_kwp(self) -> float:
        """
        Returns total peak capacity (kWp) — same as kW under STC conditions.
        Alias kept for clarity in financial reports.
        """
        return self.get_total_capacity_kw()

    def get_array_area_m2(self) -> float:
        """
        Returns the total physical area occupied by all installed panels.
        """
        return len(self.panels) * PANEL_AREA_M2

    # -------------------------------------------------------------------------
    # Cost Calculations
    # -------------------------------------------------------------------------

    def get_panel_cost_usd(self) -> float:
        """Total purchase cost of all panels in USD."""
        return len(self.panels) * PANEL_COST_USD

    def get_installation_cost_usd(self) -> float:
        """Labour and mounting installation cost in USD."""
        return self.get_total_capacity_kw() * INSTALLATION_COST_USD_PER_KW

    def get_inverter_cost_usd(self) -> float:
        """Inverter cost based on total system capacity in USD."""
        return self.get_total_capacity_kw() * INVERTER_COST_USD_PER_KW

    def get_total_capex_usd(self) -> float:
        """
        Total capital expenditure (CAPEX) in USD.
        Includes panels + installation + inverters.
        """
        return (
            self.get_panel_cost_usd()
            + self.get_installation_cost_usd()
            + self.get_inverter_cost_usd()
        )

    def get_annual_opex_usd(self) -> float:
        """
        Annual operating expenditure (OPEX) in USD.
        Calculated as a fixed ratio of total CAPEX.
        """
        return self.get_total_capex_usd() * MAINTENANCE_COST_RATIO

    # -------------------------------------------------------------------------
    # Representation
    # -------------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Factory(name='{self.name}', "
            f"roof={self.roof_area_m2}m², "
            f"panels={len(self.panels)}, "
            f"capacity={self.get_total_capacity_kw():.1f}kW)"
        )

    def summary(self) -> dict:
        """
        Returns a dictionary snapshot of the factory's key parameters.
        Used by ReportGenerator for PDF output.
        """
        return {
            "name"              : self.name,
            "latitude"          : self.latitude,
            "longitude"         : self.longitude,
            "altitude_m"        : self.altitude_m,
            "roof_area_m2"      : self.roof_area_m2,
            "usable_roof_ratio" : self.usable_roof_ratio,
            "num_panels"        : len(self.panels),
            "total_capacity_kw" : round(self.get_total_capacity_kw(), 2),
            "total_capex_usd"   : round(self.get_total_capex_usd(), 2),
            "annual_opex_usd"   : round(self.get_annual_opex_usd(), 2),
            "optimal_tilt_deg"  : self.optimal_tilt_deg,
            "optimal_azimuth_deg": self.optimal_azimuth_deg,
        }