import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import config

logger = logging.getLogger(__name__)

_blocked_sources: dict[str, float] = {}
_BLOCK_SECONDS = 6 * 3600


def is_blocked(source: str) -> bool:
    import time
    unblock_at = _blocked_sources.get(source, 0)
    if time.time() < unblock_at:
        return True
    _blocked_sources.pop(source, None)
    return False


def block_source(source: str) -> None:
    import time
    _blocked_sources[source] = time.time() + _BLOCK_SECONDS
    logger.warning("소스 %s 6시간 차단됨", source)


def build_scheduler(wanted_job_func, saramin_job_func) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Asia/Seoul")

    scheduler.add_job(
        wanted_job_func,
        trigger=IntervalTrigger(minutes=config.WANTED_POLL_INTERVAL_MINUTES),
        id="wanted_collector",
        name="원티드 수집",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.add_job(
        saramin_job_func,
        trigger=IntervalTrigger(minutes=config.SARAMIN_POLL_INTERVAL_MINUTES),
        id="saramin_collector",
        name="사람인 수집",
        replace_existing=True,
        max_instances=1,
    )

    return scheduler
