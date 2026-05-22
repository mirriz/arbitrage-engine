# --- NEW: Add datetime imports at the very top of the file ---
from datetime import datetime, timedelta, timezone 
from celery import shared_task
from app.db.database import SessionLocal
from app.db.models import SearchConfig, FoundOpportunity
from app.services.ebay_client import search_buy_it_now, search_ending_soon_auctions
from app.services.engine import calculate_arbitrage_profit
from app.services.notifier import send_discord_alert

@shared_task(name="tasks.run_arbitrage_pipeline")
def run_arbitrage_pipeline(config_id: int):
    db = SessionLocal()
    
    try:
        config = db.query(SearchConfig).filter(SearchConfig.id == config_id).first()
        if not config: 
            return

        # 1. ESTABLISH THE MARKET FLOOR (Buy It Now)
        bin_listings = search_buy_it_now(
            query=config.search_term, 
            min_price=config.min_listing_price,
            max_price=config.max_listing_price,
            category_id=config.category_id
        )
        
        bin_prices = []
        for b in bin_listings:
            try:
                bin_prices.append(float(b["sellingStatus"][0]["currentPrice"][0]["__value__"]))
            except (KeyError, IndexError, ValueError):
                continue
                
        if not bin_prices:
            print(f"No active BIN market found for {config.search_term}. Skipping.")
            return
            
        bin_prices.sort()
        floor_sample = bin_prices[:3]
        market_floor_price = sum(floor_sample) / len(floor_sample)

        # 2. SCAN AUCTIONS ENDING SOON
        auction_listings = search_ending_soon_auctions(
            query=config.search_term, 
            min_price=config.min_listing_price,
            max_price=config.max_listing_price,
            category_id=config.category_id
        )

        # --- NEW: Define the time boundaries (Now vs 1 Hour from Now) ---
        now_utc = datetime.now(timezone.utc)
        one_hour_from_now = now_utc + timedelta(hours=1)

        # 3. EVALUATE MARGINS
        for item in auction_listings:
            try:
                current_bid = float(item["sellingStatus"][0]["currentPrice"][0]["__value__"])
                title = item["title"][0]
                url = item["viewItemURL"][0]
                item_id = item["itemId"][0]
                
                # --- NEW: Check the time remaining ---
                end_time_str = item.get("endTime", [""])[0]
                if not end_time_str:
                    continue # Skip if eBay didn't return a date
                
                # Convert eBay's ISO 8601 string to a Python datetime object
                end_time = datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))
                
                # If the auction ends more than 1 hour away, skip it immediately
                if end_time > one_hour_from_now:
                    continue

            except (KeyError, IndexError, ValueError):
                continue
            
            existing_opportunity = db.query(FoundOpportunity).filter(FoundOpportunity.fb_listing_id == item_id).first()
            if existing_opportunity:
                continue 
            
            profit = calculate_arbitrage_profit(current_bid, market_floor_price, est_shipping=15.0)
            
            if profit >= config.min_profit_flat:
                opportunity = FoundOpportunity(
                    config_id=config.id,
                    fb_listing_id=item_id,
                    fb_title=title,
                    fb_price=current_bid,
                    fb_url=url,
                    market_floor_price=market_floor_price,
                    calculated_profit=profit,
                    status="New"
                )
                db.add(opportunity)
                
                try:
                    db.commit()
                    send_discord_alert(title, current_bid, market_floor_price, profit, url, config.search_term)
                except Exception as e:
                    db.rollback()
                    print(f"Failed to save opportunity {item_id}: {e}")
                    
    finally:
        db.close()

@shared_task(name="tasks.run_all_configs")
def run_all_configs():
    db = SessionLocal()
    try:
        configs = db.query(SearchConfig).filter(SearchConfig.is_active == True).all()
        for config in configs:
            run_arbitrage_pipeline.delay(config.id)
    finally:
        db.close()