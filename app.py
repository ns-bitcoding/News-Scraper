from fastapi import FastAPI, HTTPException, Request
from scraper import cnbc_scraper, investing_scraper

app = FastAPI()

# Mapping: domain → scraper functions
SCRAPERS = {
    "cnbc": {
        "latest": cnbc_scraper.scrape,
        # "detail": cnbc_scraper.detail_page,
        # "search": cnbc_scraper.scrape
    },
    "investing": {
        "latest": investing_scraper.latest_news,
        "detail": investing_scraper.detail_page,
        "search": investing_scraper.scrape_keyword
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
