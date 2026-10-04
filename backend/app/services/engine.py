from app.db.models import SearchConfig

EBAY_FEE_PERCENTAGE = 0.00
EBAY_FLAT_FEE = 0.30

def calculate_arbitrage_profit(listing_price: float, ebay_median: float, est_shipping: float) -> float:
    """
    Calculates the expected net profit after eBay fees and shipping.
    """
    ebay_fees = EBAY_FLAT_FEE
    expected_net_from_ebay = ebay_median - ebay_fees - est_shipping
    net_profit = expected_net_from_ebay - listing_price
    
    return round(net_profit, 2)

def evaluate_opportunity(ebay_listing: dict, ebay_median: float, config: SearchConfig, est_shipping: float = 5.0) -> bool:
    """
    Evaluates if an active eBay listing meets the user's profit thresholds compared to eBay sold items.
    """
    if ebay_median <= 0:
        return False
        
    try:
        price_str = ebay_listing.get("sellingStatus", [{}])[0].get("currentPrice", [{}])[0].get("__value__", "0")
        listing_price = float(price_str)
    except (ValueError, IndexError, TypeError):
        return False
        
    if listing_price <= 0:
        return False
        
    # NEW CHECK: Min Item Price Filter to exclude cheap accessories/straps
    if listing_price < config.min_item_price:
        return False

    print(listing_price, ebay_median, est_shipping)
    profit = calculate_arbitrage_profit(listing_price, ebay_median, est_shipping)
    
    if profit < config.min_profit_flat:
        return False
        
    total_investment = listing_price + est_shipping
    if total_investment > 0:
        profit_percentage = (profit / total_investment) * 100
        if profit_percentage < config.min_profit_percentage:
            return False
            
    return True