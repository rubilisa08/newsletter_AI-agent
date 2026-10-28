# 17장 실습 · 무료판 — 같은 12건을 "따로 채점(15장)"과 "한 화면에 놓고 보기"로 각각 골라 비교한다
#   uv run python practice/ch17_listwise_free.py
#
# LLM이 없으니 '어느 쪽이 더 중요한가'를 서로 비교하지는 못한다.
# 대신 목록 전체를 같이 봐야만 알 수 있는 것 — 여러 기사가 같은 사건을 다루는지 — 을 쓴다.
#   · 같은 사건(이름이 겹치는 제목)은 한 건만 남기고
#   · 여러 매체가 다룬 사건일수록 화제성 점수를 더한다
import re
import sys
from pathlib import Path

import feedparser, requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from graph import score, strip_tags

UA = {"User-Agent": "Mozilla/5.0 (newsletter-agent-course)"}
FEEDS = [("TechCrunch", "https://techcrunch.com/category/artificial-intelligence/feed/"),
         ("AI타임스",    "https://www.aitimes.com/rss/allArticle.xml"),
         ("The Verge",  "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml")]
titles = []
for name, url in FEEDS:
    for e in feedparser.parse(requests.get(url, headers=UA, timeout=20).content).entries[:4]:
        titles.append((name, e.title, strip_tags(e.get("summary", ""))[:300]))

points = [score({"title": t, "summary": s}) for _, t, s in titles]

# ── 15장 방식: 따로 채점해서 점수순 5건 (동점이면 목록 순서) ──
pointwise = sorted(range(len(titles)), key=lambda i: -points[i])[:5]

# ── 한 화면 방식: 제목끼리 겹치는 이름으로 같은 사건을 묶는다 ──
STOP = {"The", "This", "How", "Why", "What", "New", "Its", "And", "For", "With",
        "인공지능", "확대", "공개", "출시", "기업", "시장", "발표", "가속", "규모"}

def names(title):
    found = re.findall(r"\b[A-Z][A-Za-z0-9]+|[가-힣]{2,}", title)
    return {w for w in found if w not in STOP and w != "AI"}

group = list(range(len(titles)))                 # 처음엔 기사마다 자기 혼자 한 사건
def find(i):
    while group[i] != i:
        i = group[i]
    return i
for i in range(len(titles)):
    for j in range(i + 1, len(titles)):
        if names(titles[i][1]) & names(titles[j][1]):    # 이름이 하나라도 겹치면 같은 사건
            group[find(j)] = find(i)

events = {}
for i in range(len(titles)):
    events.setdefault(find(i), []).append(i)

ranked = []
for members in events.values():
    best = max(members, key=lambda i: points[i])          # 사건마다 대표 기사 한 건
    buzz = len({titles[i][0] for i in members}) - 1       # 다룬 매체 수만큼 화제성 가산
    ranked.append((points[best] + buzz, best, members))
listwise = [best for _, best, _ in sorted(ranked, key=lambda x: -x[0])[:5]]

def show(label, picks):
    print(label)
    for rank, i in enumerate(picks, 1):
        print(f"  {rank}위  {points[i]:>3}점  [{titles[i][0]}] {titles[i][1][:46]}")

show("① 따로 채점(15장 방식) — 상위 5건", pointwise)
print()
show("② 한 화면에 놓고 보기 — 상위 5건", listwise)
print("\n같은 사건으로 묶인 기사:")
for _, _, members in ranked:
    if len(members) > 1:
        print("  ·", " / ".join(f"[{titles[i][0]}] {titles[i][1][:30]}" for i in members))
print(f"\n두 방식 모두 고른 기사: {len(set(pointwise) & set(listwise))}건 / 5건")
