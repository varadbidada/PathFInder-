import openpyxl
from pathlib import Path

EXCEL_DIR = Path(__file__).parent.parent.parent / "JEE and NEET csv files"
filepath = EXCEL_DIR / "2024Round5.xlsx"

wb = openpyxl.load_workbook(filepath, read_only=True)
ws = wb.active
rows = list(ws.rows)

institutes = set()
for row in rows[1:5000]:
    if row[2].value:
        name = str(row[2].value)
        if 'Trichy' in name or 'Tiruchirappalli' in name or 'Tiruchirapalli' in name:
            institutes.add(name)

print("Institutes with Trichy/Tiruchirappalli:")
for inst in sorted(institutes):
    print(f"  {inst}")
