"""
URL cache/tracker to prevent re-visiting websites across runs.
"""

import json
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from loguru import logger


@dataclass
class VisitedURL:
    """Data class for storing information about a visited URL."""
    url: str
    first_visited: str  # ISO format timestamp
    last_visited: str  # ISO format timestamp
    visit_count: int
    success: bool
    emails_found: int
    error: Optional[str] = None


class URLCache:
    """
    Cache for tracking visited URLs to prevent redundant scraping.

    Stores visited URLs in a JSON file with metadata including:
    - When the URL was first/last visited
    - Whether the scrape was successful
    - How many emails were found
    - Any errors encountered
    """

    def __init__(self, cache_file: str = "storage/visited_urls.json"):
        """
        Initialize the URL cache.

        Args:
            cache_file: Path to the cache file
        """
        self.cache_file = Path(cache_file)
        self.cache: Dict[str, VisitedURL] = {}
        self._ensure_cache_dir()
        self.load()

    def _ensure_cache_dir(self):
        """Ensure the cache directory exists."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        """Load the cache from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    self.cache = {
                        url: VisitedURL(**visited_data)
                        for url, visited_data in data.items()
                    }
                logger.debug(f"Loaded {len(self.cache)} URLs from cache")
            except Exception as e:
                logger.error(f"Error loading cache: {e}")
                self.cache = {}
        else:
            logger.debug("No cache file found, starting fresh")
            self.cache = {}

    def save(self):
        """Save the cache to disk."""
        try:
            data = {
                url: asdict(visited)
                for url, visited in self.cache.items()
            }
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved {len(self.cache)} URLs to cache")
        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    def is_visited(self, url: str) -> bool:
        """
        Check if a URL has been visited.

        Args:
            url: URL to check

        Returns:
            True if URL has been visited, False otherwise
        """
        return self._normalize_url(url) in self.cache

    def mark_visited(
        self,
        url: str,
        success: bool = True,
        emails_found: int = 0,
        error: Optional[str] = None
    ):
        """
        Mark a URL as visited.

        Args:
            url: URL that was visited
            success: Whether the scrape was successful
            emails_found: Number of emails found
            error: Error message if scrape failed
        """
        normalized_url = self._normalize_url(url)
        now = datetime.now().isoformat()

        if normalized_url in self.cache:
            # Update existing entry
            visited = self.cache[normalized_url]
            visited.last_visited = now
            visited.visit_count += 1
            visited.success = success
            visited.emails_found = emails_found
            visited.error = error
        else:
            # Create new entry
            self.cache[normalized_url] = VisitedURL(
                url=normalized_url,
                first_visited=now,
                last_visited=now,
                visit_count=1,
                success=success,
                emails_found=emails_found,
                error=error
            )

        self.save()
        logger.debug(f"Marked URL as visited: {normalized_url}")

    def get_info(self, url: str) -> Optional[VisitedURL]:
        """
        Get information about a visited URL.

        Args:
            url: URL to get info for

        Returns:
            VisitedURL object if found, None otherwise
        """
        return self.cache.get(self._normalize_url(url))

    def remove(self, url: str) -> bool:
        """
        Remove a URL from the cache.

        Args:
            url: URL to remove

        Returns:
            True if removed, False if not found
        """
        normalized_url = self._normalize_url(url)
        if normalized_url in self.cache:
            del self.cache[normalized_url]
            self.save()
            logger.info(f"Removed URL from cache: {normalized_url}")
            return True
        return False

    def clear(self):
        """Clear all URLs from the cache."""
        self.cache = {}
        self.save()
        logger.info("Cleared URL cache")

    def filter_unvisited(self, urls: List[str]) -> List[str]:
        """
        Filter a list of URLs to only include unvisited ones.

        Args:
            urls: List of URLs to filter

        Returns:
            List of URLs that haven't been visited
        """
        return [url for url in urls if not self.is_visited(url)]

    def get_all_visited(self) -> List[VisitedURL]:
        """
        Get all visited URLs.

        Returns:
            List of VisitedURL objects
        """
        return list(self.cache.values())

    def get_stats(self) -> Dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        successful = sum(1 for v in self.cache.values() if v.success)
        failed = sum(1 for v in self.cache.values() if not v.success)
        total_emails = sum(v.emails_found for v in self.cache.values())

        return {
            "total_urls": len(self.cache),
            "successful_scrapes": successful,
            "failed_scrapes": failed,
            "total_emails_found": total_emails,
            "cache_file": str(self.cache_file)
        }

    def get_successful_urls(self) -> List[str]:
        """
        Get list of successfully scraped URLs.

        Returns:
            List of URLs that were successfully scraped
        """
        return [url for url, visited in self.cache.items() if visited.success]

    def get_failed_urls(self) -> List[str]:
        """
        Get list of URLs that failed to scrape.

        Returns:
            List of URLs that failed
        """
        return [url for url, visited in self.cache.items() if not visited.success]

    def cleanup_old_entries(self, days: int = 30):
        """
        Remove entries older than specified days.

        Args:
            days: Number of days to keep entries for
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)
        old_urls = []

        for url, visited in self.cache.items():
            last_visited = datetime.fromisoformat(visited.last_visited)
            if last_visited < cutoff:
                old_urls.append(url)

        for url in old_urls:
            del self.cache[url]

        if old_urls:
            self.save()
            logger.info(f"Cleaned up {len(old_urls)} old entries from cache")

    def _normalize_url(self, url: str) -> str:
        """
        Normalize a URL for consistent comparison.

        Args:
            url: URL to normalize

        Returns:
            Normalized URL
        """
        from urllib.parse import urlparse, urlunparse

        # Parse and rebuild URL to normalize it
        parsed = urlparse(url)

        # Remove trailing slash from path
        path = parsed.path.rstrip('/')

        # Remove default ports
        netloc = parsed.netloc
        if parsed.scheme == 'https' and ':443' in netloc:
            netloc = netloc.replace(':443', '')
        elif parsed.scheme == 'http' and ':80' in netloc:
            netloc = netloc.replace(':80', '')

        # Rebuild URL without fragment
        normalized = urlunparse((
            parsed.scheme.lower(),
            netloc.lower(),
            path,
            parsed.params,
            parsed.query,
            ''  # No fragment
        ))

        return normalized

    def export_to_csv(self, output_file: str):
        """
        Export cache to CSV file.

        Args:
            output_file: Path to output CSV file
        """
        import csv

        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'url', 'first_visited', 'last_visited', 'visit_count',
                'success', 'emails_found', 'error'
            ])

            for visited in self.cache.values():
                writer.writerow([
                    visited.url,
                    visited.first_visited,
                    visited.last_visited,
                    visited.visit_count,
                    visited.success,
                    visited.emails_found,
                    visited.error or ''
                ])

        logger.info(f"Exported cache to {output_file}")


def main():
    """Example usage of URLCache."""
    cache = URLCache()

    # Check if URL is visited
    test_url = "https://example.com"

    if cache.is_visited(test_url):
        print(f"URL already visited: {test_url}")
        info = cache.get_info(test_url)
        print(f"  Last visited: {info.last_visited}")
        print(f"  Emails found: {info.emails_found}")
    else:
        print(f"URL not visited yet: {test_url}")

        # Mark as visited
        cache.mark_visited(test_url, success=True, emails_found=5)
        print(f"Marked as visited")

    # Get statistics
    stats = cache.get_stats()
    print(f"\nCache statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
