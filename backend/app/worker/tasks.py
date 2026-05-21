from celery import shared_task
from app.db.database import SessionLocal
from app.db.models import SearchConfig, FoundOpportunity
from app.services.ebay_client import search_buy_it_now, search_ending_soon_auctions, get_median_sold_price
from app.services.engine import calculate_arbitrage_profit
from app.services.notifier import send_discord_alert

@shared_task(name="app.worker.tasks.run_arbitrage_pipeline")
def run_arbitrage_pipeline(config_id: int):
    db = SessionLocal()
    config = db.query(SearchConfig).filter(SearchConfig.id == config_id).first()
    if not config: return

    listings = search_buy_it_now(config.search_term) + search_ending_soon_auctions(config.search_term)
    ebay_median = get_median_sold_price(config.search_term)

    for item in listings:
        price = float(item["sellingStatus"][0]["currentPrice"][0]["__value__"])
        title = item["title"][0]
        url = item["viewItemURL"][0]
        item_id = item["itemId"][0]
        
        profit = calculate_arbitrage_profit(price, ebay_median, est_shipping=15.0)
        
        if profit >= config.min_profit_flat:
            opportunity = FoundOpportunity(
                config_id=config.id,
                fb_listing_id=item_id,
                fb_title=title,
                fb_price=price,
                fb_url=url,
                ebay_median_sold=ebay_median,
                calculated_profit=profit,
                status="New"
            )
            db.add(opportunity)
            db.commit()
            send_discord_alert(title, price, ebay_median, profit, url, config.search_term)
    
    db.close()

@shared_task(name="app.worker.tasks.run_all_configs")
def run_all_configs():
    db = SessionLocal()
    configs = db.query(SearchConfig).filter(SearchConfig.is_active == True).all()
    for config in configs:
        run_arbitrage_pipeline.delay(config.id)
    db.close()