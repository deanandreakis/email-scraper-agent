# Setup Guide

This guide will help you set up and run the Email Scraper Agent.

## Prerequisites

- Python 3.9 or higher
- [UV](https://github.com/astral-sh/uv) - Fast Python package installer (recommended)
- Google API credentials
- Internet connection

## Quick Start with UV (Recommended)

UV is the recommended way to set up this project. It's significantly faster than pip and handles virtual environments automatically.

### 1. Install UV

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv

# Or with Homebrew (macOS)
brew install uv
```

### 2. Clone the Repository

```bash
git clone <repository-url>
cd email-scraper-agent
```

### 3. Install Dependencies

```bash
# UV automatically creates a virtual environment and installs all dependencies
uv sync

# This creates a .venv directory with all dependencies installed
```

### 4. Install Playwright Browsers

```bash
# Run playwright install using UV
uv run playwright install

# Or install only Chromium to save space
uv run playwright install chromium
```

### 5. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your favorite editor
nano .env  # or vim, code, etc.
```

Add your Google API key to the `.env` file:

```env
GOOGLE_API_KEY=your_actual_api_key_here
GOOGLE_PROJECT_ID=your_project_id  # Optional

# Adjust other settings as needed
MAX_WEBSITES=10
MAX_EMAILS_PER_SITE=50
OUTPUT_FORMAT=csv
```

### 6. Test the Installation

```bash
# Test configuration
uv run python main.py config

# Analyze a topic (doesn't do scraping)
uv run python main.py analyze --topic "technology companies"
```

### 7. Run Your First Scrape

```bash
uv run python main.py run --topic "renewable energy companies" --max-sites 3
```

That's it! You're ready to use the Email Scraper Agent.

## Alternative Setup with pip

If you prefer to use traditional pip and venv:

### 1. Clone the Repository

```bash
git clone <repository-url>
cd email-scraper-agent
```

### 2. Create a Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Playwright Browsers

```bash
playwright install
```

### 5. Configure Environment Variables

Follow steps 5-7 from the UV setup above, but use `python` instead of `uv run python`.

## Get Google API Credentials

You need a Google API key to use the Generative AI features:

### Option 1: Google AI Studio (Easier)

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key and add it to `.env`

### Option 2: Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the "Generative Language API"
4. Create credentials (API Key)
5. Copy your API key and add it to `.env`

## UV Commands Reference

Here are common UV commands you'll use with this project:

```bash
# Install dependencies from pyproject.toml
uv sync

# Add a new dependency
uv add package-name

# Remove a dependency
uv remove package-name

# Run a Python script
uv run python script.py

# Run the CLI
uv run python main.py run --topic "your topic"

# Update all dependencies
uv sync --upgrade

# Show installed packages
uv pip list

# Activate the virtual environment (if needed)
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
```

## Troubleshooting

### Import Errors

If you get import errors:

```bash
# With UV
uv sync

# With pip
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Playwright Browser Issues

If Playwright can't find browsers:

```bash
# With UV
uv run playwright install

# Or install only Chromium (smaller download)
uv run playwright install chromium

# With pip (in activated venv)
playwright install
```

### Google API Errors

If you get authentication errors:

1. Check that `GOOGLE_API_KEY` is set correctly in `.env`
2. Verify the API key is valid on [Google AI Studio](https://makersuite.google.com/app/apikey)
3. Make sure you haven't exceeded API quotas
4. Ensure the Generative Language API is enabled in your Google Cloud project

### Rate Limiting

If you're getting rate limited:

1. Reduce `MAX_WEBSITES` in `.env`
2. Increase `DELAY_BETWEEN_REQUESTS`
3. Wait before retrying

### UV Installation Issues

If UV installation fails:

```bash
# Try installing with pip instead
pip install uv

# Or use pipx
pipx install uv
```

## Usage Examples

### Basic Command Line Usage

```bash
# Simple scrape
uv run python main.py run --topic "healthcare startups"

# With more options
uv run python main.py run \
  --topic "AI companies in California" \
  --max-sites 15 \
  --output my_emails.csv \
  --format csv \
  --country US

# Analyze before scraping
uv run python main.py analyze --topic "fintech companies"

# View current configuration
uv run python main.py config

# Show help
uv run python main.py --help
```

### Python Script Usage

```python
import asyncio
from agent import EmailScraperAgent

async def main():
    agent = EmailScraperAgent(
        topic="technology startups",
        max_websites=10
    )

    result = await agent.run()
    agent.display_summary()
    agent.save_emails("tech_emails.csv")

asyncio.run(main())
```

Run the script:
```bash
uv run python my_script.py
```

### See More Examples

Check out `example.py` for more detailed usage examples:

```bash
uv run python example.py
```

## Development Setup

If you're planning to contribute or develop:

```bash
# Install with dev dependencies
uv sync --all-extras

# This installs:
# - pytest for testing
# - black and ruff for code formatting
# - mypy for type checking

# Run tests
uv run pytest

# Format code
uv run black .
uv run ruff check --fix .

# Type checking
uv run mypy .
```

## Configuration Options

All configuration can be set via:

1. `.env` file (recommended)
2. Command line arguments
3. Python code

See `.env.example` for all available options.

## Project Files

- `pyproject.toml` - Project metadata and dependencies (for UV)
- `requirements.txt` - Dependencies list (fallback for pip)
- `.env.example` - Environment variable template
- `README.md` - Main documentation
- `SETUP.md` - This file

## Next Steps

- Read the [README.md](README.md) for detailed documentation
- Check [example.py](example.py) for code examples
- Review the code in `agent.py`, `scraper.py`, and `google_agent.py`
- Join the community and contribute!

## Ethical Usage

Please use this tool responsibly:

- Respect robots.txt
- Don't overwhelm servers with requests
- Comply with data protection laws (GDPR, CCPA, etc.)
- Use only for legitimate business purposes
- Respect website terms of service

## Getting Help

If you encounter issues:

1. Check the logs (set `LOG_LEVEL=DEBUG` in `.env`)
2. Review the troubleshooting section above
3. Check existing GitHub issues
4. Create a new issue with details about your problem

## Why UV?

UV offers several advantages over traditional pip:

- **Speed**: 10-100x faster than pip
- **Reliability**: Better dependency resolution
- **Simplicity**: Automatic virtual environment management
- **Modern**: Built with Rust for performance
- **Compatible**: Works with existing pip/requirements.txt projects

Learn more at: https://github.com/astral-sh/uv

Enjoy using the Email Scraper Agent!
