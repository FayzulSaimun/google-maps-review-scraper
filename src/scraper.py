import asyncio
import csv
import json
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal
from urllib.parse import quote

try:
    from curl_cffi.requests import AsyncSession
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False

from tqdm import tqdm

from .parser import GoogleMapsResponseParser
from .emulation import BrowserEmulator
from .logger import setup_logger, get_logger


class GoogleMapsReviewsScraper:
    """
    Async scraper for Google Maps reviews using curl_cffi with browser impersonation.
    """
    
    def __init__(
        self,
        proxy: Optional[str] = None,
        request_interval: float = 0.4,
        n_retries: int = 10,
        retry_time: float = 30,
        random_impersonate: bool = True,
        log_level: str = "INFO",
    ):
        """
        Initialize the Google Maps Reviews Scraper.

        Args:
            proxy: Proxy URL in format: http://username:password@ip:port
            request_interval: Time to wait between requests in seconds
            n_retries: Number of retries on request failure
            retry_time: Time to wait before retrying in seconds
            random_impersonate: If True, randomly select browser impersonation for each request
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        if not CURL_CFFI_AVAILABLE:
            raise ImportError(
                "curl_cffi is required for this scraper. Install with: pip install curl_cffi"
            )

        self.proxy = proxy
        self.request_interval = request_interval
        self.n_retries = n_retries
        self.retry_time = retry_time
        self.random_impersonate = random_impersonate
        self.base_url = "https://www.google.com/maps/rpc/listugcposts"
        self.emulator = BrowserEmulator()
        self.parser = GoogleMapsResponseParser()

        # Setup logger
        import logging
        level = getattr(logging, log_level.upper(), logging.INFO)
        self.logger = setup_logger(level=level)
    
    def _parse_url_to_feature_id(self, url: str) -> Optional[str]:
        """
        Extract feature ID from Google Maps URL.
        
        Args:
            url: Google Maps URL
            
        Returns:
            Feature ID string or None if not found
        """
        pattern = r"0[xX][0-9a-fA-F]+:0[xX][0-9a-fA-F]+"
        match = re.search(pattern, url)
        if match:
            return match.group(0)
        return None
    
    def _build_pb_parameter(
        self, feature_id: str, next_page_token: str = "", count: int = 10
    ) -> str:
        """
        Build the Protocol Buffer parameter for the API request.
        
        Args:
            feature_id: The place feature ID
            next_page_token: Pagination token
            count: Number of reviews per request
            
        Returns:
            Protocol Buffer parameter string
        """
        encoded_feature_id = quote(feature_id)
        
        # Build pb parameter based on observed browser behavior
        pb_param = (
            f"!1m6!1s{encoded_feature_id}"
            f"!6m4!4m1!1e1!4m1!1e3"
            f"!2m2!1i{count}!2s{next_page_token}"
            f"!5m2!1stest!7e81"
            f"!8m9!2b1!3b1!5b1!7b1!12m4!1b1!2b1!4m1!1e1"
            f"!11m4!1e3!2e1!6m1!1i2!13m1!1e1"
        )
        return pb_param
    
    async def _make_request(
        self, feature_id: str, next_page_token: str = "", hl: str = "en"
    ) -> str:
        """
        Make request to the Google Maps API.
        
        Args:
            feature_id: The place feature ID
            next_page_token: Pagination token
            hl: Language code
            
        Returns:
            Response text
        """
        pb_param = self._build_pb_parameter(feature_id, next_page_token, count=10)
        url = f"{self.base_url}?authuser=0&hl={hl}&gl=us&pb={pb_param}"
        
        headers = {
            "accept": "*/*",
            "accept-language": f"{hl}-US,{hl};q=0.9",
            "referer": "https://www.google.com/maps/",
        }
        
        # Get browser impersonation
        if self.random_impersonate:
            impersonate = self.emulator.get_random()
        else:
            impersonate = self.emulator.get_next()
        
        # Create session with impersonation and proxy
        async with AsyncSession(
            impersonate=impersonate,
            proxies={"http": self.proxy, "https": self.proxy} if self.proxy else None,
        ) as session:
            response = await session.get(url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
            
            return response.text
    
    def _save_to_temp(
        self, 
        reviews: List[Dict[str, Any]], 
        temp_file: Path,
        output_format: Literal["json", "csv"]
    ):
        """
        Save reviews to temporary file incrementally.
        
        Args:
            reviews: List of review dictionaries
            temp_file: Path to temporary file
            output_format: Output format (json or csv)
        """
        if output_format == "json":
            # Save as JSON with proper encoding
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(reviews, f, indent=2, ensure_ascii=False)
        elif output_format == "csv":
            # Save as CSV with proper encoding
            if reviews:
                fieldnames = [
                    "review_id", "user_name", "user_url", "user_reviews",
                    "rating", "relative_date", "text_date", "text",
                    "response_text", "response_relative_date", 
                    "response_text_date", "retrieval_date"
                ]
                
                with open(temp_file, "w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                    writer.writeheader()
                    writer.writerows(reviews)
    
    async def scrape_reviews(
        self, 
        url: str, 
        n_reviews: Optional[int] = None, 
        hl: str = "en", 
        verbose: bool = True,
        output_format: Literal["json", "csv"] = "json",
        output_file: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Scrape reviews from Google Maps using the async API.
        
        Args:
            url: Google Maps URL
            n_reviews: Number of reviews to scrape. If None, scrapes all available
                      reviews (typically ~574 reviews, which is Google's API limit).
            hl: Language code (default: "en")
            verbose: Show progress bar and status messages
            output_format: Output format - "json" or "csv" (default: "json")
            output_file: Optional output file path. If None, returns reviews only.
            
        Returns:
            List of review dictionaries with fields:
            - review_id: Unique review identifier
            - user_name: Reviewer's name
            - user_url: Link to user's profile
            - rating: Star rating (1-5)
            - relative_date: Date string (e.g., "2 weeks ago")
            - text: Review text content
            - response_text: Owner's response (if any)
            - and more...
            
        Example:
            # Scrape and save as JSON
            reviews = await scraper.scrape_reviews(
                url, n_reviews=100, output_format="json", output_file="reviews.json"
            )
            
            # Scrape and save as CSV
            reviews = await scraper.scrape_reviews(
                url, output_format="csv", output_file="reviews.csv"
            )
        """
        # Extract feature ID
        feature_id = self._parse_url_to_feature_id(url)
        if not feature_id:
            raise ValueError(f"Could not extract feature ID from URL: {url}")

        if verbose:
            self.logger.info(f"Starting scrape for feature: {feature_id}")
            if output_file:
                self.logger.info(f"Output: {output_file} ({output_format})")
            if n_reviews:
                self.logger.info(f"Target: {n_reviews} reviews")
        
        all_reviews = []
        next_page_token = ""
        page = 0
        
        # Create temporary file for incremental saving
        # Use tmp folder in current directory
        temp_dir = Path.cwd() / "tmp"
        temp_dir.mkdir(exist_ok=True)
        temp_file = temp_dir / f"gmaps_reviews_temp_{feature_id}.{output_format}"
        
        # Setup progress bar if verbose
        pbar = None
        if verbose:
            if n_reviews:
                pbar = tqdm(total=n_reviews, desc="Fetching reviews", unit=" reviews")
            else:
                pbar = tqdm(desc="Fetching reviews", unit=" reviews", total=0)
        
        try:
            # Continue fetching until we have enough reviews or reach the end
            while True:
                retries = self.n_retries
                while retries > 0:
                    try:
                        # Make request
                        response_text = await self._make_request(
                            feature_id, next_page_token, hl
                        )
                        
                        # Parse response
                        data = self.parser.parse_response(response_text)
                        
                        if not data or len(data) < 3:
                            if verbose:
                                if pbar is not None:
                                    pbar.close()
                                    print()  # Add newline after progress bar
                                self.logger.info(
                                    f"Completed: {len(all_reviews)} reviews (API limit reached)"
                                )
                            break
                        
                        # Extract pagination token
                        next_page_token = self.parser.extract_pagination_token(data)
                        
                        # Track reviews count before adding new ones
                        reviews_before = len(all_reviews)
                        
                        # Extract reviews
                        reviews = self.parser.extract_reviews(data)
                        all_reviews.extend(reviews)
                        
                        # Save to temporary file incrementally
                        self._save_to_temp(all_reviews, temp_file, output_format)
                        
                        # Update progress bar
                        if pbar is not None:
                            reviews_added = len(all_reviews) - reviews_before
                            pbar.update(reviews_added)
                        
                        # Break retry loop on success
                        break
                    
                    except Exception as e:
                        retries -= 1
                        if retries == 0:
                            if verbose:
                                if pbar is not None:
                                    pbar.close()
                                    print()  # Add newline after progress bar
                                self.logger.error(f"Failed after {self.n_retries} retries: {e}")
                            # Save what we have so far
                            if all_reviews and output_file:
                                self._save_final_output(all_reviews, output_file, output_format)
                                self.logger.info(f"Saved {len(all_reviews)} reviews before error")
                            raise
                        else:
                            if verbose:
                                if pbar is not None:
                                    pbar.write(f"⚠ Retry {self.n_retries - retries}/{self.n_retries}: {str(e)[:60]}...")
                                else:
                                    self.logger.warning(f"Retry {self.n_retries - retries}/{self.n_retries}: {str(e)[:60]}...")
                            await asyncio.sleep(self.retry_time)
                
                # Check if we've reached the target
                if n_reviews and len(all_reviews) >= n_reviews:
                    if verbose:
                        if pbar is not None:
                            pbar.close()
                            print()  # Add newline after progress bar
                        self.logger.info(f"Completed: {n_reviews} reviews (target reached)")
                    break

                # Check if there are more pages
                if not next_page_token:
                    if verbose:
                        if pbar is not None:
                            pbar.close()
                            print()  # Add newline after progress bar
                        self.logger.info(f"Completed: {len(all_reviews)} reviews")
                    break
                
                # Sleep between requests
                await asyncio.sleep(self.request_interval)
                page += 1
            
            # Close progress bar if still open
            if pbar is not None:
                pbar.close()
                if verbose:
                    print()  # Add newline after progress bar

            # Trim to requested number
            final_reviews = all_reviews[:n_reviews] if n_reviews else all_reviews

            # Save to final output file if specified
            if output_file:
                self._save_final_output(final_reviews, output_file, output_format)
                if verbose:
                    self.logger.info(f"✓ Saved {len(final_reviews)} reviews to {output_file}")

            # Clean up temp file
            if temp_file.exists():
                temp_file.unlink()

            return final_reviews

        except Exception as e:
            # On any error, temp file is already saved with latest data
            if verbose:
                self.logger.error(f"✗ Error occurred. Recovery file: {temp_file}")
                self.logger.info(f"Recoverable: {len(all_reviews)} reviews")
            raise
    
    def _save_final_output(
        self,
        reviews: List[Dict[str, Any]],
        output_file: str,
        output_format: Literal["json", "csv"]
    ):
        """
        Save final output to file.
        
        Args:
            reviews: List of review dictionaries
            output_file: Output file path
            output_format: Output format (json or csv)
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if output_format == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(reviews, f, indent=2, ensure_ascii=False)
        elif output_format == "csv":
            if reviews:
                fieldnames = [
                    "review_id", "user_name", "user_url", "user_reviews",
                    "rating", "relative_date", "text_date", "text",
                    "response_text", "response_relative_date",
                    "response_text_date", "retrieval_date"
                ]
                
                with open(output_path, "w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                    writer.writeheader()
                    writer.writerows(reviews)


class GoogleMapsReviewsScraperSync:
    """
    Synchronous wrapper for GoogleMapsReviewsScraper.
    Provides a blocking interface for non-async codebases.
    """
    
    def __init__(
        self,
        proxy: Optional[str] = None,
        request_interval: float = 0.4,
        n_retries: int = 10,
        retry_time: float = 30,
        random_impersonate: bool = True,
        log_level: str = "INFO",
    ):
        """
        Initialize the synchronous Google Maps Reviews Scraper.

        Args:
            proxy: Proxy URL in format: http://username:password@ip:port
            request_interval: Time to wait between requests in seconds
            n_retries: Number of retries on request failure
            retry_time: Time to wait before retrying in seconds
            random_impersonate: If True, randomly select browser impersonation
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self._scraper = GoogleMapsReviewsScraper(
            proxy=proxy,
            request_interval=request_interval,
            n_retries=n_retries,
            retry_time=retry_time,
            random_impersonate=random_impersonate,
            log_level=log_level,
        )
    
    def scrape_reviews(
        self,
        url: str,
        n_reviews: Optional[int] = None,
        hl: str = "en",
        verbose: bool = True,
        output_format: Literal["json", "csv"] = "json",
        output_file: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Scrape reviews from Google Maps (blocking call).
        Args:
            url: Google Maps URL
            n_reviews: Number of reviews to scrape. If None, scrapes all available
            hl: Language code (default: "en")
            verbose: Show progress bar and status messages
            output_format: Output format - "json" or "csv" (default: "json")
            output_file: Optional output file path

        Returns:
            List of review dictionaries
        """
        return asyncio.run(
            self._scraper.scrape_reviews(url, n_reviews, hl, verbose, output_format, output_file)
        )
