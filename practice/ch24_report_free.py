# 24장 실습 · 무료판 — 같은 기사 세 건을 취재해 Draft 세 칸을 LLM 없이 채운다
#   uv run python practice/ch24_report_free.py
#
# 본문 추출(trafilatura)과 G1 기준선은 강의와 같다. LLM이 쓰던 세 칸은 graph.py 의 무료 draft()로 채운다:
#   headline = 원래 제목 · summary = 피드가 준 요약 · why = 걸린 개발팀 키워드
import re
import sys
from pathlib import Path

import feedparser, requests, trafilatura
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from graph import draft, strip_tags

UA = {"User-Agent": "Mozilla/5.0 (newsletter-agent-course)"}

class Draft(BaseModel):        # ← 강의와 같은 세 칸
    headline: str = Field(description="20자 내외의 한국어 헤드라인")
    summary:  str = Field(description="세 문장 요약. ~합니다체, 과장 없이 건조하게")
    why:      str = Field(description="국내 개발팀에게 왜 중요한지 한 문장")

feed = feedparser.parse(requests.get(
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    headers=UA, timeout=20).content)

for e in feed.entries[:3]:
    downloaded = trafilatura.fetch_url(e.link)
    body = trafilatura.extract(downloaded) if downloaded else None
    if not body or len(body) < 600:          # ← 섹션 3에서 정한 G1 기준선
        print("─" * 66)
        print("취재 제외:", e.title[:60], f"(본문 {len(body or '')}자)")
        continue
    item = {"title": e.title, "summary": strip_tags(e.get("summary", ""))[:300]}
    out = Draft(**draft(item, body))         # ← LLM 대신 무료 draft, 같은 스키마 검사
    korean_ok = bool(re.search(r"[가-힣]", out.headline + out.summary))   # 같은 장의 한국어 확인
    print("─" * 66)
    print("원문:", e.title[:60], f"(본문 {len(body)}자)")
    print("  헤드라인:", out.headline)
    print("  요약    :", out.summary[:120], "…")
    print("  why     :", out.why or "(키워드 없음)")
    print("  한국어  :", "예" if korean_ok else "아니요 — 영어 그대로")
