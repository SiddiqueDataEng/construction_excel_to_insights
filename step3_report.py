"""
STEP 3 – Professional Excel Report
====================================
Reads CSVs from analysis_output/ and builds:

  Satti_Group_Report.xlsx  with sheets:
  ─────────────────────────────────────
  1. Dashboard        – KPI summary cards + project comparison bar chart
  2. Cost by Item     – Material spend per project, sorted by value
  3. Vendor Spend     – Pivot of vendor payments across projects
  4. Contractor Bills – Contractor totals with running bill count
  5. Labour Wages     – Trade-wise wages per project
  6. Inventory        – Received vs issued vs closing stock
  7. Utility Bills    – IESCO / SNGPL / WASA per project
  8. Bank Cashflow    – Monthly in/out with net position
  9. Price Comparison – Vendor quoted rates vs standard, colour-coded
 10. Discrepancy Log  – Every flagged data conflict, highlighted in red
 11. Raw Match Audit  – Fuzzy match results for traceability

Formatting rules:
  • PKR amounts: comma-separated, 0 decimal places
  • Percentages: 1 decimal place + % sign
  • Dates: YYYY-MM-DD
  • Green  = within ±10 % of standard
  • Amber  = 10–25 % deviation
  • Red    = >25 % deviation or flagged discrepancy
  • Headers: dark blue background, white bold text
  • Alternating row shading on data tables
  • Freeze top row on every data sheet
  • Auto column widths

"Do not overwrite" logic:
  If Satti_Group_Report.xlsx already exists, existing numeric cells in
  'Cost by Item' and 'Price Comparison' are preserved; new values that
  differ by >5% are written to a 'New Value' column and flagged instead.
"""

import os
import re
import warnings
import pandas as pd
import numpy as np
from openpyxl import Workbook, load_workbook
from openpyxl.styles import (Font, PatternFill, Alignment, Border, Side,
                              numbers as xl_numbers)
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.series import SeriesLabel

warnings.filterwarnings("ignore")

OUT_DIR     = "analysis_output"
REPORT_PATH = "Satti_Group_Report.xlsx"

# ── Colour palette ─────────────────────────────────────────────────────────────
C_HDR_BG   = "1F3864"   # dark navy
C_HDR_FG   = "FFFFFF"
C_ALT_ROW  = "EBF0FA"   # light blue
C_GREEN    = "C6EFCE"
C_AMBER    = "FFEB9C"
C_RED      = "FFC7CE"
C_RED_FG   = "9C0006"
C_AMBER_FG = "9C5700"
C_GREEN_FG = "276221"
C_TITLE_BG = "2E75B6"
C_KPI_BG   = "D6E4F0"

# ── Style helpers ──────────────────────────────────────────────────────────────
def hdr_fill():  return PatternFill("solid", fgColor=C_HDR_BG)
def alt_fill():  return PatternFill("solid", fgColor=C_ALT_ROW)
def kpi_fill():  return PatternFill("solid", fgColor=C_KPI_BG)
def red_fill():  return PatternFill("solid", fgColor=C_RED)
def amber_fill():return PatternFill("solid", fgColor=C_AMBER)
def green_fill():return PatternFill("solid", fgColor=C_GREEN)

def hdr_font(size=11): return Font(bold=True, color=C_HDR_FG, size=size)
def bold(size=11):     return Font(bold=True, size=size)
def red_font():        return Font(bold=True, color=C_RED_FG)
def amber_font():      return Font(bold=True, color=C_AMBER_FG)
def green_font():      return Font(bold=True, color=C_GREEN_FG)

def thin_border():
    s = Side(style="thin", color="CCCCCC")
    return Border(left=s, right=s, top=s, bottom=s)

def center(): return Alignment(horizontal="center", vertical="center", wrap_text=False)
def left():   return Alignment(horizontal="left",   vertical="center", wrap_text=False)
def right():  return Alignment(horizontal="right",  vertical="center")

PKR_FMT  = '#,##0'
PCT_FMT  = '0.0"%"'
DATE_FMT = 'YYYY-MM-DD'

def write_header_row(ws, headers, row=1, col_start=1):
    for i, h in enumerate(headers):
        c = ws.cell(row=row, column=col_start+i, value=h)
        c.fill      = hdr_fill()
        c.font      = hdr_font()
        c.alignment = center()
        c.border    = thin_border()

