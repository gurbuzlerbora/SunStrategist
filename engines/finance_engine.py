"""
Financial Analysis & ROI Engine
-------------------------------
This is the 'money brain' of the project. It takes all the solar energy
we calculated and turns it into actual Euros.

How it works:
1. It looks at how much money we save on electricity bills every month.
2. It adds 'eco-bonuses' (carbon credits) because we're being green.
3. It subtracts the costs to build (CAPEX) and fix (OPEX) the system.
4. It even knows that 100 Euros today is worth more than 100 Euros in 10 years
   by using some smart math (NPV and Inflation).

Finally, it tells us the most important thing: Is this a good deal?
And exactly how many years until we get our investment back?

Key Financial Concepts:
- CAPEX (Capital Expenditure): The buy-in price. The big bill we pay on Day 1 to buy all the panels, batteries, and pay the workers for installation.
- OPEX (Operating Expenditure): The running cost. The smaller, annual money spent on cleaning, maintenance, and keeping the system healthy over its 20-year life.

"""

from typing import List
from config import (
    TARIFF_DAY_EUR_PER_KWH,
    TARIFF_NIGHT_EUR_PER_KWH,
    TARIFF_PEAK_EUR_PER_KWH,
    TARIFF_ANNUAL_INCREASE_RATE,
    PEAK_HOURS,
    DAY_HOURS,
    CARBON_EMISSION_FACTOR_KG_PER_KWH,
    CARBON_CREDIT_EUR_PER_TON,
    DISCOUNT_RATE,
    INFLATION_RATE,
    PROJECT_LIFETIME,
    MAINTENANCE_COST_RATIO,
)
from models.factory import Factory
from models.battery import Battery


