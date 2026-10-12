import json
import time

import requests
from bs4 import BeautifulSoup

SCRAPING_SITE = "IEFA"
BASE_URL      = "https://www.iefa.org"
LIST_URL      = f"{BASE_URL}/scholarships"

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

    soup    = BeautifulSoup(response.text, "lxml")
    section = {}

    info_table = soup.find("table", class_="table table-v2")
    if info_table:
        info = {}
        for row in info_table.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if th:
                info[th.get_text(strip=True)] = td.get_text(strip=True) if td else ""
        if info:
            section["Info"] = info

    for h2 in soup.find_all("h2", class_="section-title"):
        heading_text = h2.get_text(" ", strip=True)
        desc_div = h2.find_next_sibling("div", class_="description")
        if not desc_div:
            break
        text = desc_div.get_text(strip=True)
        if text:
            section[heading_text] = text

    if not section:
        print(f"No text found in: {url}")
        return None

    return {"title": title, "data": section}


def scrape() -> list[dict]:
    scraped_titles = set()
    results        = []

    try:
        response = requests.get(LIST_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[FATAL] Webpage not found: {e}")
        return []

    try:
        soup = BeautifulSoup(response.text, "lxml")
    except Exception as e:
        print(f"[FATAL] Could not parse HTML: {e}")
        return []

    table = soup.find("table", class_="table table-v2")
    if not table:
        print("[FATAL] Could not find the 'table-v2' table.")
        return []

    tbody = table.find("tbody")
    if not tbody:
        print("[FATAL] Table has no tbody.")
        return []

    for row in tbody.find_all("tr"):
        try:
            cells = row.find_all("td")
            if len(cells) < 3:
                continue

            name_cell, field_cell, desc_cell = cells[0], cells[1], cells[2]

            links = [a for a in name_cell.find_all("a") if a.get_text(strip=True)]
            if not links:
                continue
            title_link = links[-1]
            title_text = title_link.get_text(strip=True)
            href       = title_link.get("href")
            if not title_text or not href:
                continue

            more_info = href if href.startswith("http") else BASE_URL + href
            if title_text in scraped_titles:
                continue
            scraped_titles.add(title_text)

            field_text       = field_cell.get_text(strip=True)
            nationality_tag  = desc_cell.find("p", class_="award-list-nationality")
            host_tag         = desc_cell.find("p", class_="award-list-location")

            def strip_span(tag):
                if not tag:
                    return None
                text = tag.get_text(strip=True)
                span = tag.find("span")
                if span:
                    text = text.replace(span.get_text(strip=True), "", 1).strip()
                return text

            nationality_text = strip_span(nationality_tag)
            host_text        = strip_span(host_tag)

            desc_copy = BeautifulSoup(str(desc_cell), "lxml")
            for tag in desc_copy.find_all("p", class_=["award-list-nationality", "award-list-location"]):
                tag.decompose()
            description_text = desc_copy.get_text(strip=True)

            details = get_details(more_info, title_text)
            if details:
                details["field"]               = field_text
                details["description_preview"] = description_text
                details["nationality"]         = nationality_text
                details["host_countries"]      = host_text
                results.append({
                    "source_site": SCRAPING_SITE,
                    "source_url":  more_info,
                    "raw_text":    json.dumps(details, ensure_ascii=False),
                })

            time.sleep(1.5)

        except Exception as e:
            print(f"Error processing row: {e}")
            continue

    return results


if __name__ == "__main__":
    data = scrape()
    print(json.dumps(data, ensure_ascii=False, indent=2))
