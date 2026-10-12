import json
import time

from app.scrapers import op_corner, scholar_union, op_universe, op_desk, iefa, scholar_ads
from app.db.db import insert_raw, get_unprocessed, insert_processed, marking, title_getter
from app.pipeline.normalize import normalize
from app.pipeline.title_normalize import dupe_check

SCRAPERS = [op_universe, op_corner, op_desk, scholar_union, iefa, scholar_ads]


def run_all():
    """Scrape every source and persist raw results to the database."""
    for scraper in SCRAPERS:
        try:
            items = scraper.scrape()
            for item in items:
                insert_raw(item)
            print(f"Successfully processed {len(items)} items from {scraper.__name__}")
        except Exception as e:
            print(f"Failed to scrape from {scraper.__name__}  ERROR: {e}")


def normalize_with_retry(raw_text: str, max_retries: int = 4) -> dict | None:
    """Call normalize() with exponential back-off on rate-limit errors."""
    for attempt in range(max_retries):
        try:
            return normalize(raw_text)
        except Exception as e:
            error_text = str(e)
            if "json_validate_failed" in error_text:
                print("Data could not be extracted — skipping.")
                return None
            if "429" in error_text or "rate_limit" in error_text:
                wait = 10 * (attempt + 1)
                print(f"Rate limited. Retrying ({attempt + 1}/{max_retries}) after {wait}s …")
                time.sleep(wait)
            else:
                raise
    raise Exception(f"Model not responding after {max_retries} retries.")


def run_normalize():
    """Normalize every unprocessed raw row and insert the structured result."""
    rows            = get_unprocessed()
    existing_titles = title_getter()

    for row in rows:
        raw_data       = json.loads(row.raw_text)
        scraped_title  = raw_data.get("title", "")

        if len(row.raw_text) > 6000:
            print(f"Skipping '{scraped_title}' — oversized payload.")
            marking(row.id)
            continue

        if dupe_check(scraped_title, existing_titles):
            print(f"Skipping '{scraped_title}' — duplicate.")
            marking(row.id)
            continue

        try:
            clean_info = normalize_with_retry(row.raw_text)
            if clean_info is None:
                print(f"Skipping row {row.id} — normalization returned nothing.")
                continue
            success = insert_processed(clean_info, row.source_url)
            if success:
                marking(row.id)
                existing_titles.append(clean_info["title"])
            else:
                print(f"Unsuccessful insert for row {row.id}.")
        except Exception as e:
            print(f"Normalization failed for {row.source_url}  ERROR: {e}")

        time.sleep(3)


if __name__ == "__main__":
    run_all()
    run_normalize()
