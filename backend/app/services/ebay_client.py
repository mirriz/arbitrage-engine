import os
import requests
import base64
import statistics
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()
EBAY_APP_ID = os.getenv("EBAY_APP_ID")
EBAY_CERT_ID = os.getenv("EBAY_CERT_ID")
COMPSNIPER_API_KEY = os.getenv("COMPSNIPER_API_KEY")

def _is_mock_mode():
    """Returns True if there is no valid API key configured."""
    return (
        not EBAY_APP_ID or 
        not EBAY_CERT_ID or 
        "your_api_key" in EBAY_APP_ID.lower() or 
        EBAY_CERT_ID.strip() == ""
    )

def _generate_mock_listings(query: str, listing_type: str):
    """Generates profitable dummy data formatted exactly like eBay's legacy API response."""
    item_name = query if query else "Seiko Astron SBXY061"
    base_price = "700.00" if listing_type == "Auction" else "750.00"
    return [
        {
            "itemId": [f"MOCK_{listing_type.upper()}_01"],
            "title": [f"{item_name} - Excellent Condition ({listing_type})"],
            "viewItemURL": [f"https://www.ebay.co.uk/itm/mock-item-1"],
            "sellingStatus": [{"currentPrice": [{"__value__": base_price}]}]
        },
        {
            "itemId": [f"MOCK_{listing_type.upper()}_02"],
            "title": [f"{item_name} - Near Mint"],
            "viewItemURL": [f"https://www.ebay.co.uk/itm/mock-item-2"],
            "sellingStatus": [{"currentPrice": [{"__value__": str(float(base_price) + 25.50)}]}]
        }
    ]

# Global cache for the OAuth token so we don't request a new one on every search
_cached_token = None
_token_expiry = None

def _get_oauth_token():
    global _cached_token, _token_expiry
    
    # Return the cached token if it is still valid
    if _cached_token and _token_expiry and datetime.now() < _token_expiry:
        return _cached_token

    url = "https://api.ebay.com/identity/v1/oauth2/token"
    credentials = f"{EBAY_APP_ID}:{EBAY_CERT_ID}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope"
    }

    try:
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            token_data = response.json()
            _cached_token = token_data["access_token"]
            
            # Pad the expiration by 5 minutes (300 seconds) to be safe
            expires_in = int(token_data.get("expires_in", 7200)) - 300
            _token_expiry = datetime.now() + timedelta(seconds=expires_in)
            return _cached_token
        else:
            print(f"Failed to generate eBay OAuth Token - Status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"Exception during eBay Token generation: {e}")
        return None

def _map_to_legacy(browse_items):
    """
    Converts the modern Browse API JSON response back into the heavily nested 
    arrays used by the legacy Finding API, so we don't have to rewrite tasks.py.
    """
    legacy_items = []
    for item in browse_items:
        price = item.get("price", {}).get("value", "0.0")
        
        legacy_items.append({
            "itemId": [item.get("itemId", "UNKNOWN")],
            "title": [item.get("title", "No Title")],
            "viewItemURL": [item.get("itemWebUrl", "")],
            "sellingStatus": [{"currentPrice": [{"__value__": str(price)}]}]
        })
    return legacy_items

def search_buy_it_now(query: str):
    if _is_mock_mode():
        return _generate_mock_listings(query, "FixedPrice")

    token = _get_oauth_token()
    if not token:
        return []

    url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_GB"
    }
    params = {
        "q": query,
        "filter": "buyingOptions:{FIXED_PRICE}",
        "sort": "price",
        "limit": 10
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            items = data.get("itemSummaries", [])
            return _map_to_legacy(items)
        else:
            print(f"Error parsing eBay API (BIN) - Status {response.status_code}: {response.text}")
            return []
    except Exception as e:
        print(f"Exception during eBay BIN search: {e}")
        return []

def search_ending_soon_auctions(query: str):
    if _is_mock_mode():
        return _generate_mock_listings(query, "Auction")

    token = _get_oauth_token()
    if not token:
        return []

    url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_GB"
    }
    params = {
        "q": query,
        "filter": "buyingOptions:{AUCTION}",
        "sort": "-endingSoonest", # Modern API uses minus sign for sorting
        "limit": 10
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            items = data.get("itemSummaries", [])
            return _map_to_legacy(items)
        else:
            print(f"Error parsing eBay API (Auctions) - Status {response.status_code}: {response.text}")
            return []
    except Exception as e:
        print(f"Exception during eBay Auctions search: {e}")
        return []

def get_median_sold_price(query: str) -> float:
    if _is_mock_mode():
        return 1500.0  
        
    if not COMPSNIPER_API_KEY:
        print("Missing COMPSNIPER_API_KEY in environment variables.")
        return 0.0

    url = "https://api.compsniper.com/v1/scrape"
    headers = {
        "Authorization": f"Bearer {COMPSNIPER_API_KEY}"
    }
    params = {
        "keyword": query,
        "count": 50
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        if response.status_code != 200:
            print(f"CompSniper API Error - Status {response.status_code}: {response.text}")
            return 0.0
            
        data = response.json()
        return float(data.get("summary", {}).get("median", 0.0))
        
    except Exception as e:
        print(f"Failed to fetch sold data from CompSniper: {e}")
        return 0.0