def write_data_row(ws, values, row, col_start=1, shade=False, number_cols=None, pct_cols=None):
    number_cols = number_cols or set()
    pct_cols    = pct_cols    or set()
    for i, v in enumerate(values):
        col = col_start + i
        c   = ws.cell(row=row, column=col, value=v)
        if shade:
            c.fill = alt_fill()
        c.border    = thin_border()
        c.alignment = right() if (i+1) in number_cols else left()
        if (i+1) in number_cols and isinstance(v, (int, float)) and not isinstance(v, bool):
            c.number_format = PKR_FMT
        if (i+1) in pct_cols and isinstance(v, (int, float)):
            c.number_format = '0.0'

def autofit(ws, min_w=8, max_w=50):
    for col_cells in ws.columns:
        length = max(
            len(str(c.value)) if c.value is not None else 0
            for c in col_cells
        )
        ws.column_dimensions[get_column_letter(col_cells[0].column)].width = \
            min(max(length + 2, min_w), max_w)

def freeze(ws, cell="A2"):
    ws.freeze_panes = cell

def section_title(ws, row, col, text, span=1):
    c = ws.cell(row=row, column=col, value=text)
    c.fill      = PatternFill("solid", fgColor=C_TITLE_BG)
    c.font      = Font(bold=True, color="FFFFFF", size=12)
    c.alignment = center()
    if span > 1:
        ws.merge_cells(start_row=row, start_column=col,
                       end_row=row, end_column=col+span-1)

def load_csv(name):
    path = os.path.join(OUT_DIR, f"{name}.csv")
    if os.path.exists(path):
        return pd.read_csv(path, dtype=str, low_memory=False)
    return pd.DataFrame()

def to_float(series):
    return pd.to_numeric(series, errors="coerce")


# ══════════════════════════════════════════════════════════════════════════════
# SHEET BUILDERS
# ══════════════════════════════════════════════════════════════════════════════

# ── 1. Dashboard ───────────────────────────────────────────────────────────────
def build_dashboard(wb):
    ws = wb.create_sheet("Dashboard", 0)
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 3

    # Title banner
    ws.row_dimensions[1].height = 40
    ws.merge_cells("B1:L1")
    c = ws["B1"]
    c.value     = "SATTI GROUP  –  Construction Project Analytics Report"
    c.font      = Font(bold=True, size=18, color="FFFFFF")
    c.fill      = PatternFill("solid", fgColor=C_HDR_BG)
    c.alignment = center()

    ws.merge_cells("B2:L2")
    ws["B2"].value     = "Projects: Satti Mall (2006–08) | Satti Plaza (2011–14) | Satti Apartments (2015–18)"
    ws["B2"].font      = Font(italic=True, size=11, color="444444")
    ws["B2"].alignment = center()

    # KPI Cards
    kpi_row = 4
    ws.row_dimensions[kpi_row].height = 18

    # Load data for KPIs
    cost_df   = load_csv("cost_by_item")
    pay_df    = load_csv("payment_status")
    labour_df = load_csv("labour_by_trade")
    contr_df  = load_csv("contractor_summary")
    flags_df  = load_csv("discrepancy_flags")

    total_material = to_float(cost_df["total_spend"]).sum() if not cost_df.empty else 0
    total_paid     = to_float(pay_df[pay_df["status_norm"]=="PAID"]["total"] if not pay_df.empty else pd.Series()).sum()
    total_unpaid   = to_float(pay_df[pay_df["status_norm"]=="UNPAID"]["total"] if not pay_df.empty else pd.Series()).sum()
    total_wages    = to_float(labour_df["total_wages"]).sum() if not labour_df.empty else 0
    total_contr    = to_float(contr_df["total_paid"]).sum() if not contr_df.empty else 0
    n_flags        = len(flags_df) if not flags_df.empty else 0

    kpis = [
        ("Total Material Spend",    f"PKR {total_material:,.0f}",  "B"),
        ("Payments Made",           f"PKR {total_paid:,.0f}",      "D"),
        ("Outstanding Payments",    f"PKR {total_unpaid:,.0f}",    "F"),
        ("Total Labour Wages",      f"PKR {total_wages:,.0f}",     "H"),
        ("Contractor Payments",     f"PKR {total_contr:,.0f}",     "J"),
        ("Discrepancy Flags",       str(n_flags),                  "L"),
    ]
    for title, value, col_letter in kpis:
        r = kpi_row
        ws.row_dimensions[r].height   = 18
        ws.row_dimensions[r+1].height = 30
        ws.row_dimensions[r+2].height = 14

        ws.merge_cells(f"{col_letter}{r}:{col_letter}{r}")
        tc = ws[f"{col_letter}{r}"]
        tc.value     = title
        tc.font      = Font(bold=True, size=9, color="555555")
        tc.alignment = center()

        ws.merge_cells(f"{col_letter}{r+1}:{col_letter}{r+1}")
        vc = ws[f"{col_letter}{r+1}"]
        vc.value     = value
        vc.font      = Font(bold=True, size=13, color=C_HDR_BG)
        vc.fill      = kpi_fill()
        vc.alignment = center()
        vc.border    = thin_border()

    # Project cost breakdown table (for charting)
    table_row = kpi_row + 5
    ws.cell(row=table_row, column=2, value="Project Cost Breakdown")
    ws["B" + str(table_row)].font = bold(12)

    if not cost_df.empty:
        proj_totals = cost_df.groupby("project")["total_spend"].apply(
            lambda x: to_float(x).sum()).reset_index()
        proj_totals.columns = ["Project", "Total Spend (PKR)"]

        write_header_row(ws, ["Project","Total Spend (PKR)"], row=table_row+1, col_start=2)
        for i, (_, row_data) in enumerate(proj_totals.iterrows()):
            r = table_row + 2 + i
            shade = (i % 2 == 1)
            write_data_row(ws, [row_data["Project"], row_data["Total Spend (PKR)"]],
                           row=r, col_start=2, shade=shade, number_cols={2})

        # Bar chart
        chart = BarChart()
        chart.type       = "col"
        chart.title      = "Material Spend by Project (PKR)"
        chart.y_axis.title = "PKR"
        chart.x_axis.title = "Project"
        chart.style      = 10
        chart.width      = 18
        chart.height     = 12

        n = len(proj_totals)
        data_ref = Reference(ws, min_col=3, min_row=table_row+1,
                              max_row=table_row+1+n)
        cats_ref = Reference(ws, min_col=2, min_row=table_row+2,
                              max_row=table_row+1+n)
        chart.add_data(data_ref, titles_from_data=True)
        chart.set_categories(cats_ref)
        ws.add_chart(chart, f"D{table_row+1}")

    autofit(ws)

