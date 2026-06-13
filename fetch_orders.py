#!/usr/bin/env python3
"""
fetch_orders.py — Pull eBay orders and output a ready-to-paste Excel file.

Usage:
    python fetch_orders.py
    python fetch_orders.py --from 2024-12-28 --to 2024-12-31
    python fetch_orders.py --from 2025-01-01 --to 2025-01-07 --out my_orders.xlsx
"""

import argparse
import base64
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
from openpyxl import Workbook
from rapidfuzz import process, fuzz

load_dotenv()

EBAY_ENV = os.getenv("EBAY_ENV", "production")
CLIENT_ID = os.getenv("EBAY_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET", "")

API_BASE = {
    "production": "https://api.ebay.com",
    "sandbox": "https://api.sandbox.ebay.com",
}[EBAY_ENV]

TOKEN_URL = f"{API_BASE}/identity/v1/oauth2/token"
ORDERS_URL = f"{API_BASE}/sell/fulfillment/v1/order"
SCOPE = "https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly"

CONFIG_DIR = Path(__file__).parent
PRODUCT_MAP_PATH = CONFIG_DIR / "product_map.json"
POSTAGE_COSTS_PATH = CONFIG_DIR / "postage_costs.json"


def get_app_token() -> str:
    if not CLIENT_ID or not CLIENT_SECRET:
        sys.exit(
            "ERROR: EBAY_CLIENT_ID and EBAY_CLIENT_SECRET must be set in .env\n"
            "Copy .env.example to .env and fill in your credentials."
        )
    credentials = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    resp = requests.post(
        TOKEN_URL,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "client_credentials", "scope": SCOPE},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def fetch_orders(token: str, from_date: str, to_date: str) -> list[dict]:
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    # eBay expects ISO 8601 UTC
    from_iso = f"{from_date}T00:00:00.000Z"
    to_iso = f"{to_date}T23:59:59.999Z"

    orders = []
    offset = 0
    limit = 200

    while True:
        params = {
            "filter": f"creationdate:[{from_iso}..{to_iso}]",
            "limit": limit,
            "offset": offset,
        }
        resp = requests.get(ORDERS_URL, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        page = data.get("orders", [])
        orders.extend(page)
        total = data.get("total", 0)
        offset += limit
        if offset >= total:
            break

    print(f"Fetched {len(orders)} orders from eBay ({from_date} to {to_date})")
    return orders


def load_product_map() -> dict:
    with open(PRODUCT_MAP_PATH) as f:
        return json.load(f)


def load_postage_costs() -> dict:
    with open(POSTAGE_COSTS_PATH) as f:
        return json.load(f)


def build_title_index(product_map: dict) -> dict[str, str]:
    """Returns {ebay_title_lower: internal_name}."""
    index = {}
    for internal_name, cfg in product_map.items():
        for title in cfg.get("ebay_titles", []):
            index[title.lower()] = internal_name
    return index


def map_product(ebay_title: str, title_index: dict, product_map: dict) -> tuple[str, str | None]:
    """Returns (internal_name, postage_type). internal_name is flagged if unknown."""
    lower = ebay_title.lower()

    # Exact match first
    if lower in title_index:
        internal = title_index[lower]
        return internal, product_map[internal]["postage_type"]

    # Fuzzy match (threshold 70)
    result = process.extractOne(lower, title_index.keys(), scorer=fuzz.WRatio, score_cutoff=70)
    if result:
        matched_key = result[0]
        internal = title_index[matched_key]
        print(f"  Fuzzy matched '{ebay_title}' → '{internal}' (score {result[1]:.0f})")
        return internal, product_map[internal]["postage_type"]

    print(f"  WARNING: No mapping found for '{ebay_title}' — flagging row")
    return f"??? {ebay_title}", None


def parse_amount(value) -> float:
    """Extract float from eBay amount object or plain value."""
    if isinstance(value, dict):
        return float(value.get("value", 0))
    return float(value or 0)


def parse_date(iso_str: str) -> str:
    """Convert eBay ISO timestamp to DD/MM/YYYY."""
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return dt.strftime("%d/%m/%Y")


def transform_orders(orders: list[dict], product_map: dict, postage_costs: dict) -> list[dict]:
    title_index = build_title_index(product_map)
    rows = []

    for order in orders:
        order_id = order.get("orderId", "")
        creation_date = parse_date(order.get("creationDate", ""))
        line_items = order.get("lineItems", [])
        is_multiple = len(line_items) > 1

        pricing = order.get("pricingSummary", {})
        delivery_cost = parse_amount(pricing.get("deliveryCost", 0))
        # Split postage evenly across line items
        postage_per_item = round(delivery_cost / len(line_items), 2) if line_items else 0

        # Promo / adjustment — eBay uses adjustments array
        adjustments = order.get("adjustments", [])
        promo_total = sum(parse_amount(a.get("amount", 0)) for a in adjustments if a.get("adjustmentType") == "PROMOTION")
        promo_per_item = round(promo_total / len(line_items), 2) if line_items else 0

        # Refund info
        payment_summary = order.get("paymentSummary", {})
        refunds = payment_summary.get("refunds", [])
        has_refund = len(refunds) > 0
        refund_amount = sum(parse_amount(r.get("amount", 0)) for r in refunds)

        for item in line_items:
            ebay_title = item.get("title", "")
            internal_name, postage_type = map_product(ebay_title, title_index, product_map)
            quantity = int(item.get("quantity", 1))

            line_total = parse_amount(item.get("lineItemCost", item.get("total", 0)))
            sale_price = round(line_total, 2)

            handling_cost = postage_costs.get(postage_type, 0) if postage_type else 0

            rows.append({
                "Date": creation_date,
                "Platform": "eBay",
                "Order ID": order_id,
                "Multiple (?)": "TRUE" if is_multiple else "FALSE",
                "batch_id": "",
                "Product": internal_name,
                "Quantity": quantity,
                "Sale Price": sale_price,
                "Postage Cost": postage_per_item,
                "Handling Cost": handling_cost,
                "Promo Cost": promo_per_item,
                "Refund (?)": "TRUE" if has_refund else "FALSE",
                "Refund Amount": round(refund_amount, 2) if has_refund else "",
                "Replacement (?)": "FALSE",
                "Replacement Cost": "",
                "Returned (?)": "FALSE",
            })

    return rows


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


def main():
    parser = argparse.ArgumentParser(description="Fetch eBay orders and export to Excel")
    today = datetime.now(timezone.utc).date()
    week_ago = today - timedelta(days=7)

    parser.add_argument("--from", dest="from_date", default=str(week_ago), help="Start date YYYY-MM-DD (default: 7 days ago)")
    parser.add_argument("--to", dest="to_date", default=str(today), help="End date YYYY-MM-DD (default: today)")
    parser.add_argument("--out", dest="output", default=f"ebay_orders_{today}.xlsx", help="Output filename")
    args = parser.parse_args()

    print(f"eBay Order Tracker — {args.from_date} to {args.to_date}")
    print(f"Environment: {EBAY_ENV}")

    token = get_app_token()
    orders = fetch_orders(token, args.from_date, args.to_date)

    if not orders:
        print("No orders found for this date range.")
        return

    product_map = load_product_map()
    postage_costs = load_postage_costs()

    rows = transform_orders(orders, product_map, postage_costs)
    write_excel(rows, args.output)


if __name__ == "__main__":
    main()
