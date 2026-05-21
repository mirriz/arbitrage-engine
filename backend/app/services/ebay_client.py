import os
import requests
import statistics
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()
EBAY_APP_ID = os.getenv("EBAY_APP_ID")
EBAY_GLOBAL_ID = "EBAY-GB"  # Targets the UK marketplace

def _is_mock_mode():
    """Returns True if there is no valid API key configured."""
    return not EBAY_APP_ID or EBAY_APP_ID.strip() == "" or "your_api_key" in EBAY_APP_ID.lower()

def _generate_mock_listings(query: str, listing_type: str):
    """Generates profitable dummy data formatted exactly like eBay's API response."""
    # We default to a realistic JDM watch example if the query happens to be blank
    item_name = query if query else "Seiko Astron SBXY061"
    
    # Set prices artificially low so your engine.py calculates a high profit margin.
    # This ensures your minimum thresholds are met and your Discord alerts trigger.
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

def _get_headers(operation_name: str):
    """Helper to generate headers for the eBay Finding API."""
    return {
        "X-EBAY-SOA-GLOBAL-ID": EBAY_GLOBAL_ID,
        "X-EBAY-SOA-SECURITY-APPNAME": EBAY_APP_ID,
        "X-EBAY-SOA-OPERATION-NAME": operation_name,
        "X-EBAY-SOA-RESPONSE-DATA-FORMAT": "JSON",
    }

def search_buy_it_now(query: str):
    if _is_mock_mode():
        return _generate_mock_listings(query, "FixedPrice")

    url = "https://svcs.ebay.com/services/search/FindingService/v1"
    headers = _get_headers("findItemsAdvanced")
    
    params = {
        "REST-PAYLOAD": "true",
        "keywords": query,
        "itemFilter(0).name": "ListingType",
        "itemFilter(0).value": "FixedPrice",
        "sortOrder": "PricePlusShippingLowest",
        "paginationInput.entriesPerPage": 10
    }
    
    response = requests.get(url, headers=headers, params=params).json()
    items = response.get("findItemsAdvancedResponse", [{}])[0].get("searchResult", [{}])[0].get("item", [])
    return items if isinstance(items, list) else []

def search_ending_soon_auctions(query: str):
    if _is_mock_mode():
        return _generate_mock_listings(query, "Auction")

    url = "https://svcs.ebay.com/services/search/FindingService/v1"
    headers = _get_headers("findItemsAdvanced")
    
    end_time = (datetime.now(timezone.utc) + timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    
    params = {
        "REST-PAYLOAD": "true",
        "keywords": query,
        "itemFilter(0).name": "ListingType",
        "itemFilter(0).value": "Auction",
        "itemFilter(1).name": "EndTimeTo",
        "itemFilter(1).value": end_time,
        "sortOrder": "EndTimeSoonest",
        "paginationInput.entriesPerPage": 10
    }
    
    response = requests.get(url, headers=headers, params=params).json()
    items = response.get("findItemsAdvancedResponse", [{}])[0].get("searchResult", [{}])[0].get("item", [])
    return items if isinstance(items, list) else []

def get_median_sold_price(query: str) -> float:
    if _is_mock_mode():
        return 1500.0  # Artificially high to guarantee a positive arbitrage calculation during testing
        
    url = "https://svcs.ebay.com/services/search/FindingService/v1"
    headers = _get_headers("findCompletedItems") 
    
    params = {
        "REST-PAYLOAD": "true",
        "keywords": query,
        "itemFilter(0).name": "SoldItemsOnly",
        "itemFilter(0).value": "true",
        "sortOrder": "EndTimeSoonest",
        "paginationInput.entriesPerPage": 50 
    }
    
    response = requests.get(url, headers=headers, params=params).json()
    items = response.get("findCompletedItemsResponse", [{}])[0].get("searchResult", [{}])[0].get("item", [])
    
    if not items or not isinstance(items, list):
        return 0.0
        
    prices = []
    for item in items:
        try:
            price_str = item.get("sellingStatus", [{}])[0].get("currentPrice", [{}])[0].get("__value__", "0")
            price = float(price_str)
            if price > 0:
                prices.append(price)
        except (ValueError, IndexError, TypeError):
            continue
            
    return statistics.median(prices) if prices else 0.0