class FinancialModel:
    """
    Computes full financial performance of a solar installation including:
    - Annual revenue from energy savings
    - Carbon credit income
    - 20-year cash flow table
    - NPV, IRR, and simple payback period
    - ROI under multiple scenarios
    """

    def __init__(self, factory: Factory, battery: Battery = None):
        """
        Args:
            factory : Factory instance with installed panels.
            battery : Optional Battery instance for BESS modelling.
        """
        self.factory = factory
        self.battery = battery

        # Populated after calc_cashflow_table()
        self._cashflow_table: List[dict] = []

    # -------------------------------------------------------------------------
    # Tariff Helpers
    # -------------------------------------------------------------------------

    def get_effective_tariff(self, year: int) -> dict:
        """
        Returns day/night/peak tariffs for a given project year,
        adjusted for annual tariff increase rate.

        Args:
            year: Project year (0 = installation year).

        Returns:
            Dict with keys: day, night, peak (EUR/kWh).
        """
        multiplier = (1 + TARIFF_ANNUAL_INCREASE_RATE) ** year
        return {
            "day"  : round(TARIFF_DAY_EUR_PER_KWH   * multiplier, 4),
            "night": round(TARIFF_NIGHT_EUR_PER_KWH  * multiplier, 4),
            "peak" : round(TARIFF_PEAK_EUR_PER_KWH   * multiplier, 4),
        }

    def calc_blended_tariff(self, year: int) -> float:
        """
        Calculates a weighted blended tariff based on operating hours.

        Weights:
            Peak  hours : 4h  / 24h
            Day   hours : 12h / 24h  (excluding peak)
            Night hours : 8h  / 24h

        Args:
            year: Project year.

        Returns:
            Blended tariff in EUR/kWh.
        """
        tariff       = self.get_effective_tariff(year)
        peak_weight  = len(PEAK_HOURS) / 24
        day_weight   = (len(DAY_HOURS) - len(PEAK_HOURS)) / 24
        night_weight = 1 - peak_weight - day_weight

        blended = (
            tariff["peak"]  * peak_weight  +
            tariff["day"]   * day_weight   +
            tariff["night"] * night_weight
        )
        return round(blended, 4)

    # -------------------------------------------------------------------------
    # Annual Revenue
    # -------------------------------------------------------------------------

    def calc_annual_energy_revenue(
        self,
        annual_output_kwh: float,
        year: int,
    ) -> float:
        """
        Calculates annual electricity bill savings from solar generation.
        Uses blended tariff for the given year.

        Args:
            annual_output_kwh : Total energy produced by panels that year.
            year              : Project year (for tariff escalation).

        Returns:
            Annual revenue / savings in EUR.
        """
        blended = self.calc_blended_tariff(year)
        return round(annual_output_kwh * blended, 2)

    def calc_carbon_savings(self, annual_output_kwh: float) -> dict:
        """
        Calculates CO2 emissions avoided and carbon credit income.

        Formula:
            co2_kg   = output_kwh * emission_factor
            co2_tons = co2_kg / 1000
            income   = co2_tons * credit_price

        Args:
            annual_output_kwh: Energy produced in kWh.

        Returns:
            Dict with co2_avoided_kg, co2_avoided_tons, carbon_income_eur.
        """
        co2_kg   = annual_output_kwh * CARBON_EMISSION_FACTOR_KG_PER_KWH
        co2_tons = co2_kg / 1000
        income   = co2_tons * CARBON_CREDIT_EUR_PER_TON

        return {
            "co2_avoided_kg"   : round(co2_kg, 2),
            "co2_avoided_tons" : round(co2_tons, 2),
            "carbon_income_eur": round(income, 2),
        }

    def calc_battery_savings(
        self,
        annual_output_kwh: float,
        year: int,
    ) -> float:
        """
        Estimates additional savings from battery peak-shifting.
        Battery stores cheap off-peak solar and discharges during
        expensive peak hours, capturing the tariff spread.

        Args:
            annual_output_kwh : Annual solar output in kWh.
            year              : Project year.

        Returns:
            Additional annual savings from BESS in EUR.
        """
        if self.battery is None:
            return 0.0

        tariff          = self.get_effective_tariff(year)
        tariff_spread   = tariff["peak"] - tariff["day"]
        usable_capacity = self.battery.get_usable_capacity_at_year(year)

        # Assume battery cycles once per day on average
        annual_cycles      = 365
        annual_shifted_kwh = (
            usable_capacity
            * annual_cycles
            * self.battery.efficiency
        )

        # Cap shifted energy at 30% of total solar output (realistic limit)
        annual_shifted_kwh = min(annual_shifted_kwh, annual_output_kwh * 0.30)
        savings            = annual_shifted_kwh * tariff_spread

        return round(savings, 2)

    # -------------------------------------------------------------------------
    # CAPEX & OPEX
    # -------------------------------------------------------------------------

    def get_total_capex(self) -> float:
        """
        Returns total initial capital expenditure including
        solar system and optional battery storage (EUR).
        """
        solar_capex   = self.factory.get_total_capex_usd()
        battery_capex = self.battery.get_total_cost_usd() if self.battery else 0.0
        return round(solar_capex + battery_capex, 2)

    def get_annual_opex(self, year: int) -> float:
        """
        Returns total annual operating expenditure for a given year,
        adjusted for inflation.

        Args:
            year: Project year.

        Returns:
            Annual OPEX in EUR.
        """
        base_opex  = self.factory.get_annual_opex_usd()
        inflation  = (1 + INFLATION_RATE) ** year
        return round(base_opex * inflation, 2)

    # -------------------------------------------------------------------------
    # 20-Year Cash Flow Table
    # -------------------------------------------------------------------------

    def calc_cashflow_table(
        self,
        energy_forecast: List[dict],
    ) -> List[dict]:
        """
        Builds a full 20-year cash flow table combining all revenue
        and cost streams.

        Args:
            energy_forecast: Output of SolarEngine.calc_lifetime_energy_forecast()
                             List of dicts with 'year' and 'annual_output_kwh'.

        Returns:
            List of annual cash flow dicts:
            [
                {
                    year, annual_output_kwh,
                    energy_revenue_eur, carbon_income_eur, battery_savings_eur,
                    total_revenue_eur, opex_eur,
                    net_cashflow_eur, cumulative_cashflow_eur,
                    discounted_cashflow_eur, npv_cumulative_eur,
                },
                ...
            ]
        """
        total_capex       = self.get_total_capex()
        cumulative_cf     = -total_capex   # Year 0 starts with CAPEX outflow
        cumulative_npv    = -total_capex
        table             = []

        for entry in energy_forecast:
            year       = entry["year"]
            output_kwh = entry["annual_output_kwh"]

            # Skip year 0 as production year — CAPEX only
            if year == 0:
                table.append({
                    "year"                  : 0,
                    "annual_output_kwh"     : 0,
                    "energy_revenue_eur"    : 0,
                    "carbon_income_eur"     : 0,
                    "battery_savings_eur"   : 0,
                    "total_revenue_eur"     : 0,
                    "opex_eur"              : 0,
                    "net_cashflow_eur"      : round(-total_capex, 2),
                    "cumulative_cashflow_eur": round(cumulative_cf, 2),
                    "discounted_cashflow_eur": round(-total_capex, 2),
                    "npv_cumulative_eur"    : round(cumulative_npv, 2),
                })
                continue

            # Revenue streams
            energy_rev     = self.calc_annual_energy_revenue(output_kwh, year)
            carbon         = self.calc_carbon_savings(output_kwh)
            battery_sav    = self.calc_battery_savings(output_kwh, year)
            total_revenue  = energy_rev + carbon["carbon_income_eur"] + battery_sav

            # Costs
            opex           = self.get_annual_opex(year)
            net_cf         = total_revenue - opex

            # Cumulative
            cumulative_cf += net_cf

            # Discounted cash flow (DCF) for NPV
            discount_factor    = (1 + DISCOUNT_RATE) ** year
            discounted_cf      = net_cf / discount_factor
            cumulative_npv    += discounted_cf

            table.append({
                "year"                   : year,
                "annual_output_kwh"      : output_kwh,
                "energy_revenue_eur"     : energy_rev,
                "carbon_income_eur"      : carbon["carbon_income_eur"],
                "battery_savings_eur"    : battery_sav,
                "total_revenue_eur"      : round(total_revenue, 2),
                "opex_eur"               : opex,
                "net_cashflow_eur"       : round(net_cf, 2),
                "cumulative_cashflow_eur": round(cumulative_cf, 2),
                "discounted_cashflow_eur": round(discounted_cf, 2),
                "npv_cumulative_eur"     : round(cumulative_npv, 2),
            })

        self._cashflow_table = table
        return table

    # -------------------------------------------------------------------------
    # Key Financial Metrics
    # -------------------------------------------------------------------------

    def calc_payback_period(self) -> float:
        """
        Finds the simple payback period in years — the first year where
        cumulative cash flow turns positive.

        Returns:
            Payback period in years (float). Returns -1 if never paid back.
        """
        for row in self._cashflow_table:
            if row["year"] > 0 and row["cumulative_cashflow_eur"] >= 0:
                return float(row["year"])
        return -1.0

    def calc_npv(self) -> float:
        """
        Returns the final Net Present Value (NPV) at end of project lifetime.

        Returns:
            NPV in EUR.
        """
        if not self._cashflow_table:
            raise RuntimeError(
                "[FinancialModel] Run calc_cashflow_table() first."
            )
        return self._cashflow_table[-1]["npv_cumulative_eur"]

    def calc_roi(self) -> float:
        """
        Calculates simple Return on Investment (ROI) over project lifetime.

        Formula:
            ROI = (total_net_revenue - capex) / capex * 100

        Returns:
            ROI as a percentage (float).
        """
        capex         = self.get_total_capex()
        total_revenue = sum(
            r["net_cashflow_eur"]
            for r in self._cashflow_table
            if r["year"] > 0
        )
        return round(((total_revenue - capex) / capex) * 100, 2)

    def calc_irr(self) -> float:
        """
        Estimates Internal Rate of Return (IRR) using Newton-Raphson method.
        IRR is the discount rate at which NPV = 0.

        Returns:
            IRR as a decimal (e.g. 0.12 = 12%). Returns -1 if no solution found.
        """
        cashflows = [-self.get_total_capex()] + [
            r["net_cashflow_eur"]
            for r in self._cashflow_table
            if r["year"] > 0
        ]

        rate = 0.10  # Initial guess
        for _ in range(1000):
            npv = sum(
                cf / (1 + rate) ** t
                for t, cf in enumerate(cashflows)
            )
            # Derivative of NPV with respect to rate
            d_npv = sum(
                -t * cf / (1 + rate) ** (t + 1)
                for t, cf in enumerate(cashflows)
            )
            if d_npv == 0:
                break
            new_rate = rate - npv / d_npv
            if abs(new_rate - rate) < 1e-7:
                return round(new_rate, 4)
            rate = new_rate

        return -1.0

    def get_summary_metrics(self) -> dict:
        """
        Returns a single dictionary of all key financial metrics.
        Used by ReportGenerator for the executive summary section.

        Returns:
            Dict with capex, npv, irr, roi, payback, lifetime totals.
        """
        total_output  = sum(
            r["annual_output_kwh"] for r in self._cashflow_table
        )
        total_carbon  = sum(
            r["carbon_income_eur"] for r in self._cashflow_table
        )
        total_revenue = sum(
            r["total_revenue_eur"] for r in self._cashflow_table
        )

        return {
            "total_capex_eur"          : round(self.get_total_capex(), 2),
            "npv_eur"                  : self.calc_npv(),
            "irr_pct"                  : round(self.calc_irr() * 100, 2),
            "roi_pct"                  : self.calc_roi(),
            "payback_years"            : self.calc_payback_period(),
            "lifetime_output_kwh"      : round(total_output, 0),
            "lifetime_carbon_income_eur": round(total_carbon, 2),
            "lifetime_revenue_eur"     : round(total_revenue, 2),
        }