"""
Sensitivity Analysis Engine
---------------------------
This is the 'What-If?' brain of the project. It tests how our
investment holds up if the future isn't exactly like we planned.

How it works:
1. It creates three different worlds: Optimistic, Realistic, and Pessimistic.
2. It tweaks key variables: "What if the sun shines less?", "What if electricity
   prices skyrocket?", or "What if the installation costs more than expected?"
3. It compares all scenarios so we can see the risk and safety margins before
   spending a single Euro.
"""

from typing import List
from config import SCENARIOS
from engines.finance_engine import FinancialModel
from models.factory import Factory
from models.battery import Battery


class SensitivityAnalyzer:
    """
    Runs optimistic, realistic, and pessimistic financial scenarios
    by applying multipliers to irradiance, tariff, and cost inputs.
    Produces a comparative summary across all three scenarios.
    """

    def __init__(self, factory: Factory, battery: Battery = None):
        """
        Args:
            factory : Factory instance with installed panels.
            battery : Optional Battery instance.
        """
        self.factory  = factory
        self.battery  = battery
        self.results  = {}   # populated after run_all()

    # -------------------------------------------------------------------------
    # Single Scenario Runner
    # -------------------------------------------------------------------------

    def run_scenario(
        self,
        scenario_name: str,
        energy_forecast: List[dict],
    ) -> dict:
        """
        Runs a single named scenario by scaling the energy forecast
        and financial inputs with the scenario's multipliers.

        Args:
            scenario_name   : One of 'optimistic', 'realistic', 'pessimistic'.
            energy_forecast : Base forecast from SolarEngine (year 0 = install).

        Returns:
            Dict containing scenario name, multipliers, cashflow table,
            and summary metrics.

        Raises:
            ValueError: If scenario_name is not found in config.SCENARIOS.
        """
        if scenario_name not in SCENARIOS:
            raise ValueError(
                f"[SensitivityAnalyzer] Unknown scenario '{scenario_name}'. "
                f"Valid options: {list(SCENARIOS.keys())}"
            )

        multipliers = SCENARIOS[scenario_name]
        irr_mult    = multipliers["irradiance"]
        tar_mult    = multipliers["tariff"]
        cost_mult   = multipliers["cost"]

        # --- Scale energy forecast by irradiance multiplier ------------------
        scaled_forecast = []
        for entry in energy_forecast:
            scaled_forecast.append({
                "year"              : entry["year"],
                "annual_output_kwh" : round(entry["annual_output_kwh"] * irr_mult, 2),
                "degradation_factor": entry["degradation_factor"],
                "efficiency_pct"    : entry["efficiency_pct"],
            })

        # --- Build a patched FinancialModel with scaled tariffs --------------
        model = FinancialModel(self.factory, self.battery)
        model = self._patch_tariffs(model, tar_mult)
        model = self._patch_costs(model, cost_mult)

        # --- Run cash flow calculation ---------------------------------------
        cashflow_table  = model.calc_cashflow_table(scaled_forecast)
        summary_metrics = model.get_summary_metrics()

        result = {
            "scenario"       : scenario_name,
            "multipliers"    : multipliers,
            "cashflow_table" : cashflow_table,
            "metrics"        : summary_metrics,
        }

        self.results[scenario_name] = result
        print(
            f"[SensitivityAnalyzer] '{scenario_name}' — "
            f"NPV: {summary_metrics['npv_eur']:,.0f} EUR | "
            f"IRR: {summary_metrics['irr_pct']}% | "
            f"Payback: {summary_metrics['payback_years']} yrs"
        )

        return result

    # -------------------------------------------------------------------------
    # All Scenarios
    # -------------------------------------------------------------------------

    def run_all(self, energy_forecast: List[dict]) -> dict:
        """
        Runs all three scenarios (optimistic, realistic, pessimistic)
        and stores results internally.

        Args:
            energy_forecast: Base forecast from SolarEngine.

        Returns:
            Dict keyed by scenario name, each containing metrics and table.
        """
        print("[SensitivityAnalyzer] Running all scenarios ...\n")

        for name in ["optimistic", "realistic", "pessimistic"]:
            self.run_scenario(name, energy_forecast)

        print("\n[SensitivityAnalyzer] All scenarios complete.")
        return self.results

    # -------------------------------------------------------------------------
    # Comparison Table
    # -------------------------------------------------------------------------

    def get_comparison_table(self) -> List[dict]:
        """
        Returns a flat comparison table of key metrics across all scenarios.
        Useful for PDF report summary and bar chart generation.

        Returns:
            List of 3 dicts, one per scenario:
            [
                {
                    scenario, irradiance_mult, tariff_mult, cost_mult,
                    capex_eur, npv_eur, irr_pct, roi_pct,
                    payback_years, lifetime_output_kwh,
                    lifetime_revenue_eur, lifetime_carbon_eur
                },
                ...
            ]

        Raises:
            RuntimeError: If run_all() has not been called yet.
        """
        if not self.results:
            raise RuntimeError(
                "[SensitivityAnalyzer] No results found. Call run_all() first."
            )

        table = []
        for name, result in self.results.items():
            m = result["metrics"]
            p = result["multipliers"]
            table.append({
                "scenario"              : name,
                "irradiance_mult"       : p["irradiance"],
                "tariff_mult"           : p["tariff"],
                "cost_mult"             : p["cost"],
                "capex_eur"             : m["total_capex_eur"],
                "npv_eur"               : m["npv_eur"],
                "irr_pct"               : m["irr_pct"],
                "roi_pct"               : m["roi_pct"],
                "payback_years"         : m["payback_years"],
                "lifetime_output_kwh"   : m["lifetime_output_kwh"],
                "lifetime_revenue_eur"  : m["lifetime_revenue_eur"],
                "lifetime_carbon_eur"   : m["lifetime_carbon_income_eur"],
            })

        return table

    # -------------------------------------------------------------------------
    # Private Patching Helpers
    # -------------------------------------------------------------------------

    def _patch_tariffs(
        self,
        model: FinancialModel,
        multiplier: float,
    ) -> FinancialModel:
        """
        Monkey-patches the blended tariff calculation on a FinancialModel
        instance to apply the scenario tariff multiplier.

        Args:
            model      : FinancialModel instance to patch.
            multiplier : Tariff scaling factor.

        Returns:
            Patched FinancialModel instance.
        """
        original_tariff = model.calc_blended_tariff

        def scaled_tariff(year: int) -> float:
            return original_tariff(year) * multiplier

        model.calc_blended_tariff = scaled_tariff
        return model

    def _patch_costs(
        self,
        model: FinancialModel,
        multiplier: float,
    ) -> FinancialModel:
        """
        Monkey-patches the CAPEX and OPEX methods to apply cost multiplier.

        Args:
            model      : FinancialModel instance to patch.
            multiplier : Cost scaling factor.

        Returns:
            Patched FinancialModel instance.
        """
        original_capex = model.get_total_capex
        original_opex  = model.get_annual_opex

        def scaled_capex() -> float:
            return original_capex() * multiplier

        def scaled_opex(year: int) -> float:
            return original_opex(year) * multiplier

        model.get_total_capex  = scaled_capex
        model.get_annual_opex  = scaled_opex
        return model

    # -------------------------------------------------------------------------
    # Representation
    # -------------------------------------------------------------------------

    def __repr__(self) -> str:
        ran = list(self.results.keys()) or "none"
        return (
            f"SensitivityAnalyzer(factory='{self.factory.name}', "
            f"scenarios_run={ran})"
        )