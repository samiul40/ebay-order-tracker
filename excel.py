import csv

COLUMNS = [
    "Date",
    "Date (num)",
    "Platform",
    "Order ID",
    "Multiple (?)",
    "Batch Helper",
    "batch_id",
    "Product",
    "Category",
    "Quantity",
    "Sale Price",
    "Unit Cost",
    "Postage Cost",
    "Handling Cost",
    "Transaction Fee",
    "Promo Cost",
    "Refund (?)",
    "Refund Amount",
    "Replacement (?)",
    "Replacement Cost",
    "Returned (?)",
    "Expenditure",
    "Profit / Loss",
    "Profit Margin",
]


def write_excel(rows: list[dict], output_path: str):
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=COLUMNS, extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} rows → {output_path}")
