# News Scraper API

A FastAPI-based web service that scrapes news and financial data from various sources including CNBC, Investing.com, and Forex Factory.

## Features

* **Multi-source Support**: Scrape data from CNBC, Investing.com, and Forex Factory
* **RESTful API**: Easy-to-use endpoints for different types of data retrieval
* **Asynchronous Processing**: Built with FastAPI for high performance
* **Structured Data**: Returns well-formatted JSON responses

## Supported Endpoints

### CNBC & Investing.com

* `GET /v1/{domain}/latest-news` - Get latest news
* `POST /v1/{domain}/search-news` - Search news by keyword
* `POST /v1/{domain}/detail-page` - Get detailed article content

### Forex Factory

* `POST /v1/forexfactory/calendar` - Get economic calendar for a specific date
* `POST /v1/forexfactory/range` - Get calendar data for a date range
* `POST /v1/forexfactory/history` - Get historical event data

## Request Models

* **DetailRequest**: `{ "url": "https://example.com/article" }`
* **SearchRequest**: `{ "keyword": "bitcoin" }`
* **CalendarRequest**: `{ "date": "YYYY-MM-DD" }`
* **RangeRequest**: `{ "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD" }`
* **HistoryRequest**: `{ "event_id": "12345" }`

## Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd news
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

Start the FastAPI development server:

```bash
uvicorn app:app --reload
```

The API will be available at `http://127.0.0.1:8000`

## API Documentation

Once the server is running, access:

* Interactive API docs: `http://127.0.0.1:8000/docs`

## Project Structure

```
news/
│
├── app.py                     # Main FastAPI application with API endpoints
├── .gitignore                 # Git ignore file
├── requirements.txt           # Python dependencies
├── README.md                  # Project documentation
│
├── scraper/                   # Scraper implementations
│   ├── cnbc_scraper.py        # Fetches news from CNBC
│   ├── investing_scraper.py   # Scrapes news from Investing.com
│   ├── forexfactory_scraper.py# Retrieves Forex Factory calendar
│   ├── checker.py             # Counts keyword occurrences in news articles
│   └── keywords.txt           # List of keywords for news filtering
│
└── venv/                      # Python virtual environment
```

### Key Components

1. **API Layer** (`app.py`):

   * FastAPI application with RESTful endpoints
   * Handles requests and routes them to appropriate scrapers
   * Input validation using Pydantic models

2. **Scrapers** (`scraper/`):

   * `cnbc_scraper.py`: Fetches news articles from CNBC
   * `investing_scraper.py`: Scrapes news articles from Investing.com
   * `forexfactory_scraper.py`: Retrieves economic calendar and historical data from Forex Factory
   * `checker.py`: Counts keyword occurrences in news article titles and content from a JSON file

## Dependencies

* FastAPI - Web framework
* Uvicorn - ASGI server
* BeautifulSoup4 - HTML parsing
* Requests - HTTP requests
* Pandas - Data manipulation
* Python-dotenv - Environment variable management

## Example Usage

### Get Latest News from CNBC

```bash
curl -X 'GET' \
  'http://127.0.0.1:8000/v1/cnbc/latest-news' \
  -H 'accept: application/json'
```

### Search for News

```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/v1/cnbc/search-news' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{"keyword": "bitcoin"}'
```

### Get Article Details

```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/v1/cnbc/detail-page' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://example.com/article"}'
```

### Get Economic Calendar

```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/v1/forexfactory/calendar' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{"date": "2023-11-01"}'
```

### Get Calendar Data for a Date Range

```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/v1/forexfactory/range' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{"start_date": "2023-11-01", "end_date": "2023-11-07"}'
```

### Get Historical Event Data

```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/v1/forexfactory/history' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{"event_id": "12345"}'
```
