#!/usr/bin/env python3
"""
fetch_orders.py — Pull eBay orders and output a ready-to-paste Excel file.

Usage:
    python fetch_orders.py
    python fetch_orders.py --from 2024-12-28 --to 2024-12-31
    python fetch_orders.py --from 2025-01-01 --to 2025-01-07 --out my_orders.xlsx
"""

import argparse
from datetime import datetime, timedelta, timezone

from pathlib import Path

from api import fetch_orders
from auth import get_user_token
from config import EBAY_ENV
from excel import write_excel
from finances import fetch_ad_fees
from transform import load_postage_costs, load_product_map, transform_orders

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch eBay orders and export to Excel"
    )
    today = datetime.now(timezone.utc).date()
    week_ago = today - timedelta(days=7)

    parser.add_argument(
        "--from",
        dest="from_date",
        default=str(week_ago),
        help="Start date YYYY-MM-DD (default: 7 days ago)",
    )
    parser.add_argument(
        "--to",
        dest="to_date",
        default=str(today),
        help="End date YYYY-MM-DD (default: today)",
    )
    parser.add_argument(
        "--out",
        dest="output",
        default=str(OUTPUT_DIR / f"ebay_orders_{today}.csv"),
        help="Output filename",
    )
    args = parser.parse_args()

    print(f"eBay Order Tracker — {args.from_date} to {args.to_date}")
    print(f"Environment: {EBAY_ENV}")

    token = get_user_token()
    orders = fetch_orders(token, args.from_date, args.to_date)

    if not orders:
        print("No orders found for this date range.")
        return

    product_map = load_product_map()
    postage_costs = load_postage_costs()

    ad_fees = fetch_ad_fees(token, args.from_date, args.to_date)
    orders.sort(key=lambda o: o.get("creationDate", ""))
    rows = transform_orders(orders, product_map, postage_costs, ad_fees)
    write_excel(rows, args.output)


if __name__ == "__main__":
    main()
