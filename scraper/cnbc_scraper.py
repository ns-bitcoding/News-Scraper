import logging
import requests
from bs4 import BeautifulSoup


logging.basicConfig(level=logging.INFO)


def scrape():
    URL = "https://www.cnbc.com/world/?region=world"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    }

    try:
        response = requests.get(URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Error fetching the URL: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    details = list()
    latest_news = soup.select(".LatestNews-container")

    for news in latest_news:
        try:
            dd = {
                "news_url": news.select_one("a.LatestNews-headline")["href"] if news.select_one("a.LatestNews-headline") else "",
                "title": news.select_one("a.LatestNews-headline").text.strip() if news.select_one("a.LatestNews-headline") else "",
                "time": news.select_one("time").text.strip() if news.select_one("time") else ""
            }
            if dd.get("news_url") or dd.get("title"):
                details.append(dd)
        except Exception as e:
            logging.warning(f"Error parsing news item: {e}")

    return details
