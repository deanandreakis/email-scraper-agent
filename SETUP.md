# Setup Guide

This guide will help you set up and run the Email Scraper Agent.

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Google API credentials
- Internet connection

## Step-by-Step Setup

### 1. Clone or Download the Repository

```bash
git clone <repository-url>
cd email-scraper-agent
```

### 2. Create a Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Playwright Browsers

Crawlee uses Playwright for web scraping, which requires browser binaries:

```bash
playwright install
```

This will download Chromium, Firefox, and WebKit browsers.

### 5. Get Google API Credentials

You need a Google API key to use the Generative AI features:

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key

Alternatively, if you're using Google Cloud:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the "Generative Language API"
4. Create credentials (API Key)
5. Copy your API key

### 6. Configure Environment Variables

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

### 7. Test the Installation

Run a quick test to ensure everything is working:

```bash
# Test configuration
python main.py config

# Analyze a topic (doesn't do scraping)
python main.py analyze --topic "technology companies"
```

### 8. Run Your First Scrape

```bash
# Run the agent with a simple topic
python main.py run --topic "renewable energy companies" --max-sites 3
```

This will:
- Analyze the topic
- Find relevant websites
- Scrape them for emails
- Save results to a CSV file

## Troubleshooting

### Import Errors

If you get import errors:

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Playwright Browser Issues

If Playwright can't find browsers:

```bash
# Reinstall browsers
playwright install

# Or install only Chromium (smaller download)
playwright install chromium
```

### Google API Errors

If you get authentication errors:

1. Check that `GOOGLE_API_KEY` is set correctly in `.env`
2. Verify the API key is valid on [Google AI Studio](https://makersuite.google.com/app/apikey)
3. Make sure you haven't exceeded API quotas

### Rate Limiting

If you're getting rate limited:

1. Reduce `MAX_WEBSITES` in `.env`
2. Increase `DELAY_BETWEEN_REQUESTS`
3. Wait before retrying

## Usage Examples

### Basic Command Line Usage

```bash
# Simple scrape
python main.py run --topic "healthcare startups"

# With more options
python main.py run \
  --topic "AI companies in California" \
  --max-sites 15 \
  --output my_emails.csv \
  --format csv \
  --country US

# Analyze before scraping
python main.py analyze --topic "fintech companies"
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

### See More Examples

Check out `example.py` for more detailed usage examples:

```bash
python example.py
```

## Configuration Options

All configuration can be set via:

1. `.env` file (recommended)
2. Command line arguments
3. Python code

See `.env.example` for all available options.

## Next Steps

- Read the [README.md](README.md) for detailed documentation
- Check [example.py](example.py) for code examples
- Review the code in `agent.py`, `scraper.py`, and `google_agent.py`

## Getting Help

If you encounter issues:

1. Check the logs (set `LOG_LEVEL=DEBUG` in `.env`)
2. Review the troubleshooting section above
3. Check GitHub issues
4. Create a new issue with details

## Ethical Usage

Please use this tool responsibly:

- Respect robots.txt
- Don't overwhelm servers with requests
- Comply with data protection laws (GDPR, CCPA, etc.)
- Use only for legitimate business purposes
- Respect website terms of service

Enjoy using the Email Scraper Agent!
