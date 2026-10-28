"""1. 수집(collect): 여러 소스에서 오늘의 AI 소식 후보를 모은다."""

import logging

from newsletter.state import NewsletterState

log = logging.getLogger(__name__)


def collect(state: NewsletterState) -> NewsletterState:
    log.info("[1/5 collect] 시작 (run_date=%s)", state.get("run_date"))

    # TODO: RSS·블로그·HN·GitHub 등에서 최근 24시간 AI 소식 수집
    candidates = []

    log.info("[1/5 collect] 후보 %d건 수집", len(candidates))
    return {"candidates": candidates}
