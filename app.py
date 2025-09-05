from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Request
from scraper import cnbc_scraper, investing_scraper, forexfactory_scraper

app = FastAPI()

class CalendarRequest(BaseModel):
    date: str  

class RangeRequest(BaseModel):
    start_date: str  # Format: YYYY-MM-DD
    end_date: str    # Format: YYYY-MM-DD

# Mapping: domain → scraper functions
SCRAPERS = {
    "cnbc": {
        "latest": cnbc_scraper.latest_news,
        "detail": cnbc_scraper.detail_page,
        "search": cnbc_scraper.scrape_keyword
    },
    "investing": {
        "latest": investing_scraper.latest_news,
        "detail": investing_scraper.detail_page,
        "search": investing_scraper.scrape_keyword
    },
    "forexfactory": {
        "calendar": forexfactory_scraper.Scraper,
        "history": forexfactory_scraper.HistoryScraper,
        "date_range": forexfactory_scraper.RangeScraper
    }
}


@app.get("/v1/{domain}/latest-news")
async def latest_news(domain: str):
    """
    Get latest news for a given domain
    Example: GET /v1/investing/latest-news
    """
    scraper_map = SCRAPERS.get(domain.lower())
    if not scraper_map or "latest" not in scraper_map:
        raise HTTPException(status_code=404, detail=f"No scraper found for domain '{domain}'")

    return scraper_map["latest"]()


@app.post("/v1/{domain}/detail-page")
async def detail_news(domain: str, request: Request):
    """
    Get full detail page of a news article for a given domain
    Example: POST /v1/investing/detail-page
    Payload: {"url": "https://www.investing.com/news/..."}
    """
    scraper_map = SCRAPERS.get(domain.lower())
    if not scraper_map or "detail" not in scraper_map:
        raise HTTPException(status_code=404, detail=f"No scraper found for domain '{domain}'")

    data = await request.json()
    url = data.get("url", "")

    if not url:
        raise HTTPException(status_code=400, detail="URL is required in payload")

    return scraper_map["detail"](url)


@app.post("/v1/{domain}/search-news")
async def search_news(domain: str, request: Request):
    """
    Search news for a given domain using keyword
    Example: POST /v1/investing/search-news
    Payload: {"keyword": "gold market"}
    """
    scraper_map = SCRAPERS.get(domain.lower())
    if not scraper_map or "search" not in scraper_map:
        raise HTTPException(status_code=404, detail=f"No scraper found for domain '{domain}'")

    data = await request.json()
    keyword = data.get("keyword", "").strip()

    if not keyword:
        raise HTTPException(status_code=400, detail="Keyword is required in payload")

    return scraper_map["search"](keyword)

@app.post("/v1/{domain}/calendar")
async def calendar(domain: str, req: CalendarRequest):
    """
    Get economic calendar for a given domain
    Example: POST /v1/forexfactory/calendar
    Body: { "date": "2025-09-05" }
    """
    scraper_map = SCRAPERS.get(domain.lower())
    if not scraper_map or "calendar" not in scraper_map:
        raise HTTPException(status_code=404, detail=f"No calendar scraper found for domain '{domain}'")
    try:
        scraper_class = scraper_map["calendar"]
        scraper = scraper_class(req.date)

        raw_data = scraper.scrape()
        cleaned_data = scraper.clean_data()
        return {
            "date": req.date,
            "count": len(cleaned_data),
            "data": cleaned_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/v1/{domain}/range")
async def get_range(domain: str, req: RangeRequest):
    """
    Fetch ForexFactory economic calendar for a date range.
    Example: POST /v1/forexfactory/range
    Body: { "start_date": "2025-09-01", "end_date": "2025-09-05" }
    """
    scraper_map = SCRAPERS.get(domain.lower())
    if not scraper_map or "date_range" not in scraper_map:
        raise HTTPException(status_code=404, detail=f"No range scraper found for domain '{domain}'")

    try:
        scraper_class = scraper_map["date_range"]
        scraper = scraper_class(req.start_date, req.end_date)

        raw_data = scraper.scrape()
        cleaned_data = scraper.parse_events(raw_data)

        if not cleaned_data:
            raise HTTPException(status_code=404, detail=f"No events found between {req.start_date} and {req.end_date}")

        return {
            "start_date": req.start_date,
            "end_date": req.end_date,
            "count": len(cleaned_data),
            "data": cleaned_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/v1/{domain}/history")
async def get_history(domain: str, request: Request):
    """
    Fetch history data for an event by event_id
    Example: POST /v1/forexfactory/history
    Payload: {"event_id": "120345"}
    """
    scraper_map = SCRAPERS.get(domain.lower())
    if not scraper_map or "history" not in scraper_map:
        raise HTTPException(status_code=404, detail=f"No history scraper found for domain '{domain}'")

    data = await request.json()
    event_id = data.get("event_id", "")
    if not event_id:
        raise HTTPException(status_code=400, detail="event_id is required")

    try:
        history_scraper_class = scraper_map["history"]
        history_scraper = history_scraper_class()

        history_data = history_scraper.scrape(event_id)

        if not history_data:
            raise HTTPException(status_code=404, detail=f"No history data found for event_id {event_id}")

        return history_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# """
# Run the app with:
#     uvicorn app:app --reload

# In Postman:

# 1. GET latest news:
#    GET http://localhost:8000/v1/cnbc/latest-news

# 2. Search news:
#    POST http://localhost:8000/v1/cnbc/detail-page
#    Body (JSON):
#    {
#      "keyword": "stock"
#    }
# """