from fastapi import FastAPI, HTTPException, Request
from scraper import cnbc_scraper

app = FastAPI()

# Mapping: domain → scraper function
SCRAPERS = {
    "cnbc": cnbc_scraper.scrape
    # Add more scrapers here later
}

# For Multihit
@app.get("/v1/{domain}/latest-news")
async def latest_news(domain: str):
    """
    Get latest news for a given domain
    Example: GET /v1/cnbc/latest-news
    """
    scraper = SCRAPERS.get(domain.lower())
    if not scraper:
        raise HTTPException(status_code=404, detail=f"No scraper found for domain '{domain}'")
    return scraper()


# For direct-hit
@app.post("/v1/{domain}/detail-page")
async def search_news(domain: str, request: Request):
    """
    Search news for a given domain using keyword in payload
    Example: POST /v1/cnbc/detail-page
    Payload: {"keyword": "stock"}
    """
    scraper = SCRAPERS.get(domain.lower())
    if not scraper:
        raise HTTPException(status_code=404, detail=f"No scraper found for domain '{domain}'")

    data = await request.json()
    keyword = data.get("keyword", "").lower()

    if not keyword:
        raise HTTPException(status_code=400, detail="Keyword is required in payload")

    results = []
    for news in scraper():
        if keyword in news.get("title", "").lower():
            results.append(news)

    return {"keyword": keyword, "results": results}


"""
Run the app with:
    uvicorn app:app --reload

In Postman:

1. GET latest news:
   GET http://localhost:8000/v1/cnbc/latest-news

2. Search news:
   POST http://localhost:8000/v1/cnbc/detail-page
   Body (JSON):
   {
     "keyword": "stock"
   }
"""
