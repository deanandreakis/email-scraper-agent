"""
Configuration management for the Email Scraper Agent.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from loguru import logger


class Config(BaseSettings):
    """Configuration settings for the Email Scraper Agent."""

    # Google API Configuration
    google_api_key: str = Field(..., description="Google API key for Generative AI")
    google_project_id: Optional[str] = Field(None, description="Google Cloud project ID")
    google_model: str = Field("gemini-1.5-flash", description="Google AI model to use")

    # Scraping Configuration
    max_websites: int = Field(10, description="Maximum number of websites to scrape")
    max_emails_per_site: int = Field(50, description="Maximum emails to extract per site")
    max_pages_per_site: int = Field(50, description="Maximum pages to crawl per site")
    max_depth: int = Field(3, description="Maximum crawl depth")
    concurrent_requests: int = Field(5, description="Number of concurrent scraping requests")

    # Output Configuration
    output_format: str = Field("csv", description="Output format (csv or json)")
    output_dir: str = Field("./emails", description="Directory to save email data")

    # Agent Configuration
    min_confidence: float = Field(0.7, description="Minimum confidence score for emails")
    timeout_seconds: int = Field(30, description="Request timeout in seconds")
    user_agent: str = Field(
        "EmailScraperAgent/1.0",
        description="User agent string"
    )
    headless: bool = Field(True, description="Run browser in headless mode")

    # Rate Limiting
    requests_per_second: int = Field(2, description="Maximum requests per second")
    delay_between_requests: float = Field(0.5, description="Delay between requests in seconds")

    # Search Configuration
    search_country: str = Field("US", description="Country code for search")
    search_language: str = Field("en", description="Language code for search")

    # Validation
    validate_dns: bool = Field(False, description="Validate email domains via DNS")
    exclude_disposable: bool = Field(True, description="Exclude disposable email domains")

    # Logging
    log_level: str = Field("INFO", description="Logging level")
    log_file: Optional[str] = Field(None, description="Log file path")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @validator("output_format")
    def validate_output_format(cls, v):
        """Validate output format."""
        if v.lower() not in ("csv", "json"):
            raise ValueError("output_format must be 'csv' or 'json'")
        return v.lower()

    @validator("min_confidence")
    def validate_confidence(cls, v):
        """Validate confidence score."""
        if not 0 <= v <= 1:
            raise ValueError("min_confidence must be between 0 and 1")
        return v

    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()

    @validator("max_websites", "max_emails_per_site", "max_pages_per_site", "max_depth")
    def validate_positive(cls, v):
        """Validate positive integers."""
        if v <= 0:
            raise ValueError("Value must be positive")
        return v

    def setup_logging(self):
        """Configure logging based on settings."""
        logger.remove()  # Remove default handler

        # Add console handler
        logger.add(
            lambda msg: print(msg, end=""),
            level=self.log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )

        # Add file handler if specified
        if self.log_file:
            logger.add(
                self.log_file,
                level=self.log_level,
                rotation="10 MB",
                retention="1 week",
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
            )

        logger.info("Logging configured")

    def get_timeout_ms(self) -> int:
        """Get timeout in milliseconds."""
        return self.timeout_seconds * 1000

    def create_output_dir(self):
        """Create output directory if it doesn't exist."""
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"Output directory: {self.output_dir}")

    def display_settings(self):
        """Display current settings."""
        logger.info("Configuration:")
        logger.info(f"  Model: {self.google_model}")
        logger.info(f"  Max websites: {self.max_websites}")
        logger.info(f"  Max pages per site: {self.max_pages_per_site}")
        logger.info(f"  Min confidence: {self.min_confidence}")
        logger.info(f"  Output format: {self.output_format}")
        logger.info(f"  Output directory: {self.output_dir}")
        logger.info(f"  Headless mode: {self.headless}")


def load_config() -> Config:
    """
    Load configuration from environment variables and .env file.

    Returns:
        Config object
    """
    try:
        config = Config()
        config.setup_logging()
        config.create_output_dir()
        return config

    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise


def main():
    """Example usage of Config."""
    from dotenv import load_dotenv

    load_dotenv()

    try:
        config = load_config()
        config.display_settings()

    except Exception as e:
        print(f"Error: {e}")
        print("\nPlease ensure you have a .env file with required variables.")
        print("Copy .env.example to .env and fill in your values.")


if __name__ == "__main__":
    main()
