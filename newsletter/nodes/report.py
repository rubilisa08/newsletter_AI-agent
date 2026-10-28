"""3. 취재 및 요약(report): 선별된 기사 원문을 읽고 개발자 관점으로 요약한다."""

import logging

from newsletter.state import NewsletterState

log = logging.getLogger(__name__)


def report(state: NewsletterState) -> NewsletterState:
    selected = state.get("selected", [])
    log.info("[3/5 report] 시작 (%d건)", len(selected))

    # TODO: 원문 본문 가져와서 LLM으로 요약 작성
    reports = [dict(article) for article in selected]

    log.info("[3/5 report] 요약 %d건 작성", len(reports))
    return {"reports": reports}
