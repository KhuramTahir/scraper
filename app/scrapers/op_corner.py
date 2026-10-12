import json
import time
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

SCRAPING_SITE = "Opportunities Corners"

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

    soup     = BeautifulSoup(response.text, "lxml")
    main_tag = soup.find("div", class_="td-post-content tagdiv-type")
    section  = {}

    intro_section = []
    intro_para = main_tag.find("p")
    if intro_para:
        text = intro_para.get_text(strip=True)
        if text:
            intro_section.append(text)

    intro_list = main_tag.find("ul")
    if intro_list:
        items = [li.get_text(strip=True) for li in intro_list.find_all("li") if li.get_text(strip=True)]
        if items:
            intro_section.append(items)

    section["Introduction"] = intro_section

    for heading in main_tag.find_all("h3"):
        heading_text    = heading.get_text(strip=True)
        section_content = []
        list_buffer     = []
        stop            = False

        for sibling in heading.find_all_next():
            if sibling.name == "h3":
                break
            if sibling.name in ["ul", "ol"]:
                for li in sibling.find_all("li"):
                    text = li.get_text(strip=True)
                    if text == "Facebook":
                        stop = True
                        break
                    if text:
                        list_buffer.append(text)
                section_content.append(list_buffer)
                list_buffer = []
                if stop:
                    break

        if heading_text:
            section[heading_text] = section_content

    return {"title": title, "data": section}


def scrape() -> list[dict]:
    scraped_titles = set()
    results        = []
    cut_time       = datetime.now() - timedelta(days=3)

    try:
        response = requests.get("https://opportunitiescorners.com/", headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[FATAL] Webpage not found: {e}")
        return []

    soup         = BeautifulSoup(response.text, "lxml")
    scholarships = soup.find_all("div", class_="item-details")

    for scholarship in scholarships:
        time_tag = scholarship.find("span", class_="td-post-date")
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

        name_tag = scholarship.find("h3", class_="entry-title td-module-title")
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
    scrape()
