# backend/test_ebay.py
from app.services.ebay_client import search_buy_it_now, search_ending_soon_auctions, get_median_sold_price

def run_diagnostics():
    # Use a high-volume query to guarantee hits if the API is working
    test_query = "Seiko Astron"
    
    print(f"--- TESTING PIPELINE FOR: '{test_query}' ---")
    
    print("\n1. Testing Buy It Now...")
    bin_results = search_buy_it_now(test_query)
    print(f"Found {len(bin_results)} active listings.")
    if bin_results:
        print(f"Sample price: £{bin_results[0]['sellingStatus'][0]['currentPrice'][0]['__value__']}")
    print(bin_results)  # Print the buy it now results to verify the structure and content

    print("\n2. Testing Auctions Ending Soon...")
    auction_results = search_ending_soon_auctions(test_query)
    print(f"Found {len(auction_results)} auctions.")
    print(auction_results)  # Print the auction results to verify the structure and content
    
    #print("\n3. Testing Sold Median (with IQR filtering)...")
    #median_price = get_median_sold_price(test_query)
    #print(f"Calculated Median: £{median_price}")

if __name__ == "__main__":
    run_diagnostics()