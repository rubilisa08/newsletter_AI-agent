# 33장 실습 · 웹훅으로 첫 메시지 보내기 (무료 · Discord 채널에 실제로 한 줄 올라간다)
#   uv run python practice/ch33_webhook_first.py
import os, requests
from pathlib import Path

from dotenv import load_dotenv

# 강의 원본은 os.environ["DISCORD_WEBHOOK_URL"] = "https://..." 로 주소를 코드에 직접 적는다.
# 이 레포는 공개라서 주소가 GitHub에 올라가지 않도록 .env 에서 읽는다.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "")
assert WEBHOOK, "환경변수 DISCORD_WEBHOOK_URL 을 먼저 설정하세요"

r = requests.post(WEBHOOK, json={"content": "편집실 연결 확인 ✅"}, timeout=20)
print(r.status_code, r.text or "(본문 없음)")
