"""
Unit and Integration Test Suite for Enterprise Excel & Computational Intelligence Agent (`excel_specialist`).
Covers:
1. Spreadsheet schema & formula introspection
2. Natural language to coordinate & range resolution
3. Targeted cell-level modifications with 100% format & formula preservation
4. In-memory multi-sheet relational joins (inner, left)
5. Multi-dimensional pivoting with aggregation functions & grand totals
6. High-performance statistical calculations
7. State-managed transaction logging and multi-step rollbacks
8. Pre-save schema & formula syntax validation
9. Automated error-recovery execution loop
10. Agent discovery, tool execution, and on-the-fly workflow orchestration routing
"""

import io
import base64
import unittest
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from app.agents import agent_registry
from app.main import route_agent
from app.ai_generator import synthesize_on_the_fly_workflow
from app.agents.excel_specialist.tools import (
    introspect_spreadsheet,
    resolve_coordinates,
    edit_spreadsheet_cells,
    execute_statistical_analysis,
    relational_join_sheets,
    create_pivot_table,
    rollback_spreadsheet_transactions,
    validate_workbook_schema,
    global_tx_store,
    _encode_workbook_to_base64,
    _close_workbook_safely,
)


def _create_sample_sales_workbook_b64() -> str:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "SalesData"

    # Header Row
    ws["A1"] = "Region"
    ws["B1"] = "Product"
    ws["C1"] = "Q4 Revenue"
    ws["D1"] = "Units Sold"

    # Row 2 (APAC)
    ws["A2"] = "APAC"
    ws["B2"] = "Widgets"
    ws["C2"] = 150000
    ws["D2"] = 1200
    ws["C2"].font = Font(name="Calibri", size=12, bold=True, color="0000FF")
    ws["C2"].fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
    ws["C2"].number_format = "$#,##0"

    # Row 3 (EMEA)
    ws["A3"] = "EMEA"
    ws["B3"] = "Gadgets"
    ws["C3"] = 220000
    ws["D3"] = 1800
    ws["C3"].number_format = "$#,##0"

    # Row 4 (Americas)
    ws["A4"] = "Americas"
    ws["B4"] = "Widgets"
    ws["C4"] = 310000
    ws["D4"] = 2500
    ws["C4"].number_format = "$#,##0"

    # Targets Sheet
    ws2 = wb.create_sheet(title="Targets")
    ws2["A1"] = "Region"
    ws2["B1"] = "Target Revenue"
    ws2["A2"] = "APAC"
    ws2["B2"] = 180000
    ws2["A3"] = "EMEA"
    ws2["B3"] = 200000
    ws2["A4"] = "Americas"
    ws2["B4"] = 300000

    b64 = _encode_workbook_to_base64(wb)
    _close_workbook_safely(wb)
    return b64


