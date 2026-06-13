import json
from datetime import datetime

from config import POSTAGE_COSTS_PATH, PRODUCT_MAP_PATH


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


def map_product(
    ebay_title: str, title_index: dict, product_map: dict
) -> tuple[str, str | None]:
    """Returns (internal_name, postage_type).

    internal_name is flagged with '???' prefix if no mapping is found.
    """
    lower = ebay_title.lower()

    if lower in title_index:
        internal = title_index[lower]
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


def transform_orders(
    orders: list[dict],
    product_map: dict,
    postage_costs: dict,
    ad_fees: dict[str, float] | None = None,
) -> list[dict]:
    title_index = build_title_index(product_map)
    rows = []

    for order in orders:
        order_id = order.get("orderId", "")
        creation_date = parse_date(order.get("creationDate", ""))
        line_items = order.get("lineItems", [])
        # True when the order contains more than one distinct product
        is_multiple = len(line_items) > 1

        # Order-level costs split evenly across all line items
        pricing = order.get("pricingSummary", {})
        delivery_cost = parse_amount(pricing.get("deliveryCost", 0))
        order_total = parse_amount(pricing.get("total", 0))
        postage_per_item = (
            round(delivery_cost / len(line_items), 2) if line_items else 0
        )

        payment_summary = order.get("paymentSummary", {})
        total_due_seller = parse_amount(
            payment_summary.get("totalDueSeller", 0)
        )
        transaction_fee = round(order_total - total_due_seller, 2)
        transaction_fee_per_item = (
            round(transaction_fee / len(line_items), 2) if line_items else 0
        )

        ad_fee = (ad_fees or {}).get(order_id, 0)
        ad_fee_per_item = (
            round(ad_fee / len(line_items), 2) if line_items else 0
        )

        refunds = payment_summary.get("refunds", [])
        has_refund = len(refunds) > 0
        refund_amount = sum(
            parse_amount(r.get("amount", 0)) for r in refunds
        )

        for item in line_items:
            ebay_title = item.get("title", "")
            variation_aspects = item.get("variationAspects", [])
            if variation_aspects:
                variant_str = ",".join(v.get("value", "") for v in variation_aspects)
                ebay_title = f"{ebay_title}[{variant_str}]"
            # Map eBay title → internal product name and bag size
            internal_name, postage_type = map_product(
                ebay_title, title_index, product_map
            )
            quantity = int(item.get("quantity", 1))
            # lineItemCost is the total for this line (unit price × quantity)
            line_total = parse_amount(item.get("lineItemCost", item.get("total", 0)))
            sale_price = round(line_total, 2)
            # Bag cost split evenly; depends on product type so calculated per item
            handling_cost = (
                round(postage_costs.get(postage_type, 0) / len(line_items), 2)
                if postage_type
                else 0
            )

            components = product_map.get(internal_name, {}).get("components")
            if components:
                n = len(components)
                # Each unit gets an equal split; the last absorbs any rounding remainder so totals always match exactly.
                unit_sale = round(sale_price / n, 2)
                unit_postage = round(postage_per_item / n, 2)
                unit_handling = round(handling_cost / n, 2)
                unit_txn = round(transaction_fee_per_item / n, 2)
                unit_ad = round(ad_fee_per_item / n, 2)
                unit_refund = round(refund_amount / n, 2) if has_refund else None

                for i, component in enumerate(components):
                    is_last = i == n - 1
                    if is_last:
                        comp_sale = round(sale_price - unit_sale * (n - 1), 2)
                        comp_postage = round(postage_per_item - unit_postage * (n - 1), 2)
                        comp_handling = round(handling_cost - unit_handling * (n - 1), 2)
                        comp_txn = round(transaction_fee_per_item - unit_txn * (n - 1), 2)
                        comp_ad = round(ad_fee_per_item - unit_ad * (n - 1), 2)
                        comp_refund = round(refund_amount - unit_refund * (n - 1), 2) if has_refund else ""
                    else:
                        comp_sale = unit_sale
                        comp_postage = unit_postage
                        comp_handling = unit_handling
                        comp_txn = unit_txn
                        comp_ad = unit_ad
                        comp_refund = unit_refund if has_refund else ""

                    rows.append(
                        {
                            "Date": creation_date,
                            "Platform": "eBay",
                            "Order ID": order_id,
                            "Multiple (?)": "TRUE",
                            "batch_id": "",
                            "Product": component,
                            "Quantity": quantity,
                            "Sale Price": comp_sale,
                            "Postage Cost": comp_postage,
                            "Handling Cost": comp_handling,
                            "Transaction Fee": comp_txn,
                            "Promo Cost": comp_ad,
                            "Refund (?)": "TRUE" if has_refund else "FALSE",
                            "Refund Amount": comp_refund,
                            "Replacement (?)": "FALSE",
                            "Replacement Cost": "",
                            "Returned (?)": "FALSE",
                        }
                    )
            else:
                rows.append(
                    {
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
                        "Transaction Fee": transaction_fee_per_item,
                        "Promo Cost": ad_fee_per_item,
                        "Refund (?)": "TRUE" if has_refund else "FALSE",
                        "Refund Amount": (
                            round(refund_amount, 2) if has_refund else ""
                        ),
                        "Replacement (?)": "FALSE",
                        "Replacement Cost": "",
                        "Returned (?)": "FALSE",
                    }
                )

    return rows
