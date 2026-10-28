""".env 의 DISCORD_WEBHOOK_URL 로 테스트 메시지 한 건을 보내 웹훅이 동작하는지 확인한다.

    uv run python scripts/test_webhook.py
"""

import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    load_dotenv(ROOT / ".env")
    url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    if not url.startswith("https://discord.com/api/webhooks/"):
        print(".env 의 DISCORD_WEBHOOK_URL 이 비어 있거나 웹훅 주소 형식이 아닙니다.")
        return 1

    resp = requests.post(url, json={"content": "뉴스레터 에이전트 웹훅 연결 테스트입니다."}, timeout=10)
    if resp.ok:
        print("전송 성공: Discord 채널을 확인하세요.")
        return 0
    print(f"전송 실패: HTTP {resp.status_code} {resp.text}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
