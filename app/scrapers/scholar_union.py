import json
import time

import requests
from bs4 import BeautifulSoup

SCRAPING_SITE = "Scholarship Union"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection":      "keep-alive",
}


def get_details(url: str, title: str) -> dict | None:
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"No information found for: {title}\nURL: {url}")
        return None

    soup      = BeautifulSoup(response.text, "lxml")
    all_text  = soup.find("div", class_="entry-content")
    if not all_text:
        print(f"No content found for: {url}")
        return None

    headings = all_text.find_all("h2")
    if not headings:
        print(f"No headings found for: {url}")
        return None

    section = {}
    for heading in headings:
        heading_text    = heading.get_text(strip=True)
        section_content = []
        list_buffer     = []

        for sibling in heading.find_next_siblings():
            if sibling.name == "h2":
                break
            if sibling.name in ["ul", "ol"]:
                for li in sibling.find_all("li"):
                    text = li.get_text(strip=True)
                    if text:
                        list_buffer.append(text)
                section_content.append(list_buffer)
                list_buffer = []
            elif sibling.name == "p":
                text = sibling.get_text(strip=True)
                if text:
                    section_content.append(text)

        if heading_text:
            section[heading_text] = section_content

    return {"title": title, "data": section}


def scrape() -> list[dict]:
    scraped_titles = set()
    results        = []
    page           = 1

    while page < 2:
        url = (
            "https://scholarshipunion.com/scholarships-list/"
            if page == 1
            else f"https://scholarshipunion.com/scholarships-list/page/{page}/"
        )

        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"[FATAL] Webpage not found: {url}\nPage: {page}")
            break

        soup     = BeautifulSoup(response.text, "lxml")
        articles = soup.find_all("article", class_="up-listing-card")
        if not articles:
            print(f"No articles found on page {page}")
            page += 1
            time.sleep(1)
            continue

        for article in articles:
            name_tag = article.find("h3")
            if not name_tag or not name_tag.a or not name_tag.a.get("href"):
                print(f"No name found in article")
                continue
            more_info = name_tag.a["href"]
            name_text = name_tag.get_text(strip=True)
            if name_text in scraped_titles:
                continue
            scraped_titles.add(name_text)

            details = get_details(more_info, name_text)
            if details:
                results.append({
                    "source_site": SCRAPING_SITE,
                    "source_url":  more_info,
                    "raw_text":    json.dumps(details, ensure_ascii=False),
                })
            time.sleep(0.5)

        page += 1
        time.sleep(1)

    return results


if __name__ == "__main__":
    scrape()
