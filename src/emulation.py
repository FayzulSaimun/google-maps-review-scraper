"""
Browser emulation helpers for curl_cffi.
Provides utilities for rotating browser fingerprints to avoid detection.
"""

import random
from typing import List


class BrowserEmulator:
    """Handles browser emulation rotation for requests using curl_cffi impersonate."""
    
    # Available browser impersonations for curl_cffi (free version)
    # These match real browser TLS fingerprints
    # Source: https://curl-cffi.readthedocs.io/en/latest/
    IMPERSONATIONS = [
        # Latest Chrome versions (most recommended)
        "chrome136",
        "chrome136",
        "chrome133a",
        "chrome131",
        "chrome124",
        "chrome123",
        "chrome120",
        "chrome119",
        "chrome116",
        # Older Chrome versions
        "chrome110",
        "chrome107",
        "chrome104",
        "chrome101",
        "chrome100",
        "chrome99",
        # Chrome Android versions
        "chrome131_android",
        "chrome99_android",
        # Edge versions
        "edge101",
        "edge99",
        # Safari versions
        "safari15_5",
        "safari15_3",
    ]
    def __init__(self, impersonations: List[str] = None):
        """
        Initialize browser emulator.
        Args:
            impersonations: List of impersonation types to rotate through.
                           If None, uses default set of Chrome, Edge, Safari.
        """
        self.impersonations = impersonations if impersonations else self.IMPERSONATIONS.copy()
        self._index = 0
    
    def get_random(self) -> str:
        """
        Get a random browser impersonation.
        
        Returns:
            Random impersonation string
        """  # noqa: W293
        return random.choice(self.impersonations)
    
    def get_next(self) -> str:
        """
        Get the next browser impersonation in rotation.
        
        Returns:
            Next impersonation string in the rotation
        """
        impersonation = self.impersonations[self._index]
        self._index = (self._index + 1) % len(self.impersonations)
        return impersonation
    
    def reset(self):
        """Reset the rotation index to the beginning."""
        self._index = 0