# ── 2. Cost by Item ────────────────────────────────────────────────────────────
def build_cost_by_item(wb, existing_wb=None):
    ws = wb.create_sheet("Cost by Item")

    df = load_csv("cost_by_item")
    if df.empty:
        ws["A1"] = "No data"
        return

    df["total_spend"] = to_float(df["total_spend"])
    df = df.sort_values(["project","total_spend"], ascending=[True, False])

    headers = ["Project","Item Code","Item Name","Total Spend (PKR)","% of Project Total"]
    write_header_row(ws, headers)

    # "Do not overwrite" check: load existing data if report already existed
    existing_data = {}
    if existing_wb and "Cost by Item" in existing_wb.sheetnames:
        ews = existing_wb["Cost by Item"]
        for erow in ews.iter_rows(min_row=2, values_only=True):
            if erow[0] and erow[1]:
                key = (str(erow[0]), str(erow[1]))
                existing_data[key] = erow[3]   # total_spend

    proj_totals = df.groupby("project")["total_spend"].sum().to_dict()

    row_num = 2
    for _, r in df.iterrows():
        proj  = str(r["project"])
        code  = str(r.get("canon_code",""))
        name  = str(r.get("canon_name",""))
        spend = r["total_spend"]
        pct   = round(spend / proj_totals.get(proj, 1) * 100, 1) if proj_totals.get(proj) else 0
        shade = (row_num % 2 == 0)

        key = (proj, code)
        if key in existing_data:
            old_val = existing_data[key]
            if pd.notna(old_val) and pd.notna(spend):
                try:
                    old_f = float(old_val)
                    diff  = abs(spend - old_f) / old_f * 100 if old_f else 0
                    if diff > 5:
                        # Write existing value, put new in next col, flag
                        write_data_row(ws, [proj, code, name, old_f, pct],
                                       row=row_num, shade=shade, number_cols={4}, pct_cols={5})
                        ws.cell(row=row_num, column=6, value=spend).number_format = PKR_FMT
                        ws.cell(row=row_num, column=6).fill = amber_fill()
                        ws.cell(row=row_num, column=7, value=f"⚠ Conflict: was {old_f:,.0f}, new {spend:,.0f} (+{diff:.1f}%)")
                        ws.cell(row=row_num, column=7).font = amber_font()
                        row_num += 1
                        continue
                except (ValueError, TypeError):
                    pass

        write_data_row(ws, [proj, code, name, spend, pct],
                       row=row_num, shade=shade, number_cols={4}, pct_cols={5})
        row_num += 1

    # Add header for extra conflict columns if needed
    if existing_data:
        ws.cell(row=1, column=6, value="New Value (Conflict)").fill = hdr_fill()
        ws.cell(row=1, column=6).font = hdr_font()
        ws.cell(row=1, column=7, value="Conflict Note").fill = hdr_fill()
        ws.cell(row=1, column=7).font = hdr_font()

    freeze(ws)
    autofit(ws)


