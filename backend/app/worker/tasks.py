# backend/app/worker/tasks.py
import time
import logging
import re
from app.worker.celery_app import celery_app
from app.db.database import SessionLocal
from app.db.models import SearchConfig, FoundOpportunity
from app.services.engine import evaluate_opportunity, calculate_arbitrage_profit
from app.services.ebay_client import get_median_sold_price
from app.services.scraper import scrape_facebook_marketplace
from app.services.notifier import send_discord_alert

logger = logging.getLogger(__name__)

def clean_title_for_ebay(fb_title: str) -> str:
    """
    Cleans a Facebook title to make it suitable for an eBay search.
    Removes special characters, emojis, and limits to the first 5 words
    so the query is specific, but not so specific that it returns 0 comps.
    """
    # Remove anything that isn't alphanumeric or space
    clean_str = re.sub(r'[^a-zA-Z0-9\s]', '', fb_title)
    words = clean_str.split()
    
    # Return up to the first 5 words
    return " ".join(words[:5])

@celery_app.task(name="tasks.run_arbitrage_pipeline")
def run_arbitrage_pipeline(config_id: int):
    """
    Background worker pipeline. 
    """
    db = SessionLocal()
    try:
        # 1. Fetch the user's search config
        config = db.query(SearchConfig).filter(SearchConfig.id == config_id, SearchConfig.is_active == True).first()
        if not config:
            logger.info(f"Config ID {config_id} not found or inactive. Aborting task.")
            return f"Config {config_id} unavailable."

        # 2. Fire the Playwright scraper
        listings = scrape_facebook_marketplace(config.search_term)
        
        if not listings:
            logger.warning(f"No listings found on Facebook for {config.search_term}")
            return "No Facebook data found."
        
        opportunities_found = 0
        
        for listing in listings:
            # Idempotency check: Have we processed this listing before?
            existing = db.query(FoundOpportunity).filter(FoundOpportunity.fb_listing_id == listing["fb_listing_id"]).first()
            if existing:
                continue # Skip duplicates
                
            # --- NEW DYNAMIC EBAY LOGIC ---
            # 3. Clean the FB title and get a 1-to-1 market value from eBay
            searchable_title = clean_title_for_ebay(listing["title"])
            logger.info(f"Checking eBay comps for specific item: '{searchable_title}'")
            
            ebay_median = get_median_sold_price(searchable_title)
            
            # Crucial: Sleep briefly to avoid triggering eBay API rate limits when iterating fast
            time.sleep(1) 
            
            if ebay_median == 0.0:
                logger.debug(f"Skipping '{searchable_title}' - no eBay market data found.")
                continue
                
            # 4. Evaluate the economics (Estimated shipping default: $15.00)
            is_profitable = evaluate_opportunity(listing, ebay_median, config, est_shipping=15.0)
            
            if is_profitable:
                profit = calculate_arbitrage_profit(listing["price"], ebay_median, est_shipping=15.0)
                
                # 5. Save opportunity to Database
                opportunity = FoundOpportunity(
                    config_id=config.id,
                    fb_listing_id=listing["fb_listing_id"],
                    fb_title=listing["title"], 
                    fb_price=listing["price"],
                    fb_url=listing["url"],
                    ebay_median_sold=ebay_median,
                    calculated_profit=profit,
                    status="New"
                )
                db.add(opportunity)
                
                # --- NEW: SEND INSTANT ALERT ---
                send_discord_alert(
                    fb_title=listing["title"],
                    fb_price=listing["price"],
                    ebay_value=ebay_median,
                    profit=profit,
                    url=listing["url"],
                    search_term=config.search_term
                )
                
                opportunities_found += 1
                
        db.commit()
        logger.info(f"Pipeline executed successfully for config {config_id}. Discovered {opportunities_found} target matches.")
        return f"Processed {len(listings)} items. Saved {opportunities_found} opportunities."
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in arbitrage pipeline: {str(e)}")
        raise e
    finally:
        db.close()