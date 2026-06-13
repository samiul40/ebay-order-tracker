import base64
import sys

import requests

from config import CLIENT_ID, CLIENT_SECRET, SCOPE, TOKEN_URL


def get_app_token() -> str:
    if not CLIENT_ID or not CLIENT_SECRET:
        sys.exit(
            "ERROR: EBAY_CLIENT_ID and EBAY_CLIENT_SECRET "
            "must be set in .env\n"
            "Copy .env.example to .env and fill in your credentials."
        )
    raw = f"{CLIENT_ID}:{CLIENT_SECRET}".encode()
    credentials = base64.b64encode(raw).decode()
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
