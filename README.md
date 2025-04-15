# TaurBull Scraper

A tool for automatically scraping TaurBull website content and uploading it to Elevenlabs Knowledge Base to keep your AI assistant updated with the latest information.

## Features

- Automatically scrapes FAQs from the TaurBull website
- Uploads content to Elevenlabs Knowledge Base
- Associates documents with your Elevenlabs assistant
- Configurable update interval
- Environment-based configuration with `.env` file support

## Installation

### Prerequisites
- Python 3.8 or higher
- Elevenlabs account with API access and an existing assistant

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/taurbull_scraper.git
   cd taurbull_scraper
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root:
   ```
   ELEVENLABS_API_KEY=your_api_key_here
   ELEVENLABS_ASSISTANT_ID=your_assistant_id_here
   UPDATE_INTERVAL=24  # Optional, defaults to 24 hours
   ```

## Usage

### Running the Scraper

To run the scraper with the configuration from your `.env` file:

```bash
python main.py
```

You can also override the assistant ID via command line:

```bash
python main.py --assistant-id YOUR_ASSISTANT_ID
```

### Testing the Integration

To verify that your setup is working correctly:

```bash
python test_integration.py
```

This will check:
- API connection
- Knowledge base access
- Assistant integration
- Document creation/deletion

### Scheduling Regular Updates

#### Using Cron (Linux/Mac)

To run the scraper daily at 2 AM:

```bash
crontab -e
```

Add the following line:

```
0 2 * * * cd /path/to/taurbull_scraper && python main.py
```

#### Using Task Scheduler (Windows)

1. Open Task Scheduler
2. Create a Basic Task
3. Set the trigger to Daily
4. For the Action, select "Start a Program"
5. Browse to your Python executable
6. Add arguments: `/path/to/taurbull_scraper/main.py`

## Finding Your Assistant ID

For detailed instructions on finding your Elevenlabs Assistant ID, see [ASSISTANT_GUIDE.md](ASSISTANT_GUIDE.md).

## Project Structure

```
taurbull_scraper/
├── main.py                 # Main script to run the scraper
├── elevenlabs_api.py       # Elevenlabs API integration
├── scrapers/
│   ├── faq_scraper.py      # Scraper for TaurBull FAQs
│   └── ...                 # Other scrapers
├── knowledge_base.py       # Knowledge base management
├── test_integration.py     # Integration test script
├── .env                    # Configuration file (create this)
├── data/                   # Scraped data storage
└── logs/                   # Log files
```

## Troubleshooting

### Common Issues

1. **API Key Invalid**
   - Verify your API key is correct
   - Check that your account has API access enabled

2. **Assistant ID Not Found**
   - Confirm you've entered the correct Assistant ID
   - See ASSISTANT_GUIDE.md for instructions

3. **Knowledge Base Upload Failures**
   - Check your subscription plan limits
   - Verify document size is within allowed limits

### Logs

Log files are stored in the `logs/` directory and can be useful for diagnosing issues.

## Project Progress

For information about the current state of the project and upcoming features, see [PROJECT_PROGRESS.md](PROJECT_PROGRESS.md).

## License

[MIT License](LICENSE)