class TestExcelSpecialistAgent(unittest.TestCase):

    def setUp(self):
        global_tx_store.clear()
        self.sample_b64 = _create_sample_sales_workbook_b64()

    def test_spreadsheet_introspection(self):
        """Validates introspection of sheets, dimensions, headers, data types, and preview rows."""
        res = introspect_spreadsheet(file_content_base64=self.sample_b64, filename="q4_sales.xlsx")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["sheet_count"], 2)

        sales_sheet = next(s for s in res["sheets"] if s["sheet_name"] == "SalesData")
        self.assertEqual(sales_sheet["headers"], ["Region", "Product", "Q4 Revenue", "Units Sold"])
        self.assertEqual(sales_sheet["row_count"], 4)
        self.assertEqual(sales_sheet["column_types"]["Region"], "text")
        self.assertEqual(sales_sheet["column_types"]["Q4 Revenue"], "number")
        self.assertEqual(len(sales_sheet["preview_rows"]), 3)

    def test_natural_language_coordinate_resolution(self):
        """Validates fuzzy header resolution, row matching, and 2D cell intersection."""
        # Intersection query
        res = resolve_coordinates(file_content_base64=self.sample_b64, sheet_name="SalesData", query="APAC Q4 Revenue")
        self.assertEqual(res["status"], "resolved")
        self.assertEqual(res["resolution_type"], "cell_intersection")
        self.assertEqual(res["coordinate"], "C2")
        self.assertEqual(res["row_criterion"], "APAC")
        self.assertEqual(res["current_value"], 150000)

        # Quoted tokens intersection
        res_quoted = resolve_coordinates(file_content_base64=self.sample_b64, sheet_name="SalesData", query="Row 'EMEA', Column 'Units Sold'")
        self.assertEqual(res_quoted["status"], "resolved")
        self.assertEqual(res_quoted["coordinate"], "D3")
        self.assertEqual(res_quoted["current_value"], 1800)

        # Column range resolution
        res_col = resolve_coordinates(file_content_base64=self.sample_b64, sheet_name="SalesData", query="Q4 Revenue")
        self.assertEqual(res_col["status"], "resolved")
        self.assertEqual(res_col["range"], "C2:C4")

        # Column letter resolution
        res_letter = resolve_coordinates(file_content_base64=self.sample_b64, sheet_name="SalesData", query="C")
        self.assertEqual(res_letter["status"], "resolved")
        self.assertEqual(res_letter["column_letter"], "C")

        # Structural row resolution
        res_last = resolve_coordinates(file_content_base64=self.sample_b64, sheet_name="SalesData", query="last row")
        self.assertEqual(res_last["status"], "resolved")
        self.assertEqual(res_last["row"], 4)

    def test_format_preserving_cell_edits(self):
        """Validates targeted mutations preserving fonts, fills, number formats, and untouched cells."""
        res = edit_spreadsheet_cells(
            file_content_base64=self.sample_b64,
            operations=[
                {"sheet": "SalesData", "coordinate": "C2", "value": 175000},
                {"sheet": "SalesData", "coordinate": "E2", "formula": "=C2*1.1"}
            ]
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["mutations_applied"], 2)

        # Decode and inspect modified workbook
        raw = base64.b64decode(res["file_content_base64"])
        wb = openpyxl.load_workbook(io.BytesIO(raw))
        try:
            ws = wb["SalesData"]
            cell_c2 = ws["C2"]
            self.assertEqual(cell_c2.value, 175000)
            self.assertTrue(cell_c2.font.bold)
            self.assertEqual(cell_c2.font.color.rgb, "000000FF")  # Blue color preserved
            self.assertEqual(cell_c2.number_format, "$#,##0")      # Format preserved

            cell_e2 = ws["E2"]
            self.assertEqual(cell_e2.value, "=C2*1.1")

            # Verify untouched cell C3
            cell_c3 = ws["C3"]
            self.assertEqual(cell_c3.value, 220000)
        finally:
            _close_workbook_safely(wb)

    def test_multi_sheet_relational_joins(self):
        """Validates in-memory relational hash joins (inner, left) across sheets."""
        res_inner = relational_join_sheets(
            file_content_base64=self.sample_b64,
            left_sheet="SalesData",
            right_sheet="Targets",
            left_key="Region",
            right_key="Region",
            join_type="inner",
            output_sheet="Sales_Vs_Targets"
        )
        self.assertEqual(res_inner["status"], "success")
        self.assertEqual(res_inner["joined_rows"], 3)
        self.assertEqual(res_inner["columns_count"], 5)  # 4 from left + 1 non-key from right

        # Verify output sheet content
        raw = base64.b64decode(res_inner["file_content_base64"])
        wb = openpyxl.load_workbook(io.BytesIO(raw))
        try:
            self.assertIn("Sales_Vs_Targets", wb.sheetnames)
            ws_joined = wb["Sales_Vs_Targets"]
            headers = [c.value for c in ws_joined[1]]
            self.assertEqual(headers, ["Region", "Product", "Q4 Revenue", "Units Sold", "Target Revenue"])
            self.assertEqual(ws_joined["A2"].value, "APAC")
            self.assertEqual(ws_joined["E2"].value, 180000)
        finally:
            _close_workbook_safely(wb)

    def test_multidimensional_pivot_table(self):
        """Validates dynamic 2D pivoting with row indices, column dimensions, and aggregations."""
        res_pivot = create_pivot_table(
            file_content_base64=self.sample_b64,
            source_sheet="SalesData",
            index_columns=["Product"],
            pivot_columns=["Region"],
            value_column="Q4 Revenue",
            aggregation="sum",
            output_sheet="Pivot_Product_Region",
            include_totals=True
        )
        self.assertEqual(res_pivot["status"], "success")
        self.assertEqual(res_pivot["row_groups_count"], 2)  # Widgets, Gadgets

        raw = base64.b64decode(res_pivot["file_content_base64"])
        wb = openpyxl.load_workbook(io.BytesIO(raw))
        try:
            self.assertIn("Pivot_Product_Region", wb.sheetnames)
            ws_pivot = wb["Pivot_Product_Region"]
            # Row 1 is header
            headers = [c.value for c in ws_pivot[1]]
            self.assertEqual(headers[0], "Product")
            self.assertIn("Grand Total", headers)
        finally:
            _close_workbook_safely(wb)

    def test_statistical_computing(self):
        """Validates statistical calculations (mean, median, variance, stdev, percentiles, IQR)."""
        res = execute_statistical_analysis(
            file_content_base64=self.sample_b64,
            sheet_name="SalesData",
            column_or_range="C2:C4",
            output_destination="new_sheet"
        )
        self.assertEqual(res["status"], "success")
        stats = res["statistics"]
        self.assertEqual(stats["count"], 3)
        self.assertEqual(stats["sum"], 680000.0)
        self.assertEqual(round(stats["mean"], 2), 226666.67)
        self.assertEqual(stats["median"], 220000.0)
        self.assertEqual(stats["min"], 150000.0)
        self.assertEqual(stats["max"], 310000.0)
        self.assertGreater(stats["variance"], 0)
        self.assertGreater(stats["standard_deviation"], 0)
        self.assertIsNotNone(res["file_content_base64"])

    def test_transaction_logging_and_rollback(self):
        """Validates transactional logging and state-managed multi-step rollback."""
        # 1. Edit C2 to 160000
        res1 = edit_spreadsheet_cells(
            file_content_base64=self.sample_b64,
            operations=[{"sheet": "SalesData", "coordinate": "C2", "value": 160000}]
        )
        self.assertEqual(res1["status"], "success")

        # 2. Edit C2 to 195000
        res2 = edit_spreadsheet_cells(
            file_content_base64=res1["file_content_base64"],
            operations=[{"sheet": "SalesData", "coordinate": "C2", "value": 195000}]
        )
        self.assertEqual(res2["status"], "success")

        # 3. Rollback 1 step (should revert C2 to 160000)
        res_rb1 = rollback_spreadsheet_transactions(
            file_content_base64=res2["file_content_base64"],
            steps=1
        )
        self.assertEqual(res_rb1["status"], "success")
        raw1 = base64.b64decode(res_rb1["file_content_base64"])
        wb1 = openpyxl.load_workbook(io.BytesIO(raw1))
        self.assertEqual(wb1["SalesData"]["C2"].value, 160000)
        _close_workbook_safely(wb1)

        # 4. Rollback another step (should revert C2 to original 150000)
        res_rb2 = rollback_spreadsheet_transactions(
            file_content_base64=res_rb1["file_content_base64"],
            steps=1
        )
        self.assertEqual(res_rb2["status"], "success")
        raw2 = base64.b64decode(res_rb2["file_content_base64"])
        wb2 = openpyxl.load_workbook(io.BytesIO(raw2))
        self.assertEqual(wb2["SalesData"]["C2"].value, 150000)
        _close_workbook_safely(wb2)

    def test_pre_save_schema_and_formula_validation(self):
        """Validates pre-save integrity checks (formula syntax balance, bounds, sheet names)."""
        # Valid workbook
        res_valid = validate_workbook_schema(file_content_base64=self.sample_b64)
        self.assertEqual(res_valid["status"], "valid")
        self.assertTrue(res_valid["is_valid"])

        # Create workbook with syntax error formula (=SUM(A1:B2 without closing paren)
        wb_corrupt = openpyxl.Workbook()
        ws = wb_corrupt.active
        ws["A1"] = "=SUM(B1:B10"
        b64_corrupt = _encode_workbook_to_base64(wb_corrupt)
        _close_workbook_safely(wb_corrupt)

        res_corrupt = validate_workbook_schema(file_content_base64=b64_corrupt)
        self.assertEqual(res_corrupt["status"], "corrupted")
        self.assertFalse(res_corrupt["is_valid"])
        self.assertTrue(any("Unbalanced parentheses" in err for err in res_corrupt["errors"]))

    def test_error_recovery_loop(self):
        """Validates that exceptions during cell edits trigger safe recovery without file corruption."""
        # Attempt edit with invalid base64 content
        res = edit_spreadsheet_cells(
            file_content_base64="not_valid_base64_content",
            operations=[{"sheet": "SalesData", "coordinate": "A1", "value": 123}]
        )
        self.assertEqual(res["status"], "error")
        self.assertIn("aborted safely", res["message"])
        self.assertIn("Auto-rollback invoked", res["recovery_applied"])

    def test_agent_registry_and_orchestration_routing(self):
        """Validates agent registration, tool reflection, and workflow routing."""
        agent = agent_registry.get("excel_specialist")
        self.assertIsNotNone(agent)
        self.assertEqual(agent.config.id, "excel_specialist")
        self.assertEqual(agent.config.name, "Excel & Computational Intelligence Specialist")
        self.assertEqual(len(agent.tools), 8)
        self.assertEqual(len(agent.tool_handlers), 8)

        # Route agent directly
        routed = route_agent(target_id="excel_specialist", last_user_content="Perform cell edit")
        self.assertEqual(routed.config.id, "excel_specialist")

        # Synthesize on-the-fly workflow for complex excel prompt
        wf = synthesize_on_the_fly_workflow(
            prompt="Perform format-preserving cell edits and resolve coordinate for APAC Q4 Revenue in my excel file"
        )
        self.assertTrue(wf.get("is_multi_step"))
        agent_ids = [s["agent_id"] for s in wf["steps"]]
        self.assertIn("excel_specialist", agent_ids)
        self.assertEqual(wf["steps"][0]["agent_id"], "excel_specialist")

        # Synthesize live research + excel mutation pipeline
        wf_live = synthesize_on_the_fly_workflow(
            prompt="Search latest apple stock price today and update cell C4 in the spreadsheet with formulas"
        )
        self.assertTrue(wf_live.get("is_multi_step"))
        live_agents = [s["agent_id"] for s in wf_live["steps"]]
        self.assertIn("researcher", live_agents)
        self.assertIn("excel_specialist", live_agents)
        self.assertIn("synthesizer", live_agents)


if __name__ == "__main__":
    unittest.main()
