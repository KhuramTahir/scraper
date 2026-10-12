import json
import time
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

SCRAPING_SITE = "ScholarshipsAds"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

TARGET_HEADERS = {"benefits", "eligibility criteria"}


def get_details(url: str, title: str) -> dict | None:
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Could not scrape: {url}\nError: {e}")
        return None

    soup    = BeautifulSoup(response.text, "lxml")
    section = {}

    card_info = soup.find("div", class_="card-info")
    if card_info:
        info_list = card_info.find("ul")
        if info_list:
            items = [li.get_text(strip=True) for li in info_list.find_all("li") if li.get_text(strip=True)]
            if items:
                section["Info_li"] = items

    for h3 in soup.find_all("h3"):
        header_text = h3.get_text(strip=True)
        if header_text.lower() not in TARGET_HEADERS:
            continue

        section_content = []
        for sibling in h3.find_next_siblings():
            if sibling.name == "h3":
                break
            if sibling.name in ["script", "style"]:
                continue
            if sibling.name in ["ul", "ol"]:
                for li in sibling.find_all("li"):
                    text = li.get_text(strip=True)
                    if text:
                        section_content.append(text)
            else:
                text = sibling.get_text(strip=True)
                if text:
                    section_content.append(text)

        if section_content:
            section[header_text] = section_content

    if not section:
        print(f"No text found in: {url}")
        return None

    return {"title": title, "data": section}


def scrape() -> list[dict]:
    scraped_titles = set()
    results        = []
    cut_time       = datetime.now() - timedelta(days=3)

    try:
        response = requests.get(
            "https://www.scholarshipsads.com/latest-scholarships/",
            headers=HEADERS, timeout=10,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[FATAL] Webpage not found: {e}")
        return []

    soup    = BeautifulSoup(response.text, "lxml")
    section = soup.find("section", class_="home-page latest-scholarship bg-white pt-5")
    if not section:
        print("[FATAL] Could not find the 'Latest Scholarships' section.")
        return []

    cards = section.find_all("div", class_="card-scholarships")

    for card in cards:
        time_tag = card.find("span", class_="card-date")
        if not time_tag:
            continue
        time_text = time_tag.get_text(strip=True)
        try:
            py_time = datetime.strptime(time_text, "%d %b %Y")
        except ValueError:
            print(f"Unknown date format: {time_text}")
            continue
        if py_time < cut_time:
            break

        title_tag = card.find("h5", class_="card-title")
        if not title_tag or not title_tag.a:
            continue
        title_text = title_tag.get_text(strip=True)
        if title_text in scraped_titles:
            continue
        scraped_titles.add(title_text)

        more_info = title_tag.a["href"]
        details   = get_details(more_info, title_text)
        if details:
            results.append({
                "source_site": SCRAPING_SITE,
                "source_url":  more_info,
                "raw_text":    json.dumps(details, ensure_ascii=False),
            })
        time.sleep(1.5)

    return results


if __name__ == "__main__":
    scrape()
