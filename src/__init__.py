"""
Google Maps Reviews Scraper

A Python package for scraping Google Maps reviews using the listugcposts API
with browser emulation, proxy support, and async capabilities.

Example:
    Async usage:
    ```python
    import asyncio
    from google_maps_reviews import GoogleMapsReviewsScraper
    
    async def main():
        scraper = GoogleMapsReviewsScraper(
            proxy="http://user:pass@proxy:port"
        )
        reviews = await scraper.scrape_reviews(url)
        print(f"Scraped {len(reviews)} reviews")
    
    asyncio.run(main())
    ```
    
    Sync usage:
    ```python
    from google_maps_reviews import GoogleMapsReviewsScraperSync
    
    scraper = GoogleMapsReviewsScraperSync()
    reviews = scraper.scrape_reviews(url)
    print(f"Scraped {len(reviews)} reviews")
    ```
"""

from .scraper import GoogleMapsReviewsScraper, GoogleMapsReviewsScraperSync
from .parser import GoogleMapsResponseParser
from .emulation import BrowserEmulator
from .logger import setup_logger, get_logger

__version__ = "0.1.0"
__author__ = "Your Name"
__all__ = [
    "GoogleMapsReviewsScraper",
    "GoogleMapsReviewsScraperSync",
    "GoogleMapsResponseParser",
    "BrowserEmulator",
    "setup_logger",
    "get_logger",
]

