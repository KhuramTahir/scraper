import os
import json
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.pipeline.normalize import client
from app.db.db import query_scholarship

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("search_api")

APP = FastAPI(title="Scholarship Finder API")

APP.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGIN", "").split(","),
    allow_methods=["GET"],
    allow_headers=["*"],
)

FILTER_SCHEMA = {
    "type": "object",
    "properties": {
        "field_of_study": {
            "type": "string",
            "description": "'computer science' or null if not mentioned",
        },
        "degree_level": {
            "type": "string",
            "enum": ["bachelors", "masters", "phd", "not_applicable", "not_specified"],
        },
        "funding_type": {
            "type": "string",
            "enum": ["full", "partial", "paid_program", "not_specified"],
        },
        "eligible_countries": {
            "type": "string",
            "description": "User's nationality or country of residence if mentioned, else null",
        },
        "host_country": {
            "type": "string",
            "description": "Desired program location, else null",
        },
        "opportunity_type": {
            "type": "string",
            "enum": [
                "scholarship", "fellowship", "conference", "summer_school",
                "internship", "hackathon", "competition", "workshop", "other",
            ],
        },
    },
}


def extract_filters(user_query: str) -> dict:
    """Use the LLM to parse the user's free-text query into structured DB filters."""
    prompt = (
        f"Extract from this scholarship request as JSON. "
        f"Use 'not_specified' for any field not mentioned.\n"
        f"SCHEMA: {json.dumps(FILTER_SCHEMA, indent=2)}\n"
        f"USER_REQUEST: {user_query}"
    )
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.1,
    )
    return json.loads(response.choices[0].message.content)


@APP.get("/search")
def search(query: str = Query(..., min_length=1, max_length=300)):
    query = query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        filters = extract_filters(query)
    except Exception as e:
        logger.warning(f"Filter extraction failed, falling back to unfiltered search: {e}")
        filters = {}

    try:
        results = query_scholarship(filters)
    except Exception as e:
        logger.error(f"DB query failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed.") from e

    return results


@APP.get("/health")
def health():
    return {"status": "ok"}
