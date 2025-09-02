import os
import time
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from botasaurus.request import Request
from concurrent.futures import ThreadPoolExecutor, as_completed


class Scraper:
    def __init__(self, url, json_file):
        self.url = url
        self.json_file = json_file
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        }
        self.details = list()
        self.existing_urls = set()
        self.load_existing_data()

    def load_existing_data(self):
        if os.path.exists(self.json_file):
            with open(self.json_file, 'r') as f:
                existing_data = json.load(f)
                self.details = existing_data
                self.existing_urls = {item['url'] for item in existing_data}

    def scrape_article(self, news_url):
        print(f"Scraping: {news_url}")
        response = Request().get(news_url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        data = json.loads(soup.find('script', id="__NEXT_DATA__").text) if soup.find('script', id="__NEXT_DATA__") else ''

        dd = dict()
        dd['url'] = news_url
        dd['title'] = soup.find('h1', id="articleTitle").text.strip() if soup.find('h1', id="articleTitle") else ''
        dd['source'] = data['props']['pageProps']['state']['newsStore']['_article']['source_name']

        img_result = list()
        img_tag = soup.find('img', class_="h-full w-full object-contain")
        image_of_news = img_tag['src'] if img_tag else ''
        copyright = data['props']['pageProps']['state']['newsStore']['_article']['media'][0]['copyright'] if data else ''
        img_result.append({
            'image_text':copyright, 
            'image':image_of_news
        })
        dd['image'] = img_result

        dd['content'] = soup.find('div', id="article").text.strip() if soup.find('div', id="article") else ''

        text_link_results = list()
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

        date_and_time = soup.select_one('div[class^="flex flex-col gap-2 text-warren-gray"] div')
        updated_date = date_and_time.find_next_sibling('div')
        if updated_date:
            dd['posted_date'] = updated_date.text.strip('Updated ').split(', ')[0]
            dd['posted_time'] = updated_date.text.strip('Updated ').split(', ')[1]
        else:
            dd['posted_date'] = date_and_time.text.strip('Published ').split(', ')[0]
            dd['posted_time'] = date_and_time.text.strip('Published ').split(', ')[1]

        return dd

    def scrape(self):
        while True:
            main_response = Request().get(url, headers=self.headers)
            main_soup = BeautifulSoup(main_response.text, 'html.parser')

            main_urls = main_soup.select('div[class*="list_primary"] div li a')[:9]
            main_urls = [urljoin(url, tag['href']) for tag in main_urls]

            for main_section_url in main_urls:
                print(f"\nProcessing main section: {main_section_url}")

                try:
                    response = Request().get(main_section_url, headers=self.headers)
                    soup = BeautifulSoup(response.text, 'html.parser')

                    news_tags = soup.select('a[class*="text-link hover:text-link hover:underline focus:text-link focus:underline whitespace"]')
                    news_urls = [urljoin(url, tag['href']) for tag in news_tags]

                    new_urls = [u for u in news_urls if u not in self.existing_urls]
                    print(f"Found {len(new_urls)} new articles to scrape.")

                    with ThreadPoolExecutor(max_workers=5) as executor:
                        futures = [executor.submit(self.scrape_article, news_url) for news_url in new_urls]
                        for future in as_completed(futures):
                            result = future.result()
                            if result and result['url'] not in self.existing_urls:
                                self.details.append(result)
                                self.existing_urls.add(result['url'])

                    with open(self.json_file, 'w') as f:
                        json.dump(self.details, f, indent=4)

                except Exception as e:
                    print(f"Error processing {main_section_url}: {e}")

                print("Waiting 30 seconds before next main section...\n")
                time.sleep(30)  

            print("Waiting 2 minutes before restarting the full loop...\n")
            time.sleep(120)


if __name__ == "__main__":
    url = "https://www.investing.com/news/"
    scraper = Scraper(url, 'news_data.json')
    scraper.scrape()