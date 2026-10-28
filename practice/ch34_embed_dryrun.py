# 34장 실습 · embed 로 만들고 dry-run 으로 확인하기 (무료 · dry_run=True 라 보내지 않는다)
#   uv run python practice/ch34_embed_dryrun.py
import json, os, requests
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")      # DISCORD_WEBHOOK_URL

COLORS = {"모델·API": 0x0B6E77, "도구·프레임워크": 0x4C7C9C,
          "정책·규제": 0x8F5606, "사례·적용": 0x2E7D5B, "연구": 0x6A4A9C}
DEFAULT = 0x5F7476
TITLE_MAX, DESC_MAX, EMBED_MAX, TOTAL_MAX = 256, 4096, 10, 5800   # 6000에서 여유를 둔다

def build_embeds(run_id, lead, articles):
    if not articles:                                   # 조용한 날에도 한 장은 보낸다
        return [{"title": f"🗞️ {run_id}", "color": DEFAULT,
                 "description": "오늘은 조용합니다."}]
    embeds = [{"title": f"🗞️ {run_id} · AI 브리핑", "description": lead, "color": DEFAULT}]
    for i, a in enumerate(articles, 1):
        desc = a["summary"]
        if a.get("why"):
            desc += f"\n\n💡 **{a['why']}**"
        embeds.append({
            "title":       f"{i}. {a['headline']}"[:TITLE_MAX],
            "description": desc[:DESC_MAX],
            "url":         a["url"],
            "color":       COLORS.get(a.get("topic", ""), DEFAULT),
            "footer":      {"text": f"{a['source']} · {a['when']}"},
        })
    total = lambda es: sum(len(e.get("title", "")) + len(e.get("description", ""))
                           + len(e.get("footer", {}).get("text", "")) for e in es)
    while len(embeds) > EMBED_MAX or total(embeds) > TOTAL_MAX:
        embeds.pop()                                   # 뒤에서부터 덜어낸다
    return embeds

def send(run_id, lead, articles, webhook=None, dry_run=True):
    payload = {"username": "편집실", "embeds": build_embeds(run_id, lead, articles)}
    if dry_run or not webhook:
        print(f"[dry-run] embed {len(payload['embeds'])}개 · "
              f"{len(json.dumps(payload, ensure_ascii=False))}자 — 보내지 않음")
        print(json.dumps(payload["embeds"][-1], ensure_ascii=False, indent=2)[:400])
        return False
    r = requests.post(webhook, json=payload, timeout=20)
    ok = r.status_code in (200, 204)
    print("발행:", "성공" if ok else f"실패 {r.status_code} {r.text[:120]}")
    return ok

ARTICLES = [
    {"headline": "오픈AI, GPT-6 아스트라 공개", "url": "https://example.com/a",
     "summary": "오픈AI가 차세대 모델을 공개했습니다. 컨텍스트 한도가 두 배로 늘었습니다.",
     "why": "지금 쓰는 프롬프트를 그대로 옮길 수 있는지부터 확인해야 합니다.",
     "topic": "모델·API", "source": "전자신문", "when": "2시간 전"},
    {"headline": "엔비디아, 허깅페이스 인수 확정", "url": "https://example.com/b",
     "summary": "129억 달러 규모입니다. 모델 허브 운영 정책은 유지한다고 밝혔습니다.",
     "why": "사내에서 허브에 의존하는 파이프라인이 있다면 대안을 점검할 시점입니다.",
     "topic": "도구·프레임워크", "source": "TechCrunch", "when": "5시간 전"},
]

if __name__ == "__main__":
    send("2026-09-13", "모델 공개와 인수 소식이 이어졌습니다.", ARTICLES,
         webhook=os.environ.get("DISCORD_WEBHOOK_URL"), dry_run=True)   # ← False 로 바꾸면 실제 발행
