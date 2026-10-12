import json
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

SCRAPING_SITE = "Opportunity Universe"
BASE_URL      = "https://opportunity-universe.com/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

ALLOWED_TYPES = {
    "scholarship", "fellowship", "conference", "forum", "summit",
    "summer school", "winter school", "exchange", "internship",
    "research", "training", "workshop", "competition", "hackathon",
}


def get_details(url: str, title: str) -> dict | None:
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[FATAL] Webpage not found: {url}\nError: {e}")
        return None

    soup     = BeautifulSoup(response.text, "lxml")
    main_tag = soup.find("div", class_="opp-main")
    section  = {}

    if main_tag:
        for heading in main_tag.find_all("h2"):
            heading_text    = heading.get_text(strip=True)
            section_content = []
            for sibling in heading.find_next_siblings():
                if sibling.name == "h2":
                    break
                if sibling.name == "div":
                    text = sibling.get_text(strip=True)
                    if text:
                        section_content.append(text)
            if heading_text:
                section[heading_text] = section_content

        deadline = soup.find("div", class_="deadline-big")
        if deadline:
            deadline_tag = deadline.find("b")
            if deadline_tag:
                text = deadline_tag.get_text(strip=True)
                if text:
                    section["Deadline"] = text

    return {"title": title, "data": section}


def scrape() -> list[dict]:
    scraped_titles = set()
    results        = []
    page           = 1

    while page < 2:
        url = (
            "https://opportunity-universe.com/en/search?sort=newest"
            if page == 1
            else f"https://opportunity-universe.com/en/search?sort=newest&page={page}"
        )

        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"[FATAL] Webpage not found: {url}\nPage: {page}")
            return results

        soup     = BeautifulSoup(response.text, "lxml")
        articles = soup.find_all("article", class_="u-card")

        for article in articles:
            name_tag = article.find("h3")
            if not name_tag or not name_tag.a:
                continue
            name_text = name_tag.get_text(strip=True)
            if name_text in scraped_titles:
                continue
            scraped_titles.add(name_text)

            type_tag = article.find("span", class_="u-tag")
            if not type_tag:
                print(f"No scholarship tag found for: {name_text}")
                continue
            if type_tag.get_text(strip=True).lower() not in ALLOWED_TYPES:
                continue

            href = name_tag.a.get("href")
            if not href:
                print(f"No link found for: {name_text}")
                continue
            more_info = urljoin(BASE_URL, href)

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
    data = scrape()
