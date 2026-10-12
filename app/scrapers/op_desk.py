import json
import time
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

SCRAPING_SITE = "Opportunity Desk"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


def get_details(url: str, title: str) -> dict | None:
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Could not scrape: {url}\nError: {e}")
        return None

    soup      = BeautifulSoup(response.text, "lxml")
    all_text  = soup.find("div", class_="entry-content")
    if not all_text:
        print(f"No text found in: {url}")
        return None

    elements        = all_text.find_all(["p", "ul", "ol"], recursive=False)
    section_content = []
    list_buffer     = []

    for el in elements:
        if el.name == "p":
            text = el.get_text(strip=True)
            if text:
                section_content.append(text)
        elif el.name in ["ul", "ol"]:
            for li in el.find_all("li"):
                text = li.get_text(strip=True)
                if text:
                    list_buffer.append(text)
            section_content.append(list_buffer)
            list_buffer = []

    return {"title": title, "data": section_content}


def scrape() -> list[dict]:
    scraped_titles = set()
    results        = []
    cut_time       = datetime.now() - timedelta(days=3)

    try:
        response = requests.get("https://opportunitydesk.org/", headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[FATAL] Webpage not found: {e}")
        return []

    soup         = BeautifulSoup(response.text, "lxml")
    scholarships = soup.find_all("article", class_="l-post")

    for scholarship in scholarships:
        time_tag = scholarship.find("time", class_="post-date")
        if not time_tag:
            continue
        time_text = time_tag.get_text(strip=True)
        try:
            py_time = datetime.strptime(time_text, "%B %d, %Y")
        except ValueError:
            print(f"Unknown date format: {time_text}")
            continue
        if py_time < cut_time:
            break

        name_tag = scholarship.find(class_="post-title")
        if not name_tag or not name_tag.a:
            continue
        name_text = name_tag.get_text(strip=True)
        if name_text in scraped_titles:
            continue
        scraped_titles.add(name_text)

        more_info = name_tag.a["href"]
        details   = get_details(more_info, name_text)
        if details:
            results.append({
                "source_site": SCRAPING_SITE,
                "source_url":  more_info,
                "raw_text":    json.dumps(details, ensure_ascii=False),
            })
        time.sleep(1.5)

    return results


if __name__ == "__main__":
    data = scrape()
