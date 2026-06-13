# eBay Order Tracker

Pulls weekly eBay orders via the Fulfillment API and outputs a ready-to-paste Excel file matching the Sales Order Google Sheet.

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. eBay Developer credentials
1. Go to https://developer.ebay.com and sign in with your seller account
2. Create an application → go to **User Tokens** → generate **Production** keys
3. You need the **Client ID** and **Client Secret**
4. The required OAuth scope is: `https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly`

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env and fill in your EBAY_CLIENT_ID and EBAY_CLIENT_SECRET
```

## Usage

```bash
# Last 7 days (default)
python fetch_orders.py

# Specific date range
python fetch_orders.py --from 2024-12-28 --to 2024-12-31

# Custom output filename
python fetch_orders.py --from 2025-01-01 --to 2025-01-07 --out january_week1.xlsx
```

The script outputs an `.xlsx` file with these columns (matching the Sales Order sheet):

`Date | Platform | Order ID | Multiple (?) | batch_id | Product | Quantity | Sale Price | Postage Cost | Handling Cost | Promo Cost | Refund (?) | Refund Amount | Replacement (?) | Replacement Cost | Returned (?)`

Columns left blank are auto-calculated by formulas in the sheet (Unit Cost, Category, Transaction Fee, Expenditure, Profit/Loss, Profit Margin).

## Configuring products

### `product_map.json`
Maps eBay listing titles to your internal product names and postage type:

```json
{
  "Black Shoe Protector - Size L": {
    "ebay_titles": ["Black Shoe Protector Large", "..."],
    "postage_type": "large"
  }
}
```

Add a new entry whenever you list a new product on eBay. The script uses fuzzy matching so minor title variations are handled automatically.

### `postage_costs.json`
Controls the Handling Cost per postage bag type. Update these when you buy new postage bags at a different price:

```json
{
  "small": 0.03,
  "large": 0.04
}
```

## Troubleshooting

- **`??? Product Name`** in the output — eBay title didn't match any entry in `product_map.json`. Add it to the file.
- **Auth errors** — double-check your `.env` credentials and that you're using Production keys (not Sandbox).
