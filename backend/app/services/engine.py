# engine.py
from app.db.models import SearchConfig

EBAY_FEE_PERCENTAGE = 0.1325
EBAY_FLAT_FEE = 0.30

def calculate_arbitrage_profit(fb_price: float, ebay_median: float, est_shipping: float) -> float:
    """
    Calculates the expected net profit after eBay fees and shipping.
    """
    ebay_fees = (ebay_median * EBAY_FEE_PERCENTAGE) + EBAY_FLAT_FEE
    expected_net_from_ebay = ebay_median - ebay_fees - est_shipping
    net_profit = expected_net_from_ebay - fb_price
    
    return round(net_profit, 2)

def evaluate_opportunity(fb_listing: dict, ebay_median: float, config: SearchConfig, est_shipping: float = 10.0) -> bool:
    """
    Evaluates if a specific listing meets the user's profit thresholds.
    fb_listing expects: {"price": float, "title": str, ...}
    """
    fb_price = fb_listing.get("price")
    
    # 1. Calculate raw profit
    profit = calculate_arbitrage_profit(fb_price, ebay_median, est_shipping)
    
    # 2. Check flat margin requirement
    if profit < config.min_profit_flat:
        return False
        
    # 3. Check percentage margin requirement
    # Percentage is calculated based on the initial investment (FB Price + Shipping)
    total_investment = fb_price + est_shipping
    if total_investment > 0:
        profit_percentage = (profit / total_investment) * 100
        if profit_percentage < config.min_profit_percentage:
            return False
            
    return True