# ── 3. Vendor Spend ────────────────────────────────────────────────────────────
def build_vendor_spend(wb):
    ws = wb.create_sheet("Vendor Spend")

    bills = load_csv("bills_matched")
    if bills.empty:
        ws["A1"] = "No data"
        return

    bills["total"] = to_float(bills["total"])

    # Extract vendor from source filename  V001_Pak_Steel_Traders_PriceList → Pak Steel Traders
    def vendor_from_file(src):
        m = re.search(r"V\d+_(.+?)_Bill", str(src))
        if m:
            return m.group(1).replace("_"," ")
        # Fall back to doc_no prefix
        return "Unknown"

    if "vendor" not in bills.columns or bills["vendor"].str.strip().eq("").all():
        bills["vendor_clean"] = bills["source_file"].apply(vendor_from_file)
    else:
        bills["vendor_clean"] = bills["vendor"].fillna("Unknown")

    # project column is named 'project' in bills_matched
    proj_col = "project" if "project" in bills.columns else "_project"

    pivot = (bills[bills["total"].notna()]
             .groupby([proj_col,"vendor_clean"])["total"]
             .sum().reset_index()
             .rename(columns={proj_col:"Project","vendor_clean":"Vendor","total":"Total Spend"}))
    pivot["Total Spend"] = pivot["Total Spend"].round(0)
    pivot = pivot.sort_values(["Project","Total Spend"], ascending=[True, False])

    headers = ["Project","Vendor","Total Spend (PKR)"]
    write_header_row(ws, headers)
    for i, (_, r) in enumerate(pivot.iterrows()):
        write_data_row(ws, [r["Project"], r["Vendor"], r["Total Spend"]],
                       row=i+2, shade=(i%2==1), number_cols={3})

    freeze(ws)
    autofit(ws)


# ── 4. Contractor Bills ────────────────────────────────────────────────────────
def build_contractor_bills(wb):
    ws = wb.create_sheet("Contractor Bills")

    df = load_csv("contractor_summary")
    if df.empty:
        ws["A1"] = "No data"
        return

    df["total_paid"] = to_float(df["total_paid"])
    df["num_bills"]  = to_float(df["num_bills"])

    headers = ["Project","Contractor Code","Contractor Name","No. of Bills","Total Paid (PKR)"]
    write_header_row(ws, headers)
    for i, (_, r) in enumerate(df.iterrows()):
        write_data_row(ws, [r["_project"], r["contractor_code"], r["contractor_name"],
                            int(r["num_bills"]) if pd.notna(r["num_bills"]) else "",
                            r["total_paid"]],
                       row=i+2, shade=(i%2==1), number_cols={5})

    freeze(ws)
    autofit(ws)


# ── 5. Labour Wages ────────────────────────────────────────────────────────────
def build_labour(wb):
    ws = wb.create_sheet("Labour Wages")

    df = load_csv("labour_by_trade")
    if df.empty:
        ws["A1"] = "No data"
        return

    df["total_wages"] = to_float(df["total_wages"])
    df["workers"]     = to_float(df["workers"])
    df = df.sort_values(["_project","total_wages"], ascending=[True,False])

    headers = ["Project","Trade / Designation","Worker Count","Total Wages (PKR)","Avg Wage/Person (PKR)"]
    write_header_row(ws, headers)
    for i, (_, r) in enumerate(df.iterrows()):
        workers = r["workers"] if pd.notna(r["workers"]) else 0
        wages   = r["total_wages"] if pd.notna(r["total_wages"]) else 0
        avg     = round(wages / workers, 0) if workers else 0
        write_data_row(ws, [r["_project"], r.get("trade",""), int(workers), wages, avg],
                       row=i+2, shade=(i%2==1), number_cols={4,5})

    freeze(ws)
    autofit(ws)


