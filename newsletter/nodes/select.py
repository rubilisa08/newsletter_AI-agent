"""2. 선별(select): 후보 중 개발팀이 알아야 할 5건을 고른다."""

import logging

from newsletter.state import NewsletterState

log = logging.getLogger(__name__)

PICK_COUNT = 5


def select(state: NewsletterState) -> NewsletterState:
    candidates = state.get("candidates", [])
    log.info("[2/5 select] 시작 (후보 %d건)", len(candidates))

    # TODO: LLM으로 개발팀 관련도 평가 후 상위 5건 선택
    selected = candidates[:PICK_COUNT]

    log.info("[2/5 select] %d건 선별", len(selected))
    return {"selected": selected}
