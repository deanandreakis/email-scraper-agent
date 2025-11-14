#!/usr/bin/env python3
"""
Example usage of the Email Scraper Agent.
"""

import asyncio
from agent import EmailScraperAgent
from dotenv import load_dotenv


async def example_basic():
    """Basic example - scrape emails for a topic."""
    print("\n=== Example 1: Basic Usage ===\n")

    # Create agent for a specific topic
    agent = EmailScraperAgent(
        topic="technology startups in San Francisco",
        max_websites=5
    )

    # Run the agent
    result = await agent.run()

    # Display summary
    agent.display_summary()

    # Save results
    output_file = agent.save_emails()
    print(f"Emails saved to: {output_file}\n")


async def example_advanced():
    """Advanced example with custom parameters."""
    print("\n=== Example 2: Advanced Usage ===\n")

    # Create agent with custom configuration
    agent = EmailScraperAgent(
        topic="renewable energy companies in Europe",
        max_websites=10,
        output_format="json"
    )

    # Run with custom search parameters
    result = await agent.run(
        country="DE",  # Germany
        language="en",
        min_confidence=0.8  # Higher confidence threshold
    )

    # Get detailed results
    detailed = agent.get_detailed_results()

    print("\nDetailed Results by Website:")
    for url, data in list(detailed['by_website'].items())[:3]:
        print(f"\n{url}:")
        print(f"  Success: {data['success']}")
        print(f"  Pages: {data['pages_crawled']}")
        print(f"  Emails: {data['emails_found']}")

    # Save results
    output_file = agent.save_emails("renewable_energy_emails.json")
    print(f"\nResults saved to: {output_file}\n")


async def example_multiple_topics():
    """Example of running multiple topics."""
    print("\n=== Example 3: Multiple Topics ===\n")

    topics = [
        "healthcare AI companies",
        "fintech startups",
        "educational technology"
    ]

    for topic in topics:
        print(f"\nProcessing: {topic}")

        agent = EmailScraperAgent(
            topic=topic,
            max_websites=3  # Fewer sites for demo
        )

        result = await agent.run()

        print(f"  Found {result.unique_emails} unique emails")

        # Save with topic-specific filename
        topic_slug = topic.replace(" ", "_")
        agent.save_emails(f"emails_{topic_slug}.csv")


async def example_filtering():
    """Example with email filtering."""
    print("\n=== Example 4: Email Filtering ===\n")

    agent = EmailScraperAgent(
        topic="software development agencies",
        max_websites=5
    )

    # Run the agent
    result = await agent.run(min_confidence=0.9)  # Very high confidence only

    # Get unique emails
    emails = agent._get_unique_emails()

    # Filter by domain
    from email_extractor import EmailExtractor

    extractor = EmailExtractor()

    # Filter to only .com and .org domains
    filtered = extractor.filter_by_domain(
        emails,
        domains=['com', 'org']
    )

    print(f"Total emails: {len(emails)}")
    print(f"Filtered emails (.com/.org only): {len(filtered)}")

    # Display sample
    print("\nSample filtered emails:")
    for email in filtered[:5]:
        print(f"  - {email.email}")


async def example_error_handling():
    """Example with error handling."""
    print("\n=== Example 5: Error Handling ===\n")

    try:
        agent = EmailScraperAgent(
            topic="quantum computing research",
            max_websites=5
        )

        result = await agent.run()

        # Check for failures
        failed_websites = [
            site for site in agent.scraped_websites
            if not site.success
        ]

        if failed_websites:
            print(f"\nWarning: {len(failed_websites)} websites failed to scrape:")
            for site in failed_websites:
                print(f"  - {site.url}: {site.error}")

        # Still save successful results
        if result.unique_emails > 0:
            output_file = agent.save_emails()
            print(f"\nSaved {result.unique_emails} emails despite some failures")

    except Exception as e:
        print(f"Error running agent: {e}")


async def main():
    """Run all examples."""
    # Load environment variables
    load_dotenv()

    print("=" * 70)
    print("EMAIL SCRAPER AGENT - EXAMPLES")
    print("=" * 70)

    # Run examples
    # Uncomment the examples you want to run

    await example_basic()

    # await example_advanced()

    # await example_multiple_topics()

    # await example_filtering()

    # await example_error_handling()

    print("\n" + "=" * 70)
    print("Examples complete!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
