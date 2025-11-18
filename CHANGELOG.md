# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2024-11-18

### Added
- Initial release of google-maps-reviews package
- Async scraper with rnet for browser emulation
- Synchronous wrapper for non-async codebases
- Random browser fingerprint rotation (Chrome, Firefox, Safari)
- Authenticated proxy support (HTTP/HTTPS/SOCKS5)
- JSON response parser with comprehensive field extraction
- Date parsing utilities for relative dates
- CLI interface with argparse
- Docker and docker-compose deployment configuration
- Comprehensive test suite with pytest
- GitHub Actions workflows for testing and publishing
- Examples for basic usage and CSV export
- Full documentation in README.md

### Features
- Scrape up to ~574 reviews (Google API limit)
- Extract review text, ratings, dates, user info, and responses
- Progress tracking with tqdm
- Automatic pagination handling
- Retry logic with configurable attempts
- Type hints throughout the codebase
- Support for Python 3.8+

### Dependencies
- rnet >= 3.0.0rc12 for browser emulation
- tqdm >= 4.66.0 for progress bars
- python-dotenv >= 1.0.0 for environment variables

[Unreleased]: https://github.com/yourusername/google-maps-review-scraper/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/google-maps-review-scraper/releases/tag/v0.1.0

