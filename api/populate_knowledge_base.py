import bs4
import concurrent.futures
import os
import re
import requests
import xml.etree.ElementTree as ET

import redis

from chatbot.redis_utils import add_to_redis


def parse_url(url: str) -> str:
    res = requests.get(url, timeout=10)
    if res.status_code != 200:
        raise Exception(f"Status code: {res.status_code}")
    bs4_obj = bs4.BeautifulSoup(res.content, "html.parser")
    sections = bs4_obj.find_all("section")
    text = []
    for section in sections:
        text.append(section.text.strip())
    return "\n".join([t for t in text])


def get_urls(sitemap_url: str, patterns: list[str]) -> list[str]:
    """
    Given a sitemap url and a pattern, return all urls that match the pattern
    """
    urls = []
    res = requests.get(sitemap_url, timeout=10)
    if res.status_code != 200:
        raise Exception(f"Status code: {res.status_code}")
    for entry in ET.fromstring(res.content):
        url = entry[0].text
        for pattern in patterns:
            if not re.search(pattern, url):
                continue
            urls.append(url)
    return urls


def get_text_from_urls(urls: list[str]) -> dict[str, str]:
    """
    Given a list of urls, return a dictionary of url: text
    """
    url_text_dict = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        # Start the load operations and mark each future with its URL
        res = {executor.submit(parse_url, url): url for url in urls}
        for future in concurrent.futures.as_completed(res):
            url = res[future]
            try:
                data = future.result()
                url_text_dict[url] = data
            except Exception as exc:
                print('%r generated an exception: %s' % (url, exc))
    return url_text_dict


def main():
    print("connecting to Redis...")
    redis_client = redis.from_url(url=os.getenv("REDIS_URL", ""), 
        encoding='utf-8',
        decode_responses=True,
        socket_timeout=30.0)
    print("checking Redis connection...")
    if not redis_client or not redis_client.ping():
        raise Exception("Redis connection failed")
    print("Connected to Redis")

    sitemap_url = "https://eng.libretexts.org/sitemap.xml"
    books =  ["Phase_Relations_in_Reservoir_Engineering_\(Adewumi\)",]
    urls = get_urls(sitemap_url, books)
    url_text_dict = get_text_from_urls(urls)
    for url, text in url_text_dict.items():
        print(f"Adding: {url}")
        add_to_redis.add_text_to_redis(redis_client, text, url)


if __name__ == "__main__":
    main()
