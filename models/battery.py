"""
Battery Energy Storage System (BESS) Model
------------------------------------------
This is the factory's 'power bank'. It stores extra solar energy
when the sun is shining and saves it for when it's dark or when
electricity is most expensive. It also tracks how the battery
gets 'tired' (loses capacity) over the years.
"""
from config import (
    BATTERY_CAPACITY_KWH,
    BATTERY_COST_USD_PER_KWH,
    BATTERY_EFFICIENCY,
    BATTERY_MAX_SOC,
    BATTERY_MIN_SOC,
    BATTERY_DEGRADATION_RATE,
    PROJECT_LIFETIME,
)


class Battery:
    """
    Represents a Battery Energy Storage System (BESS) attached to the factory.
    Simulates charge/discharge cycles, state of charge (SoC), and
    capacity degradation over the project lifetime.
    """

    def __init__(
        self,
        capacity_kwh: float = BATTERY_CAPACITY_KWH,
        cost_usd_per_kwh: float = BATTERY_COST_USD_PER_KWH,
        efficiency: float = BATTERY_EFFICIENCY,
        max_soc: float = BATTERY_MAX_SOC,
        min_soc: float = BATTERY_MIN_SOC,
        degradation_rate: float = BATTERY_DEGRADATION_RATE,
    ):
        """
        Args:
            capacity_kwh     : Nominal storage capacity in kWh.
            cost_usd_per_kwh : Capital cost per kWh of storage (USD).
            efficiency       : Round-trip charge/discharge efficiency (0-1).
            max_soc          : Maximum allowed state of charge (e.g. 0.95).
            min_soc          : Minimum allowed state of charge (e.g. 0.11).
            degradation_rate : Annual capacity loss as a decimal (e.g. 0.02).
        """
        self.capacity_kwh     = capacity_kwh
        self.cost_usd_per_kwh = cost_usd_per_kwh
        self.efficiency       = efficiency
        self.max_soc          = max_soc
        self.min_soc          = min_soc
        self.degradation_rate = degradation_rate

        # Current state of charge (starts at 50%)
        self._current_soc = 0.50

    # -------------------------------------------------------------------------
    # Capacity & Degradation
    # -------------------------------------------------------------------------

    def get_capacity_at_year(self, year: int) -> float:
        """
        Returns the effective storage capacity (kWh) after annual degradation.

        Formula:
            capacity(year) = nominal_capacity * (1 - degradation_rate) ^ year

        Args:
            year: Project year (0 = installation year).

        Returns:
            Degraded capacity in kWh.
        """
        if year < 0:
            raise ValueError(f"Year must be >= 0, got {year}")
        return self.capacity_kwh * ((1 - self.degradation_rate) ** year)

    def get_usable_capacity_at_year(self, year: int) -> float:
        """
        Returns the usable capacity at a given year, accounting for
        SoC window (max_soc - min_soc) and degradation.

        Args:
            year: Project year.

        Returns:
            Usable energy in kWh.
        """
        return self.get_capacity_at_year(year) * (self.max_soc - self.min_soc)

    # -------------------------------------------------------------------------
    # Charge / Discharge Simulation
    # -------------------------------------------------------------------------

    def charge(self, energy_kwh: float, year: int = 0) -> float:
        """
        Charges the battery with available surplus solar energy.
        Applies round-trip efficiency loss on the way in.

        Args:
            energy_kwh : Surplus energy available for charging (kWh).
            year       : Current project year (for degraded capacity).

        Returns:
            Actual energy stored in the battery (kWh).
        """
        capacity = self.get_capacity_at_year(year)
        max_storable = (self.max_soc - self._current_soc) * capacity

        # Energy actually entering the battery after efficiency loss
        energy_in = min(energy_kwh * self.efficiency, max_storable)
        self._current_soc += energy_in / capacity

        return energy_in

    def discharge(self, energy_needed_kwh: float, year: int = 0) -> float:
        """
        Discharges the battery to meet factory energy demand.

        Args:
            energy_needed_kwh : Energy required from the battery (kWh).
            year              : Current project year (for degraded capacity).

        Returns:
            Actual energy delivered to the factory (kWh).
        """
        capacity = self.get_capacity_at_year(year)
        max_dischargeable = (self._current_soc - self.min_soc) * capacity

        energy_out = min(energy_needed_kwh, max_dischargeable)
        self._current_soc -= energy_out / capacity

        return energy_out

    def reset_soc(self, soc: float = 0.50) -> None:
        """
        Resets state of charge to a given value.
        Called at the start of each simulated day or year.

        Args:
            soc: Target state of charge (0.0 - 1.0).
        """
        if not (0.0 <= soc <= 1.0):
            raise ValueError(f"SoC must be between 0 and 1, got {soc}")
        self._current_soc = soc

    # -------------------------------------------------------------------------
    # Financial
    # -------------------------------------------------------------------------

    def get_total_cost_usd(self) -> float:
        """
        Returns total capital cost of the battery system in USD.
        """
        return self.capacity_kwh * self.cost_usd_per_kwh

    def get_lifetime_degradation_summary(self) -> list:
        """
        Returns a year-by-year list of usable capacity over the project lifetime.
        Useful for charting and financial modelling.

        Returns:
            List of dicts: [{"year": int, "capacity_kwh": float, "usable_kwh": float}]
        """
        summary = []
        for year in range(PROJECT_LIFETIME + 1):
            summary.append({
                "year"        : year,
                "capacity_kwh": round(self.get_capacity_at_year(year), 2),
                "usable_kwh"  : round(self.get_usable_capacity_at_year(year), 2),
            })
        return summary

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def current_soc(self) -> float:
        """Read-only access to current state of charge."""
        return self._current_soc

    @property
    def current_soc_pct(self) -> float:
        """Current state of charge as a percentage."""
        return self._current_soc * 100

    # -------------------------------------------------------------------------
    # Representation
    # -------------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Battery(capacity={self.capacity_kwh}kWh, "
            f"efficiency={self.efficiency:.0%}, "
            f"SoC={self.current_soc_pct:.1f}%)"
        )

    def summary(self) -> dict:
        """
        Returns a dictionary snapshot of battery specifications.
        Used by ReportGenerator for PDF output.
        """
        return {
            "capacity_kwh"        : self.capacity_kwh,
            "cost_usd_per_kwh"    : self.cost_usd_per_kwh,
            "total_cost_usd"      : self.get_total_cost_usd(),
            "efficiency_pct"      : round(self.efficiency * 100, 1),
            "max_soc_pct"         : round(self.max_soc * 100, 1),
            "min_soc_pct"         : round(self.min_soc * 100, 1),
            "usable_capacity_kwh" : round(self.get_usable_capacity_at_year(0), 2),
            "degradation_rate_pct": round(self.degradation_rate * 100, 1),
        }