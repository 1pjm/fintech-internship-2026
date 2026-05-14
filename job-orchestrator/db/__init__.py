import aiosqlite
from config import config

CREATE_JOBS_TABLE = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id      TEXT NOT NULL,
    source      TEXT NOT NULL,
    company_name TEXT,
    job_title   TEXT,
    url         TEXT,
    posted_at   TEXT,
    collected_at TEXT,
    screened_at TEXT,
    screen_result TEXT,
    PRIMARY KEY (job_id, source)
);
"""

CREATE_COMPANIES_TABLE = """
CREATE TABLE IF NOT EXISTS companies (
    company_name    TEXT PRIMARY KEY,
    size            TEXT,
    employee_count  TEXT,
    founded_year    INTEGER,
    series          TEXT,
    investors       TEXT,
    ai_products     INTEGER,
    ai_news_summary TEXT,
    enriched_at     TEXT
);
"""

CREATE_WATCHLIST_TABLE = """
CREATE TABLE IF NOT EXISTS watchlist (
    company_name TEXT PRIMARY KEY,
    added_at     TEXT,
    last_analyzed TEXT
);
"""


async def init_db() -> None:
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(CREATE_JOBS_TABLE)
        await db.execute(CREATE_COMPANIES_TABLE)
        await db.execute(CREATE_WATCHLIST_TABLE)
        await db.commit()


async def is_job_seen(job_id: str, source: str) -> bool:
    async with aiosqlite.connect(config.DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM jobs WHERE job_id = ? AND source = ?", (job_id, source)
        ) as cur:
            return await cur.fetchone() is not None


async def mark_job_seen(job: dict) -> None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            """INSERT OR IGNORE INTO jobs
               (job_id, source, company_name, job_title, url, posted_at, collected_at)
               VALUES (:job_id, :source, :company_name, :job_title, :url, :posted_at, :collected_at)""",
            job,
        )
        await db.commit()


async def update_screen_result(job_id: str, source: str, result: str, screened_at: str) -> None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            "UPDATE jobs SET screen_result = ?, screened_at = ? WHERE job_id = ? AND source = ?",
            (result, screened_at, job_id, source),
        )
        await db.commit()


async def get_cached_company(company_name: str) -> dict | None:
    from datetime import datetime, timedelta, timezone

    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM companies WHERE company_name = ?", (company_name,)
        ) as cur:
            row = await cur.fetchone()
    if row is None:
        return None
    enriched_at = datetime.fromisoformat(row["enriched_at"])
    if enriched_at.tzinfo is None:
        enriched_at = enriched_at.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) - enriched_at > timedelta(days=config.COMPANY_CACHE_DAYS):
        return None
    return dict(row)


async def delete_company_cache(company_name: str) -> None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute("DELETE FROM companies WHERE company_name = ?", (company_name,))
        await db.commit()


async def upsert_company(data: dict) -> None:
    import json

    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            """INSERT INTO companies
               (company_name, size, employee_count, founded_year, series, investors,
                ai_products, ai_news_summary, enriched_at)
               VALUES (:company_name, :size, :employee_count, :founded_year, :series,
                       :investors, :ai_products, :ai_news_summary, :enriched_at)
               ON CONFLICT(company_name) DO UPDATE SET
                 size=excluded.size, employee_count=excluded.employee_count,
                 founded_year=excluded.founded_year, series=excluded.series,
                 investors=excluded.investors, ai_products=excluded.ai_products,
                 ai_news_summary=excluded.ai_news_summary, enriched_at=excluded.enriched_at""",
            {
                **data,
                "investors": json.dumps(data.get("investors", []), ensure_ascii=False),
                "ai_products": int(data.get("ai_products", False)),
            },
        )
        await db.commit()


# ── 위시리스트 ──────────────────────────────────────────────

async def watchlist_add(company_name: str) -> None:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO watchlist (company_name, added_at) VALUES (?, ?)",
            (company_name, now),
        )
        await db.commit()


async def watchlist_remove(company_name: str) -> bool:
    async with aiosqlite.connect(config.DB_PATH) as db:
        cur = await db.execute(
            "DELETE FROM watchlist WHERE company_name = ?", (company_name,)
        )
        await db.commit()
        return cur.rowcount > 0


async def watchlist_get_all() -> list[str]:
    async with aiosqlite.connect(config.DB_PATH) as db:
        async with db.execute("SELECT company_name FROM watchlist ORDER BY added_at") as cur:
            rows = await cur.fetchall()
    return [r[0] for r in rows]


async def watchlist_update_analyzed(company_name: str) -> None:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            "UPDATE watchlist SET last_analyzed = ? WHERE company_name = ?",
            (now, company_name),
        )
        await db.commit()
