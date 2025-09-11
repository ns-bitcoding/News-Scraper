import json
import logging
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
from botasaurus.request import Request

logging.basicConfig(level=logging.INFO)


class Scraper:
    def __init__(self, date_str: str):
        self.base_url = self.build_url(date_str)
        self.details = []
        self.headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        }

    def build_url(self, date_str: str) -> str:
        """Convert YYYY-MM-DD → forex factory format (e.g., sep5.2025)"""
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        month_abbr = dt.strftime("%b").lower()   # sep
        day = dt.strftime("%-d")                 # 5 (no leading zero)
        year = dt.strftime("%Y")                 # 2025
        return f"https://www.forexfactory.com/calendar?day={month_abbr}{day}.{year}"

    def fetch_calendar_page(self):
        response = Request().get(self.base_url)
        return BeautifulSoup(response.text, "html.parser")

    def parse_event_row(self, row):
        row_data = {}
        cells = row.find_all("td")
        data_event_id = row["data-event-id"]

        row_data["event_id"] = data_event_id
        row_data["day"] = cells[0].text.split(" ")[0]
        date = cells[0].text.split(" ")[1:]
        row_data["date"] = " ".join(date)
        row_data["time"] = row.find("td", class_="calendar__cell calendar__time").text
        row_data["currency"] = row.find("td", class_="calendar__currency").text.strip()

        # Impact
        impact_class = row.find("td", class_="calendar__cell calendar__impact").find("span")["class"]
        impact_level = [cls.split("icon--ff-impact-")[-1] for cls in impact_class if "icon--ff-impact-" in cls]
        if impact_level[0] == "yel":
            row_data["impact"] = "yellow"
        elif impact_level[0] == "ora":
            row_data["impact"] = "orange"
        elif impact_level[0] == "gra":
            row_data["impact"] = "gray"
        else:
            row_data["impact"] = "red"

        row_data["event"] = row.find("span", class_="calendar__event-title").text.strip()
        row_data["actual"] = row.find("td", class_="calendar__actual").text.strip()
        row_data["forecast"] = row.find("td", class_="calendar__forecast").text.strip()
        row_data["previous"] = row.find("td", class_="calendar__previous").text.strip()

        return row_data

    def scrape(self):
        """Scrape raw calendar data (without history)"""
        soup = self.fetch_calendar_page()
        for row in soup.find_all("tr", attrs={"data-event-id": True}):
            row_data = self.parse_event_row(row)
            self.details.append(row_data)

        # Save raw data
        with open("calendar_data.json", "w") as f:
            json.dump(self.details, f, indent=4)

        return self.details

    def clean_data(self):
        """Clean scraped data and return cleaned JSON"""
        df = pd.read_json("calendar_data.json")

        df.loc[(df.day == "") | (df.day == "All") | df.day.str.contains("all|am|pm", case=False), "day"] = None
        df.day = df.day.ffill()

        df.loc[(df.date == "") | (df.date == "Day"), "date"] = None
        df.date = df.date.ffill()

        df.loc[(df.time == ""), "time"] = None
        df.time = df.time.ffill()

        cleaned_data = df.to_dict(orient="records")

        with open("cleaned_calendar_data.json", "w") as f:
            json.dump(cleaned_data, f, indent=4)

        return cleaned_data


class HistoryScraper:
    def __init__(self):
        self.headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        }

    def fetch_event_history(self, data_event_id):
        url = f"https://www.forexfactory.com/calendar/details/1-{data_event_id}"
        history = list()
        res = Request().get(url, headers=self.headers)
        base_url = 'https://www.forexfactory.com'
        related_news = list()

        news_html = res.json()['data']['linked_threads']['news']
        for html in news_html:
            news_dict = dict()
            try:
                news = BeautifulSoup(html['html'], 'html.parser')
                news_dict['news_url'] = urljoin(base_url, news.find('a')['href']) if news.find('a') else ''
                news_dict['news_title'] = news.find('a')['title'] if news.find('a') else ''
                news_dict['image'] = news.find('img')['src'] if news.find('img') else ''
                news_dict['source'] = news.find('a', attrs={'data-source': True}).text if news.find('a', attrs={'data-source': True}) else ''
                news_dict['content'] = news.select_one('p[class*="flexposts__preview flexposts__preview--pad"]').text if news.select_one('p[class*="flexposts__preview flexposts__preview--pad"]') else ''
                news_dict['date'] = news.select_one('span[class*="flexposts__nowrap flexposts__time"]').text if news.select_one('span[class*="flexposts__nowrap flexposts__time"]') else ''
                news_dict['comment'] = news.select_one('.comments').text.strip('|') if news.select_one('.comments') else ''
            except (KeyError, IndexError, TypeError, AttributeError):
                news_dict = {'news_url': '', 'news_title': '', 'image': '', 'source': '', 'content': '', 'date': '', 'comment': ''}
            related_news.append(news_dict)

        history_forex_data = res.json()['data']['history']['events']
        has_more_key = res.json()['data']['history']
        for data in history_forex_data:
            try:
                event_id = data['event_id']
                has_more = has_more_key['has_more']
                date = data['date']
                actual = data['actual']
                forecast = data['forecast']
                previous = data['previous']
                history.append({'date': date, 'history_actual': actual, 'history_forecast': forecast, 'history_previous': previous})
            except KeyError:
                continue
        return history, related_news, event_id, has_more

    def history_pagination(self, event_id, has_more=True):
        i = 1
        history = list()
        while has_more:
            url = f"https://www.forexfactory.com/calendar/history/1-{event_id}?i={i}"
            response = Request().post(url, headers=self.headers)
            i += 1
            history_forex_data = response.json()['data']['history']['events']
            for data in history_forex_data:
                try:
                    event_id = data['event_id']
                    has_more = response.json()['data']['history']['has_more']
                    date = data['date']
                    actual = data['actual']
                    forecast = data['forecast']
                    previous = data['previous']
                    history.append({'date': date, 'history_actual': actual, 'history_forecast': forecast, 'history_previous': previous})
                except KeyError:
                    continue
        return history
    
    def scrape(self, data_event_id):
        history_data, related_news, event_id, has_more = self.fetch_event_history(data_event_id)
        history_data.extend(self.history_pagination(event_id, has_more))
        return {'data_event_id': data_event_id, 'history_data': history_data, 'related_news': related_news}

