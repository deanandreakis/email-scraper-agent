# Email Scraper AI Agent

An intelligent AI agent that uses the Google Agent Development Kit and Crawlee web scraper to automatically find and extract email addresses from websites based on a given topic or classification.

## Features

- **AI-Powered Search**: Uses Google Agent Development Kit to intelligently search for relevant websites
- **Efficient Web Scraping**: Leverages Crawlee for robust and scalable web scraping
- **Email Extraction**: Automatically identifies and extracts email addresses from web pages
- **Topic-Based Discovery**: Finds websites related to your specified classification or topic
- **Data Storage**: Saves extracted emails in multiple formats (CSV, JSON)

## Prerequisites

- Python 3.9 or higher
- Google API credentials (for Agent Development Kit)
- Internet connection

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd email-scraper-agent
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
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
python main.py --topic "technology companies" --max-sites 15 --output emails.csv
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

## Project Structure

```
email-scraper-agent/
├── agent.py              # Main agent orchestration
├── scraper.py            # Crawlee-based web scraper
├── email_extractor.py    # Email extraction utilities
├── config.py             # Configuration management
├── main.py               # CLI interface
├── requirements.txt      # Python dependencies
├── .env.example          # Example environment file
└── README.md             # This file
```

## How It Works

1. **Topic Analysis**: The agent uses Google's AI to understand the topic and generate relevant search queries
2. **Website Discovery**: Searches for and identifies websites matching the classification
3. **Web Scraping**: Uses Crawlee to efficiently crawl identified websites
4. **Email Extraction**: Applies regex patterns and validation to extract email addresses
5. **Data Storage**: Saves unique emails with metadata (source, timestamp, confidence)

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
