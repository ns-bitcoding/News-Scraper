import re
import json
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote


logging.basicConfig(level=logging.INFO)


def latest_news():
    """
    Fetch latest news from cnbc.com
    Returns:
        list: Parsed latest news articles
    """

    URL = "https://www.cnbc.com/world/?region=world"
    HEADERS = {
        'accept': '*/*',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,bho;q=0.7',
        'content-type': 'application/json',
        'origin': 'https://www.cnbc.com',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
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


def scrape_keyword(keyword: str):
    """
    Search CNBC news articles by keyword.
    Args:
        keyword (str): Search keyword
    Returns:
        list: Parsed search results
    """
    BASE_URL = "https://api.queryly.com/cnbc/json.aspx"
    QUERYLY_KEY = "31a35d40a9a64ab3"
    HEADERS = {
        'accept': '*/*',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
    }

    query = quote(keyword)
    url = f"{BASE_URL}?queryly_key={QUERYLY_KEY}&query={query}"

    logging.info(f"Searching CNBC for keyword: {keyword}")

    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Error fetching search results: {e}")
        return {"error": f"Failed to fetch: {e}"}

    try:
        news_data = response.json().get('results', [])
    except Exception as e:
        logging.error(f"Error parsing JSON response: {e}")
        return {"error": f"Failed to parse JSON: {e}"}

    details = []
    for data in news_data:
        try:
            dd = {
                "news_url": data.get("url", ""),
                "title": data.get("cn:title", ""),
                "section": data.get("section", ""),
                "image": data.get("cn:promoImage", ""),
                "posted_date_time": data.get("cn:lastPubDate", "")
            }
            details.append(dd)
        except Exception as e:
            logging.warning(f"Error parsing article: {e}")

    logging.info(f"Successfully fetched {len(details)} search results for keyword '{keyword}'.")
    return details


def detail_page(url: str):
    """
    Fetch detailed news article data from CNBC.
    Args:
        url (str): CNBC article URL
    Returns:
        dict: Parsed article details
    """
    HEADERS = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
    }

    logging.info(f"Fetching article details from {url}")

    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Error fetching page: {e}")
        return {"error": f"Failed to fetch: {e}"}

    try:
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract JSON from script
        script_tag = soup.find('script', attrs={'charset': "UTF-8"})
        json_match = re.search(r'window\.__s_data\s*=\s*(\{.*?\});', script_tag.string if script_tag else "")
        if not json_match:
            logging.error("Failed to extract JSON data")
            return {"error": "No JSON data found"}

        json_string = json_match.group(1)
        json_data = json.loads(json_string)

        dd = {}

        dd['url'] = json_data['page']['page'].get('url', url)
        dd['title'] = json_data['page']['page'].get('headline', '')

        # Image and credits
        image = soup.select_one('meta[itemprop="image"]')
        image_credit = soup.select_one('div.InlineImage-imageEmbedCredit')
        dd['image_data'] = [{
            "image_text": image_credit.get_text(strip=True) if image_credit else None,
            "image": image['content'] if image else None
        }]

        # Key points
        key_points = soup.select_one('div.RenderKeyPoints-list div.group')
        dd['key_points'] = key_points.get_text(strip=True) if key_points else ""

        # Content
        contents = soup.select('div.ArticleBody-articleBody div.group')
        dd['content'] = " ".join(tag.get_text(strip=True) for tag in contents)

        # Text links inside article
        dd['text_link'] = list()
        text_link = soup.select('div.group p a')  

        for data in text_link:
            try:
                text_name = data.text.strip()
                text_href = urljoin("https://www.cnbc.com/", data['href'])
                if text_href:
                    dd['text_link'].append(
                        {
                        'text_name': text_name,
                        'text_link': text_href
                        }
                    )
            except Exception as e:
                logging.warning(f"Error parsing text_link: {e}")

        # Date & time
        date_modified = soup.select_one('time[itemprop="dateModified"]')
        date_published = soup.select_one('time[itemprop="datePublished"]')
        datetime_text = (
            date_modified.get_text("  ", strip=True) if date_modified
            else date_published.get_text("  ", strip=True) if date_published
            else ""
        )

        if datetime_text:
            parts = datetime_text.replace("Published ", "").split("  ")
            dd['posted_date'] = parts[0] if len(parts) > 0 else ""
            dd['posted_time'] = parts[1] if len(parts) > 1 else ""
        else:
            dd['posted_date'] = ""
            dd['posted_time'] = ""

        logging.info(f"Successfully parsed article: {dd['title']}")
        return dd

    except Exception as e:
        logging.error(f"Error parsing article details: {e}")
        return {"error": f"Failed to parse: {e}"}
