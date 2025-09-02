import json

with open("news_data.json", "r") as f:
    data = json.load(f)

def load_keywords_from_file(filepath):
    with open(filepath, "r") as f:
        keywords = [line.strip().lower() for line in f if line.strip()]
    return keywords


def count_keywords(text, keywords):
    count = 0
    text_lower = text.lower()
    for keyword in keywords:
        if keyword.lower() in text_lower:
            count += 1
    return count


keywords = load_keywords_from_file("keywords.txt")

for idx, item in enumerate(data):
    title = item['title']
    content = item["content"]
    url = item['url']
    count_title = count_keywords(title, keywords)
    count_content = count_keywords(content, keywords)
    print(f"URL: {url}")
    print(f"{count_title} keyword matches in Title.")
    print(f"{count_content} keyword matches in Content.")