# eBay Order Tracker

Pulls eBay orders via the Fulfillment API and outputs a CSV matching the Sales Order finance tracker.

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. eBay Developer credentials

1. Go to [developer.ebay.com](https://developer.ebay.com) and sign in with your seller account
2. Create an application (no hyphens in the name)
3. Apply for a **Marketplace Account Deletion exemption** (select "I do not persist eBay data")
4. Under **User Tokens → Your eBay Sign-in Settings**, add a redirect URL:
   - URL: `https://example.com`
   - Enable **OAuth**
   - Note the generated **RuName**
5. Copy your **App ID (Client ID)** and **Cert ID (Client Secret)** from the Application Keys page

### 3. Configure environment
```bash
cp .env.example .env
```

Edit `.env` and fill in:
```
EBAY_CLIENT_ID=your-app-id
EBAY_CLIENT_SECRET=your-cert-id
EBAY_RUNAME=your-runame
EBAY_ENV=production
```

### 4. First run — authorise the app

```bash
python fetch_orders.py
```

A browser will open asking you to log in to eBay and grant access. After clicking "Agree and Continue" you'll be redirected to `example.com` — copy the full URL from the address bar and paste it into the terminal prompt. This only happens once; the token is saved to `.tokens.json` for future runs.

## Usage

```bash
# Last 7 days (default)
python fetch_orders.py

# Specific date range
python fetch_orders.py --from 2026-06-01 --to 2026-06-13

# Custom output path
python fetch_orders.py --from 2026-06-01 --to 2026-06-13 --out output/june.csv
```

Output is saved to `output/ebay_orders_YYYY-MM-DD.csv`.

### Output columns

| Column | Source |
|---|---|
| Date | eBay API |
| Date (num) | Manual |
| Platform | Auto (eBay) |
| Order ID | eBay API |
| Multiple (?) | eBay API |
| Batch Helper | Manual |
| batch_id | Manual |
| Product | eBay API → product_map.json |
| Category | Manual |
| Quantity | eBay API |
| Sale Price | eBay API |
| Unit Cost | Manual |
| Postage Cost | eBay API |
| Handling Cost | postage_costs.json |
| Transaction Fee | eBay API (calculated) |
| Promo Cost | Manual (ad fee from eBay order page) |
| Refund (?) | eBay API |
| Refund Amount | eBay API |
| Replacement (?) | Manual |
| Replacement Cost | Manual |
| Returned (?) | Manual |
| Expenditure | Manual |
| Profit / Loss | Manual |
| Profit Margin | Manual |

## Configuring products

### `product_map.json`
Maps eBay listing titles (including variant) to your internal product names and postage type:

```json
{
  "Black Shoe Protector - Size L": {
    "ebay_titles": [
      "Shoe Shield Crease Trainer Protector[Black,L UK 7-12 / EU 41-46]"
    ],
    "postage_type": "Grey Plastic Mail Postage: 10\" - 14\""
  }
}
```

Add a new entry whenever you list a new product. If a title isn't matched, the row is flagged with `???` in the Product column.

### `postage_costs.json`
Handling cost (packaging material) per postage bag type. Update when bag prices change:

```json
{
  "Grey Plastic Mail Postage: 4\" - 6\"": 0.03,
  "Grey Plastic Mail Postage: 10\" - 14\"": 0.04
}
```

## Troubleshooting

- **`??? Product Name`** in the output — add the eBay title (with variant in brackets) to `product_map.json`
- **Auth errors** — delete `.tokens.json` and re-run to re-authorise
- **"dates in the future" error** — this is handled automatically; the end time is capped at now
