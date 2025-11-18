import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional

from .time_utils import parse_relative_date
from .logger import get_logger


class GoogleMapsResponseParser:
    """Parser for Google Maps API responses."""

    def __init__(self):
        """Initialize the parser with logger."""
        self.logger = get_logger()

    def parse_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse the API response text to JSON.
        
        Args:
            response_text: Raw response text from the API
            
        Returns:
            Parsed JSON data or None if parsing fails
        """
        # Remove security prefix
        if response_text.startswith(")]}'"):
            response_text = response_text[4:]
        
        try:
            data = json.loads(response_text)
            return data
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parse error: {str(e)[:100]}")
            return None
    
    def extract_pagination_token(self, data: Dict[str, Any]) -> str:
        """
        Extract the pagination token from API response.
        
        Args:
            data: Parsed API response data
            
        Returns:
            Pagination token string or empty string if not found
        """
        if len(data) > 1 and data[1]:
            return str(data[1])
        return ""
    
    def extract_reviews(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract all reviews from API response data.
        
        Args:
            data: Parsed API response data
            
        Returns:
            List of review dictionaries
        """
        reviews = []
        
        # Extract reviews (usually at index 2)
        if len(data) > 2 and data[2]:
            reviews_array = data[2]
            
            if isinstance(reviews_array, list):
                for review_item in reviews_array:
                    if isinstance(review_item, list) and len(review_item) > 0:
                        # review_item[0] contains the actual review data
                        review_data = self.extract_review_data(review_item[0])
                        reviews.append(review_data)
        
        return reviews
    
    def extract_review_data(self, review_array: List[Any]) -> Dict[str, Any]:
        """
        Extract review data from the nested array structure.
        
        Structure discovered from API:
        review_array[0] = Review ID string
        review_array[1] = User and metadata
            [1][2] = Review timestamp (Unix timestamp in microseconds)
            [1][4][5] = User info array (name, photo, URL)
            [1][6] = Relative date
        review_array[2] = Review content
            [2][0] = [rating]
            [2][14] = ['language']
            [2][15] = [[text, None, [start, end]]]
        review_array[3] = Response data (if exists)
            [3][1] = Response timestamp (Unix timestamp in microseconds)
            [3][3] = Response relative date
            [3][14] = [[response_text, None, [start, end]]]
            
        Args:
            review_array: The nested array containing review data
            
        Returns:
            Dictionary containing extracted review information
        """
        result = {
            "review_id": "",
            "user_name": "",
            "user_url": "",
            "user_reviews": 0,
            "rating": 0.0,
            "relative_date": "",
            "text": "",
            "text_date": None,
            "translated_text": "",
            "likes": 0,
            "response_text": "",
            "response_relative_date": "",
            "response_text_date": None,
            "translated_response_text": "",
            "retrieval_date": str(datetime.now()),
        }
        
        try:
            if not review_array or len(review_array) < 2:
                return result
            
            # Extract Review ID (index 0)
            if len(review_array) > 0 and review_array[0]:
                result["review_id"] = str(review_array[0])
            
            # Extract User and Metadata (index 1)
            if len(review_array) > 1 and isinstance(review_array[1], list):
                metadata = review_array[1]
                
                # Extract review timestamp from metadata[2] (Unix timestamp in microseconds)
                if len(metadata) > 2 and metadata[2]:
                    try:
                        timestamp = int(metadata[2])
                        # Convert microseconds to seconds for datetime
                        timestamp_seconds = timestamp / 1000000
                        review_datetime = datetime.fromtimestamp(timestamp_seconds)
                        result["text_date"] = review_datetime.isoformat()
                    except (ValueError, TypeError, OSError) as e:
                        pass
                
                # User information at metadata[4][5]
                if (
                    len(metadata) > 4
                    and isinstance(metadata[4], list)
                    and len(metadata[4]) > 5
                ):
                    user_info = metadata[4][5]
                    if isinstance(user_info, list):
                        # User name (index 0)
                        if len(user_info) > 0 and user_info[0]:
                            result["user_name"] = str(user_info[0])
                        # User profile URL (index 2, nested)
                        if (
                            len(user_info) > 2
                            and isinstance(user_info[2], list)
                            and len(user_info[2]) > 0
                        ):
                            result["user_url"] = str(user_info[2][0])
                        # User reviews count (index 10, nested in array)
                        if (
                            len(user_info) > 10
                            and isinstance(user_info[10], list)
                            and len(user_info[10]) > 0
                        ):
                            reviews_text = str(user_info[10][0])
                            match = re.search(r"(\d+)", reviews_text)
                            if match:
                                result["user_reviews"] = int(match.group(1))
                
                # Relative date at metadata[6]
                if len(metadata) > 6 and metadata[6]:
                    result["relative_date"] = str(metadata[6])
            
            # Extract Review Content (index 2)
            if len(review_array) > 2 and isinstance(review_array[2], list):
                content = review_array[2]
                
                # Rating at content[0] as [rating]
                if (
                    len(content) > 0
                    and isinstance(content[0], list)
                    and len(content[0]) > 0
                ):
                    if isinstance(content[0][0], (int, float)):
                        result["rating"] = float(content[0][0])
                
                # Review text at content[15] as [[text, None, [start, end]]]
                if (
                    len(content) > 15
                    and isinstance(content[15], list)
                    and len(content[15]) > 0
                ):
                    text_container = content[15][0]
                    if isinstance(text_container, list) and len(text_container) > 0:
                        if isinstance(text_container[0], str):
                            result["text"] = text_container[0]
            
            # Extract Response Data (index 3)
            if len(review_array) > 3 and isinstance(review_array[3], list):
                response_data = review_array[3]
                
                # Extract response timestamp from response_data[1] (Unix timestamp in microseconds)
                if len(response_data) > 1 and response_data[1]:
                    try:
                        timestamp = int(response_data[1])
                        # Convert microseconds to seconds for datetime
                        timestamp_seconds = timestamp / 1000000
                        response_datetime = datetime.fromtimestamp(timestamp_seconds)
                        result["response_text_date"] = response_datetime.isoformat()
                    except (ValueError, TypeError, OSError) as e:
                        pass
                
                # Response date at response_data[3]
                if len(response_data) > 3 and response_data[3]:
                    result["response_relative_date"] = str(response_data[3])
                
                # Response text at response_data[14] as [[text, None, [start, end]]]
                if (
                    len(response_data) > 14
                    and isinstance(response_data[14], list)
                    and len(response_data[14]) > 0
                ):
                    response_container = response_data[14][0]
                    if (
                        isinstance(response_container, list)
                        and len(response_container) > 0
                    ):
                        if isinstance(response_container[0], str):
                            result["response_text"] = response_container[0]
            
            # Parse relative dates as fallback (if timestamp wasn't available)
            # Only parse relative date if we don't already have text_date from timestamp
            if result["relative_date"] and not result["text_date"]:
                try:
                    parsed_date = parse_relative_date(
                        result["relative_date"], result["retrieval_date"]
                    )
                    if parsed_date:
                        result["text_date"] = parsed_date.isoformat()
                except Exception:
                    pass

            # Only parse relative response date if we don't already have response_text_date from timestamp
            if result["response_relative_date"] and not result["response_text_date"]:
                try:
                    parsed_date = parse_relative_date(
                        result["response_relative_date"], result["retrieval_date"]
                    )
                    if parsed_date:
                        result["response_text_date"] = parsed_date.isoformat()
                except Exception:
                    pass

        except Exception:
            pass
        
        return result

