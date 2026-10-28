# 19장 실습 · 무료판 — 구조화 출력(pydantic 스키마)으로 예선 한 묶음 돌리기
#   uv run python practice/ch19_structured_free.py
#
# 구조화 출력의 핵심은 "답의 모양을 스키마로 정해 두고, 모양이 틀린 답은 받지 않는다"예요.
# 스키마 검사는 pydantic이 하므로 무료예요. LLM 대신 키워드 점수로 Pick을 채워 같은 모양으로 돌려요.
import re
import sys
from pathlib import Path

import feedparser, requests
from pydantic import BaseModel, Field, ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from skeleton import matched, score, strip_tags

class Pick(BaseModel):
    index: int = Field(description="후보 목록에서의 번호")
    reason: str = Field(description="왜 골랐는지 한 문장")
    event: str = Field(description="이 기사가 다루는 사건을 짧은 라벨로. 같은 사건이면 같은 라벨")

class Shortlist(BaseModel):
    picks: list[Pick]

# ── 1) 왜 스키마가 필요한가: 18장의 "번호만 쉼표로" 답이 깨지는 경우 ──
print("1) 모양이 틀린 답은 스키마 검사에서 걸러져요")
answers = {
    "번호만 쉼표로 (17장 방식)": '3, 7, 그리고 9번도 좋습니다',
    "스키마 모양 (19장 방식)":   '{"picks": [{"index": 3, "reason": "API 가격 변경", "event": "API 가격"}]}',
    "칸이 빠진 JSON":           '{"picks": [{"index": 3, "reason": "API 가격 변경"}]}',
}
for label, text in answers.items():
    try:
        Shortlist.model_validate_json(text)
        print(f"   통과  {label}")
    except ValidationError as ex:
        print(f"   거절  {label} — {ex.errors()[0]['msg']}")

# ── 2) 예선 한 묶음: 같은 12건에서 5건을 Shortlist 모양으로 ──
UA = {"User-Agent": "Mozilla/5.0 (newsletter-agent-course)"}
FEEDS = [("TechCrunch", "https://techcrunch.com/category/artificial-intelligence/feed/"),
         ("AI타임스",    "https://www.aitimes.com/rss/allArticle.xml"),
         ("The Verge",  "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml")]
titles = []
for name, url in FEEDS:
    for e in feedparser.parse(requests.get(url, headers=UA, timeout=20).content).entries[:4]:
        titles.append((name, e.title, strip_tags(e.get("summary", ""))[:300]))

STOP = {"The", "This", "How", "Why", "What", "New", "Its", "And", "For", "With",
        "인공지능", "확대", "공개", "출시", "기업", "시장", "발표", "가속", "규모"}

def event_label(title):                          # LLM의 event 대신 · 제목의 첫 고유 이름
    found = [w for w in re.findall(r"\b[A-Z][A-Za-z0-9]+|[가-힣]{2,}", title)
             if w not in STOP and w != "AI"]
    return found[0] if found else "기타"

def reason(item):                                # LLM의 reason 대신 · 걸린 키워드
    labels = list(dict.fromkeys(l for w, l in matched(item) if w > 0 and l))
    return f"키워드: {' · '.join(labels)}" if labels else "개발팀 키워드 없음 (동점 중 앞 순서)"

items = [{"title": t, "summary": s} for _, t, s in titles]
top = sorted(range(len(items)), key=lambda i: -score(items[i]))[:5]
raw = {"picks": [{"index": i, "reason": reason(items[i]), "event": event_label(titles[i][1])}
                 for i in top]}

out = Shortlist.model_validate(raw)              # ← LLM 답과 똑같이 스키마 검사를 통과해야 쓴다
out.picks = [p for p in out.picks if 0 <= p.index < len(titles)]    # 없는 번호는 버린다 (20장)

print("\n2) 예선 한 묶음 — Shortlist 모양으로 받은 5건")
for p in out.picks:
    print(f"[{p.event:<22}] {titles[p.index][1][:40]}")
    print(f"{'':25}└ {p.reason[:60]}")