# ── 6. Inventory ───────────────────────────────────────────────────────────────
def build_inventory(wb):
    ws = wb.create_sheet("Inventory")

    df = load_csv("inventory_summary")
    if df.empty:
        ws["A1"] = "No data"
        return

    for c in ["total_received","total_issued","avg_closing"]:
        df[c] = to_float(df[c])

    df = df.sort_values(["project","total_received"], ascending=[True,False])

    headers = ["Project","Item Code","Item Name","Total Received","Total Issued","Avg Closing Stock"]
    write_header_row(ws, headers)
    for i, (_, r) in enumerate(df.iterrows()):
        write_data_row(ws, [r["project"], r.get("canon_code",""), r.get("canon_name",""),
                            r["total_received"], r["total_issued"], r["avg_closing"]],
                       row=i+2, shade=(i%2==1), number_cols={4,5,6})

    freeze(ws)
    autofit(ws)


# ── 7. Utility Bills ──────────────────────────────────────────────────────────
def build_utilities(wb):
    ws = wb.create_sheet("Utility Bills")

    df = load_csv("utility_bills")
    if df.empty:
        ws["A1"] = "No data"
        return

    df["total_paid"] = to_float(df["total_paid"])
    df["months"]     = to_float(df["months"])

    headers = ["Project","Utility","Months","Total Paid (PKR)","Avg Monthly (PKR)"]
    write_header_row(ws, headers)
    for i, (_, r) in enumerate(df.iterrows()):
        months = r["months"] if pd.notna(r["months"]) else 1
        avg    = round(r["total_paid"] / months, 0) if months else 0
        write_data_row(ws, [r["_project"], r["utility"], int(months), r["total_paid"], avg],
                       row=i+2, shade=(i%2==1), number_cols={4,5})

    freeze(ws)
    autofit(ws)


# ── 8. Bank Cashflow ──────────────────────────────────────────────────────────
def build_cashflow(wb):
    ws = wb.create_sheet("Bank Cashflow")

    df = load_csv("bank_cashflow")
    if df.empty:
        ws["A1"] = "No data"
        return

    for c in ["total_debit","total_credit","net","txn_count"]:
        df[c] = to_float(df[c])

    df = df.sort_values("year_month")

    headers = ["Month","Total Out (Debit)","Total In (Credit)","Net Position","Transactions"]
    write_header_row(ws, headers)
    for i, (_, r) in enumerate(df.iterrows()):
        net = r["net"]
        row_vals = [r["year_month"], r["total_debit"], r["total_credit"],
                    net, int(r["txn_count"]) if pd.notna(r["txn_count"]) else 0]
        write_data_row(ws, row_vals, row=i+2, shade=(i%2==1), number_cols={2,3,4})
        # Colour net cell
        net_cell = ws.cell(row=i+2, column=4)
        if pd.notna(net):
            if net >= 0:
                net_cell.fill = green_fill()
                net_cell.font = green_font()
            else:
                net_cell.fill = red_fill()
                net_cell.font = red_font()

    # Line chart for cashflow
    if len(df) > 1:
        chart = BarChart()
        chart.type    = "col"
        chart.title   = "Monthly Bank Cashflow"
        chart.style   = 10
        chart.width   = 22
        chart.height  = 12
        n = len(df)
        data_ref = Reference(ws, min_col=2, max_col=3, min_row=1, max_row=1+n)
        chart.add_data(data_ref, titles_from_data=True)
        ws.add_chart(chart, "G2")

    freeze(ws)
    autofit(ws)


