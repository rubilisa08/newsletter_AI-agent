"""5. 발행(publish): 검수를 통과한 뉴스레터를 Discord 채널로 보낸다."""

import logging

from newsletter.state import NewsletterState

log = logging.getLogger(__name__)


def publish(state: NewsletterState) -> NewsletterState:
    log.info("[5/5 publish] 시작 (verified=%s)", state.get("verified"))

    # TODO: DISCORD_WEBHOOK_URL로 메시지 전송
    published = False

    log.info("[5/5 publish] 발행 여부: %s", published)
    return {"published": published}
