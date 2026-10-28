# 24장 실습 · 기사 세 건을 취재해 본다 (강의 원본 · OpenAI 유료 호출 최대 3번)
#   uv run python practice/ch24_report_openai.py
# ⚠ .env 의 OPENAI_API_KEY 로 호출하므로 실행하면 OpenAI 계정에 요금이 청구된다.
#   무료로 보려면 practice/ch24_report_free.py 를 돌린다.
import os, feedparser, requests, trafilatura
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).resolve().parent.parent / ".env")   # 노트북의 키 설정 셀 대신
os.environ.setdefault("OPENAI_API_KEY", "")
client = OpenAI(default_headers={"Accept-Encoding": "gzip, deflate"})
UA = {"User-Agent": "Mozilla/5.0 (newsletter-agent-course)"}

class Draft(BaseModel):        # ← 방금 정한 세 칸
    headline: str = Field(description="20자 내외의 한국어 헤드라인")
    summary:  str = Field(description="세 문장 요약. ~합니다체, 과장 없이 건조하게")
    why:      str = Field(description="국내 개발팀에게 왜 중요한지 한 문장")

SYS = ("당신은 국내 개발팀을 위한 AI 뉴스레터 기자입니다.\n"
       "아래 기사 본문을 읽고 헤드라인·요약·왜 중요한지를 쓰세요.\n"
       "'주목된다·기대를 모은다' 같은 기자체 표현은 쓰지 마세요.")

feed = feedparser.parse(requests.get(
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    headers=UA, timeout=20).content)

for e in feed.entries[:3]:
    downloaded = trafilatura.fetch_url(e.link)
    body = trafilatura.extract(downloaded) if downloaded else None
    if not body or len(body) < 600:          # ← 섹션 3에서 정한 G1 기준선
        continue
    out = client.chat.completions.parse(
        model="gpt-4.1-mini", temperature=0,
        messages=[{"role": "system", "content": SYS},
                  {"role": "user", "content": body[:6000]}],
        response_format=Draft).choices[0].message.parsed
    print("─" * 66)
    print("원문:", e.title[:60], f"(본문 {len(body)}자)")
    print("  헤드라인:", out.headline)
    print("  요약    :", out.summary[:120], "…")
