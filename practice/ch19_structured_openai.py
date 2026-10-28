# 19장 실습 · 구조화 출력으로 예선 한 묶음 돌리기 (강의 원본 · OpenAI 유료 호출 1번)
#   uv run python practice/ch19_structured_openai.py
# ⚠ .env 의 OPENAI_API_KEY 로 호출하므로 실행하면 OpenAI 계정에 요금이 청구된다.
#   무료로 보려면 practice/ch19_structured_free.py 를 돌린다.
import feedparser, requests
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

# ── 15장 셀에서 만든 client · titles (노트북에서는 위 셀에 있던 것) ──
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
client = OpenAI(default_headers={"Accept-Encoding": "gzip, deflate"})
UA = {"User-Agent": "Mozilla/5.0 (newsletter-agent-course)"}
FEEDS = [("TechCrunch", "https://techcrunch.com/category/artificial-intelligence/feed/"),
         ("AI타임스",    "https://www.aitimes.com/rss/allArticle.xml"),
         ("The Verge",  "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml")]
titles = []
for name, url in FEEDS:
    for e in feedparser.parse(requests.get(url, headers=UA, timeout=20).content).entries[:4]:
        titles.append((name, e.title))

# ── 19장 ──
class Pick(BaseModel):
    index: int = Field(description="후보 목록에서의 번호")
    reason: str = Field(description="왜 골랐는지 한 문장")
    event: str = Field(description="이 기사가 다루는 사건을 짧은 라벨로. 같은 사건이면 같은 라벨")

class Shortlist(BaseModel):
    picks: list[Pick]

SYS = ("당신은 국내 개발팀을 위한 AI 뉴스레터 편집자입니다.\n"
       "후보를 서로 비교해 '이번 주 우리가 일하는 방식이 바뀔 만한' 기사 5건을 고르세요.\n"
       "각 기사에 대해 고른 이유와, 그 기사가 다루는 '사건' 라벨을 함께 답하세요.\n"
       "같은 사건을 다룬 기사에는 반드시 같은 라벨을 붙이세요.")

listing = "\n".join(f"{i}. [{s}] {t}" for i, (s, t) in enumerate(titles))
out = client.chat.completions.parse(          # ← parse: 스키마로 형식을 강제한다
    model="gpt-4.1-mini", temperature=0,
    messages=[{"role": "system", "content": SYS},
              {"role": "user", "content": listing}],
    response_format=Shortlist).choices[0].message.parsed

for p in out.picks:
    print(f"[{p.event:<22}] {titles[p.index][1][:40]}")
    print(f"{'':25}└ {p.reason[:60]}")
