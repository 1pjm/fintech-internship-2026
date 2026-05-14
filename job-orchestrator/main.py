import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from config import config
from db import init_db
from collectors import wanted, saramin
from screener import jd_screener
from enricher import company_enricher
from reporters import report_builder, telegram
from scheduler import build_scheduler, is_blocked, block_source

# ── 로깅 설정 ──────────────────────────────────────────────
config.LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(config.LOG_PATH, encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def _log_stage(stage: int, name: str, lines: list[str]) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    header = f"[{stage}단계 {name} 완료] {ts}"
    block = "\n  ".join(["", header] + lines)
    logger.info(block)
    print(block)


async def run_pipeline(sources: list[str] | None = None) -> None:
    if sources is None:
        sources = ["wanted", "saramin"]

    # ── 1단계: 수집 ────────────────────────────────────────
    all_jobs: list[dict] = []
    wanted_count = saramin_count = 0
    collect_errors: list[str] = []

    if "wanted" in sources and not is_blocked("wanted"):
        try:
            w_jobs = await wanted.collect()
            wanted_count = len(w_jobs)
            all_jobs.extend(w_jobs)
        except Exception as e:
            if "차단" in str(e) or "403" in str(e) or "429" in str(e):
                block_source("wanted")
                await telegram.send_block_alert("원티드")
            collect_errors.append(f"원티드: {e}")

    if "saramin" in sources and not is_blocked("saramin"):
        try:
            s_jobs = await saramin.collect()
            saramin_count = len(s_jobs)
            all_jobs.extend(s_jobs)
        except Exception as e:
            if "차단" in str(e) or "403" in str(e) or "429" in str(e):
                block_source("saramin")
                await telegram.send_block_alert("사람인")
            collect_errors.append(f"사람인: {e}")

    _log_stage(1, "job-collector", [
        f"✅ 원티드: {wanted_count}건 수집",
        f"✅ 사람인: {saramin_count}건 수집",
        *(f"❌ 실패: {e}" for e in collect_errors) or ["❌ 실패: 없음"],
        f"→ 총 {len(all_jobs)}건 → 2단계로 전달",
    ])

    if not all_jobs:
        return

    # ── 2단계: 스크리닝 ─────────────────────────────────────
    passed, screen_stats = await jd_screener.screen(all_jobs)

    cond_detail = " / ".join(
        f"조건{k}: {v}건" for k, v in screen_stats["condition"].items() if v
    ) or "없음"

    _log_stage(2, "job-screener", [
        f"✅ PASS: {screen_stats['pass']}건 ({cond_detail})",
        f"⏭️ 중복 skip: {screen_stats['skip_dup']}건",
        f"❌ Claude API 오류: {screen_stats['claude_error']}건",
        f"→ 신규 통과 {len(passed)}건 → 3단계로 전달",
    ])

    if not passed:
        return

    # ── 3단계: 기업 enrichment ──────────────────────────────
    enriched, enrich_stats = await company_enricher.enrich_batch(passed)

    _log_stage(3, "company-enricher", [
        f"✅ 신규 enrichment: {enrich_stats['new']}개사",
        f"💾 캐시 사용: {enrich_stats['cached']}개사",
        f"❌ 수집 실패: {enrich_stats['failed']}개사",
        f"→ {len(enriched)}건 리포트 완성 → 4단계로 전달",
    ])

    # ── 4단계: 리포트 생성 ──────────────────────────────────
    reports, report_count = await report_builder.build_batch(enriched)

    _save_filtered(reports)

    _log_stage(4, "report-builder", [
        f"✅ 리포트 생성: {report_count}건",
    ])

    # ── 5단계: 텔레그램 발송 ────────────────────────────────
    # 미발송 건 먼저 재시도
    await telegram.retry_unsent()

    send_stats = await telegram.send_reports(reports)

    _log_stage(5, "job-reporter", [
        f"✅ 텔레그램 발송: {send_stats['sent']}건",
        f"❌ 실패: {send_stats['failed']}건",
    ])


def _save_filtered(reports: list[dict]) -> None:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    path = config.REPORTS_FILTERED_DIR / f"{today}.json"
    config.REPORTS_FILTERED_DIR.mkdir(parents=True, exist_ok=True)

    existing: list[dict] = []
    if path.exists():
        try:
            existing = json.loads(path.read_text())
        except Exception:
            pass

    existing.extend(reports)
    path.write_text(json.dumps(existing, ensure_ascii=False, indent=2))


async def _wanted_job() -> None:
    await run_pipeline(sources=["wanted"])


async def _saramin_job() -> None:
    await run_pipeline(sources=["saramin"])


async def main() -> None:
    await init_db()
    logger.info("DB 초기화 완료")

    # 시작 시 즉시 전체 실행
    await run_pipeline()

    # 스케줄러 시작
    scheduler = build_scheduler(_wanted_job, _saramin_job)
    scheduler.start()
    logger.info(
        "스케줄러 시작 — 원티드 %d분 / 사람인 %d분 간격",
        config.WANTED_POLL_INTERVAL_MINUTES,
        config.SARAMIN_POLL_INTERVAL_MINUTES,
    )

    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("파이프라인 종료")


if __name__ == "__main__":
    asyncio.run(main())
