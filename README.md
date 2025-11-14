# Email Scraper AI Agent

An intelligent AI agent that uses the Google Agent Development Kit and Crawlee web scraper to automatically find and extract email addresses from websites based on a given topic or classification.

## Features

- **AI-Powered Search**: Uses Google Agent Development Kit to intelligently search for relevant websites
- **Efficient Web Scraping**: Leverages Crawlee for robust and scalable web scraping
- **Email Extraction**: Automatically identifies and extracts email addresses from web pages
- **Topic-Based Discovery**: Finds websites related to your specified classification or topic
- **Smart Caching**: Automatically tracks visited websites to prevent duplicate scraping
- **Data Storage**: Saves extracted emails in multiple formats (CSV, JSON)

## Prerequisites

- Python 3.9 or higher
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer (recommended)
- Google API credentials (for Agent Development Kit)
- Internet connection

## Installation

### Option 1: Using UV (Recommended)

UV is a fast Python package installer and resolver. It's the recommended way to set up this project.

1. Install UV (if not already installed):
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

2. Clone the repository:
```bash
git clone <repository-url>
cd email-scraper-agent
```

3. Create virtual environment and install dependencies:
```bash
# UV automatically creates a virtual environment and installs dependencies
uv sync
```

4. Install Playwright browsers (required by Crawlee):
```bash
uv run playwright install
```

5. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your Google API credentials
```

### Option 2: Using pip

1. Clone the repository:
```bash
git clone <repository-url>
cd email-scraper-agent
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers (required by Crawlee):
```bash
playwright install
```

5. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your Google API credentials
```

## Getting Google API Credentials

You need a Google API key to use the Generative AI features. There are two ways to get one:

### Option 1: Google AI Studio (Recommended - Easiest)

This is the **fastest way** to get started. No Google Cloud project setup required!

1. **Visit Google AI Studio**
   - Go to: https://aistudio.google.com/app/apikey
   - Sign in with your Google account

2. **Create API Key**
   - Click "Get API Key" or "Create API Key"
   - Choose "Create API key in new project" (auto-creates a project for you)
   - Copy the API key immediately

3. **Add to your .env file**
   ```env
   GOOGLE_API_KEY=AIzaSy...your_actual_key_here
   ```

**What you get (Free Tier):**
- Access to Gemini models (gemini-1.5-flash, gemini-1.5-pro)
- 15 requests per minute free (gemini-1.5-flash), 2 RPM (gemini-1.5-pro)
- Perfect for development and testing
- No billing required

### Option 2: Google Cloud Console (For Production)

Use this if you need more control, higher quotas, or production features.

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/

2. **Create a New Project**
   - Click "Select a project" → "New Project"
   - Name it (e.g., "email-scraper-agent")
   - Click "Create"

3. **Enable the API**
   - Search for "Generative Language API"
   - Click "Enable"

4. **Create Credentials**
   - Go to "APIs & Services" → "Credentials"
   - Click "+ CREATE CREDENTIALS" → "API Key"
   - Copy the API key
   - (Optional) Add restrictions for security

5. **Add to your .env file**
   ```env
   GOOGLE_API_KEY=your_api_key_here
   GOOGLE_PROJECT_ID=your-project-id  # Optional
   ```

### Which Option Should I Choose?

| Feature | Google AI Studio | Google Cloud Console |
|---------|-----------------|---------------------|
| **Setup Time** | 2 minutes | 5-10 minutes |
| **Complexity** | Very simple | More complex |
| **Best For** | Testing, development | Production, teams |
| **Quotas** | 60 req/min free | Configurable with billing |

**Recommendation**: Start with **Google AI Studio**. You can always migrate later.

### Testing Your API Key

Once configured, test it:

```bash
# Test configuration
uv run python main.py config

# Test with topic analysis (quick, no scraping)
uv run python main.py analyze --topic "technology companies"
```

If you see analysis results, your API key is working! 🎉

### Security Best Practices

- **Never commit** your API key to git (already handled via `.gitignore`)
- **Restrict the key** (in Cloud Console) to specific APIs
- **Monitor usage** at https://aistudio.google.com/app/apikey
- **Rotate keys** periodically for security

## Configuration

Create a `.env` file with the following variables:

```env
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_PROJECT_ID=your_project_id
MAX_WEBSITES=10
MAX_EMAILS_PER_SITE=50
OUTPUT_FORMAT=csv
```

## Usage

### Basic Usage

```python
from agent import EmailScraperAgent

# Initialize the agent
agent = EmailScraperAgent(
    topic="healthcare startups",
    max_websites=10
)

# Run the agent
emails = agent.run()

# Save results
agent.save_emails("healthcare_emails.csv")
```

### Command Line Usage

```bash
# With UV
uv run python main.py run --topic "technology companies" --max-sites 15 --output emails.csv

# Or if activated in virtual environment
python main.py run --topic "technology companies" --max-sites 15 --output emails.csv
```

### Advanced Usage

```python
from agent import EmailScraperAgent

