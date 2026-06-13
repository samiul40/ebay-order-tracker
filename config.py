import os
from pathlib import Path

from dotenv import load_dotenv

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
