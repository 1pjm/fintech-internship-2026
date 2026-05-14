import asyncio
import json
import logging
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Callable, Awaitable

import httpx

from config import config

logger = logging.getLogger(__name__)

TELEGRAM_API = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}"

HELP_TEXT = """
🤖 <b>JobMonster 명령어 안내</b>

/status      — 파이프라인 현재 상태 조회
/run         — 파이프라인 즉시 실행
/pause       — 자동 수집 일시 중단
/resume      — 자동 수집 재개
/jobs        — 오늘 공고 + 기업분석 리포트
/stats       — 누적 통계 조회
/analyze [기업명] — 특정 기업 즉시 분석
/watch [기업명]   — 관심 기업 등록
/unwatch [기업명] — 관심 기업 삭제
/watchlist   — 관심 기업 목록 조회
/help        — 이 도움말 보기
""".strip()

# 파이프라인 상태 공유 객체
class PipelineState:
    def __init__(self):
        self.is_running: bool = False
        self.is_paused: bool = False
        self.last_run_at: str = "없음"
        self.today_count: int = 0
        self.total_count: int = 0
        self.last_stage: str = "대기 중"
        self.errors: list[str] = []

    def to_status_text(self) -> str:
        icon = "⏸️" if self.is_paused else ("🔄" if self.is_running else "✅")
        state_str = "일시정지" if self.is_paused else ("실행 중" if self.is_running else "대기 중")
        return (
            f"{icon} <b>파이프라인 상태</b>\n\n"
            f"상태: {state_str}\n"
            f"마지막 실행: {self.last_run_at}\n"
            f"현재 단계: {self.last_stage}\n"
            f"오늘 수집: {self.today_count}건\n"
            f"누적 수집: {self.total_count}건\n"
            + (f"\n⚠️ 최근 오류:\n" + "\n".join(f"  • {e}" for e in self.errors[-3:]) if self.errors else "")
        )


pipeline_state = PipelineState()


def _api(endpoint: str, payload: dict) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{TELEGRAM_API}/{endpoint}",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        logger.error("Telegram API 오류 (%s): %s — %s", endpoint, e.code, e.read().decode())
        return {}
    except Exception as e:
        logger.error("Telegram API 요청 실패 (%s): %s", endpoint, e)
        return {}


async def send(chat_id: str | int, text: str, reply_markup: dict | None = None) -> None:
    payload: dict = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{TELEGRAM_API}/sendMessage", json=payload, timeout=15)
            resp.raise_for_status()
    except Exception as e:
        logger.error("sendMessage 실패 (%s): %s", chat_id, e)


async def send_keyboard(chat_id: str | int, text: str) -> None:
    keyboard = {
        "keyboard": [
            [{"text": "📊 상태"}, {"text": "▶️ 즉시실행"}],
            [{"text": "⏸️ 일시정지"}, {"text": "▶️ 재개"}],
            [{"text": "📋 오늘 공고"}, {"text": "📈 통계"}],
            [{"text": "🔄 수집모드"}],
        ],
        "resize_keyboard": True,
        "persistent": True,
    }
    await send(chat_id, text, reply_markup=keyboard)


async def _get_updates(offset: int) -> list[dict]:
    payload = {"offset": offset, "timeout": 20, "allowed_updates": ["message"]}
    result = await asyncio.get_event_loop().run_in_executor(
        None, lambda: _api("getUpdates", payload)
    )
    return result.get("result", [])


def _get_today_jobs() -> list[dict]:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    path = config.REPORTS_FILTERED_DIR / f"{today}.json"
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text())
    except Exception:
        return []


def _format_jobs_summary(jobs: list[dict]) -> str:
    if not jobs:
        return "📭 오늘 수집된 공고가 없습니다."
    lines = [f"📋 <b>오늘 수집된 공고 ({len(jobs)}건)</b>\n"]
    for i, job in enumerate(jobs[:10], 1):
        d_day = job.get("d_day", 0)
        d_str = f"D-{d_day}" if d_day > 0 else "D-Day"
        lines.append(
            f"{i}. <b>{job.get('company_name', '')}</b> — {job.get('job_title', '')}\n"
            f"   ⏰ {d_str} | <a href=\"{job.get('url', '')}\">바로가기</a>"
        )
    if len(jobs) > 10:
        lines.append(f"\n...외 {len(jobs) - 10}건")
    return "\n".join(lines)


