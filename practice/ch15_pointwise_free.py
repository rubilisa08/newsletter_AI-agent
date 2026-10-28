# 15장 실습 · 무료판 — 같은 12건을 OpenAI 대신 skeleton.py 의 키워드 점수로 따로따로 매긴다
#   uv run python practice/ch15_pointwise_free.py
import sys
from collections import Counter
from pathlib import Path

import feedparser, requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from skeleton import score, strip_tags

UA = {"User-Agent": "Mozilla/5.0 (newsletter-agent-course)"}

FEEDS = [("TechCrunch", "https://techcrunch.com/category/artificial-intelligence/feed/"),
         ("AI타임스",    "https://www.aitimes.com/rss/allArticle.xml"),
         ("The Verge",  "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml")]
titles = []
for name, url in FEEDS:
    for e in feedparser.parse(requests.get(url, headers=UA, timeout=20).content).entries[:4]:
        titles.append((name, e.title, strip_tags(e.get("summary", ""))[:300]))

scores = []
for src, t, summary in titles:             # ← 기사마다 한 번씩, 서로 모르는 채로
    scores.append((score({"title": t, "summary": summary}), src, t))

for s, src, t in sorted(scores, key=lambda x: -x[0]):
    print(f"{s:<6}{src:<12}{t[:44]}")
dist = Counter(s for s, _, _ in scores)
print("\n점수 분포:", " · ".join(f"{k}점 {v}건" for k, v in sorted(dist.items(), key=lambda kv: -kv[0])))
print(f"서로 다른 점수 값: {len(dist)}개 / 후보 {len(scores)}건")
