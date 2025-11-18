"""
Time and date parsing utilities for Google Maps reviews.
Handles relative dates like "2 weeks ago" and converts them to datetime objects.
"""

import re
from datetime import datetime, timedelta
from typing import Optional


def parse_relative_date(relative_date: str, reference_date: Optional[str] = None) -> Optional[datetime]:
    """
    Parse relative date strings like "2 weeks ago", "3 months ago" to datetime.
    
    Args:
        relative_date: The relative date string (e.g., "2 weeks ago", "a month ago")
        reference_date: The reference datetime string to calculate from (ISO format)
                       If None, uses current datetime
    
    Returns:
        datetime object or None if parsing fails
    """
    if not relative_date:
        return None
    
    # Parse reference date or use now
    if reference_date:
        try:
            ref_dt = datetime.fromisoformat(reference_date)
        except (ValueError, TypeError):
            ref_dt = datetime.now()
    else:
        ref_dt = datetime.now()
    
    relative_date = relative_date.lower().strip()
    
    # Handle "just now" or "now"
    if relative_date in ["just now", "now", "today"]:
        return ref_dt
    
    # Handle "yesterday"
    if "yesterday" in relative_date:
        return ref_dt - timedelta(days=1)
    
    # Pattern for "X time_unit ago" (e.g., "2 weeks ago", "a month ago")
    patterns = [
        (r'(\d+)\s*second[s]?\s+ago', 'seconds'),
        (r'(\d+)\s*minute[s]?\s+ago', 'minutes'),
        (r'(\d+)\s*hour[s]?\s+ago', 'hours'),
        (r'(\d+)\s*day[s]?\s+ago', 'days'),
        (r'(\d+)\s*week[s]?\s+ago', 'weeks'),
        (r'(\d+)\s*month[s]?\s+ago', 'months'),
        (r'(\d+)\s*year[s]?\s+ago', 'years'),
    ]
    
    for pattern, unit in patterns:
        match = re.search(pattern, relative_date)
        if match:
            value = int(match.group(1))
            if unit == 'seconds':
                return ref_dt - timedelta(seconds=value)
            elif unit == 'minutes':
                return ref_dt - timedelta(minutes=value)
            elif unit == 'hours':
                return ref_dt - timedelta(hours=value)
            elif unit == 'days':
                return ref_dt - timedelta(days=value)
            elif unit == 'weeks':
                return ref_dt - timedelta(weeks=value)
            elif unit == 'months':
                # Approximate: 30 days per month
                return ref_dt - timedelta(days=value * 30)
            elif unit == 'years':
                # Approximate: 365 days per year
                return ref_dt - timedelta(days=value * 365)
    
    # Handle "a/an X ago" patterns (e.g., "a week ago", "an hour ago")
    single_patterns = [
        (r'an?\s+second\s+ago', timedelta(seconds=1)),
        (r'an?\s+minute\s+ago', timedelta(minutes=1)),
        (r'an?\s+hour\s+ago', timedelta(hours=1)),
        (r'an?\s+day\s+ago', timedelta(days=1)),
        (r'an?\s+week\s+ago', timedelta(weeks=1)),
        (r'an?\s+month\s+ago', timedelta(days=30)),
        (r'an?\s+year\s+ago', timedelta(days=365)),
    ]
    
    for pattern, delta in single_patterns:
        if re.search(pattern, relative_date):
            return ref_dt - delta
    
    # If we can't parse it, return None
    return None


def parse_datetime_str(date_str: str) -> Optional[datetime]:
    """
    Parse various datetime string formats to datetime object.
    
    Args:
        date_str: The datetime string to parse
    
    Returns:
        datetime object or None if parsing fails
    """
    if not date_str:
        return None
    
    # Common datetime formats
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # Try ISO format
    try:
        return datetime.fromisoformat(date_str)
    except (ValueError, TypeError):
        pass
    
    return None

