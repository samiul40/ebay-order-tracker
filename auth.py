import base64
import json
import sys
import urllib.parse
import webbrowser
from pathlib import Path

import requests

from config import AUTH_URL, CLIENT_ID, CLIENT_SECRET, RUNAME, SCOPE, TOKEN_URL

TOKENS_FILE = Path(__file__).parent / ".tokens.json"


def _load_tokens() -> dict | None:
    if TOKENS_FILE.exists():
        return json.loads(TOKENS_FILE.read_text())
    return None


def _save_tokens(tokens: dict):
    TOKENS_FILE.write_text(json.dumps(tokens, indent=2))


def _basic_auth() -> str:
    return base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()


def _exchange_code(code: str) -> dict:
    resp = requests.post(
        TOKEN_URL,
        headers={
            "Authorization": f"Basic {_basic_auth()}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "authorization_code", "code": code, "redirect_uri": RUNAME},
    )
    resp.raise_for_status()
    return resp.json()


def _do_refresh(refresh_token: str) -> dict:
    resp = requests.post(
        TOKEN_URL,
        headers={
            "Authorization": f"Basic {_basic_auth()}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "refresh_token", "refresh_token": refresh_token, "scope": SCOPE},
    )
    resp.raise_for_status()
    return resp.json()


def _authorize() -> str:
    if not RUNAME:
        sys.exit(
            "ERROR: EBAY_RUNAME must be set in .env\n"
            "Add the RuName from developer.ebay.com/my/auth to your .env file."
        )

    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": RUNAME,
        "response_type": "code",
        "scope": SCOPE,
    }
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    print("\neBay authorization required.")
    print("Opening your browser — log in to eBay and click 'Agree and Continue'.")
    print(f"\nIf the browser doesn't open, visit:\n{auth_url}\n")
    webbrowser.open(auth_url)

    print("After granting access your browser will show a URL like:")
    print("  https://localhost:8080?code=v%5E1.1%23i%5E1...")
    print("Copy the FULL URL from the address bar and paste it below.\n")

    pasted = input("Paste the redirect URL (or just the code): ").strip()

    if "code=" in pasted:
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(pasted).query)
        code = urllib.parse.unquote(qs.get("code", [""])[0])
    else:
        code = pasted

    if not code:
        sys.exit("ERROR: Could not find authorization code. Please try again.")

    return code


def get_user_token() -> str:
    if not CLIENT_ID or not CLIENT_SECRET:
        sys.exit(
            "ERROR: EBAY_CLIENT_ID and EBAY_CLIENT_SECRET must be set in .env\n"
            "Copy .env.example to .env and fill in your credentials."
        )

    tokens = _load_tokens()

    if tokens and tokens.get("refresh_token"):
        try:
            new_tokens = _do_refresh(tokens["refresh_token"])
            _save_tokens({**tokens, **new_tokens})
            return new_tokens["access_token"]
        except requests.HTTPError:
            print("Refresh token expired, re-authorizing...")

    code = _authorize()
    tokens = _exchange_code(code)
    _save_tokens(tokens)
    return tokens["access_token"]
