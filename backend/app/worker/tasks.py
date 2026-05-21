# backend/app/worker/tasks.py
import time
import logging
from app.worker.celery_app import celery_app
from app.db.database import SessionLocal
from app.db.models import SearchConfig, FoundOpportunity
from app.services.engine import evaluate_opportunity, calculate_arbitrage_profit

logger = logging.getLogger(__name__)

# Mock Scraper Function (We will replace this with real scraping logic next)
def mock_fb_scraper(search_term: str):
    logger.info(f"Simulating Facebook Marketplace scrape for: {search_term}")
    time.sleep(2) # Simulate network lag
    
    # Simulating finding an underpriced item
    return [
        {
            "fb_listing_id": f"fb_mock_{int(time.time())}_1",
            "title": f"Excellent {search_term} - pristine condition",
            "price": 600.0,
            "url": "https://www.facebook.com/marketplace/item/mock123"
        }
    ]

# Mock eBay Valuation Function
def mock_ebay_valuation(search_term: str) -> float:
    logger.info(f"Simulating eBay sold listings search for: {search_term}")
    # Returning a realistic median resale price for calculation verification
    return 950.0

@celery_app.task(name="tasks.run_arbitrage_pipeline")
def run_arbitrage_pipeline(config_id: int):
    """
    Background worker pipeline. 
    1. Fetches configuration parameters.
    2. Scrapes the source marketplace.
    3. Cross-references against target market value.
    4. Evaluates margins and stores positive arbitrage matches.
    """
    db = SessionLocal()
    try:
        # 1. Fetch the user's search config
        config = db.query(SearchConfig).filter(SearchConfig.id == config_id, SearchConfig.is_active == True).first()
        if not config:
            logger.info(f"Config ID {config_id} not found or inactive. Aborting task.")
            return f"Config {config_id} unavailable."
        
        # 2. Fire the scraper
        listings = mock_fb_scraper(config.search_term)
        
        # 3. Get true market value from eBay
        ebay_median = mock_ebay_valuation(config.search_term)
        
        opportunities_found = 0
        
        for listing in listings:
            # Idempotency check: Have we processed this listing before?
            existing = db.query(FoundOpportunity).filter(FoundOpportunity.fb_listing_id == listing["fb_listing_id"]).first()
            if existing:
                continue # Skip duplicates
                
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