"""
Main Email Scraper Agent orchestration.
"""

import asyncio
import csv
import json
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from loguru import logger

from google_agent import GoogleSearchAgent, WebsiteCandidate
from scraper import EmailScraper, ScrapedWebsite
from email_extractor import EmailData
from config import Config
from url_cache import URLCache


@dataclass
class AgentResult:
    """Data class for agent execution results."""
    topic: str
    total_websites_found: int
    total_websites_scraped: int
    total_pages_crawled: int
    total_emails_found: int
    unique_emails: int
    execution_time: float
    timestamp: datetime
    websites: List[Dict]
    emails: List[Dict]


class EmailScraperAgent:
    """
    Main AI agent for discovering websites and scraping emails.

    This agent uses Google's Generative AI to understand topics and find
    relevant websites, then uses Crawlee to scrape those websites for emails.
    """

    def __init__(
        self,
        topic: str,
        config: Optional[Config] = None,
        max_websites: Optional[int] = None,
        output_format: Optional[str] = None,
        force_rescrape: bool = False,
        url_cache: Optional[URLCache] = None
    ):
        """
        Initialize the Email Scraper Agent.

        Args:
            topic: Topic or classification to search for
            config: Configuration object (if None, loads from env)
            max_websites: Override max websites from config
            output_format: Override output format from config
            force_rescrape: Force re-scraping of previously visited URLs
            url_cache: URL cache instance (if None, creates new one)
        """
        self.topic = topic

        # Load or use provided config
        if config is None:
            from config import load_config
            self.config = load_config()
        else:
            self.config = config

        # Override config if specified
        if max_websites is not None:
            self.config.max_websites = max_websites
        if output_format is not None:
            self.config.output_format = output_format

        # Initialize URL cache
        self.url_cache = url_cache if url_cache is not None else URLCache()

        # Initialize components
        self.google_agent = GoogleSearchAgent(
            api_key=self.config.google_api_key,
            model=self.config.google_model
        )

        self.scraper = EmailScraper(
            max_pages_per_site=self.config.max_pages_per_site,
            max_depth=self.config.max_depth,
            timeout=self.config.get_timeout_ms(),
            min_confidence=self.config.min_confidence,
            url_cache=self.url_cache,
            force_rescrape=force_rescrape
        )

        # Results storage
        self.website_candidates: List[WebsiteCandidate] = []
        self.scraped_websites: List[ScrapedWebsite] = []
        self.all_emails: List[EmailData] = []
        self.result: Optional[AgentResult] = None

        logger.info(f"Initialized EmailScraperAgent for topic: {topic}")

    async def run(
        self,
        country: Optional[str] = None,
        language: Optional[str] = None,
        min_confidence: Optional[float] = None
    ) -> AgentResult:
        """
        Run the agent to find and scrape websites.

        Args:
            country: Country code for search (overrides config)
            language: Language code for search (overrides config)
            min_confidence: Minimum email confidence (overrides config)

        Returns:
            AgentResult object with results
        """
        start_time = datetime.now()
        logger.info(f"Starting agent execution for topic: {self.topic}")

        # Use config defaults if not specified
        country = country or self.config.search_country
        language = language or self.config.search_language

        if min_confidence is not None:
            self.scraper.email_extractor.min_confidence = min_confidence

        try:
            # Step 1: Analyze topic
            logger.info("Step 1: Analyzing topic...")
            topic_analysis = self.google_agent.analyze_topic(self.topic)
            logger.info(f"Topic industry: {topic_analysis.get('industry', 'Unknown')}")

            # Step 2: Generate website candidates
            logger.info("Step 2: Generating website candidates...")
            self.website_candidates = self.google_agent.generate_website_candidates(
                topic=self.topic,
                num_websites=self.config.max_websites,
                country=country,
                language=language
            )
            logger.info(f"Found {len(self.website_candidates)} website candidates")

            # Step 3: Scrape websites
            logger.info("Step 3: Scraping websites for emails...")
            urls = [candidate.url for candidate in self.website_candidates]

            self.scraped_websites = await self.scraper.scrape_multiple_websites(
                urls=urls,
                max_concurrent=self.config.concurrent_requests
            )

            # Step 4: Aggregate results
            logger.info("Step 4: Aggregating results...")
            self._aggregate_results()

            # Calculate metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            successful_scrapes = sum(1 for site in self.scraped_websites if site.success)
            total_pages = sum(site.page_count for site in self.scraped_websites)

            # Create result
            self.result = AgentResult(
                topic=self.topic,
                total_websites_found=len(self.website_candidates),
                total_websites_scraped=successful_scrapes,
                total_pages_crawled=total_pages,
                total_emails_found=len(self.all_emails),
                unique_emails=len(self._get_unique_emails()),
                execution_time=execution_time,
                timestamp=datetime.now(),
                websites=[asdict(candidate) for candidate in self.website_candidates],
                emails=[asdict(email) for email in self.all_emails]
            )

            logger.info(f"Agent execution complete in {execution_time:.2f}s")
            logger.info(f"Found {self.result.unique_emails} unique emails from {successful_scrapes} websites")

            return self.result

        except Exception as e:
            logger.error(f"Error during agent execution: {e}")
            raise

    def _aggregate_results(self):
        """Aggregate emails from all scraped websites."""
        self.all_emails = []

        for website in self.scraped_websites:
            if website.success:
                for email_dict in website.emails:
                    # Convert dict back to EmailData
                    email_data = EmailData(
                        email=email_dict['email'],
                        source_url=email_dict['source_url'],
                        found_at=datetime.fromisoformat(email_dict['found_at']),
                        confidence=email_dict['confidence'],
                        context=email_dict.get('context')
                    )
                    self.all_emails.append(email_data)

        logger.info(f"Aggregated {len(self.all_emails)} total emails")

    def _get_unique_emails(self) -> List[EmailData]:
        """Get unique emails (deduplicated)."""
        email_dict = {}

        for email_data in self.all_emails:
            email = email_data.email

            if email not in email_dict:
                email_dict[email] = email_data
            else:
                # Keep the one with higher confidence
                if email_data.confidence > email_dict[email].confidence:
                    email_dict[email] = email_data

        return list(email_dict.values())

    def save_emails(self, output_path: Optional[str] = None) -> str:
        """
        Save emails to a file.

        Args:
            output_path: Output file path (if None, auto-generates)

        Returns:
            Path to saved file
        """
        if self.result is None:
            raise RuntimeError("No results to save. Run the agent first.")

        # Generate output path if not provided
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            topic_slug = self.topic.lower().replace(" ", "_")[:30]
            extension = self.config.output_format
            output_path = Path(self.config.output_dir) / f"{topic_slug}_{timestamp}.{extension}"
        else:
            output_path = Path(output_path)

        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Get unique emails
        unique_emails = self._get_unique_emails()

        # Save based on format
        if self.config.output_format == "csv":
            self._save_csv(output_path, unique_emails)
        else:
            self._save_json(output_path, unique_emails)

        logger.info(f"Saved {len(unique_emails)} emails to {output_path}")
        return str(output_path)

    def _save_csv(self, path: Path, emails: List[EmailData]):
        """Save emails to CSV file."""
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow(['email', 'source_url', 'found_at', 'confidence', 'context'])

            # Write emails
            for email_data in emails:
                writer.writerow([
                    email_data.email,
                    email_data.source_url,
                    email_data.found_at.isoformat(),
                    f"{email_data.confidence:.3f}",
                    email_data.context or ''
                ])

    def _save_json(self, path: Path, emails: List[EmailData]):
        """Save emails to JSON file."""
        data = {
            "metadata": {
                "topic": self.topic,
                "total_websites": self.result.total_websites_scraped,
                "total_emails": len(emails),
                "run_date": self.result.timestamp.isoformat(),
                "execution_time": self.result.execution_time
            },
            "emails": [
                {
                    "email": email_data.email,
                    "source_url": email_data.source_url,
                    "found_at": email_data.found_at.isoformat(),
                    "confidence": email_data.confidence,
                    "context": email_data.context
                }
                for email_data in emails
            ]
        }

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_detailed_results(self) -> Dict:
        """
        Get detailed results including per-website breakdown.

        Returns:
            Dictionary with detailed results
        """
        if self.result is None:
            raise RuntimeError("No results available. Run the agent first.")

        results_by_website = {}

        for website in self.scraped_websites:
            results_by_website[website.url] = {
                "success": website.success,
                "pages_crawled": website.page_count,
                "emails_found": len(website.emails),
                "error": website.error,
                "emails": website.emails
            }

        return {
            "summary": asdict(self.result),
            "by_website": results_by_website
        }

    def display_summary(self):
        """Display a summary of results."""
        if self.result is None:
            logger.warning("No results to display. Run the agent first.")
            return

        print("\n" + "=" * 60)
        print(f"EMAIL SCRAPER AGENT RESULTS")
        print("=" * 60)
        print(f"Topic: {self.topic}")
        print(f"Execution time: {self.result.execution_time:.2f}s")
        print(f"\nWebsites:")
        print(f"  - Candidates found: {self.result.total_websites_found}")
        print(f"  - Successfully scraped: {self.result.total_websites_scraped}")
        print(f"  - Total pages crawled: {self.result.total_pages_crawled}")
        print(f"\nEmails:")
        print(f"  - Total found: {self.result.total_emails_found}")
        print(f"  - Unique emails: {self.result.unique_emails}")
        print("=" * 60 + "\n")


async def main():
    """Example usage of EmailScraperAgent."""
    import sys

    # Example topic
    topic = "renewable energy companies" if len(sys.argv) < 2 else sys.argv[1]

    # Create and run agent
    agent = EmailScraperAgent(
        topic=topic,
        max_websites=5  # Limit for demo
    )

    # Run the agent
    result = await agent.run()

    # Display summary
    agent.display_summary()

    # Save results
    output_file = agent.save_emails()
    print(f"Results saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