import json
import logging
from botasaurus.request import Request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]  # logs to console
)

logger = logging.getLogger(__name__)


class RangeScraper:
    def __init__(self, start_date: str, end_date: str):
        self.url = "https://www.forexfactory.com/calendar/apply-settings/1?navigation=0"
        self.start_date = start_date
        self.end_date = end_date

        self.headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en,en-IN;q=0.9,en-US;q=0.8,hi;q=0.7",
            "content-type": "application/json",
            "origin": "https://www.forexfactory.com",
            "referer": f"https://www.forexfactory.com/calendar?day={start_date}", 
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        }

        self.payload = {
            "default_view": "this_week",
            "impacts": [3, 2, 1, 0],
            "event_types": [1, 2, 3, 4, 5, 7, 8, 9, 10, 11],
            "currencies": [1, 2, 3, 4, 5, 6, 7, 8, 9],
            "begin_date": self.start_date,   
            "end_date": self.end_date        
        }

        logger.info(f"Initialized ForexFactoryRangeScraper with start_date={self.start_date}, end_date={self.end_date}")

    def scrape(self):
        """Fetch economic calendar events for given date range"""
        logger.info(f"Sending POST request to {self.url} for date range {self.start_date} → {self.end_date}")

        try:
            r = Request().post(
                self.url,
                headers=self.headers,
                data=json.dumps(self.payload)
            )
            logger.info("Request successful")
        except Exception as e:
            logger.error(f"Request failed: {e}", exc_info=True)
            raise

        try:
            data = r.json()
            logger.info(f"Parsed JSON response successfully with {len(data.get('days', []))} days of data")
        except Exception as e:
            logger.warning(f"Failed to parse JSON, returning raw text. Error: {e}")
            data = r.text

        with open("calendar_range.json", "w") as f:
            json.dump(data, f, indent=4)
            logger.info("Saved raw response to calendar_range.json")

        return data
    
    def parse_events(self, raw_json):
        """Convert raw API JSON into cleaned format"""
        logger.info("Parsing events from raw JSON")
        details = []

        try:
            for day in raw_json.get("days", []):
                events = day.get("events", [])
                logger.info(f"Processing {len(events)} events for day {day.get('date')}")

                for ev in events:
                    impact_class = ev.get("impactClass", "")
                    impact_level = impact_class.split("-")[-1] if impact_class else None

                    if impact_level == "yel":
                        impact = "yellow"
                    elif impact_level == "ora":
                        impact = "orange"
                    elif impact_level == "gra":
                        impact = "gray"
                    else:
                        impact = "red"

                    row_data = {
                        "event_id": ev.get("id"),
                        "day": day.get("date").split(" ")[0],   
                        "date": ev.get("date"),
                        "time": ev.get("timeLabel"),
                        "currency": ev.get("currency"),
                        "impact": impact,
                        "event": ev.get("name"),
                        "actual": ev.get("actual"),
                        "forecast": ev.get("forecast"),
                        "previous": ev.get("previous"),
                    }
                    details.append(row_data)
            
            logger.info(f"Parsed total {len(details)} events successfully")

        except Exception as e:
            logger.error(f"Error while parsing events: {e}", exc_info=True)

        return details

    def scrape_cleaned(self):
        """Scrape + return cleaned events"""
        logger.info("Starting scrape_cleaned process")
        raw = self.scrape()  
        logger.info("Raw data fetched, now parsing")
        cleaned = self.parse_events(raw)
        logger.info(f"Scrape completed with {len(cleaned)} cleaned events")
        return cleaned