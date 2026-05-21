# backend/app/services/scraper.py
import urllib.parse
import logging
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

def scrape_facebook_marketplace(search_term: str) -> list:
    """
    Uses Playwright to scrape Facebook Marketplace for a given search term.
    """
    encoded_query = urllib.parse.quote(search_term)
    url = f"https://www.facebook.com/marketplace/search/?query={encoded_query}"
    
    results = []
    
    # Start the Playwright context
    with sync_playwright() as p:
        # NOTE: For production, you will need to add a residential proxy here:
        # browser = p.chromium.launch(proxy={"server": "http://username:pass@proxy-server.com:port"})
        browser = p.chromium.launch(headless=True)
        
        # Spoof a standard user agent
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            logger.info(f"Navigating to FB Marketplace for: {search_term}")
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            
            # Wait for React to render the items
            page.wait_for_timeout(3000)
            
            # Scroll down to trigger lazy loading of the feed
            page.mouse.wheel(0, 1500)
            page.wait_for_timeout(2000)
            
            # Look for all anchor tags that link to a marketplace item
            listings = page.locator('a[href*="/marketplace/item/"]').all()
            
            for listing in listings[:15]:  # Limit to 15 to avoid processing clutter
                try:
                    link = listing.get_attribute("href")
                    if not link:
                        continue
                        
                    # Format the URL
                    full_url = f"https://www.facebook.com{link}" if link.startswith("/") else link
                        
                    # Extract the unique listing ID from the URL string
                    # e.g., /marketplace/item/123456789/ -> 123456789
                    item_id = link.split("/marketplace/item/")[1].split("/")[0]
                    
                    # Extract visible text. Playwright separates elements with newlines.
                    # Usually looks like: ["$500", "MacBook Pro", "Ships to you"]
                    text_content = listing.inner_text().split('\n')
                    
                    # Heuristic: Find the first string containing a dollar sign
                    price_str = next((t for t in text_content if '$' in t), None)
                    
                    # Heuristic: Find the first non-empty string that isn't the price
                    other_text = [t for t in text_content if t and '$' not in t and t.lower() != 'free']
                    title = other_text[0] if other_text else "Unknown Title"
                    
                    if price_str:
                        # Clean the price string (e.g., "$1,200" -> 1200.0)
                        clean_price = price_str.replace('$', '').replace(',', '').strip()
                        price = float(clean_price)
                        
                        results.append({
                            "fb_listing_id": item_id,
                            "title": title,
                            "price": price,
                            "url": full_url
                        })
                        
                except Exception as e:
                    logger.debug(f"Failed to parse an individual listing: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Playwright scraping failed: {e}")
        finally:
            browser.close()
            
    logger.info(f"Successfully scraped {len(results)} items from Facebook Marketplace.")
    return results