from openpyxl import Workbook

COLUMNS = [
    "Date",
    "Platform",
    "Order ID",
    "Multiple (?)",
    "batch_id",
    "Product",
    "Quantity",
    "Sale Price",
    "Postage Cost",
    "Handling Cost",
    "Promo Cost",
    "Refund (?)",
    "Refund Amount",
    "Replacement (?)",
    "Replacement Cost",
    "Returned (?)",
]


def write_excel(rows: list[dict], output_path: str):
    wb = Workbook()
    ws = wb.active
    ws.title = "eBay Orders"

    ws.append(COLUMNS)

    for row in rows:
        ws.append([row.get(col, "") for col in COLUMNS])

    wb.save(output_path)
    print(f"Saved {len(rows)} rows → {output_path}")