# Initialize with custom configuration
agent = EmailScraperAgent(
    topic="renewable energy companies in California",
    max_websites=20,
    max_emails_per_site=30,
    output_format="json"
)

# Run with custom search parameters
emails = agent.run(
    country="US",
    language="en",
    min_confidence=0.7
)

# Get detailed results
results = agent.get_detailed_results()
for website, data in results.items():
    print(f"Website: {website}")
    print(f"Emails found: {len(data['emails'])}")
    print(f"Confidence: {data['confidence']}")
```

## URL Cache - Preventing Duplicate Scraping

The agent automatically tracks all visited websites to avoid scraping them again. This saves time and respects websites by not overwhelming them with repeated requests.

### How It Works

- **Automatic Tracking**: Every website you scrape is saved to `storage/visited_urls.json`
- **Skip Previously Visited**: On subsequent runs, the agent automatically skips URLs it has already visited
- **Persistent Across Sessions**: The cache persists between runs, so you can resume work anytime
- **Metadata Storage**: Stores visit timestamps, success status, and number of emails found

### Managing the Cache

View cache statistics:
```bash
uv run python main.py cache stats
```

List all visited URLs:
```bash
uv run python main.py cache list
uv run python main.py cache list --successful-only
uv run python main.py cache list --failed-only --limit 10
```

Force re-scraping (ignore cache):
```bash
uv run python main.py run --topic "healthcare" --force-rescrape
```

Clear the entire cache:
```bash
uv run python main.py cache clear
```

Remove a specific URL:
```bash
uv run python main.py cache remove https://example.com
```

Clean up old entries (older than 30 days):
```bash
uv run python main.py cache cleanup --days 30
```

Export cache to CSV:
```bash
uv run python main.py cache export --output cache_report.csv
```

### Programmatic Usage

```python
from agent import EmailScraperAgent
from url_cache import URLCache

# Create agent with force_rescrape option
agent = EmailScraperAgent(
    topic="technology startups",
    force_rescrape=True  # Re-scrape even if already visited
)

# Or manage cache directly
cache = URLCache()

# Check if URL is visited
if cache.is_visited("https://example.com"):
    print("Already visited!")

# Get stats
stats = cache.get_stats()
print(f"Total URLs cached: {stats['total_urls']}")

# Clear cache
cache.clear()
```

## Project Structure

```
email-scraper-agent/
├── agent.py              # Main agent orchestration
├── scraper.py            # Crawlee-based web scraper
├── email_extractor.py    # Email extraction utilities
├── google_agent.py       # Google AI integration
├── config.py             # Configuration management
├── url_cache.py          # URL caching to prevent duplicate scraping
├── main.py               # CLI interface
├── example.py            # Usage examples
├── pyproject.toml        # Project metadata and dependencies (UV)
├── requirements.txt      # Python dependencies (pip fallback)
├── .env.example          # Example environment file
├── SETUP.md              # Detailed setup guide
├── storage/              # Cache and data storage (gitignored)
│   └── visited_urls.json # Visited URLs cache
└── README.md             # This file
```

## How It Works

1. **Topic Analysis**: The agent uses Google's AI to understand the topic and generate relevant search queries
2. **Website Discovery**: Searches for and identifies websites matching the classification
3. **Cache Check**: Automatically checks if websites have been visited before to avoid duplicate work
4. **Web Scraping**: Uses Crawlee to efficiently crawl identified websites
5. **Email Extraction**: Applies regex patterns and validation to extract email addresses
6. **Cache Update**: Stores visited URLs with metadata for future reference
7. **Data Storage**: Saves unique emails with metadata (source, timestamp, confidence)

## Output Format

### CSV Format
```csv
email,source_url,found_at,confidence,timestamp
contact@example.com,https://example.com,2024-01-01 12:00:00,0.95,2024-01-01 12:00:00
```

### JSON Format
```json
{
  "emails": [
    {
      "email": "contact@example.com",
      "source_url": "https://example.com",
      "found_at": "2024-01-01T12:00:00",
      "confidence": 0.95,
      "timestamp": "2024-01-01T12:00:00"
    }
  ],
  "metadata": {
    "topic": "technology companies",
    "total_websites": 10,
    "total_emails": 45,
    "run_date": "2024-01-01T12:00:00"
  }
}
```

## Limitations

- Respects robots.txt and website scraping policies
- Rate-limited to avoid overwhelming servers
- May not access websites behind authentication
- Email validation is pattern-based and may have false positives

## Ethical Considerations

This tool is designed for legitimate business purposes such as:
- Lead generation for B2B sales
- Market research
- Contact discovery for partnerships

Please use responsibly and in compliance with:
- GDPR and data protection laws
- CAN-SPAM Act
- Website terms of service
- Robots.txt directives

## Contributing

Contributions are welcome! Please submit pull requests or open issues for bugs and feature requests.

## License

MIT License - See LICENSE file for details
