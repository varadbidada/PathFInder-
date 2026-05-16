import openpyxl
from pathlib import Path

EXCEL_DIR = Path(__file__).parent.parent.parent / "JEE and NEET csv files"

for year, filename in [("2022", "2022Round6.xlsx"), ("2023", "2023Round6.xlsx"), ("2024", "2024Round5.xlsx")]:
    filepath = EXCEL_DIR / filename
    wb = openpyxl.load_workbook(filepath, read_only=True)
    ws = wb.active
    rows = list(ws.rows)
    
    for row in rows[1:500]:
        if (row[2].value and 'Bombay' in str(row[2].value) and 
            'Computer Science and Engineering (4 Years' in str(row[3].value) and 
            row[5].value == 'OPEN' and row[6].value == 'Gender-Neutral'):
            print(f"{year}: {row[3].value} | Close: {row[8].value}")
