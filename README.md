# Google Maps Reviews Scraper

A Python package for scraping Google Maps reviews without browser dependencies using curl_cffi.

## Features

- 🎭 Browser impersonation (Chrome 99-136, Edge, Safari, Chrome Android)
- 🔒 Proxy support with authentication
- ⚡ Async and sync interfaces
- 💾 Incremental saving (auto-saves during scraping)
- 📊 JSON and CSV output formats
- 🌍 UTF-8 encoding for all languages

## Installation

```bash
pip google-maps-reviews
```

## Usage
### Async Usage

```python
import asyncio
from google_maps_reviews import GoogleMapsReviewsScraper

async def main():
    scraper = GoogleMapsReviewsScraper(
        proxy="http://username:password@ip:port",  # Optional
        request_interval=0.5,
        random_impersonate=True
    )
    
    reviews = await scraper.scrape_reviews(
        url="https://www.google.com/maps/place/...",
        n_reviews=100,  # None for all available reviews
        hl="en",
        output_format="json",  # or "csv"
        output_file="reviews.json"
    )
    
    print(f"Scraped {len(reviews)} reviews")

asyncio.run(main())
```

### Sync Usage

```python
from google_maps_reviews import GoogleMapsReviewsScraperSync

scraper = GoogleMapsReviewsScraperSync(
    proxy="http://username:password@ip:port",  # Optional
    request_interval=0.5
)

reviews = scraper.scrape_reviews(
    url="https://www.google.com/maps/place/...",
    n_reviews=100,
    output_format="csv",
    output_file="reviews.csv"
)

print(f"Scraped {len(reviews)} reviews")
```

> **No Reviews Found**
> 1. You have to select the proper url from place page.
> 2. Go to the place page and click on the "Reviews" tab.
> 3. The url will be like this: `https://www.google.com/maps/place/.../reviews`
> 4. Copy the url and paste it in the code.

### Output Formats

**JSON Output:**
```python
reviews = scraper.scrape_reviews(
    url=url,
    output_format="json",
    output_file="reviews.json"
)
```

**CSV Output:**
```python
reviews = scraper.scrape_reviews(
    url=url,
    output_format="csv",
    output_file="reviews.csv"
)
```

### Proxy Configuration

```python
scraper = GoogleMapsReviewsScraper(
    proxy="http://username:password@ip:port"
)
```

Supported proxy types: HTTP, HTTPS, SOCKS5

## Review Data Structure

Each review contains:

```json
{
    "review_id": "unique_id",
    "user_name": "John Doe",
    "user_url": "https://...",
    "user_reviews": 42,
    "rating": 5.0,
    "relative_date": "2 weeks ago",
    "text": "Great place!",
    "text_date": "2024-01-15T10:30:00",
    "response_text": "Thank you!",
    "response_text_date": "2024-01-20T14:00:00",
    "retrieval_date": "2024-02-01T12:00:00"
}
```

## Important Notes

### Incremental Saving

Data is automatically saved to a temporary file during scraping in a `tmp` folder in your current working directory:
- **Location**: `./tmp/gmaps_reviews_temp_<feature_id>.<format>`
- **Auto-creation**: The `tmp` folder is automatically created on first run if it doesn't exist

If the script is interrupted, your data is safe in the temporary file and can be recovered from the `tmp` folder.

## Configuration Options

```python
scraper = GoogleMapsReviewsScraper(
    proxy="http://user:pass@ip:port",  # Proxy URL (optional)
    request_interval=0.5,               # Seconds between requests
    n_retries=10,                       # Retry attempts on failure
    retry_time=30,                      # Wait time before retry (seconds)
    random_impersonate=True,            # Random browser rotation
    log_level="INFO"                    # Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
)
```

### Logging Configuration

Control logging verbosity:

```python
# Minimal output (only errors)
scraper = GoogleMapsReviewsScraper(log_level="ERROR")

# Standard output (default)
scraper = GoogleMapsReviewsScraper(log_level="INFO")

# Detailed debugging
scraper = GoogleMapsReviewsScraper(log_level="DEBUG")

# Completely quiet (no progress bar, no logs)
reviews = scraper.scrape_reviews(url, verbose=False)
```

You can also customize the logger directly:

```python
from google_maps_reviews import setup_logger
import logging

# Setup custom logger
setup_logger(level=logging.WARNING, colored=True)

# Then use scraper
scraper = GoogleMapsReviewsScraper()
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Disclaimer

⚠️ **IMPORTANT - READ CAREFULLY**

This tool is provided for **educational and research purposes only**.

### Legal Notice

- This scraper is intended for learning about web scraping techniques and API interactions
- Users must comply with Google's Terms of Service and robots.txt
- Scraping may violate Google's Terms of Service
- Use at your own risk

### Ethical Guidelines

- **Respect Rate Limits**: Use reasonable request intervals (0.5-1 second minimum)
- **Don't Overload Servers**: Avoid excessive requests that could impact Google's services
- **Data Privacy**: Handle scraped data responsibly and respect user privacy
- **Commercial Use**: This tool should not be used for commercial purposes without proper authorization
- **Legal Compliance**: Ensure compliance with applicable laws and regulations in your jurisdiction

### No Warranty

This software is provided "as is", without warranty of any kind. The authors and contributors:
- Are not responsible for any misuse or damages caused by this tool
- Do not guarantee the accuracy or completeness of scraped data
- Do not guarantee the tool will work continuously (Google may change their API)
- Are not liable for any legal consequences resulting from use of this tool

### Use Responsibly

✅ **Acceptable Use:**
- Educational purposes and learning
- Research and academic studies
- Personal projects with limited scope
- Testing and development

❌ **Unacceptable Use:**
- Large-scale commercial data collection
- Violating Google's Terms of Service
- Excessive requests that impact Google's infrastructure
- Any illegal activities
- Selling or distributing scraped data without authorization

**By using this tool, you acknowledge that you have read, understood, and agree to this disclaimer. You accept full responsibility for your use of this tool and any consequences that may arise.**
---