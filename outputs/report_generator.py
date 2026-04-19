"""
Professional PDF Reporting Suite
--------------------------------
This module acts as the final 'Publisher' of the project. It uses the
FPDF2 engine to assemble technical data, financial tables, and
Matplotlib charts into a high-fidelity, industrial-grade PDF report.

The generator focuses on 'Executive Clarity'--ensuring that complex
engineering simulations are translated into actionable business insights.

Key Features:
- Custom Branding: Standardized headers, footers, and color palettes.
- KPI Visualization: High-impact metric boxes for immediate ROI awareness.
- Automated Layout: Dynamic multi-page assembly from cover to sensitivity.
"""

import os
from datetime import datetime
from typing import List
from fpdf import FPDF, XPos, YPos
from config import (
    PROJECT_NAME,
    VERSION,
    OUTPUT_DIR,
    REPORT_FILENAME,
    PROJECT_LIFETIME,
)


# =============================================================================
# Base PDF Class
# =============================================================================

class SunStrategistPDF(FPDF):
    """
    Custom FPDF subclass defining the header, footer, and
    shared styling helpers used across all report pages.
    """

    PRIMARY_COLOR   = (30,  144, 255)   # Dodger Blue
    SECONDARY_COLOR = (46,  204, 113)   # Emerald Green
    DARK_COLOR      = (30,   30,  45)   # Near Black
    LIGHT_BG        = (245, 247, 250)   # Light Grey Background
    TEXT_COLOR      = (40,   40,  55)   # Soft Dark Text
    MUTED_COLOR     = (120, 130, 145)   # Muted Grey

    def header(self) -> None:
        """Renders the top header bar on every page."""
        # Background bar
        self.set_fill_color(*self.DARK_COLOR)
        self.rect(0, 0, 210, 14, style="F")

        # Logo / title
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 3)
        self.cell(80, 8, f"[SUN] {PROJECT_NAME} v{VERSION}", align="L")

        # Right side -- date
        self.set_font("Helvetica", "", 8)
        self.set_text_color(180, 190, 200)
        self.set_xy(110, 3)
        self.cell(90, 8,
                  f"Generated: {datetime.now().strftime('%d %b %Y  %H:%M')}",
                  align="R")

        self.ln(10)

    def footer(self) -> None:
        """Renders the bottom footer bar on every page."""
        self.set_y(-12)
        self.set_fill_color(*self.DARK_COLOR)
        self.rect(0, self.get_y(), 210, 15, style="F")
        self.set_font("Helvetica", "", 7)
        self.set_text_color(150, 160, 175)
        self.cell(0, 8,
                  f"SunStrategist Industrial Solar Optimizer  |  Page {self.page_no()}  |  "
                  f"Confidential -- For internal use only",
                  align="C")

    # -------------------------------------------------------------------------
    # Styling Helpers
    # -------------------------------------------------------------------------

    def section_title(self, title: str) -> None:
        """Renders a styled section heading with a colored underline."""
        self.ln(4)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*self.PRIMARY_COLOR)
        self.cell(0, 8, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        # Underline rule
        self.set_draw_color(*self.PRIMARY_COLOR)
        self.set_line_width(0.5)
        self.line(self.get_x(), self.get_y(),
                  self.get_x() + 190, self.get_y())
        self.ln(3)
        self.set_text_color(*self.TEXT_COLOR)

    def subsection_title(self, title: str) -> None:
        """Renders a smaller subsection heading."""
        self.ln(2)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*self.SECONDARY_COLOR)
        self.cell(0, 6, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*self.TEXT_COLOR)

    def body_text(self, text: str) -> None:
        """Renders standard body paragraph text."""
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*self.TEXT_COLOR)
        self.multi_cell(0, 5, text)
        self.ln(2)

    def kv_row(self, label: str, value: str, highlight: bool = False) -> None:
        """
        Renders a key-value row with optional highlight background.

        Args:
            label    : Left-side label text.
            value    : Right-side value text.
            highlight: If True, renders with a light background fill.
        """
        if highlight:
            self.set_fill_color(*self.LIGHT_BG)
        else:
            self.set_fill_color(255, 255, 255)

        self.set_font("Helvetica", "", 9)
        self.set_text_color(*self.MUTED_COLOR)
        self.cell(85, 6, label, fill=True)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*self.TEXT_COLOR)
        self.cell(0, 6, value, fill=True,
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def metric_box(
        self,
        label: str,
        value: str,
        x: float,
        y: float,
        w: float = 42,
        h: float = 20,
        color: tuple = None,
    ) -> None:
        """
        Renders a highlighted metric box (KPI card style).

        Args:
            label : Metric label (shown below value).
            value : Main metric value (large font).
            x, y  : Position on page.
            w, h  : Box dimensions.
            color : Optional RGB fill color tuple.
        """
        fill = color or self.PRIMARY_COLOR
        self.set_fill_color(*fill)
        self.set_draw_color(*fill)
        self.rect(x, y, w, h, style="F")
        # Value (large)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(255, 255, 255)
        self.set_xy(x + 1, y + 2)
        self.cell(w - 2, 9, value, align="C")

        # Label (small)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(220, 230, 240)
        self.set_xy(x + 1, y + 11)
        self.cell(w - 2, 6, label, align="C")

        self.set_text_color(*self.TEXT_COLOR)


# =============================================================================
# Report Generator
# =============================================================================

class ReportGenerator:
    """
    Assembles all analysis results into a multi-page PDF report
    using the SunStrategistPDF engine.
    """

    def __init__(
        self,
        factory_summary   : dict,
        weather_data      : dict,
        energy_forecast   : List[dict],
        monthly_data      : List[dict],
        cashflow_table    : List[dict],
        metrics           : dict,
        comparison_table  : List[dict],
        chart_paths       : dict,
        battery_summary   : dict = None,
    ):
        """
        Args:
            factory_summary  : Factory.summary()
            weather_data     : WeatherAPI.fetch() result
            energy_forecast  : SolarEngine.calc_lifetime_energy_forecast()
            monthly_data     : SolarEngine.calc_monthly_output_kwh()
            cashflow_table   : FinancialModel.calc_cashflow_table()
            metrics          : FinancialModel.get_summary_metrics()
            comparison_table : SensitivityAnalyzer.get_comparison_table()
            chart_paths      : generate_all_charts() result dict
            battery_summary  : Battery.summary() (optional)
        """
        self.factory   = factory_summary
        self.weather   = weather_data
        self.forecast  = energy_forecast
        self.monthly   = monthly_data
        self.cashflow  = cashflow_table
        self.metrics   = metrics
        self.scenarios = comparison_table
        self.charts    = chart_paths
        self.battery   = battery_summary
        self.pdf       = SunStrategistPDF(orientation="P", unit="mm", format="A4")
        self.pdf.set_margins(10, 18, 10)
        self.pdf.set_auto_page_break(auto=True, margin=15)

    # -------------------------------------------------------------------------
    # Page 1 -- Cover & Executive Summary
    # -------------------------------------------------------------------------

    def _page_cover(self) -> None:
        """Renders the cover / executive summary page."""
        self.pdf.add_page()

        # Hero banner
        self.pdf.set_fill_color(20, 25, 40)
        self.pdf.rect(0, 14, 210, 55, style="F")

        self.pdf.set_font("Helvetica", "B", 24)
        self.pdf.set_text_color(255, 255, 255)
        self.pdf.set_xy(10, 22)
        self.pdf.cell(190, 12, "SunStrategist", align="C")

        self.pdf.set_font("Helvetica", "", 11)
        self.pdf.set_text_color(150, 200, 255)
        self.pdf.set_xy(10, 36)
        self.pdf.cell(190, 8, "Industrial Solar Optimizer & Financial Forecaster", align="C")

        self.pdf.set_font("Helvetica", "B", 10)
        self.pdf.set_text_color(100, 160, 220)
        self.pdf.set_xy(10, 48)
        self.pdf.cell(190, 8,
                      f"{self.factory['name']}  |  "
                      f"Lat {self.factory['latitude']}°  "
                      f"Lon {self.factory['longitude']}°",
                      align="C")

        self.pdf.ln(60)

        # KPI metric boxes
        self.pdf.section_title("Executive Summary")
        m = self.metrics

        kpi_data = [
            ("Total CAPEX",        f"EUR{m['total_capex_eur']:,.0f}",
             SunStrategistPDF.DARK_COLOR),
            ("20-Yr NPV",          f"EUR{m['npv_eur']:,.0f}",
             SunStrategistPDF.PRIMARY_COLOR),
            ("IRR",                f"{m['irr_pct']}%",
             SunStrategistPDF.SECONDARY_COLOR),
            ("ROI",                f"{m['roi_pct']}%",
             (155, 89, 182)),
        ]

        x_start = 12
        y_pos   = self.pdf.get_y() + 2
        for label, value, color in kpi_data:
            self.pdf.metric_box(label, value, x_start, y_pos, color=color)
            x_start += 46

        self.pdf.ln(28)

        kpi_data2 = [
            ("Payback Period",     f"{m['payback_years']:.0f} yrs",
             (231, 76, 60)),
            ("Lifetime Output",    f"{m['lifetime_output_kwh']:,.0f} kWh",
             (52, 152, 219)),
            ("Carbon Income",      f"EUR{m['lifetime_carbon_income_eur']:,.0f}",
             (39, 174, 96)),
            ("Lifetime Revenue",   f"EUR{m['lifetime_revenue_eur']:,.0f}",
             (243, 156, 18)),
        ]

        x_start = 12
        y_pos   = self.pdf.get_y() + 2
        for label, value, color in kpi_data2:
            self.pdf.metric_box(label, value, x_start, y_pos, color=color)
            x_start += 46

        self.pdf.ln(28)

        # Factory & Location Summary
        self.pdf.section_title("Factory & System Overview")
        rows = [
            ("Factory Name",         self.factory["name"]),
            ("Location (Lat / Lon)", f"{self.factory['latitude']}° / {self.factory['longitude']}°"),
            ("Roof Area",            f"{self.factory['roof_area_m2']:,} m2"),
            ("Panels Installed",     f"{self.factory['num_panels']:,} panels"),
            ("Total Capacity",       f"{self.factory['total_capacity_kw']:,.1f} kWp"),
            ("Optimal Tilt",         f"{self.factory['optimal_tilt_deg']}°"),
            ("Optimal Azimuth",      f"{self.factory['optimal_azimuth_deg']}°"),
            ("Annual Irradiance",    f"{self.weather['annual_irradiance_kwh_m2']} kWh/m2"),
            ("Daily Peak Sun Hours", f"{self.weather['peak_sun_hours_daily']} h/day"),
            ("Total CAPEX",          f"EUR{self.factory['total_capex_usd']:,.0f}"),
            ("Annual OPEX",          f"EUR{self.factory['annual_opex_usd']:,.0f}"),
        ]
        for i, (k, v) in enumerate(rows):
            self.pdf.kv_row(k, v, highlight=(i % 2 == 0))

    # -------------------------------------------------------------------------
    # Page 2 -- Energy Production Analysis
    # -------------------------------------------------------------------------

    def _page_energy(self) -> None:
        """Renders the energy production analysis page."""
        self.pdf.add_page()
        self.pdf.section_title("Energy Production Analysis")

        # 20-year forecast chart
        if "energy_forecast" in self.charts:
            self.pdf.image(self.charts["energy_forecast"],
                           x=10, w=190)
            self.pdf.ln(4)

        # Monthly breakdown chart
        self.pdf.subsection_title("Monthly Production & Peak Sun Hours")
        if "monthly_output" in self.charts:
            self.pdf.image(self.charts["monthly_output"],
                           x=10, w=190)
            self.pdf.ln(4)

        # Seasonal note
        self.pdf.body_text(
            "Berlin's solar profile shows strong seasonal variation. Peak production "
            "occurs in June-July (~4.5 PSH/day) while December-January represents "
            "the minimum (~0.8 PSH/day). The system is sized to maximise annual "
            "yield rather than peak-month output."
        )

    # -------------------------------------------------------------------------
    # Page 3 -- Financial Analysis
    # -------------------------------------------------------------------------

    def _page_financial(self) -> None:
        """Renders the financial analysis page."""
        self.pdf.add_page()
        self.pdf.section_title("20-Year Financial Analysis")

        # Cash flow chart
        if "cashflow" in self.charts:
            self.pdf.image(self.charts["cashflow"], x=10, w=190)
            self.pdf.ln(4)

        # Revenue breakdown chart
        self.pdf.subsection_title("Annual Revenue Stream Breakdown")
        if "revenue_breakdown" in self.charts:
            self.pdf.image(self.charts["revenue_breakdown"], x=10, w=190)
            self.pdf.ln(4)

        # Cash flow table -- first 10 years
        self.pdf.subsection_title("Cash Flow Table (Years 1 - 10)")
        self._render_cashflow_table(self.cashflow[:11])

    # -------------------------------------------------------------------------
    # Page 4 -- Cash Flow Table (Years 11-20) & Sensitivity
    # -------------------------------------------------------------------------

    def _page_sensitivity(self) -> None:
        """Renders the sensitivity analysis and remaining cash flow table."""
        self.pdf.add_page()

        # Cash flow table -- years 11-20
        self.pdf.section_title("Cash Flow Table (Years 11 - 20)")
        self._render_cashflow_table(self.cashflow[11:])

        self.pdf.ln(4)

        # Sensitivity chart
        self.pdf.section_title("Sensitivity Analysis")
        if "sensitivity" in self.charts:
            self.pdf.image(self.charts["sensitivity"], x=10, w=190)
            self.pdf.ln(4)

        # Scenario comparison table
        self.pdf.subsection_title("Scenario Metrics Comparison")
        self._render_scenario_table()

    # -------------------------------------------------------------------------
    # Page 5 -- Battery Analysis (optional)
    # -------------------------------------------------------------------------

    def _page_battery(self) -> None:
        """Renders the BESS analysis page if battery data is available."""
        if not self.battery:
            return

        self.pdf.add_page()
        self.pdf.section_title("Battery Energy Storage System (BESS) Analysis")

        # Battery specs
        self.pdf.subsection_title("Battery Specifications")
        rows = [
            ("Nominal Capacity",      f"{self.battery['capacity_kwh']} kWh"),
            ("Usable Capacity",       f"{self.battery['usable_capacity_kwh']} kWh"),
            ("Round-Trip Efficiency", f"{self.battery['efficiency_pct']}%"),
            ("Max SoC",               f"{self.battery['max_soc_pct']}%"),
            ("Min SoC",               f"{self.battery['min_soc_pct']}%"),
            ("Annual Degradation",    f"{self.battery['degradation_rate_pct']}%"),
            ("Total BESS Cost",       f"EUR{self.battery['total_cost_usd']:,.0f}"),
        ]
        for i, (k, v) in enumerate(rows):
            self.pdf.kv_row(k, v, highlight=(i % 2 == 0))

        self.pdf.ln(4)

        # Battery degradation chart
        if "battery_degradation" in self.charts:
            self.pdf.image(self.charts["battery_degradation"], x=10, w=190)

    # -------------------------------------------------------------------------
    # Table Renderers
    # -------------------------------------------------------------------------

    def _render_cashflow_table(self, rows: List[dict]) -> None:
        """
        Renders a compact cash flow table into the PDF.

        Args:
            rows: Subset of cashflow_table list.
        """
        headers = ["Yr", "Output(kWh)", "Energy Rev(EUR)",
                   "Carbon(EUR)", "BESS(EUR)", "OPEX(EUR)",
                   "Net CF(EUR)", "Cumul.(EUR)"]
        widths  = [10, 28, 28, 20, 18, 20, 26, 26]

        # Header row
        self.pdf.set_fill_color(*SunStrategistPDF.DARK_COLOR)
        self.pdf.set_text_color(255, 255, 255)
        self.pdf.set_font("Helvetica", "B", 7)
        for h, w in zip(headers, widths):
            self.pdf.cell(w, 6, h, border=0, fill=True, align="C")
        self.pdf.ln()

        # Data rows
        self.pdf.set_font("Helvetica", "", 7)
        for i, row in enumerate(rows):
            if row["year"] == 0:
                continue
            fill = i % 2 == 0
            self.pdf.set_fill_color(*SunStrategistPDF.LIGHT_BG) if fill \
                else self.pdf.set_fill_color(255, 255, 255)
            self.pdf.set_text_color(*SunStrategistPDF.TEXT_COLOR)

            net = row["net_cashflow_eur"]
            cum = row["cumulative_cashflow_eur"]

            self.pdf.cell(widths[0], 5, str(row["year"]),              fill=fill, align="C")
            self.pdf.cell(widths[1], 5, f"{row['annual_output_kwh']:,.0f}", fill=fill, align="R")
            self.pdf.cell(widths[2], 5, f"EUR{row['energy_revenue_eur']:,.0f}", fill=fill, align="R")
            self.pdf.cell(widths[3], 5, f"EUR{row['carbon_income_eur']:,.0f}",  fill=fill, align="R")
            self.pdf.cell(widths[4], 5, f"EUR{row['battery_savings_eur']:,.0f}", fill=fill, align="R")
            self.pdf.cell(widths[5], 5, f"EUR{row['opex_eur']:,.0f}",           fill=fill, align="R")

            # Color net CF red/green
            self.pdf.set_text_color(
                *((39, 174, 96) if net >= 0 else (231, 76, 60))
            )
            self.pdf.cell(widths[6], 5, f"EUR{net:,.0f}", fill=fill, align="R")

            self.pdf.set_text_color(
                *((39, 174, 96) if cum >= 0 else (231, 76, 60))
            )
            self.pdf.cell(widths[7], 5, f"EUR{cum:,.0f}", fill=fill, align="R",
                          new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.pdf.ln(2)

    def _render_scenario_table(self) -> None:
        """Renders a comparison table for sensitivity analysis scenarios."""
        headers = ["Scenario", "NPV (EUR)", "IRR (%)", "ROI (%)",
                   "Payback (yrs)", "Lifetime Rev (EUR)"]
        widths  = [32, 36, 24, 24, 30, 44]

        self.pdf.set_fill_color(*SunStrategistPDF.DARK_COLOR)
        self.pdf.set_text_color(255, 255, 255)
        self.pdf.set_font("Helvetica", "B", 8)
        for h, w in zip(headers, widths):
            self.pdf.cell(w, 6, h, border=0, fill=True, align="C")
        self.pdf.ln()

        color_map = {
            "optimistic" : (39,  174, 96),
            "realistic"  : (52,  152, 219),
            "pessimistic": (231, 76,  60),
        }

        self.pdf.set_font("Helvetica", "", 8)
        for row in self.scenarios:
            sc = row["scenario"]
            self.pdf.set_text_color(*color_map.get(sc, (40, 40, 55)))
            self.pdf.cell(widths[0], 6, sc.capitalize(),         align="L")
            self.pdf.set_text_color(*SunStrategistPDF.TEXT_COLOR)
            self.pdf.cell(widths[1], 6, f"EUR{row['npv_eur']:,.0f}",          align="R")
            self.pdf.cell(widths[2], 6, f"{row['irr_pct']}%",               align="C")
            self.pdf.cell(widths[3], 6, f"{row['roi_pct']}%",               align="C")
            self.pdf.cell(widths[4], 6, f"{row['payback_years']:.0f}",      align="C")
            self.pdf.cell(widths[5], 6, f"EUR{row['lifetime_revenue_eur']:,.0f}",
                          align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.pdf.ln(2)

    # -------------------------------------------------------------------------
    # Master Build
    # -------------------------------------------------------------------------

    def build(self) -> str:
        """
        Assembles all pages and saves the final PDF report.

        Returns:
            Full path to the generated PDF file.
        """
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        print("[ReportGenerator] Building PDF report ...")

        self._page_cover()
        self._page_energy()
        self._page_financial()
        self._page_sensitivity()
        self._page_battery()

        output_path = os.path.join(OUTPUT_DIR, REPORT_FILENAME)
        self.pdf.output(output_path)

        print(f"[ReportGenerator] Report saved → {output_path}")
        return output_path