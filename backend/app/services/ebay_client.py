import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()
EBAY_APP_ID = os.getenv("EBAY_APP_ID")
EBAY_CERT_ID = os.getenv("EBAY_CERT_ID")

def _is_mock_mode():
    return not EBAY_APP_ID or "your_api_key" in EBAY_APP_ID.lower()

def _get_oauth_token():
    if not EBAY_APP_ID or not EBAY_CERT_ID:
        raise ValueError("Missing EBAY_APP_ID or EBAY_CERT_ID in environment.")
        
    creds = f"{EBAY_APP_ID}:{EBAY_CERT_ID}"
    encoded_creds = base64.b64encode(creds.encode()).decode()
    
    url = "https://api.ebay.com/identity/v1/oauth2/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded_creds}"
    }
    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope"
    }
    
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json().get("access_token")

def _map_to_legacy(summaries: list) -> list:
    """Adapts modern REST JSON back to the legacy Finding API structure for tasks.py"""
    legacy_items = []
    for item in summaries:
        # THE FIX: Check for 'price' (Buy It Now) OR 'currentBidPrice' (Auctions)
        price_obj = item.get("price") or item.get("currentBidPrice") or {}
        price_val = price_obj.get("value", "0")

        legacy_items.append({
            "itemId": [item.get("itemId", "")],
            "title": [item.get("title", "")],
            "viewItemURL": [item.get("itemWebUrl", "")],
            "sellingStatus": [{
                "currentPrice": [{
                    "__value__": price_val
                }]
            }]
        })
    return legacy_items

def search_buy_it_now(query: str, min_price: float = 0.0, max_price: float = None, category_id: str = None):
    if _is_mock_mode():
        return []
        
    # --- ADD THIS SANITIZATION ---
    min_price = float(min_price) if min_price is not None else 0.0
    max_price = float(max_price) if max_price is not None else None

    token = _get_oauth_token()
    url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_GB"
    }
    
    # Base filter for Buy It Now
    filter_str = "buyingOptions:{FIXED_PRICE}"
    
    if min_price > 0 and max_price:
        filter_str += f",price:[{min_price}..{max_price}],priceCurrency:GBP"
    elif min_price > 0:
        filter_str += f",price:[{min_price}..],priceCurrency:GBP"
    elif max_price:
        filter_str += f",price:[0..{max_price}],priceCurrency:GBP"
        
    params = {
        "q": query,
        "limit": 10,
        "sort": "price",
        "filter": filter_str
    }
    
    if category_id:
        params["category_ids"] = category_id
        
    response = requests.get(url, headers=headers, params=params).json()
    items = response.get("itemSummaries", [])
    return _map_to_legacy(items)


def search_ending_soon_auctions(query: str, min_price: float = 0.0, max_price: float = None, category_id: str = None):
    if _is_mock_mode():
        return []
        
    # --- ADD THIS SANITIZATION ---
    min_price = float(min_price) if min_price is not None else 0.0
    max_price = float(max_price) if max_price is not None else None

    token = _get_oauth_token()
    url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_GB"
    }
    
    # Base filter for Auctions
    filter_str = "buyingOptions:{FIXED_PRICE}"
    
    if min_price > 0 and max_price:
        filter_str += f",price:[{min_price}..{max_price}],priceCurrency:GBP"
    elif min_price > 0:
        filter_str += f",price:[{min_price}..],priceCurrency:GBP"
    elif max_price:
        filter_str += f",price:[0..{max_price}],priceCurrency:GBP"
        
    params = {
        "q": query,
        "limit": 10,
        "sort": "endingSoonest",
        "filter": filter_str
    }
    
    if category_id:
        params["category_ids"] = category_id
        
    response = requests.get(url, headers=headers, params=params).json()
    items = response.get("itemSummaries", [])
    return _map_to_legacy(items)

def get_median_sold_price(query: str) -> float:
    # Requires migration to third-party scraping API due to eBay Developer limits
    return 15000.0