async def handle_command(
    chat_id: int,
    text: str,
    run_pipeline_fn: Callable[[], Awaitable[None]],
    scheduler,
) -> None:
    cmd = text.strip().lower().split()[0] if text.strip() else ""

    # 키보드 버튼 텍스트 → 명령어 매핑
    btn_map = {
        "📊 상태": "/status",
        "▶️ 즉시실행": "/run",
        "⏸️ 일시정지": "/pause",
        "▶️ 재개": "/resume",
        "📋 오늘 공고": "/jobs",
        "📈 통계": "/stats",
    }
    cmd = btn_map.get(text.strip(), cmd)

    if cmd in ("/start", "/help"):
        await send_keyboard(chat_id, f"안녕하세요! JobMonster 봇입니다 👋\n\n{HELP_TEXT}")

    elif cmd == "/status":
        await send(chat_id, pipeline_state.to_status_text())

    elif cmd == "/run":
        if pipeline_state.is_running:
            await send(chat_id, "⚠️ 파이프라인이 이미 실행 중입니다.")
            return
        if pipeline_state.is_paused:
            await send(chat_id, "⚠️ 일시정지 상태입니다. /resume 으로 재개 후 실행하세요.")
            return
        await send(chat_id, "🔄 파이프라인을 즉시 실행합니다...")
        asyncio.create_task(run_pipeline_fn())

    elif cmd == "/pause":
        if pipeline_state.is_paused:
            await send(chat_id, "이미 일시정지 상태입니다.")
            return
        pipeline_state.is_paused = True
        if scheduler and scheduler.running:
            scheduler.pause()
        await send(chat_id, "⏸️ 자동 수집을 일시정지했습니다.\n/resume 으로 재개할 수 있습니다.")

    elif cmd == "/resume":
        if not pipeline_state.is_paused:
            await send(chat_id, "현재 실행 중인 상태입니다.")
            return
        pipeline_state.is_paused = False
        if scheduler and scheduler.running:
            scheduler.resume()
        await send(chat_id, "▶️ 자동 수집을 재개했습니다.")

    elif cmd == "/jobs":
        jobs = _get_today_jobs()
        await send(chat_id, _format_jobs_summary(jobs))
        if not jobs:
            return
        await send(chat_id, f"🔍 총 <b>{len(jobs)}건</b>의 기업분석 리포트를 순차 발송합니다...")
        from reporters.company_report import send as send_report
        from enricher.news_search import fetch_articles
        sent_companies: set[str] = set()
        for job in jobs[:10]:
            company = job.get("company_name", "")
            if not company or company in sent_companies:
                continue
            articles = await asyncio.get_event_loop().run_in_executor(
                None, lambda c=company: fetch_articles(c)
            )
            await send_report(job, articles)
            sent_companies.add(company)
            await asyncio.sleep(1)

    elif cmd == "/stats":
        jobs = _get_today_jobs()
        pipeline_state.today_count = len(jobs)
        text_out = (
            f"📈 <b>수집 통계</b>\n\n"
            f"오늘 수집: {pipeline_state.today_count}건\n"
            f"누적 수집: {pipeline_state.total_count}건\n"
            f"마지막 실행: {pipeline_state.last_run_at}\n"
            f"수집 주기: 원티드 30분 / 사람인 60분"
        )
        await send(chat_id, text_out)

    elif cmd == "/analyze":
        parts = text.strip().split(maxsplit=1)
        if len(parts) < 2:
            await send(chat_id, "사용법: /analyze 기업명\n예) /analyze 카카오페이")
            return
        company = parts[1].strip()
        await send(chat_id, f"🔍 <b>{company}</b> 분석 중...")
        from reporters.company_report import analyze_company
        ok = await analyze_company(company)
        if not ok:
            await send(chat_id, f"❌ {company} 분석에 실패했습니다.")

    elif cmd == "/watch":
        parts = text.strip().split(maxsplit=1)
        if len(parts) < 2:
            await send(chat_id, "사용법: /watch 기업명\n예) /watch 카카오페이")
            return
        company = parts[1].strip()
        from db import watchlist_add
        await watchlist_add(company)
        await send(chat_id, f"✅ <b>{company}</b> 관심 기업에 등록했습니다.")

    elif cmd == "/unwatch":
        parts = text.strip().split(maxsplit=1)
        if len(parts) < 2:
            await send(chat_id, "사용법: /unwatch 기업명\n예) /unwatch 카카오페이")
            return
        company = parts[1].strip()
        from db import watchlist_remove
        removed = await watchlist_remove(company)
        if removed:
            await send(chat_id, f"✅ <b>{company}</b> 관심 기업에서 삭제했습니다.")
        else:
            await send(chat_id, f"❌ <b>{company}</b> 는 관심 기업 목록에 없습니다.")

    elif cmd == "/watchlist":
        from db import watchlist_get_all
        companies = await watchlist_get_all()
        if not companies:
            await send(chat_id, "📭 등록된 관심 기업이 없습니다.\n/watch 기업명 으로 추가하세요.")
        else:
            lines = [f"⭐ <b>관심 기업 목록 ({len(companies)}개)</b>\n"]
            for i, c in enumerate(companies, 1):
                lines.append(f"{i}. {c}")
            lines.append("\n분석: /analyze 기업명 | 삭제: /unwatch 기업명")
            await send(chat_id, "\n".join(lines))

    elif text.strip() == "🔄 수집모드" or cmd == "/mode" and len(text.strip().split()) < 2:
        current = config.CAREER_LEVEL
        mode_name = {"entry": "신입·경력무관", "career": "경력직", "all": "전체"}.get(current, current)
        await send(
            chat_id,
            f"현재 수집 모드: <b>{mode_name}</b>\n\n변경하려면 아래 명령어를 입력하세요:\n\n"
            "/mode entry — 신입·경력무관 공고만\n"
            "/mode career — 경력직 공고만\n"
            "/mode all — 전체",
        )

    elif cmd.startswith("/mode"):
        parts = text.strip().split()
        if len(parts) < 2:
            await send(chat_id, "사용법: /mode entry | /mode career | /mode all")
            return
        mode = parts[1].lower()
        if mode not in ("entry", "career", "all"):
            await send(chat_id, "❌ 올바른 모드: entry | career | all")
            return
        import config as cfg_module
        cfg_module.config.CAREER_LEVEL = mode
        mode_name = {"entry": "신입·경력무관", "career": "경력직", "all": "전체"}[mode]
        await send(chat_id, f"✅ 수집 모드 변경: <b>{mode_name}</b>")

    else:
        await send(chat_id, f"❓ 알 수 없는 명령어입니다.\n/help 로 명령어 목록을 확인하세요.")


async def start_polling(
    run_pipeline_fn: Callable[[], Awaitable[None]],
    scheduler,
    allowed_chat_id: int | None = None,
) -> None:
    """Telegram long polling 루프 — main.py에서 asyncio.create_task로 실행."""
    offset = 0
    logger.info("텔레그램 봇 폴링 시작")

    while True:
        try:
            updates = await _get_updates(offset)
            for update in updates:
                offset = update["update_id"] + 1
                msg = update.get("message", {})
                chat_id = msg.get("chat", {}).get("id")
                text = msg.get("text", "")

                if not chat_id or not text:
                    continue

                # 허용된 채팅 ID만 처리
                if allowed_chat_id and chat_id != allowed_chat_id:
                    await send(chat_id, "⛔ 인증되지 않은 사용자입니다.")
                    continue

                logger.info("수신 명령 [%s]: %s", chat_id, text)
                asyncio.create_task(
                    handle_command(chat_id, text, run_pipeline_fn, scheduler)
                )
        except asyncio.CancelledError:
            logger.info("텔레그램 봇 폴링 종료")
            break
        except Exception as e:
            logger.error("폴링 오류: %s", e)
            await asyncio.sleep(5)
