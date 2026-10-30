"""Export the model as an Excel workbook with live formulas.

Values are not pasted in. Every rate, allocation and variance is an Excel
formula pointing at the Inputs sheet, so changing a driver changes the answer.
That is the difference between a model and a report.
"""
from __future__ import annotations
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from .sample import PRODUCTS, POOL, ABSORPTION

BOLD = Font(bold=True)
HEAD = Font(bold=True, color="FFFFFF")
FILL = PatternFill("solid", fgColor="1F4E79")
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")
MONEY = '#,##0'
RATE = '#,##0.00'
PCT = '0.0%'
THIN = Border(bottom=Side(style="thin", color="BFBFBF"))


def _head(ws, row, labels, widths=None):
    for c, label in enumerate(labels, start=1):
        cell = ws.cell(row=row, column=c, value=label)
        cell.font = HEAD; cell.fill = FILL
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
    if widths:
        for c, w in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(c)].width = w


def build(path: str) -> str:
    wb = Workbook()

    # ---------------------------------------------------------------- Inputs
    ws = wb.active; ws.title = "Inputs"
    ws["A1"] = "Product and customer profitability: inputs"; ws["A1"].font = Font(bold=True, size=13)
    ws["A2"] = "Every shaded cell is an input. Everything else in this workbook is a formula."
    _head(ws, 4,
          ["Code", "Product", "Plant", "Units", "Price", "Direct material",
           "Direct labour", "Machine hrs/unit", "Setups", "Order lines"],
          [8, 26, 10, 10, 10, 14, 13, 14, 9, 12])
    r = 5
    for p in PRODUCTS:
        for c, v in enumerate([p.code, p.name, p.plant, p.units, p.price,
                               p.direct_material, p.direct_labour,
                               p.machine_hours, p.setups, p.order_lines], start=1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.fill = INPUT_FILL
            if c in (4, 9, 10): cell.number_format = MONEY
            if c in (5, 6, 7, 8): cell.number_format = RATE
        r += 1
    first, last = 5, r - 1

    ws.cell(row=r + 1, column=1, value="Overhead pool").font = BOLD
    pool_rows = {}
    for i, (label, val) in enumerate([("Machining (driver: machine hours)", POOL.machining),
                                      ("Setup (driver: setups)", POOL.setup),
                                      ("Order handling (driver: order lines)", POOL.order_handling)]):
        rr = r + 2 + i
        ws.cell(row=rr, column=1, value=label)
        c = ws.cell(row=rr, column=4, value=val); c.fill = INPUT_FILL; c.number_format = MONEY
        pool_rows[label.split(" (")[0]] = rr
    total_row = r + 5
    ws.cell(row=total_row, column=1, value="Total overhead").font = BOLD
    tc = ws.cell(row=total_row, column=4,
                 value=f"=SUM(D{r+2}:D{r+4})"); tc.font = BOLD; tc.number_format = MONEY

    ab = total_row + 2
    ws.cell(row=ab, column=1, value="Absorption variance inputs").font = BOLD
    for i, (label, val, fmt) in enumerate([
            ("Budgeted overhead", ABSORPTION.budgeted_overhead, MONEY),
            ("Budgeted machine hours", ABSORPTION.budgeted_hours, MONEY),
            ("Actual overhead", ABSORPTION.actual_overhead, MONEY),
            ("Actual machine hours", ABSORPTION.actual_hours, MONEY)]):
        ws.cell(row=ab + 1 + i, column=1, value=label)
        c = ws.cell(row=ab + 1 + i, column=4, value=val); c.fill = INPUT_FILL; c.number_format = fmt
    AB = {"bud_oh": ab + 1, "bud_hrs": ab + 2, "act_oh": ab + 3, "act_hrs": ab + 4}

    # ------------------------------------------------------------- Plantwide
    p1 = wb.create_sheet("Plantwide")
    p1["A1"] = "Method 1: single plantwide rate on machine hours"; p1["A1"].font = Font(bold=True, size=12)
    p1["A2"] = "Rate = total overhead / total machine hours. One rate for every product."
    p1["A4"] = "Total machine hours"; p1["D4"] = f"=SUMPRODUCT(Inputs!D{first}:D{last},Inputs!H{first}:H{last})"
    p1["D4"].number_format = MONEY
    p1["A5"] = "Total overhead"; p1["D5"] = f"=Inputs!D{total_row}"; p1["D5"].number_format = MONEY
    p1["A6"] = "Plantwide rate per machine hour"; p1["D6"] = "=D5/D4"
    p1["D6"].number_format = RATE; p1["D6"].font = BOLD
    _head(p1, 8, ["Code", "Product", "Revenue", "Direct cost", "Gross margin",
                  "Machine hrs", "Overhead", "Net margin", "Net %"],
          [8, 26, 14, 14, 14, 12, 14, 14, 9])
    for i in range(len(PRODUCTS)):
        R, S = 9 + i, first + i
        p1.cell(row=R, column=1, value=f"=Inputs!A{S}")
        p1.cell(row=R, column=2, value=f"=Inputs!B{S}")
        p1.cell(row=R, column=3, value=f"=Inputs!D{S}*Inputs!E{S}").number_format = MONEY
        p1.cell(row=R, column=4, value=f"=Inputs!D{S}*(Inputs!F{S}+Inputs!G{S})").number_format = MONEY
        p1.cell(row=R, column=5, value=f"=C{R}-D{R}").number_format = MONEY
        p1.cell(row=R, column=6, value=f"=Inputs!D{S}*Inputs!H{S}").number_format = MONEY
        p1.cell(row=R, column=7, value=f"=F{R}*$D$6").number_format = MONEY
        p1.cell(row=R, column=8, value=f"=E{R}-G{R}").number_format = MONEY
        p1.cell(row=R, column=9, value=f"=IF(C{R}=0,0,H{R}/C{R})").number_format = PCT
    T = 9 + len(PRODUCTS)
    p1.cell(row=T, column=2, value="Total").font = BOLD
    for col in "CDEFGH":
        c = p1[f"{col}{T}"]; c.value = f"=SUM({col}9:{col}{T-1})"; c.font = BOLD; c.number_format = MONEY
        c.border = THIN

    # -------------------------------------------------------------- Activity
    p2 = wb.create_sheet("Activity")
    p2["A1"] = "Method 2: one rate per cost driver"; p2["A1"].font = Font(bold=True, size=12)
    p2["A2"] = "Each overhead pool is absorbed by the activity that causes it."
    p2["A4"] = "Total machine hours"; p2["D4"] = f"=SUMPRODUCT(Inputs!D{first}:D{last},Inputs!H{first}:H{last})"
    p2["A5"] = "Total setups";        p2["D5"] = f"=SUM(Inputs!I{first}:I{last})"
    p2["A6"] = "Total order lines";   p2["D6"] = f"=SUM(Inputs!J{first}:J{last})"
    p2["A8"] = "Machining rate per hour";  p2["D8"] = f"=Inputs!D{pool_rows['Machining']}/D4"
    p2["A9"] = "Setup rate per setup";     p2["D9"] = f"=Inputs!D{pool_rows['Setup']}/D5"
    p2["A10"] = "Order rate per line";     p2["D10"] = f"=Inputs!D{pool_rows['Order handling']}/D6"
    for ref in ("D4", "D5", "D6"): p2[ref].number_format = MONEY
    for ref in ("D8", "D9", "D10"): p2[ref].number_format = RATE; p2[ref].font = BOLD
    _head(p2, 12, ["Code", "Product", "Revenue", "Direct cost", "Gross margin",
                   "Machining OH", "Setup OH", "Order OH", "Overhead", "Net margin", "Net %"],
          [8, 26, 14, 14, 14, 13, 12, 12, 14, 14, 9])
    for i in range(len(PRODUCTS)):
        R, S = 13 + i, first + i
        p2.cell(row=R, column=1, value=f"=Inputs!A{S}")
        p2.cell(row=R, column=2, value=f"=Inputs!B{S}")
        p2.cell(row=R, column=3, value=f"=Inputs!D{S}*Inputs!E{S}").number_format = MONEY
        p2.cell(row=R, column=4, value=f"=Inputs!D{S}*(Inputs!F{S}+Inputs!G{S})").number_format = MONEY
        p2.cell(row=R, column=5, value=f"=C{R}-D{R}").number_format = MONEY
        p2.cell(row=R, column=6, value=f"=Inputs!D{S}*Inputs!H{S}*$D$8").number_format = MONEY
        p2.cell(row=R, column=7, value=f"=Inputs!I{S}*$D$9").number_format = MONEY
        p2.cell(row=R, column=8, value=f"=Inputs!J{S}*$D$10").number_format = MONEY
        p2.cell(row=R, column=9, value=f"=SUM(F{R}:H{R})").number_format = MONEY
        p2.cell(row=R, column=10, value=f"=E{R}-I{R}").number_format = MONEY
        p2.cell(row=R, column=11, value=f"=IF(C{R}=0,0,J{R}/C{R})").number_format = PCT
    T2 = 13 + len(PRODUCTS)
    p2.cell(row=T2, column=2, value="Total").font = BOLD
    for col in "CDEFGHIJ":
        c = p2[f"{col}{T2}"]; c.value = f"=SUM({col}13:{col}{T2-1})"; c.font = BOLD
        c.number_format = MONEY; c.border = THIN

    # ------------------------------------------------------------ Comparison
    p3 = wb.create_sheet("Comparison")
    p3["A1"] = "What changes when the allocation method changes"; p3["A1"].font = Font(bold=True, size=12)
    p3["A2"] = "Revenue and direct cost are identical in both. Only the overhead split moves."
    _head(p3, 4, ["Code", "Product", "Net: plantwide", "Net: activity",
                  "Difference", "Sign flips?"], [8, 26, 16, 16, 14, 12])
    for i in range(len(PRODUCTS)):
        R = 5 + i
        p3.cell(row=R, column=1, value=f"=Plantwide!A{9+i}")
        p3.cell(row=R, column=2, value=f"=Plantwide!B{9+i}")
        p3.cell(row=R, column=3, value=f"=Plantwide!H{9+i}").number_format = MONEY
        p3.cell(row=R, column=4, value=f"=Activity!J{13+i}").number_format = MONEY
        p3.cell(row=R, column=5, value=f"=D{R}-C{R}").number_format = MONEY
        p3.cell(row=R, column=6, value=f'=IF(SIGN(C{R})<>SIGN(D{R}),"FLIPS","")')
        p3.cell(row=R, column=6).font = Font(bold=True, color="C00000")
    TT = 5 + len(PRODUCTS)
    p3.cell(row=TT, column=2, value="Total").font = BOLD
    for col in "CDE":
        c = p3[f"{col}{TT}"]; c.value = f"=SUM({col}5:{col}{TT-1})"; c.font = BOLD
        c.number_format = MONEY; c.border = THIN
    p3.cell(row=TT + 2, column=1,
            value="Totals agree because both methods absorb the same pool. "
                  "The argument is never about the total, only about who carries it.")

    # ----------------------------------------------------- Absorption variance
    p4 = wb.create_sheet("Absorption")
    p4["A1"] = "Over and under absorption, split into its two causes"; p4["A1"].font = Font(bold=True, size=12)
    p4.column_dimensions["A"].width = 42; p4.column_dimensions["D"].width = 16
    rows = [
        ("Budgeted overhead",            f"=Inputs!D{AB['bud_oh']}", MONEY),
        ("Budgeted machine hours",       f"=Inputs!D{AB['bud_hrs']}", MONEY),
        ("Budgeted absorption rate",     "=D3/D4", RATE),
        ("Actual overhead incurred",     f"=Inputs!D{AB['act_oh']}", MONEY),
        ("Actual machine hours",         f"=Inputs!D{AB['act_hrs']}", MONEY),
        ("Overhead absorbed into product", "=D7*D5", MONEY),
        ("", "", MONEY),
        ("Expenditure variance  (budget - actual spend)", "=D3-D6", MONEY),
        ("Volume variance  (actual hrs - budget hrs) x rate", "=(D7-D4)*D5", MONEY),
        ("Total over / (under) absorbed", "=D10+D11", MONEY),
    ]
    for i, (label, formula, fmt) in enumerate(rows):
        R = 3 + i
        p4.cell(row=R, column=1, value=label)
        if formula:
            c = p4.cell(row=R, column=4, value=formula); c.number_format = fmt
            if R in (5, 10, 11, 12): c.font = BOLD
    p4.cell(row=13, column=1, value="Check: absorbed minus actual").font = Font(italic=True)
    p4.cell(row=13, column=4, value="=D8-D6").number_format = MONEY
    p4.cell(row=15, column=1,
            value="A negative total is under-absorbed: a charge to the P&L. "
                  "Expenditure is a spending problem. Volume is a capacity problem. "
                  "They are fixed by different people.")

    wb.save(path)
    return path


if __name__ == "__main__":
    import sys
    print(build(sys.argv[1] if len(sys.argv) > 1 else "product-profitability-model.xlsx"))
