# 17장 실습 · 한 화면에 놓고 비교하기 (강의 원본 · OpenAI 유료 호출 1번)
#   uv run python practice/ch17_listwise_openai.py
# ⚠ .env 의 OPENAI_API_KEY 로 호출하므로 실행하면 OpenAI 계정에 요금이 청구된다.
#   무료로 비교해 보려면 practice/ch17_listwise_free.py 를 돌린다.
import feedparser, requests
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

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

# ── 17장 ──
listing = "\n".join(f"{i}. [{s}] {t}" for i, (s, t) in enumerate(titles))
SYS = ("당신은 국내 개발팀을 위한 AI 뉴스레터 편집자입니다.\n"
       "아래 후보를 서로 비교해 '이번 주 우리가 일하는 방식이 바뀔 만한' 순서대로 "
       "상위 5건을 고르세요. 번호만 쉼표로 구분해 답하세요. 설명 금지.")

r = client.chat.completions.create(                # ← 호출 한 번, 전부 한 화면에
    model="gpt-4.1-mini", temperature=0, max_tokens=40,
    messages=[{"role": "system", "content": SYS},
              {"role": "user", "content": listing}])
picked = [int(x) for x in r.choices[0].message.content.strip().replace(" ", "").split(",")][:5]

print("한 화면에 놓고 비교한 결과 — 상위 5건")
for rank, i in enumerate(picked, 1):
    print(f"  {rank}위  [{titles[i][0]}] {titles[i][1][:46]}")
