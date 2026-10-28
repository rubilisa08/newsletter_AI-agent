# 15장 실습 · Pointwise Scoring으로 기사마다 점수 매기기 (강의 원본 · OpenAI 유료 호출 12번)
#   uv run python practice/ch15_pointwise_openai.py
# ⚠ .env 의 OPENAI_API_KEY 로 호출하므로 실행할 때마다 OpenAI 계정에 요금이 청구된다.
#   무료로 같은 실험을 보려면 practice/ch15_pointwise_free.py 를 돌린다.
import os, feedparser, requests
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parent.parent / ".env")      # 노트북의 "위 셀"에서 키를 넣던 자리
client = OpenAI(default_headers={"Accept-Encoding": "gzip, deflate"})
UA = {"User-Agent": "Mozilla/5.0 (newsletter-agent-course)"}

FEEDS = [("TechCrunch", "https://techcrunch.com/category/artificial-intelligence/feed/"),
         ("AI타임스",    "https://www.aitimes.com/rss/allArticle.xml"),
         ("The Verge",  "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml")]
titles = []
for name, url in FEEDS:
    for e in feedparser.parse(requests.get(url, headers=UA, timeout=20).content).entries[:4]:
        titles.append((name, e.title))

RUBRIC = ("당신은 국내 개발팀을 위한 AI 뉴스레터 편집자입니다.\n"
          "아래 기사 제목이 '이번 주 우리가 일하는 방식이 바뀔 만한가'라는 "
          "기준에서 얼마나 중요한지 1~10점으로 매기세요. 숫자만 답하세요.")

scores = []
for src, t in titles:                      # ← 기사마다 한 번씩, 서로 모르는 채로
    r = client.chat.completions.create(
        model="gpt-4.1-mini", temperature=0, max_tokens=5,
        messages=[{"role": "system", "content": RUBRIC},
                  {"role": "user", "content": t}])
    scores.append((r.choices[0].message.content.strip(), src, t))

for s, src, t in sorted(scores, key=lambda x: -int(x[0])):
    print(f"{s:<6}{src:<12}{t[:44]}")
dist = Counter(s for s, _, _ in scores)
print("\n점수 분포:", " · ".join(f"{k}점 {v}건" for k, v in sorted(dist.items(), key=lambda kv: -int(kv[0]))))
print(f"서로 다른 점수 값: {len(dist)}개 / 후보 {len(scores)}건")
