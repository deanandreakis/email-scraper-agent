"""
Crawlee-based web scraper for extracting content and emails from websites.
"""

import asyncio
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse
import tldextract
from loguru import logger

from crawlee.playwright_crawler import PlaywrightCrawler, PlaywrightCrawlingContext
from crawlee.storages import Dataset

from email_extractor import EmailExtractor, EmailData


@dataclass
class ScrapedWebsite:
    """Data class for scraped website information."""
    url: str
    title: str
    emails: List[Dict]
    page_count: int
    success: bool
    error: Optional[str] = None


class EmailScraper:
    """Web scraper for extracting emails from websites using Crawlee."""

    def __init__(
        self,
        max_pages_per_site: int = 50,
        max_depth: int = 3,
        timeout: int = 30000,
        min_confidence: float = 0.7,
        headless: bool = True
    ):
        """
        Initialize the email scraper.

        Args:
            max_pages_per_site: Maximum pages to crawl per website
            max_depth: Maximum crawl depth
            timeout: Page timeout in milliseconds
            min_confidence: Minimum email confidence score
            headless: Whether to run browser in headless mode
        """
        self.max_pages_per_site = max_pages_per_site
        self.max_depth = max_depth
        self.timeout = timeout
        self.headless = headless

        self.email_extractor = EmailExtractor(
            validate_dns=False,  # Skip DNS validation for speed
            min_confidence=min_confidence
        )

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
        logger.info(f"Starting to scrape website: {url}")

        # Reset state for new website
        self.visited_urls.clear()
        self.emails_found.clear()
        self.current_domain = self._get_domain(url)

        try:
            # Create crawler
            crawler = PlaywrightCrawler(
                max_requests_per_crawl=self.max_pages_per_site,
                headless=self.headless,
                request_handler=self._create_request_handler(),
            )

            # Run crawler
            await crawler.run([url])

            # Deduplicate emails
            unique_emails = self.email_extractor.deduplicate(self.emails_found)

            logger.info(f"Scraping complete. Found {len(unique_emails)} unique emails from {len(self.visited_urls)} pages")

            return ScrapedWebsite(
                url=url,
                title=self._get_domain(url),
                emails=[asdict(email) for email in unique_emails],
                page_count=len(self.visited_urls),
                success=True
            )

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return ScrapedWebsite(
                url=url,
                title=self._get_domain(url),
                emails=[],
                page_count=0,
                success=False,
                error=str(e)
            )

    def _create_request_handler(self):
        """Create the request handler for Crawlee."""

        async def request_handler(context: PlaywrightCrawlingContext) -> None:
            """Handle each page request."""
            url = context.request.url

            # Skip if already visited
            if url in self.visited_urls:
                return

            self.visited_urls.add(url)
            logger.debug(f"Processing page: {url}")

            try:
                # Wait for page to load
                await context.page.wait_for_load_state('networkidle', timeout=self.timeout)

                # Get page content
                html = await context.page.content()
                title = await context.page.title()

                # Extract emails from HTML
                emails = self.email_extractor.extract_from_html(html, url)
                self.emails_found.extend(emails)

                logger.debug(f"Found {len(emails)} emails on {url}")

                # Find and enqueue links to crawl
                if len(self.visited_urls) < self.max_pages_per_site:
                    links = await self._extract_links(context)
                    for link in links[:10]:  # Limit links per page
                        await context.enqueue_links([link])

            except Exception as e:
                logger.error(f"Error processing page {url}: {e}")

        return request_handler

    async def _extract_links(self, context: PlaywrightCrawlingContext) -> List[str]:
        """
        Extract relevant links from the current page.

        Args:
            context: Crawling context

        Returns:
            List of URLs to crawl
        """
        try:
            # Get all links
            links = await context.page.eval_on_selector_all(
                'a[href]',
                '(elements) => elements.map(el => el.href)'
            )

            # Filter links
            filtered_links = []
            for link in links:
                if self._should_crawl_link(link):
                    filtered_links.append(link)

            return filtered_links

        except Exception as e:
            logger.error(f"Error extracting links: {e}")
            return []

    def _should_crawl_link(self, url: str) -> bool:
        """
        Determine if a link should be crawled.

        Args:
            url: URL to check

        Returns:
            True if should crawl, False otherwise
        """
        # Skip if already visited
        if url in self.visited_urls:
            return False

        # Parse URL
        parsed = urlparse(url)

        # Skip non-http(s) URLs
        if parsed.scheme not in ('http', 'https'):
            return False

        # Only crawl same domain
        link_domain = self._get_domain(url)
        if link_domain != self.current_domain:
            return False

        # Skip common non-content pages
        skip_extensions = {'.pdf', '.zip', '.jpg', '.png', '.gif', '.mp4', '.mp3'}
        if any(parsed.path.lower().endswith(ext) for ext in skip_extensions):
            return False

        # Skip common non-content paths
        skip_paths = {'/login', '/signup', '/cart', '/checkout', '/admin'}
        if any(skip in parsed.path.lower() for skip in skip_paths):
            return False

        return True

    def _get_domain(self, url: str) -> str:
        """
        Extract the domain from a URL.

        Args:
            url: URL to extract domain from

        Returns:
            Domain string
        """
        extracted = tldextract.extract(url)
        return f"{extracted.domain}.{extracted.suffix}"

    async def scrape_multiple_websites(
        self,
        urls: List[str],
        max_concurrent: int = 3
    ) -> List[ScrapedWebsite]:
        """
        Scrape multiple websites concurrently.

        Args:
            urls: List of URLs to scrape
            max_concurrent: Maximum concurrent scraping tasks

        Returns:
            List of ScrapedWebsite objects
        """
        results = []
        semaphore = asyncio.Semaphore(max_concurrent)

        async def scrape_with_semaphore(url: str):
            async with semaphore:
                return await self.scrape_website(url)

        # Create tasks
        tasks = [scrape_with_semaphore(url) for url in urls]

        # Execute with progress
        for i, task in enumerate(asyncio.as_completed(tasks)):
            result = await task
            results.append(result)
            logger.info(f"Completed {i + 1}/{len(urls)} websites")

        return results


async def main():
    """Example usage of EmailScraper."""
    scraper = EmailScraper(
        max_pages_per_site=10,
        max_depth=2,
        min_confidence=0.7
    )

    # Scrape a single website
    result = await scraper.scrape_website("https://example.com")

    print(f"\nResults for {result.url}:")
    print(f"  Success: {result.success}")
    print(f"  Pages crawled: {result.page_count}")
    print(f"  Emails found: {len(result.emails)}")

    for email in result.emails[:5]:  # Show first 5
        print(f"    - {email['email']} (confidence: {email['confidence']:.2f})")


if __name__ == "__main__":
    asyncio.run(main())
