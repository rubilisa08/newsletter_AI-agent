"""4. 검수(verify): 요약이 원문과 맞는지, 건수·링크·형식이 올바른지 확인한다."""

import logging

from newsletter.state import NewsletterState

log = logging.getLogger(__name__)


def verify(state: NewsletterState) -> NewsletterState:
    reports = state.get("reports", [])
    log.info("[4/5 verify] 시작 (%d건)", len(reports))

    # TODO: 사실관계·링크·5건 여부·디스코드 글자 수 제한 검사
    issues: list[str] = []

    log.info("[4/5 verify] 문제 %d건", len(issues))
    return {"verified": not issues, "issues": issues}
