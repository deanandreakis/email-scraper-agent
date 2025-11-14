#!/usr/bin/env python3
"""
Command-line interface for the Email Scraper Agent.
"""

import asyncio
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from loguru import logger

from agent import EmailScraperAgent
from config import load_config


console = Console()


@click.group()
def cli():
    """Email Scraper Agent - Find emails from websites based on topics."""
    pass


@cli.command()
@click.option(
    '--topic', '-t',
    required=True,
    help='Topic or classification to search for'
)
@click.option(
    '--max-sites', '-m',
    type=int,
    help='Maximum number of websites to scrape'
)
@click.option(
    '--output', '-o',
    type=click.Path(),
    help='Output file path'
)
@click.option(
    '--format', '-f',
    type=click.Choice(['csv', 'json'], case_sensitive=False),
    help='Output format (csv or json)'
)
@click.option(
    '--country', '-c',
    default='US',
    help='Country code for search'
)
@click.option(
    '--language', '-l',
    default='en',
    help='Language code for search'
)
@click.option(
    '--min-confidence',
    type=float,
    help='Minimum confidence score for emails (0.0 to 1.0)'
)
@click.option(
    '--headless/--no-headless',
    default=True,
    help='Run browser in headless mode'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose logging'
)
def run(topic, max_sites, output, format, country, language, min_confidence, headless, verbose):
    """
    Run the email scraper agent for a given topic.

    Example:
        python main.py run --topic "healthcare startups" --max-sites 10
    """
    asyncio.run(_run_agent(
        topic=topic,
        max_sites=max_sites,
        output=output,
        format=format,
        country=country,
        language=language,
        min_confidence=min_confidence,
        headless=headless,
        verbose=verbose
    ))


async def _run_agent(
    topic,
    max_sites,
    output,
    format,
    country,
    language,
    min_confidence,
    headless,
    verbose
):
    """Internal async function to run the agent."""
    try:
        # Load config
        config = load_config()

        # Override config with CLI arguments
        if max_sites:
            config.max_websites = max_sites
        if format:
            config.output_format = format
        if verbose:
            config.log_level = "DEBUG"
            config.setup_logging()
        if not headless:
            config.headless = False

        # Create agent
        console.print(f"\n[bold blue]Email Scraper Agent[/bold blue]")
        console.print(f"Topic: [green]{topic}[/green]")
        console.print(f"Max websites: [yellow]{config.max_websites}[/yellow]\n")

        agent = EmailScraperAgent(
            topic=topic,
            config=config
        )

        # Run agent with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Running agent...", total=None)

            result = await agent.run(
                country=country,
                language=language,
                min_confidence=min_confidence
            )

            progress.update(task, completed=True)

        # Display results
        _display_results(agent)

        # Save results
        output_file = agent.save_emails(output)
        console.print(f"\n[bold green]Results saved to:[/bold green] {output_file}")

        # Show sample emails
        _display_sample_emails(agent)

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}", style="red")
        if verbose:
            logger.exception("Detailed error:")
        sys.exit(1)


def _display_results(agent):
    """Display results summary in a nice table."""
    result = agent.result

    # Summary table
    table = Table(title="Results Summary", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Topic", result.topic)
    table.add_row("Execution Time", f"{result.execution_time:.2f}s")
    table.add_row("Websites Found", str(result.total_websites_found))
    table.add_row("Websites Scraped", str(result.total_websites_scraped))
    table.add_row("Pages Crawled", str(result.total_pages_crawled))
    table.add_row("Total Emails", str(result.total_emails_found))
    table.add_row("Unique Emails", str(result.unique_emails))

    console.print("\n")
    console.print(table)


def _display_sample_emails(agent, limit=10):
    """Display sample emails."""
    emails = agent._get_unique_emails()[:limit]

    if not emails:
        console.print("\n[yellow]No emails found[/yellow]")
        return

    table = Table(title=f"Sample Emails (showing {len(emails)} of {len(agent._get_unique_emails())})", show_header=True, header_style="bold magenta")
    table.add_column("Email", style="cyan", no_wrap=False)
    table.add_column("Source", style="blue", no_wrap=False, max_width=40)
    table.add_column("Confidence", style="green", justify="right")

    for email in emails:
        table.add_row(
            email.email,
            email.source_url,
            f"{email.confidence:.2f}"
        )

    console.print("\n")
    console.print(table)


@cli.command()
@click.option(
    '--topic', '-t',
    required=True,
    help='Topic to analyze'
)
def analyze(topic):
    """
    Analyze a topic without scraping.

    This shows what the AI understands about the topic and what keywords it would use.
    """
    try:
        config = load_config()

        from google_agent import GoogleSearchAgent

        console.print(f"\n[bold blue]Analyzing topic:[/bold blue] {topic}\n")

        agent = GoogleSearchAgent(config.google_api_key, config.google_model)

        # Analyze topic
        analysis = agent.analyze_topic(topic)

        # Display analysis
        console.print("[bold]Topic Summary:[/bold]")
        console.print(f"  {analysis['topic_summary']}\n")

        console.print("[bold]Industry:[/bold]")
        console.print(f"  {analysis['industry']}\n")

        console.print("[bold]Categories:[/bold]")
        for cat in analysis['key_categories']:
            console.print(f"  • {cat}")

        console.print("\n[bold]Search Keywords:[/bold]")
        for keyword in analysis['search_keywords']:
            console.print(f"  • {keyword}")

        console.print("\n[bold]Typical Domains:[/bold]")
        for domain in analysis.get('typical_domains', [])[:5]:
            console.print(f"  • {domain}")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")
        sys.exit(1)


@cli.command()
def config():
    """Display current configuration."""
    try:
        cfg = load_config()

        table = Table(title="Configuration", show_header=True, header_style="bold magenta")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Google Model", cfg.google_model)
        table.add_row("Max Websites", str(cfg.max_websites))
        table.add_row("Max Pages per Site", str(cfg.max_pages_per_site))
        table.add_row("Max Depth", str(cfg.max_depth))
        table.add_row("Min Confidence", str(cfg.min_confidence))
        table.add_row("Output Format", cfg.output_format)
        table.add_row("Output Directory", cfg.output_dir)
        table.add_row("Headless Mode", str(cfg.headless))
        table.add_row("Timeout", f"{cfg.timeout_seconds}s")
        table.add_row("Log Level", cfg.log_level)

        console.print("\n")
        console.print(table)
        console.print("\n[dim]Configuration loaded from .env file[/dim]\n")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")
        console.print("\n[yellow]Tip:[/yellow] Copy .env.example to .env and configure your settings")
        sys.exit(1)


@cli.command()
def version():
    """Display version information."""
    console.print("\n[bold blue]Email Scraper Agent[/bold blue]")
    console.print("Version: 1.0.0")
    console.print("Author: AI Agent Development\n")


if __name__ == "__main__":
    cli()
