import os
import json
from dotenv import load_dotenv
from groq import Groq

from app.pipeline.text_cleaner import raw_cleaned_func

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SCHEMA = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "Opportunity name"
        },
        "description": {
            "type": "string",
            "description": "Summary of what it offers, not who can apply"
        },
        "host_country": {
            "type": "string",
            "description": "Host location or 'various'"
        },
        "eligible_countries": {
            "type": "string",
            "description": "Who can apply based on nationality"
        },
        "opportunity_type": {
            "type": "string",
            "enum": ["scholarship", "fellowship", "conference", "summer_school",
                     "internship", "hackathon", "competition", "workshop", "other"]
        },
        "degree_level": {
            "type": "string",
            "enum": ["bachelors", "masters", "phd", "not_applicable", "not_specified"]
        },
        "deadline": {
            "type": "string",
            "description": "YYYY-MM-DD or 'unknown'"
        },
        "eligibility": {
            "type": "string",
            "description": "Concisely who can apply. Include GPA, age, or document requirements if stated."
        },
        "language_requirement": {
            "type": "string",
            "description": "Language proficiency, e.g. 'IELTS 6.5', 'native English', or 'not_specified'"
        },
        "amount": {
            "type": "string",
            "description": "Funding amount, or 'fully funded'"
        },
        "funding_type": {
            "type": "string",
            "enum": ["full", "partial", "paid_program", "not_specified"]
        },
        "field_of_study": {
            "type": "string",
            "description": "Academic field, or 'any' if not restricted"
        },
    },
    "required": ["title", "eligibility", "opportunity_type"],
}


def normalize(raw_text: str) -> dict:
    """Extract structured scholarship data from raw scraped text via LLM."""
    cleaned = raw_cleaned_func(raw_text)
    prompt  = (
        f"Extract scholarship data as JSON per this schema.\n"
        f"SCHEMA: {json.dumps(SCHEMA)}\n"
        f"TEXT: {cleaned}"
    )

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.1,
    )
    return json.loads(response.choices[0].message.content)
