# 8장 실습 · 소스 여섯 곳이 실제로 무엇을 주는지 재 보기
#   uv run python practice/ch08_feed_probe.py
import feedparser, requests, re
from datetime import datetime, timezone

UA = {"User-Agent": "Mozilla/5.0 (newsletter-agent-course)"}
SOURCES = [
    ("OpenAI",     "https://openai.com/blog/rss.xml"),
    ("DeepMind",   "https://deepmind.google/blog/rss.xml"),
    ("TechCrunch", "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("The Verge",  "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
    ("MIT TR",     "https://www.technologyreview.com/feed/"),
    ("AI타임스",    "https://www.aitimes.com/rss/allArticle.xml"),
]
now = datetime.now(timezone.utc)
print(f"{'소스':<11}{'상태':<6}{'건수':>5}{'요약길이':>9}{'최신글':>9}")
print("-" * 42)
for name, url in SOURCES:
    r = requests.get(url, headers=UA, timeout=20)
    f = feedparser.parse(r.content)
    e = f.entries[0]
    body = e.get("content", [{}])[0].get("value") if e.get("content") else e.get("summary", "")
    text = re.sub(r"<[^>]+>", "", body or "").strip()
    t = e.get("published_parsed")
    age = (now - datetime(*t[:6], tzinfo=timezone.utc)).total_seconds() / 3600 if t else None
    print(f"{name:<11}{r.status_code:<6}{len(f.entries):>5}{len(text):>9}"
          f"{(f'{age:.0f}h' if age is not None else '?'):>9}")
