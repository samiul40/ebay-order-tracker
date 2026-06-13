from datetime import datetime, timezone

import requests

from config import ORDERS_URL


def fetch_orders(token: str, from_date: str, to_date: str) -> list[dict]:
    """Fetch all eBay orders within an inclusive date range.

    Uses the eBay Fulfillment API.

    Paginates automatically until all orders are retrieved.

    Args:
        token: OAuth bearer token for the eBay API.
        from_date: Start date in YYYY-MM-DD format (inclusive, 00:00:00 UTC).
        to_date: End date in YYYY-MM-DD format (inclusive, 23:59:59 UTC).

    Returns:
        List of raw order dicts as returned by the eBay API.

    Raises:
        requests.HTTPError: If any paginated request returns a non-2xx status.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    # eBay expects ISO 8601 UTC; cap end time at now to avoid "future date" errors
    from_iso = f"{from_date}T00:00:00.000Z"
    end_of_day = datetime.fromisoformat(f"{to_date}T23:59:59+00:00")
    capped = min(end_of_day, datetime.now(timezone.utc))
    to_iso = capped.strftime("%Y-%m-%dT%H:%M:%S.000Z")

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
        if not resp.ok:
            print(f"API error {resp.status_code}: {resp.text}")
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
