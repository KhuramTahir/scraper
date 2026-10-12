# Scholar Scraper

A pipeline that scrapes scholarship listings from multiple sources, normalizes them with an LLM, stores them in SQL Server, and serves them through a FastAPI search endpoint.

---

## Project Structure

```
scholar-scrapper/
├── app/
│   ├── api/
│   │   └── search_api.py        # FastAPI app — /search and /health endpoints
│   ├── db/
│   │   └── db.py                # All SQL Server interactions (read/write/query)
│   ├── pipeline/
│   │   ├── normalize.py         # LLM-based structured extraction (Groq)
│   │   ├── text_cleaner.py      # Flatten raw scraped JSON → plain text for LLM
│   │   └── title_normalize.py   # Fuzzy duplicate detection
│   └── scrapers/
│       ├── iefa.py
│       ├── op_corner.py
│       ├── op_desk.py
│       ├── op_universe.py
│       ├── scholar_ads.py
│       └── scholar_union.py
├── frontend/
│   └── index.html               # Single-page search UI
├── run.py                       # Entry point: scrape → normalize → store
├── requirements.txt
├── .env                         # API keys and DB config (never commit)
└── .gitignore
```

---

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
```

Copy `.env` and fill in your values:

```
GROQ_API_KEY=...
DB_SERVER=...
DB_DATABASE=...
ALLOWED_ORIGIN=http://127.0.0.1:5500
```

---

## Running

### Scrape + normalize
```bash
python run.py
```

### API server
```bash
uvicorn app.api.search_api:APP --reload
```

### Frontend
Open `frontend/index.html` with Live Server or any static file server pointing at port 5500.

---

## Sources

| Scraper | Site |
|---|---|
| `iefa.py` | iefa.org |
| `op_corner.py` | opportunitiescorners.com |
| `op_desk.py` | opportunitydesk.org |
| `op_universe.py` | opportunity-universe.com |
| `scholar_ads.py` | scholarshipsads.com |
| `scholar_union.py` | scholarshipunion.com |
