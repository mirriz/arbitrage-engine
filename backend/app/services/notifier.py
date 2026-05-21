import os
import requests
from dotenv import load_dotenv

load_dotenv()
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def send_discord_alert(fb_title, fb_price, ebay_value, profit, url, search_term):
    if not DISCORD_WEBHOOK_URL: return
    
    embed = {
        "title": "🚨 Profitable Arbitrage Found!",
        "fields": [
            {"name": "Item", "value": fb_title},
            {"name": "Price", "value": f"£{fb_price:.2f}", "inline": True},
            {"name": "Profit", "value": f"£{profit:.2f}", "inline": True},
        ],
        "url": url,
        "color": 3066993
    }
    requests.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]})