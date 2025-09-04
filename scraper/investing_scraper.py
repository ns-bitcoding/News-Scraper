import json
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from botasaurus.request import Request

logging.basicConfig(level=logging.INFO)


def latest_news():
    """
    Fetch latest news from Investing.com
    Returns:
        list: Parsed latest news articles
    """
    URL = "https://www.investing.com/news/latest-news"
    HEADERS = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'content-type': 'application/x-www-form-urlencoded',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest'
    }

    logging.info(f"Fetching latest news from {URL}")

    try:
        response = Request().get(URL, headers=HEADERS)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Error fetching latest news: {e}")
        return {"error": f"Failed to fetch: {e}"}

    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        json_data = json.loads(soup.find('script', id="__NEXT_DATA__").text)
        news_data = json_data['props']['pageProps']['state']['newsStore']['_news']
    except Exception as e:
        logging.error(f"Error parsing JSON from page: {e}")
        return {"error": f"Failed to parse JSON: {e}"}

    details = []
    base_url = "https://www.investing.com/"

    for data in news_data:
        try:
            dd = {
                "url": urljoin(base_url, data.get("link", "")),
                "source": data.get("source_name", ""),
                "time": data.get("date", ""),
                "image": data.get("imageHref", ""),
                "image_copyright": data.get("image_copyright", ""),
                "title": data.get("title", ""),
                "content": data.get("body", "")
            }
            details.append(dd)
        except Exception as e:
            logging.warning(f"Error parsing article: {e}")

    logging.info(f"Successfully parsed {len(details)} articles from Investing.com latest news.")
    return details


def scrape_keyword(keyword: str):
    """
    Search Investing.com news by keyword
    Args:
        keyword (str): Search keyword
    Returns:
        list: Parsed news articles
    """
    URL = "https://www.investing.com/search/service/SearchInnerPage"
    PAYLOAD = f'search_text={keyword.replace(" ", "%2520")}&tab=news&isFilter=true'
    HEADERS = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'content-type': 'application/x-www-form-urlencoded',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest'
    }

    logging.info("Sending request to Investing.com API...")

    try:
        response = Request().post(URL, headers=HEADERS, data=PAYLOAD)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Error fetching the URL: {e}")
        return []

    try:
        news_data = response.json().get('news', [])
    except Exception as e:
        logging.error(f"Error parsing JSON response: {e}")
        return []

    details = []
    logging.info(f"Parsing {len(news_data)} news articles...")

    for data in news_data:
        try:
            dd = {
                "url": urljoin("https://www.investing.com/", data.get("link", "")),
                "source": data.get("providerName", ""),
                "time": data.get("date", ""),
                "image": data.get("image", ""),
                "title": data.get("name", ""),
                "content": data.get("content", "")
            }
            if dd.get("title"):  # only append valid news
                details.append(dd)
        except Exception as e:
            logging.warning(f"Error parsing news item: {e}")

    logging.info(f"Successfully parsed {len(details)} news articles.")
    return details


def detail_page(url: str):
    """
    Fetch and parse article detail page from Investing.com
    Args:
        url (str): Article URL
    Returns:
        dict: Parsed article details
    """
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
    }

    logging.info(f"Fetching detail page: {url}")
    try:
        response = Request().get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Error fetching detail page: {e}")
        return {"error": f"Failed to fetch URL: {e}"}

    soup = BeautifulSoup(response.text, 'html.parser')
    details = list()

    try:
        dd = {}
        # JSON data
        data = json.loads(soup.find('script', id="__NEXT_DATA__").text)

        # Title
        dd['title'] = soup.find('h1', id="articleTitle").text.strip() if soup.find('h1', id="articleTitle") else ''

        # Source
        dd['source'] = data['props']['pageProps']['state']['newsStore']['_article']['source_name']

        # Image + copyright
        img_result = []
        img_tag = soup.find('img', class_="h-full w-full object-contain")
        image_of_news = img_tag['src'] if img_tag else ''
        copyright = (
            data['props']['pageProps']['state']['newsStore']['_article']['media'][0]['copyright']
            if data['props']['pageProps']['state']['newsStore']['_article'].get('media') else ''
        )
        img_result.append({
            'image_text': copyright,
            'image': image_of_news
        })
        dd['image'] = img_result

        # Content
        dd['content'] = soup.find('div', id="article").text.strip() if soup.find('div', id="article") else ''

        # Text links
        text_link_results = []
        base_url = 'https://www.investing.com/'
        text_links = soup.find_all('a', class_="aqlink js-hover-me")
        for textlink in text_links:
            text_name = textlink.text
            text_href = urljoin(base_url, textlink['href'])
            text_link_results.append({
                'text_name': text_name,
                'text_href': text_href
            })
        dd['text_link'] = text_link_results

        # Date and time
        date_and_time = soup.select_one('div[class^="flex flex-col gap-2 text-warren-gray"] div')
        updated_date = date_and_time.find_next_sibling('div') if date_and_time else None
        if updated_date:
            dd['posted_date'] = updated_date.text.strip('Updated ').split(', ')[0]
            dd['posted_time'] = updated_date.text.strip('Updated ').split(', ')[1]
        elif date_and_time:
            dd['posted_date'] = date_and_time.text.strip('Published ').split(', ')[0]
            dd['posted_time'] = date_and_time.text.strip('Published ').split(', ')[1]
        else:
            dd['posted_date'] = ''
            dd['posted_time'] = ''

        details.append(dd)

        logging.info("Successfully parsed detail page.")

    except Exception as e:
        logging.error(f"Error parsing detail page: {e}")
        return {"error": f"Failed to parse details: {e}"}

    return details


# def multi_detail_page(urls: list[str]):
#     """
#     Fetch and parse multiple article detail pages from Investing.com
#     Args:
#         urls (list): List of article URLs
#     Returns:
#         list: Parsed details for each URL
#     """
#     results = []
#     for url in urls:
#         try:
#             detail = detail_page(url)
#             results.append({
#                 "url": url,
#                 "data": detail
#             })
#         except Exception as e:
#             results.append({
#                 "url": url,
#                 "error": str(e)
#             })
#     return results