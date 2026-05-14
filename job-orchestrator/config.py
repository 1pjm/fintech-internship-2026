import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")


def _require(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(f"Required environment variable '{key}' is not set.")
    return val


class Config:
    # Anthropic (선택)
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Gemini (무료 스크리닝)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = "gemini-2.0-flash-lite"

    # 신입/경력 구분 (entry | career | all)
    CAREER_LEVEL: str = os.getenv("CAREER_LEVEL", "all")

    # 원티드
    WANTED_ACCESS_TOKEN: str = os.getenv("WANTED_ACCESS_TOKEN", "")
    WANTED_BASE_URL: str = "https://www.wanted.co.kr/api/v4/jobs"
    WANTED_POLL_INTERVAL_MINUTES: int = 30

    # 사람인
    SARAMIN_API_KEY: str = os.getenv("SARAMIN_API_KEY", "")
    SARAMIN_BASE_URL: str = "https://oapi.saramin.co.kr/job-search"
    SARAMIN_POLL_INTERVAL_MINUTES: int = 60

    # 텔레그램
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # 크런치베이스
    CRUNCHBASE_API_KEY: str = os.getenv("CRUNCHBASE_API_KEY", "")

    # Claude 모델
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"
    CLAUDE_MAX_TOKENS: int = 500

    # 경로
    DB_PATH: Path = BASE_DIR / "db" / "jobs.sqlite"
    REPORTS_RAW_DIR: Path = BASE_DIR / "reports" / "jobs" / "raw"
    REPORTS_FILTERED_DIR: Path = BASE_DIR / "reports" / "jobs" / "filtered"
    REPORTS_UNSENT_DIR: Path = BASE_DIR / "reports" / "jobs" / "unsent"
    COMPANIES_DIR: Path = BASE_DIR / "reports" / "companies"
    LOG_PATH: Path = BASE_DIR / "logs" / "pipeline.log"

    # 재시도 정책
    MAX_RETRIES: int = 3
    RETRY_BACKOFF: list[int] = [5, 15, 45]

    # 기업 캐시 TTL (일)
    COMPANY_CACHE_DAYS: int = 7

    # 스크리닝 키워드
    JOB_KEYWORDS: list[str] = ["서비스 기획", "서비스 PM", "AX 기획", "AI 기획", "디지털 전환", "UX 기획"]
    INDUSTRY_KEYWORDS: list[str] = ["핀테크", "금융", "페이먼트", "인슈어테크", "뱅킹"]
    AI_KEYWORDS: list[str] = ["LLM", "GPT", "생성형AI", "RAG", "AI에이전트", "Claude", "ChatGPT", "거대언어모델"]


config = Config()
