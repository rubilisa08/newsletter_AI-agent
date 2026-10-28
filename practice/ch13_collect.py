# 13장 실습 · collect 함수로 수집 노드를 채우고 그래프를 다시 돌리기 (강의 원본 코드)
#   uv run python practice/ch13_collect.py
#
# 노트북에서는 collect를 다시 정의하면 globals()로 새 함수가 들어간다.
# 파일에서는 graph 모듈의 collect 자리에 이 함수를 넣어 같은 효과를 낸다.
# 실제로 쓰는 개선판(소스 11곳 · AI타임스 중복 판정 수정 · 한국 시각)은 graph.py 에 있다.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import graph

import feedparser, requests, re
from datetime import datetime, timedelta, timezone

UA = {"User-Agent": "Mozilla/5.0 (newsletter-agent-course)"}
SOURCES = [
    ("OpenAI",     "https://openai.com/blog/rss.xml"),
    ("DeepMind",   "https://deepmind.google/blog/rss.xml"),
    ("TechCrunch", "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("The Verge",  "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
    ("AI타임스",    "https://www.aitimes.com/rss/allArticle.xml"),
]

def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s or "").strip()

def published_at(entry):
    t = entry.get("published_parsed")
    return datetime(*t[:6], tzinfo=timezone.utc) if t else None

def collect(s: dict) -> dict:                   # ① 자료 수집 — 빈 노드를 갈아 끼운다
    cutoff = datetime.now(timezone.utc) - timedelta(hours=s["hours"])
    items, dead, seen = [], [], set()
    for name, url in SOURCES:
        try:
            feed = feedparser.parse(requests.get(url, headers=UA, timeout=20).content)
        except Exception:
            dead.append(name)                   # 한 곳이 죽어도 나머지는 계속
            continue
        for e in feed.entries:
            at = published_at(e)
            if not at or at < cutoff:           # time window 밖이거나 날짜가 없으면 버린다
                continue
            key = e.link.split("?")[0].rstrip("/")       # 추적용 꼬리표를 떼고 비교
            if key in seen:
                continue
            seen.add(key)
            items.append({"title": e.title, "url": e.link, "source": name, "at": at,
                          "summary": strip_tags(e.get("summary", ""))[:300]})
    return {"collected": items,
            "log": [f"① 수집   {s['hours']}시간 time window · {len(items)}건"
                    + (f" · 응답 없음 {dead}" if dead else "")]}

graph.collect = collect                      # 노드를 갈아 끼운다 — build()가 이 이름으로 찾아 붙인다

out = graph.run()
for line in out["log"]:                         # 그래프는 그대로, 노드만 바뀌었다
    print(line)

from collections import Counter
print("소스별:", dict(Counter(i["source"] for i in out["collected"])))
