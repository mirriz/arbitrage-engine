import os
import requests
from dotenv import load_dotenv

load_dotenv()
EBAY_APP_ID = os.getenv("EBAY_APP_ID")

def search_buy_it_now(query: str):
    url = "https://svcs.ebay.com/services/search/FindingService/v1"
    params = {
        "OPERATION-NAME": "findItemsAdvanced",
        "SERVICE-VERSION": "1.0.0",
        "SECURITY-APPNAME": EBAY_APP_ID,
        "RESPONSE-DATA-FORMAT": "JSON",
        "keywords": query,
        "itemFilter(0).name": "ListingType",
        "itemFilter(0).value": "FixedPrice",
        "sortOrder": "PricePlusShippingLowest",
        "paginationInput.entriesPerPage": 5
    }
    response = requests.get(url, params=params).json()
    items = response.get("findItemsAdvancedResponse", [{}])[0].get("searchResult", [{}])[0].get("item", [])
    return items if isinstance(items, list) else []

def search_ending_soon_auctions(query: str):
    url = "https://svcs.ebay.com/services/search/FindingService/v1"
    params = {
        "OPERATION-NAME": "findItemsAdvanced",
        "SERVICE-VERSION": "1.0.0",
        "SECURITY-APPNAME": EBAY_APP_ID,
        "RESPONSE-DATA-FORMAT": "JSON",
        "keywords": query,
        "itemFilter(0).name": "ListingType",
        "itemFilter(0).value": "Auction",
        "sortOrder": "EndTimeSoonest",
        "paginationInput.entriesPerPage": 5
    }
    response = requests.get(url, params=params).json()
    items = response.get("findItemsAdvancedResponse", [{}])[0].get("searchResult", [{}])[0].get("item", [])
    return items if isinstance(items, list) else []

def get_median_sold_price(query: str):
    return 950.0  # Mock value