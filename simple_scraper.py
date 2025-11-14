"""
Simple HTTP-based email scraper that works around SSL issues.
"""

import asyncio
import httpx
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse, urlencode
from bs4 import BeautifulSoup
import tldextract
from loguru import logger

from email_extractor import EmailExtractor, EmailData
from url_cache import URLCache


@dataclass
class ScrapedWebsite:
    """Data class for scraped website information."""
    url: str
    title: str
    emails: List[Dict]
    page_count: int
    success: bool
    error: Optional[str] = None


class SimpleEmailScraper:
    """Simple HTTP-based email scraper."""

    def __init__(
        self,
        max_pages_per_site: int = 50,
        max_depth: int = 3,
        timeout: int = 30,
        min_confidence: float = 0.7,
        url_cache: Optional[URLCache] = None,
        force_rescrape: bool = False
    ):
        """
        Initialize the email scraper.

        Args:
            max_pages_per_site: Maximum pages to crawl per website
            max_depth: Maximum crawl depth
            timeout: Request timeout in seconds
            min_confidence: Minimum email confidence score
            url_cache: URL cache instance to track visited websites
            force_rescrape: Force re-scraping of previously visited URLs
        """
        self.max_pages_per_site = max_pages_per_site
        self.max_depth = max_depth
        self.timeout = timeout
        self.force_rescrape = force_rescrape

        self.email_extractor = EmailExtractor(
            validate_dns=False,
            min_confidence=min_confidence
        )

        self.url_cache = url_cache if url_cache is not None else URLCache()
        self.visited_urls: Set[str] = set()
        self.emails_found: List[EmailData] = []
        self.current_domain: Optional[str] = None

    async def scrape_website(self, url: str) -> ScrapedWebsite:
        """
        Scrape a single website for emails.

        Args:
            url: Website URL to scrape

        Returns:
            ScrapedWebsite object with results
        """
        # Check cache first
        if not self.force_rescrape and self.url_cache.is_visited(url):
            cache_info = self.url_cache.get_info(url)
            logger.info(f"URL already visited (cached): {url}")
            logger.info(f"  Last visited: {cache_info.last_visited}")
            logger.info(f"  Emails found: {cache_info.emails_found}")
            logger.info(f"  Skipping... (use force_rescrape=True to re-scrape)")

            return ScrapedWebsite(
                url=url,
                title=self._get_domain(url),
                emails=[],
                page_count=0,
                success=cache_info.success,
                error="Skipped - already visited (cached)" if cache_info.success else cache_info.error
            )

        logger.info(f"Starting to scrape website: {url}")

        # Reset state for new website
        self.visited_urls.clear()
        self.emails_found.clear()
        self.current_domain = self._get_domain(url)

        try:
            # Create HTTP client with SSL verification disabled for this environment
            async with httpx.AsyncClient(
                verify=False,
                timeout=self.timeout,
                follow_redirects=True
            ) as client:
                # Start crawling from the base URL
                await self._crawl_page(client, url)

            # Deduplicate emails
            unique_emails = self.email_extractor.deduplicate(self.emails_found)

            logger.info(f"Scraping complete. Found {len(unique_emails)} unique emails from {len(self.visited_urls)} pages")

            # Mark URL as visited in cache
            self.url_cache.mark_visited(
                url=url,
                success=True,
                emails_found=len(unique_emails)
            )

            return ScrapedWebsite(
                url=url,
                title=self._get_domain(url),
                emails=[asdict(email) for email in unique_emails],
                page_count=len(self.visited_urls),
                success=True
            )

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")

            # Mark URL as visited with error
            self.url_cache.mark_visited(
                url=url,
                success=False,
                emails_found=0,
                error=str(e)
            )

            return ScrapedWebsite(
                url=url,
                title=self._get_domain(url),
                emails=[],
                page_count=0,
                success=False,
                error=str(e)
            )

    async def _crawl_page(self, client: httpx.AsyncClient, url: str, depth: int = 0):
        """
        Crawl a single page and its links.

        Args:
            client: HTTP client
            url: URL to crawl
            depth: Current crawl depth
        """
        # Stop if we've reached limits
        if (url in self.visited_urls or
            len(self.visited_urls) >= self.max_pages_per_site or
            depth > self.max_depth):
            return

        self.visited_urls.add(url)
        logger.debug(f"Processing page: {url} (depth: {depth})")

        try:
            # Fetch the page
            response = await client.get(url)
            response.raise_for_status()

            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.text, 'lxml')

            # Extract emails from HTML
            emails = self.email_extractor.extract_from_html(response.text, url)
            self.emails_found.extend(emails)

            logger.debug(f"Found {len(emails)} emails on {url}")

            # Extract and crawl links if we haven't hit the limit
            if len(self.visited_urls) < self.max_pages_per_site and depth < self.max_depth:
                links = self._extract_links_from_soup(soup, url)

                # Crawl a subset of links (limit to avoid too many requests)
                for link in links[:10]:
                    if len(self.visited_urls) >= self.max_pages_per_site:
                        break
                    await self._crawl_page(client, link, depth + 1)

        except Exception as e:
            logger.error(f"Error processing page {url}: {e}")

    def _extract_links_from_soup(self, soup, base_url: str) -> List[str]:
        """Extract relevant links from the page."""
        try:
            links = []
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                absolute_url = urljoin(base_url, href)

                if self._should_crawl_link(absolute_url):
                    links.append(absolute_url)

            return links

        except Exception as e:
            logger.error(f"Error extracting links: {e}")
            return []

    def _should_crawl_link(self, url: str) -> bool:
        """Determine if a link should be crawled."""
        if url in self.visited_urls:
            return False

        parsed = urlparse(url)

        if parsed.scheme not in ('http', 'https'):
            return False

        link_domain = self._get_domain(url)
        if link_domain != self.current_domain:
            return False

        skip_extensions = {'.pdf', '.zip', '.jpg', '.png', '.gif', '.mp4', '.mp3'}
        if any(parsed.path.lower().endswith(ext) for ext in skip_extensions):
            return False

        skip_paths = {'/login', '/signup', '/cart', '/checkout', '/admin'}
        if any(skip in parsed.path.lower() for skip in skip_paths):
            return False

        return True

    def _get_domain(self, url: str) -> str:
        """Extract the domain from a URL."""
        extracted = tldextract.extract(url)
        return f"{extracted.domain}.{extracted.suffix}"

    async def scrape_multiple_websites(
        self,
        urls: List[str],
        max_concurrent: int = 3
    ) -> List[ScrapedWebsite]:
        """Scrape multiple websites concurrently."""
        results = []
        semaphore = asyncio.Semaphore(max_concurrent)

        async def scrape_with_semaphore(url: str):
            async with semaphore:
                return await self.scrape_website(url)

        tasks = [scrape_with_semaphore(url) for url in urls]

        for i, task in enumerate(asyncio.as_completed(tasks)):
            result = await task
            results.append(result)
            logger.info(f"Completed {i + 1}/{len(urls)} websites")

        return results
