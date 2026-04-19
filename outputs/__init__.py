"""
Outputs Package Entry Point
---------------------------
This file acts as the 'Reception Desk' for our presentation layer.
It collects the complex chart generation and PDF reporting tools
into a single, easy-to-access spot. This keeps our main script
clean and professional by allowing simple imports.
"""
from outputs.charts import generate_all_charts
from outputs.report_generator import ReportGenerator