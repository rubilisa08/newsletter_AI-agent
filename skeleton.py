import operator
import re
from datetime import datetime, timedelta, timezone
from typing import Annotated, TypedDict
from urllib.parse import urlsplit

import feedparser
import requests
from langgraph.graph import StateGraph, START, END

class Brief(TypedDict):
    hours:     int                              # 수집 time window(시간)
    collected: list                             # ① 수집한 기사
    picked:    list                             # ② 선별해 남긴 다섯 건
    drafted:   Annotated[list, operator.add]    # ③ 취재한 초안 — 워커들이 나눠 채운다
    log:       Annotated[list, operator.add]    # 무슨 일이 있었는지

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

KST = timezone(timedelta(hours=9))
NAIVE_KST = {"AI타임스"}                       # 시간대 없이 한국 시각으로 적는 피드

def published_at(entry, tz=timezone.utc):
    t = entry.get("published_parsed")
    return datetime(*t[:6], tzinfo=tz) if t else None

def url_key(link):                             # utm_ 같은 추적용 꼬리표만 떼고 비교
    parts = urlsplit(link)
    query = "&".join(q for q in parts.query.split("&") if q and not q.startswith("utm_"))
    return f"{parts.netloc}{parts.path.rstrip('/')}?{query}"

def collect(s: dict) -> dict:                  # ① 자료 수집 — 2부(13장)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=s["hours"])
    items, dead, seen = [], [], set()
    for name, url in SOURCES:
        try:
            feed = feedparser.parse(requests.get(url, headers=UA, timeout=20).content)
        except Exception:
            dead.append(name)                   # 한 곳이 죽어도 나머지는 계속
            continue
        for e in feed.entries:
            at = published_at(e, KST if name in NAIVE_KST else timezone.utc)
            if not at or at < cutoff:           # time window 밖이거나 날짜가 없으면 버린다
                continue
            key = url_key(e.link)               # AI타임스는 ?idxno= 가 기사 번호라 통째로 떼면 안 된다
            if key in seen:
                continue
            seen.add(key)
            items.append({"title": e.title, "url": e.link, "source": name, "at": at,
                          "summary": strip_tags(e.get("summary", ""))[:300]})
    return {"collected": items,
            "log": [f"① 수집   {s['hours']}시간 time window · {len(items)}건"
                    + (f" · 응답 없음 {dead}" if dead else "")]}

TARGET, PER_SOURCE = 5, 2                       # 최종 발행 건수, 한 소스에서 최대 몇 건

# 무료 버전 — LLM 대신 키워드 점수로 고른다. 나중에 3부(20장)의 OpenAI 버전으로 갈아 끼운다.
# 기준은 강의의 CRITERIA: "개발팀이 일하는 방식이 바뀔 만한가", 홍보성 소식은 버린다.
SCORES = [
    (r"\bAPIs?\b|\bSDK\b|오픈\s?API",                                    3),
    (r"\bopen[- ]?(sourc\w*|weights?)\b|오픈소스|오픈 웨이트",                  2),
    (r"\b(release[sd]?|launch(es|ed)?)\b|출시|공개",                          1),
    (r"\b(pric\w*|rate limits?|deprecat\w*)\b|가격|요금|한도|종료",           3),
    (r"\b(developers?|coding|code|agents?|GitHub|benchmark\w*)\b|개발자|코딩|에이전트", 2),
    (r"\b(GPT|Claude|Gemini|Llama|Qwen|DeepSeek|Mistral|LLM)\w*",           1),
    (r"\b(raises?|funding|valuation|IPO|investors?|VCs?)\b|투자|유치|상장|MOU|협약|수상", -3),
    (r"\b(sues?|lawsuit)\b|소송",                                          -1),
    (r"\[게시판\]|\[인사\]|단신",                                           -9),  # 여러 소식을 모은 목록 기사
]

def score(item):
    text = f"{item['title']} {item['summary']}"
    return sum(w for pat, w in SCORES if re.search(pat, text, re.IGNORECASE))

def select(s: dict) -> dict:                   # ② 중요도 선별 — 무료 키워드 버전
    ranked = sorted(s["collected"], key=lambda it: (score(it), it["at"]), reverse=True)
    picked, per_source = [], {}
    for it in ranked:
        if len(picked) == TARGET:
            break
        if per_source.get(it["source"], 0) >= PER_SOURCE:     # 한 매체가 다섯 칸을 다 차지하지 않게
            continue
        per_source[it["source"]] = per_source.get(it["source"], 0) + 1
        picked.append({**it, "score": score(it)})
    return {"picked": picked,
            "log": [f"② 선별   {len(s['collected'])} → {len(picked)}건 (키워드 점수)"]}

def report(s: dict) -> dict:                   # ③ 요약       — 섹션 6에서 채운다
    return {"drafted": [], "log": [f"③ 취재   {len(s['picked'])}건 (빈 노드)"]}

def verify(s: dict) -> dict:                   # ④ 검수       — 섹션 7에서 채운다
    return {"log": [f"④ 검수   {len(s['drafted'])}건 (빈 노드)"]}

def publish(s: dict) -> dict:                  # ⑤ 발행       — 섹션 8에서 채운다
    return {"log": [f"⑤ 발행   {len(s['drafted'])}건 (빈 노드)"]}

def build():                                    # 노드를 이름으로 찾아 붙인다
    g = StateGraph(Brief)
    for name in ("collect", "select", "report", "verify", "publish"):
        g.add_node(name, globals()[name])
    g.add_edge(START, "collect")
    g.add_edge("collect", "select")
    g.add_edge("select", "report")
    g.add_edge("report", "verify")
    g.add_edge("verify", "publish")
    g.add_edge("publish", END)
    return g

INIT = {"hours": 24,
        "collected": [], "picked": [], "drafted": [], "log": []}

def run():
    return build().compile().invoke(INIT)

if __name__ == "__main__":                      # main.py가 import할 때는 실행하지 않는다
    for line in run()["log"]:
        print(line)
