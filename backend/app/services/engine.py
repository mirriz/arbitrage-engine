from app.db.models import SearchConfig

EBAY_FEE_PERCENTAGE = 0.1325
EBAY_FLAT_FEE = 0.30

def calculate_arbitrage_profit(listing_price: float, ebay_median: float, est_shipping: float) -> float:
    """
    Calculates the expected net profit after eBay fees and shipping.
    """
    ebay_fees = (ebay_median * EBAY_FEE_PERCENTAGE) + EBAY_FLAT_FEE
    expected_net_from_ebay = ebay_median - ebay_fees - est_shipping
    net_profit = expected_net_from_ebay - listing_price
    
    return round(net_profit, 2)

def evaluate_opportunity(ebay_listing: dict, ebay_median: float, config: SearchConfig, est_shipping: float = 10.0) -> bool:
    """
    Evaluates if an active eBay listing meets the user's profit thresholds compared to eBay sold items.
    """
    # If we couldn't find comparable sold items to establish a median, reject
    if ebay_median <= 0:
        return False
        
    try:
        # Extract the current listing price from eBay's JSON payload
        price_str = ebay_listing.get("sellingStatus", [{}])[0].get("currentPrice", [{}])[0].get("__value__", "0")
        listing_price = float(price_str)
    except (ValueError, IndexError, TypeError):
        return False
        
    if listing_price <= 0:
        return False
        
    # 1. Calculate raw profit
    profit = calculate_arbitrage_profit(listing_price, ebay_median, est_shipping)
    
    # 2. Check flat margin requirement
    if profit < config.min_profit_flat:
        return False
        
    # 3. Check percentage margin requirement
    total_investment = listing_price + est_shipping
    if total_investment > 0:
        profit_percentage = (profit / total_investment) * 100
        if profit_percentage < config.min_profit_percentage:
            return False
            
    return True