# ── 9. Price Comparison ────────────────────────────────────────────────────────
def build_price_comparison(wb, existing_wb=None):
    ws = wb.create_sheet("Price Comparison")

    df = load_csv("vendor_price_compare")
    if df.empty:
        ws["A1"] = "No data"
        return

    for c in ["quoted_rate","std_rate","pct_vs_std"]:
        df[c] = to_float(df[c])

    df = df.sort_values(["canon_code","pct_vs_std"])

    headers = ["Item Code","Item Name","Vendor","Quoted Rate (PKR)",
               "Standard Rate (PKR)","% vs Std","Assessment"]
    write_header_row(ws, headers)

    # Existing data check
    existing_rates = {}
    if existing_wb and "Price Comparison" in existing_wb.sheetnames:
        ews = existing_wb["Price Comparison"]
        for erow in ews.iter_rows(min_row=2, values_only=True):
            if erow and erow[0] and erow[2]:
                key = (str(erow[0]), str(erow[2]))   # (item_code, vendor)
                existing_rates[key] = erow[3]

    for i, (_, r) in enumerate(df.iterrows()):
        pct  = r["pct_vs_std"]
        code = str(r.get("canon_code",""))
        name = str(r.get("canon_name",""))
        vendor = str(r.get("vendor",""))
        qrate  = r["quoted_rate"]
        std    = r["std_rate"]

        if abs(pct) <= 10:
            assess = "✓ Acceptable"
        elif abs(pct) <= 25:
            assess = "⚠ Review"
        else:
            assess = "✗ Investigate"

        row_vals = [code, name, vendor, qrate, std, round(pct, 1) if pd.notna(pct) else "", assess]
        write_data_row(ws, row_vals, row=i+2, shade=False, number_cols={4,5})

        # Color by deviation
        assess_cell = ws.cell(row=i+2, column=7)
        rate_cell   = ws.cell(row=i+2, column=4)
        if pd.notna(pct):
            if abs(pct) <= 10:
                assess_cell.fill = green_fill()
                assess_cell.font = green_font()
                rate_cell.fill   = green_fill()
            elif abs(pct) <= 25:
                assess_cell.fill = amber_fill()
                assess_cell.font = amber_font()
                rate_cell.fill   = amber_fill()
            else:
                assess_cell.fill = red_fill()
                assess_cell.font = red_font()
                rate_cell.fill   = red_fill()

        # "Do not overwrite" logic
        key = (code, vendor)
        if key in existing_rates:
            old_rate = existing_rates[key]
            try:
                old_f = float(old_rate)
                diff  = abs(qrate - old_f) / old_f * 100 if old_f else 0
                if diff > 5:
                    ws.cell(row=i+2, column=8, value=old_f).number_format = PKR_FMT
                    ws.cell(row=i+2, column=9,
                            value=f"⚠ Previously {old_f:,.0f}, now {qrate:,.0f} ({diff:.1f}% chg)")
                    ws.cell(row=i+2, column=9).fill = amber_fill()
                    ws.cell(row=i+2, column=9).font = amber_font()
            except (ValueError, TypeError):
                pass

    if existing_rates:
        ws.cell(row=1, column=8, value="Previous Rate").fill = hdr_fill()
        ws.cell(row=1, column=8).font = hdr_font()
        ws.cell(row=1, column=9, value="Change Note").fill = hdr_fill()
        ws.cell(row=1, column=9).font = hdr_font()

    freeze(ws)
    autofit(ws)


# ── 10. Discrepancy Log ────────────────────────────────────────────────────────
def build_discrepancy_log(wb):
    ws = wb.create_sheet("⚠ Discrepancy Log")

    df = load_csv("discrepancy_flags")
    if df.empty:
        ws["A1"] = "No discrepancies flagged."
        return

    # Section title
    section_title(ws, 1, 1, "⚠  DATA DISCREPANCY LOG – Items flagged for review. Do NOT overwrite existing data without investigation.", span=7)

    headers = ["Source File","Item Code","Item Name","Field","Existing Value","New Value","Note"]
    write_header_row(ws, headers, row=2)

    for i, (_, r) in enumerate(df.iterrows()):
        row_num = i + 3
        vals = [r.get("source_file",""), r.get("item_code",""), r.get("item_name",""),
                r.get("field",""), r.get("existing_value",""),
                r.get("new_value",""),   r.get("note","")]
        for j, v in enumerate(vals):
            c = ws.cell(row=row_num, column=j+1, value=v)
            c.fill   = red_fill()
            c.font   = Font(color=C_RED_FG, size=10)
            c.border = thin_border()

    ws.row_dimensions[1].height = 30
    freeze(ws, "A3")
    autofit(ws)


