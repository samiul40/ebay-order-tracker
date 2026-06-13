import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

EBAY_ENV = os.getenv("EBAY_ENV", "production")
CLIENT_ID = os.getenv("EBAY_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET", "")
RUNAME = os.getenv("EBAY_RUNAME", "")
REDIRECT_URI = os.getenv("EBAY_REDIRECT_URI", "http://localhost:8080")

API_BASE = {
    "production": "https://api.ebay.com",
    "sandbox": "https://api.sandbox.ebay.com",
}[EBAY_ENV]

AUTH_BASE = {
    "production": "https://auth.ebay.com",
    "sandbox": "https://auth.sandbox.ebay.com",
}[EBAY_ENV]

TOKEN_URL = f"{API_BASE}/identity/v1/oauth2/token"
AUTH_URL = f"{AUTH_BASE}/oauth2/authorize"
ORDERS_URL = f"{API_BASE}/sell/fulfillment/v1/order"
FINANCES_URL = f"{API_BASE}/sell/finances/v1/transaction"
SCOPE = "https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly https://api.ebay.com/oauth/api_scope/sell.finances"

CONFIG_DIR = Path(__file__).parent
PRODUCT_MAP_PATH = CONFIG_DIR / "product_map.json"
POSTAGE_COSTS_PATH = CONFIG_DIR / "postage_costs.json"
