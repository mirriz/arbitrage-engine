# backend/app/services/ebay_client.py
import os
import requests
import statistics
import logging
from dotenv import load_dotenv
load_dotenv()
logger = logging.getLogger(__name__)

EBAY_APP_ID = os.getenv("EBAY_APP_ID", "MISSING_APP_ID")

def get_median_sold_price(search_term: str, limit: int = 10) -> float:
    """
    Queries the eBay Finding API for recently sold items matching the search term.
    Calculates and returns the median sold price.
    """
    url = "https://svcs.ebay.com/services/search/FindingService/v1"
    
    headers = {
        "X-EBAY-SOA-SECURITY-APPNAME": EBAY_APP_ID,
        "X-EBAY-SOA-OPERATION-NAME": "findCompletedItems",
        "X-EBAY-SOA-RESPONSE-DATA-FORMAT": "JSON",
        "X-EBAY-SOA-GLOBAL-ID": "EBAY-US", # The US marketplace
    }
    
    params = {
        "keywords": search_term,
        "itemFilter(0).name": "SoldItemsOnly",
        "itemFilter(0).value": "true",
        "itemFilter(1).name": "Condition",
        "itemFilter(1).value": "Used", 
        "paginationInput.entriesPerPage": limit,
        "sortOrder": "EndTimeSoonest"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Drill down into eBay's nested response structure
        items = data.get("findCompletedItemsResponse", [{}])[0].get("searchResult", [{}])[0].get("item", [])
        
        if not items:
            logger.warning(f"No sold items found on eBay for: {search_term}")
            return 0.0
            
        prices = []
        for item in items:
            selling_status = item.get("sellingStatus", [{}])[0]
            price_info = selling_status.get("currentPrice", [{}])[0]
            price_value = price_info.get("__value__")
            
            if price_value:
                prices.append(float(price_value))
                
        if not prices:
            return 0.0
            
        median_price = statistics.median(prices)
        logger.info(f"Calculated eBay median for '{search_term}': ${median_price:.2f} from {len(prices)} items.")
        
        return round(median_price, 2)
        
    except Exception as e:
        logger.error(f"eBay API error for '{search_term}': {str(e)}")
        return 0.0 # Return 0.0 so the engine gracefully skips arbitrage eval