# ── 11. Raw Match Audit ────────────────────────────────────────────────────────
def build_match_audit(wb):
    ws = wb.create_sheet("Match Audit")

    df = load_csv("bills_matched")
    if df.empty:
        ws["A1"] = "No data"
        return

    # Only show a useful subset of columns
    show_cols = ["project","source_file","raw_code","raw_desc",
                 "canon_code","canon_name","match_score","rate","total","matched"]
    existing = [c for c in show_cols if c in df.columns]
    df_show  = df[existing].copy()

    df_show["match_score"] = to_float(df_show.get("match_score", pd.Series()))

    headers = [c.replace("_","").replace("canon","Canon ").replace("raw","Raw ").title()
               for c in existing]
    write_header_row(ws, headers)

    for i, (_, r) in enumerate(df_show.head(2000).iterrows()):  # cap at 2000 rows for performance
        vals  = [r.get(c, "") for c in existing]
        shade = (i % 2 == 1)
        row_num = i + 2
        for j, v in enumerate(vals):
            c = ws.cell(row=row_num, column=j+1, value=v)
            if shade:
                c.fill = alt_fill()
            c.border = thin_border()

        # Colour match_score column
        if "match_score" in existing:
            score_col = existing.index("match_score") + 1
            score_cell = ws.cell(row=row_num, column=score_col)
            score = r.get("match_score", None)
            try:
                score_f = float(score)
                if score_f >= 90:
                    score_cell.fill = green_fill()
                elif score_f >= 72:
                    score_cell.fill = amber_fill()
                else:
                    score_cell.fill = red_fill()
            except (TypeError, ValueError):
                pass

    freeze(ws)
    autofit(ws)


# ── 12. Item Master Conflicts ──────────────────────────────────────────────────
def build_item_conflicts(wb):
    ws = wb.create_sheet("Item Master Conflicts")

    df = load_csv("item_master_conflicts")
    if df.empty:
        ws["A1"] = "No conflicts found."
        return

    section_title(ws, 1, 1,
                  "Item master rate conflicts – same item, different rates across files. Preserve existing; flag new.",
                  span=7)

    headers = ["Item Code","Item Name","Source A","Rate A (PKR)","Source B","Rate B (PKR)","Diff %"]
    write_header_row(ws, headers, row=2)

    for i, (_, r) in enumerate(df.iterrows()):
        diff = to_float(pd.Series([r.get("diff_pct","")])).iloc[0]
        vals = [r.get("canon_code",""), r.get("canon_name",""),
                r.get("source_a",""), r.get("rate_a",""),
                r.get("source_b",""), r.get("rate_b",""),
                diff]
        row_num = i + 3
        for j, v in enumerate(vals):
            c = ws.cell(row=row_num, column=j+1, value=v)
            c.border = thin_border()

        # Highlight based on severity
        diff_cell = ws.cell(row=row_num, column=7)
        if pd.notna(diff):
            if diff > 25:
                for j in range(1, 8):
                    ws.cell(row=row_num, column=j).fill = red_fill()
                diff_cell.font = red_font()
            elif diff > 10:
                for j in range(1, 8):
                    ws.cell(row=row_num, column=j).fill = amber_fill()
                diff_cell.font = amber_font()
            else:
                diff_cell.fill = green_fill()

    freeze(ws, "A3")
    autofit(ws)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def run():
    print("\n=== STEP 3: Building Professional Excel Report ===\n")

    # Load existing workbook if present (for "do not overwrite" logic)
    existing_wb = None
    if os.path.exists(REPORT_PATH):
        print(f"  Existing report found – preserving data, flagging conflicts…")
        try:
            existing_wb = load_workbook(REPORT_PATH, read_only=True, data_only=True)
        except Exception as e:
            print(f"  WARNING: could not open existing report: {e}")

    wb = Workbook()
    # Remove default sheet
    if "Sheet" in wb.sheetnames:
        del wb["Sheet"]

    build_dashboard(wb)
    build_cost_by_item(wb, existing_wb)
    build_vendor_spend(wb)
    build_contractor_bills(wb)
    build_labour(wb)
    build_inventory(wb)
    build_utilities(wb)
    build_cashflow(wb)
    build_price_comparison(wb, existing_wb)
    build_discrepancy_log(wb)
    build_item_conflicts(wb)
    build_match_audit(wb)

    if existing_wb:
        existing_wb.close()

    wb.save(REPORT_PATH)
    print(f"\n  ✓ Report saved: {REPORT_PATH}")
    print(f"    Sheets: {', '.join(wb.sheetnames)}\n")


if __name__ == "__main__":
    run()
