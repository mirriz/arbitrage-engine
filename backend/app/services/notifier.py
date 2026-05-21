# backend/app/services/notifier.py
import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def send_discord_alert(fb_title: str, fb_price: float, ebay_value: float, profit: float, url: str, search_term: str):
    """
    Sends a formatted Embed message to a Discord channel.
    """
    if not DISCORD_WEBHOOK_URL:
        return

    embed = {
        "title": "🚨 Profitable Arbitrage Found!",
        "description": f"Found a match for target: **{search_term}**",
        "color": 3066993, # A nice vibrant green
        "fields": [
            {"name": "Item Details", "value": fb_title, "inline": False},
            {"name": "Buy (Facebook)", "value": f"${fb_price:.2f}", "inline": True},
            {"name": "Sell (eBay)", "value": f"${ebay_value:.2f}", "inline": True},
            {"name": "Net Profit", "value": f"${profit:.2f}", "inline": True},
        ],
        "url": url,
        "footer": {"text": "Arbitrage Engine v1.0"}
    }

    data = {
        "username": "Arbitrage Bot",
        "embeds": [embed]
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=5)
        response.raise_for_status()
        logger.info(f"Discord alert sent successfully for '{fb_title}'")
    except Exception as e:
        logger.error(f"Failed to send Discord alert: {str(e)}")