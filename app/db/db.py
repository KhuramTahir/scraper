import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={os.getenv('DB_SERVER')};"
        f"DATABASE={os.getenv('DB_DATABASE')};"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )


def insert_raw(data):
    try:
        conn = get_connection()
    except pyodbc.Error as e:
        print(f"Connection failed: {e}")
        return False

    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT 1 FROM raw_scholarships_data WHERE source_url = ?",
            data["source_url"]
        )
        if cur.fetchone():
            print(f"Data already present for {data['source_url']}")
            return False
        cur.execute(
            "INSERT INTO raw_scholarships_data (source_site, source_url, raw_text) VALUES (?, ?, ?)",
            data["source_site"], data["source_url"], data["raw_text"]
        )
        conn.commit()
        return True
    except pyodbc.Error as e:
        print(f"Could not write data for {data.get('source_url')}  ERROR: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def get_unprocessed():
    try:
        conn = get_connection()
    except pyodbc.Error as e:
        print(f"Connection failed: {e}")
        return []

    cur = conn.cursor()
    cur.execute("SELECT id, raw_text, source_url FROM raw_scholarships_data WHERE processed = 0")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def insert_processed(data, source_url):
    try:
        conn = get_connection()
    except pyodbc.Error as e:
        print(f"Connection failed: {e}")
        return False

    cur = conn.cursor()
    deadline_value = None if data.get("deadline") == "unknown" else data.get("deadline")
    opportunity_type = (data.get("opportunity_type") or "")[:100]
    degree_level     = (data.get("degree_level") or "")[:100]
    funding_type     = (data.get("funding_type") or "")[:100]

    try:
        cur.execute(
            """INSERT INTO processed_sholarships_info
               (title, description, host_country, eligible_countries, opportunity_type,
                degree_level, deadline, eligibility, language_requirement,
                amount, funding_type, field_of_study, source_url)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            data.get("title"),
            data.get("description"),
            data.get("host_country"),
            data.get("eligible_countries"),
            opportunity_type,
            degree_level,
            deadline_value,
            data.get("eligibility"),
            data.get("language_requirement"),
            data.get("amount"),
            funding_type,
            data.get("field_of_study"),
            source_url,
        )
        conn.commit()
        return True
    except pyodbc.Error as e:
        print(f"Could not write data for {source_url}  ERROR: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def marking(raw_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE raw_scholarships_data SET processed = 1 WHERE ID = ?", raw_id)
        conn.commit()
    except pyodbc.Error as e:
        print(f"Mark failed for {raw_id}  ERROR: {e}")
    finally:
        cur.close()
        conn.close()


def title_getter():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT title FROM processed_sholarships_info")
    titles = [row.title for row in cur.fetchall()]
    cur.close()
    conn.close()
    return titles


def query_scholarship(filters):
    parameters = []
    score_conditions = []

    def add_filter(column, value, exact=False):
        if value and value != "not_specified":
            op  = " = "    if exact else " LIKE "
            val = value    if exact else f"%{value}%"
            score_conditions.append(f"CASE WHEN {column} {op} ? THEN 1 ELSE 0 END")
            parameters.append(val)

    add_filter("host_country",      filters.get("host_country"))
    add_filter("field_of_study",    filters.get("field_of_study"))
    add_filter("eligible_countries",filters.get("eligible_countries"))
    add_filter("funding_type",      filters.get("funding_type"),      exact=True)
    add_filter("degree_level",      filters.get("degree_level"),      exact=True)
    add_filter("opportunity_type",  filters.get("opportunity_type"),  exact=True)

    score_text = " + ".join(score_conditions) if score_conditions else "0"

    query = f"""
    WITH ranked AS (
        SELECT *, ({score_text}) AS match_score
        FROM processed_sholarships_info
    ),
    best AS (
        SELECT MAX(match_score) AS highest_score FROM ranked
    )
    SELECT TOP 20 *
    FROM ranked
    WHERE match_score >= (
        SELECT CASE
            WHEN highest_score >= 2 THEN highest_score - 1
            ELSE highest_score
        END
        FROM best
    )
    ORDER BY match_score DESC, created_at DESC
    """

    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(query, parameters)
    columns = [col[0] for col in cur.description]
    rows    = [dict(zip(columns, row)) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return rows
