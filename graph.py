import json
import operator
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from typing import Annotated, TypedDict
from urllib.parse import urlsplit

import feedparser
import requests
import trafilatura
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from pydantic import BaseModel, Field

# Windows에서 출력을 파일·파이프로 넘기면 cp949로 인코딩돼 이모지·'—'에서 멈춘다. 출력은 늘 UTF-8로.
if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

class Brief(TypedDict):
    hours:     int                              # 수집 time window(시간)
    collected: list                             # ① 수집한 기사
    picked:    list                             # ② 선별해 남긴 다섯 건
    drafted:   Annotated[list, operator.add]    # ③ 취재한 초안 — 워커들이 나눠 채운다
    verified:  list                             # ④ 검수를 통과한 것 (31장에서 더한 칸)
    log:       Annotated[list, operator.add]    # 무슨 일이 있었는지

UA = {"User-Agent": "Mozilla/5.0 (newsletter-agent-course)"}
SOURCES = [                                     # RSS·Atom 피드 10곳 (사다리 ②칸)
    # 1차 소스 — 사건 당사자가 직접 발표하는 곳
    ("OpenAI",       "https://openai.com/blog/rss.xml"),
    ("DeepMind",     "https://deepmind.google/blog/rss.xml"),
    ("Google AI",    "https://blog.google/technology/ai/rss/"),
    ("Hugging Face", "https://huggingface.co/blog/feed.xml"),
    ("AWS ML",       "https://aws.amazon.com/blogs/machine-learning/feed/"),
    # 2차 소스 — 발표를 받아 쓰는 매체
    ("TechCrunch",   "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("The Verge",    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
    ("MIT TR",       "https://www.technologyreview.com/feed/"),
    ("AI타임스",      "https://www.aitimes.com/rss/allArticle.xml"),
    ("전자신문",       "https://rss.etnews.com/04.xml"),             # AI·SW 섹션
]
HN_API = "https://hn.algolia.com/api/v1/search_by_date"          # Hacker News 공개 API (사다리 ①칸)
HN_MIN_POINTS = 20                                               # 이 점수 아래 글은 화제가 안 된 것으로 본다

def strip_tags(s):
    s = re.sub(r"<[^>]+>", " ", s or "")                   # 문단 태그 자리에 띄어쓰기
    s = re.sub(r"([.!?])(?=[가-힣A-Z\"'“‘])", r"\1 ", s)   # "앞섰다.중국"처럼 붙은 문장 사이 (3.8 같은 숫자는 그대로)
    return re.sub(r"\s+", " ", s).strip()

KST = timezone(timedelta(hours=9))
NAIVE_KST = {"AI타임스"}                       # 시간대 없이 한국 시각으로 적는 피드

def published_at(entry, tz=timezone.utc):
    t = entry.get("published_parsed") or entry.get("updated_parsed")   # Atom은 updated만 줄 때가 있다
    return datetime(*t[:6], tzinfo=tz) if t else None

def collect_hn(cutoff):                        # Hacker News는 RSS 대신 공개 API로 가져온다
    r = requests.get(HN_API, timeout=20, params={
        "query": "AI", "tags": "story", "hitsPerPage": 50,
        "numericFilters": f"created_at_i>{int(cutoff.timestamp())},points>={HN_MIN_POINTS}"})
    r.raise_for_status()
    items = []
    for h in r.json()["hits"]:
        if not h.get("title"):                  # 제목 없는 글은 건너뛴다
            continue
        url = h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}"
        # HN은 피드 요약이 없다. 본문은 재배포하지 않으므로 화제성과 원문 도메인으로 요약 칸을 채운다
        items.append({"title": h["title"], "url": url, "source": "Hacker News",
                      "at": datetime.fromtimestamp(h["created_at_i"], timezone.utc),
                      "summary": f"Hacker News에서 {h.get('points') or 0}점 · 댓글 {h.get('num_comments') or 0}개를 "
                                 f"받은 글입니다. 원문: {urlsplit(url).netloc}"})
    return items

def url_key(link):                             # utm_ 같은 추적용 꼬리표만 떼고 비교
    parts = urlsplit(link)
    query = "&".join(q for q in parts.query.split("&") if q and not q.startswith("utm_"))
    return f"{parts.netloc}{parts.path.rstrip('/')}?{query}"

def collect(s: dict) -> dict:                  # ① 자료 수집 — 2부(13장)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=s["hours"])
    items, dead, seen = [], [], set()
    for name, url in SOURCES:
        try:
            r = requests.get(url, headers=UA, timeout=20)
            r.raise_for_status()                # 403·500 오류 페이지를 '0건'이 아니라 '응답 없음'으로 센다
            feed = feedparser.parse(r.content)
        except Exception:
            dead.append(name)                   # 한 곳이 죽어도 나머지는 계속
            continue
        for e in feed.entries:
            if not e.get("link") or not e.get("title"):   # 링크나 제목이 빠진 글 하나로 전체가 멈추지 않게
                continue
            at = published_at(e, KST if name in NAIVE_KST else timezone.utc)
            if not at or at < cutoff:           # time window 밖이거나 날짜가 없으면 버린다
                continue
            key = url_key(e.link)               # AI타임스는 ?idxno= 가 기사 번호라 통째로 떼면 안 된다
            if key in seen:
                continue
            seen.add(key)
            items.append({"title": e.title, "url": e.link, "source": name, "at": at,
                          "summary": strip_tags(e.get("summary", ""))[:300]})
    try:
        for it in collect_hn(cutoff):
            key = url_key(it["url"])
            if key not in seen:                 # 매체 기사와 같은 링크면 한 번만
                seen.add(key)
                items.append(it)
    except Exception:
        dead.append("Hacker News")
    return {"collected": items,
            "log": [f"① 수집   {s['hours']}시간 time window · {len(items)}건"
                    + (f" · 응답 없음 {dead}" if dead else "")]}

BATCH, TARGET = 40, 5          # 예선 묶음 크기, 최종 발행 건수
PER_SOURCE = 2                 # 본선에서 한 매체가 차지할 수 있는 최대 칸 수

class Pick(BaseModel):                          # 19장 구조화 출력 스키마
    index: int = Field(description="후보 목록에서의 번호")
    reason: str = Field(description="왜 골랐는지 한 문장")
    event: str = Field(description="이 기사가 다루는 사건을 짧은 라벨로. 같은 사건이면 같은 라벨")

class Shortlist(BaseModel):
    picks: list[Pick]

# 무료 버전 — LLM 대신 키워드 점수로 고른다. 유료로 바꿀 땐 ask_picks 만 20장 코드로 갈아 끼운다
# (practice/ch20_select_openai.py). 기준은 강의의 CRITERIA를 키워드로 옮긴 것:
# "개발팀이 일하는 방식이 바뀔 만한가", "도구·API의 가격·한도·정책 변화", 홍보성 소식은 버린다.
SCORES = [                                     # (패턴, 점수, report의 why에 쓸 이름)
    (r"\bAPIs?\b|\bSDK\b|오픈\s?API",                                    3, "API·SDK"),
    (r"\bopen[- ]?(sourc\w*|weights?)\b|오픈소스|오픈 웨이트",                  2, "오픈소스"),
    (r"\b(release[sd]?|launch(es|ed)?)\b|출시|공개",                          1, "출시"),
    (r"\b(pric\w*|rate limits?|deprecat\w*)\b|가격|요금|한도|종료",           3, "가격·한도"),
    (r"\b(developers?|coding|code|agents?|GitHub|benchmark\w*)\b|개발자|코딩|에이전트", 2, "개발 도구"),
    (r"\b(GPT|Claude|Gemini|Llama|Qwen|DeepSeek|Mistral|LLM)\w*",           1, "모델"),
    (r"\b(raises?|funding|valuation|IPO|investors?|VCs?)\b|투자|유치|상장|MOU|협약|수상", -3, ""),
    (r"\b(sues?|lawsuit)\b|소송",                                          -1, ""),
    (r"\[게시판\]|\[인사\]|단신",                                           -9, ""),  # 여러 소식을 모은 목록 기사
]

def matched(item):
    text = f"{item['title']} {item['summary']}"
    return [(w, label) for pat, w, label in SCORES if re.search(pat, text, re.IGNORECASE)]

def score(item):
    return sum(w for w, _ in matched(item))

def labels(item):                              # 걸린 개발팀 키워드 이름들
    return list(dict.fromkeys(label for w, label in matched(item) if w > 0 and label))

def ask_picks(items, n):                       # 무료 ask_picks — 20장과 같은 모양(Pick 목록)을 돌려준다
    ranked = sorted(range(len(items)), key=lambda i: (score(items[i]), items[i]["at"]), reverse=True)
    cap = PER_SOURCE if n <= TARGET else n     # 본선에서만 매체당 칸 수를 제한한다
    picks, per_source = [], {}
    for i in ranked:
        if len(picks) == n:
            break
        src = items[i]["source"]
        if per_source.get(src, 0) >= cap:
            continue
        per_source[src] = per_source.get(src, 0) + 1
        found = labels(items[i])
        picks.append(Pick(index=i,
                          reason=f"키워드: {' · '.join(found)}" if found else "개발팀 키워드 없음",
                          event=found[0] if found else "기타"))
    return [p for p in picks if 0 <= p.index < len(items)]      # 없는 번호는 버린다

def select(s: dict) -> dict:                   # ② 중요도 선별 — 20장 구조 그대로
    items = s["collected"]
    survivors = []
    for i in range(0, len(items), BATCH):       # 예선 — 묶음마다 여덟 건
        chunk = items[i:i + BATCH]
        survivors += [chunk[p.index] for p in ask_picks(chunk, 8)]
    finals = ask_picks(survivors, TARGET)       # 본선 — 한 화면에 놓고 다섯 건
    return {"picked": [survivors[p.index] for p in finals],
            "log": [f"② 선별   {len(items)} → 예선 {len(survivors)} → {len(finals)}건"]}

MIN_BODY = 600                                  # 요약을 쓰려면 최소 이 정도는 있어야 한다 (11장 G1)

class ReportIn(TypedDict):                      # 워커가 받는 것은 기사 하나뿐
    item: dict

def extract_body(url):
    d = trafilatura.fetch_url(url)
    return trafilatura.extract(d) if d else None

# 무료 버전 — LLM 없이 피드가 준 요약을 그대로 쓴다. 나중에 4부(25장)의 OpenAI draft()로 갈아 끼운다.
# 본문은 G1 관문과 검수용으로만 쓰고 발행하지 않는다 (제목·요약·원문 링크만 재배포).
def draft(item, body):
    found = labels(item)
    return {"headline": item["title"],
            "summary":  item["summary"],
            "why":      f"개발팀 관련: {' · '.join(found)}" if found else ""}

def fan_report(s: dict):                        # 기사 수만큼 워커를 펼친다
    if not s["picked"]:                         # 고른 게 없으면 바로 검수로 — 조용한 날 카드라도 보내려고
        return "verify"
    return [Send("report", {"item": it}) for it in s["picked"]]

def report(s: ReportIn) -> dict:               # ③ 취재·요약 — 기사 한 건을 맡는다
    it = s["item"]
    try:
        body = extract_body(it["url"])
    except Exception:
        body = None
    if not body or len(body) < MIN_BODY:
        return {"drafted": [],
                "log": [f"   취재 제외 {it['source']} · 본문 {len(body or '')}자"]}
    return {"drafted": [{**it, "body": body[:6000], **draft(it, body)}],
            "log": [f"   취재 {it['source']} · 본문 {len(body)}자"]}

class Verdict(BaseModel):                       # 30장 검수 결과 스키마
    ok:       bool      = Field(description="요약이 원문에 근거하면 true")
    problems: list[str] = Field(description="근거 없는 부분. 없으면 빈 목록")

# 무료 버전 — LLM 대조 대신 형식만 본다. 유료로 바꿀 땐 check 만 30장 코드로 갈아 끼운다
# (practice/ch30_verify_openai.py). 무료 draft는 매체가 쓴 피드 요약을 그대로 쓰므로
# 요약이 원문과 어긋나는 환각은 생기지 않는다. 대신 그대로 내보내면 안 되는 모양을 거른다.
MIN_SUMMARY = 40                                # 이보다 짧은 요약은 내용이 없는 것으로 본다

def check(d):
    problems = []
    if len(d["summary"].strip()) < MIN_SUMMARY:
        problems.append(f"요약이 비었거나 너무 짧음 ({len(d['summary'].strip())}자)")
    if d["summary"].strip() == d["headline"].strip():
        problems.append("요약이 제목을 되풀이함")
    if not d["url"].startswith(("http://", "https://")):
        problems.append("원문 링크가 올바르지 않음")
    return Verdict(ok=not problems, problems=problems)

def verify(s: dict) -> dict:                   # ④ 검수 — 30장 구조 그대로
    kept, dropped = [], []
    for d in s["drafted"]:
        (kept if check(d).ok else dropped).append(d)
    return {"verified": kept,                  # 리듀서 없는 새 칸에 담는다
            "log": [f"④ 검수   {len(s['drafted'])} → {len(kept)}건"
                    + (f" · 불합격 {[x['source'] for x in dropped]}" if dropped else "")]}

# ── 6부 · 발행 (34~35장, OpenAI 없음) ──
COLORS = {"모델·API": 0x0B6E77, "도구·프레임워크": 0x4C7C9C,
          "정책·규제": 0x8F5606, "사례·적용": 0x2E7D5B, "연구": 0x6A4A9C}
DEFAULT = 0x5F7476
TITLE_MAX, DESC_MAX, EMBED_MAX, TOTAL_MAX = 256, 4096, 10, 5800   # 6000에서 여유를 둔다

def build_embeds(run_id, lead, articles):
    if not articles:                                   # 조용한 날에도 한 장은 보낸다
        return [{"title": f"🗞️ {run_id}", "color": DEFAULT,
                 "description": "오늘은 조용합니다."}]
    embeds = [{"title": f"🗞️ {run_id} · AI 브리핑", "description": lead, "color": DEFAULT}]
    for i, a in enumerate(articles, 1):
        desc = a["summary"]
        if a.get("why"):
            desc += f"\n\n💡 **{a['why']}**"
        embeds.append({
            "title":       f"{i}. {a['headline']}"[:TITLE_MAX],
            "description": desc[:DESC_MAX],
            "url":         a["url"],
            "color":       COLORS.get(a.get("topic", ""), DEFAULT),
            "footer":      {"text": f"{a['source']} · {a['when']}"},
        })
    total = lambda es: sum(len(e.get("title", "")) + len(e.get("description", ""))
                           + len(e.get("footer", {}).get("text", "")) for e in es)
    while len(embeds) > EMBED_MAX or total(embeds) > TOTAL_MAX:
        embeds.pop()                                   # 뒤에서부터 덜어낸다
    return embeds

def send(run_id, lead, articles, webhook=None, dry_run=True):
    payload = {"username": "편집실", "embeds": build_embeds(run_id, lead, articles)}
    if dry_run or not webhook:
        print(f"[dry-run] embed {len(payload['embeds'])}개 · "
              f"{len(json.dumps(payload, ensure_ascii=False))}자 — 보내지 않음")
        print(json.dumps(payload["embeds"][-1], ensure_ascii=False, indent=2)[:400])
        return False
    r = requests.post(webhook, json=payload, timeout=20)
    ok = r.status_code in (200, 204)
    print("발행:", "성공" if ok else f"실패 {r.status_code} {r.text[:120]}")
    return ok

def make_lead(arts):
    if not arts:
        return ""
    srcs = ", ".join(dict.fromkeys(a["source"] for a in arts))
    return f"오늘은 {len(arts)}건을 골랐습니다. ({srcs})"

def publish(s: dict) -> dict:                 # ⑤ 발행 — 35장
    arts = [{"headline": a["headline"], "summary": a["summary"], "why": a["why"],
             "url": a["url"], "source": a["source"], "topic": a.get("event", ""),
             "when": a["at"].astimezone(KST).strftime("%m-%d %H:%M")}   # 독자 기준 한국 시각으로
            for a in s["verified"]]
    today   = datetime.now().strftime("%Y-%m-%d")
    dry_run = os.environ.get("DRY_RUN", "1") != "0"   # "0"일 때만 보낸다 — 그 밖의 값은 모두 보내지 않음
    webhook = os.environ.get("DISCORD_WEBHOOK_URL")
    if not dry_run and not webhook:                    # 보내라고 했는데 주소가 없으면 실행을 실패로 끝낸다
        raise RuntimeError("DRY_RUN=0 인데 DISCORD_WEBHOOK_URL 이 비어 있습니다")
    sent  = send(today, make_lead(arts), arts, webhook=webhook, dry_run=dry_run)
    if not dry_run and not sent:                       # Discord가 거절하면(4xx·5xx) 초록불로 끝나지 않게 한다
        raise RuntimeError("Discord 발행 실패 — 위 '발행: 실패' 줄의 상태 코드를 확인하세요")
    label = f"{len(arts)}건" if arts else "조용합니다"
    return {"log": [f"⑤ 발행   {label} · {'보냄' if sent else 'dry-run'}"]}

def build():                                    # 노드를 이름으로 찾아 붙인다
    g = StateGraph(Brief)
    for name in ("collect", "select", "report", "verify", "publish"):
        g.add_node(name, globals()[name])
    g.add_edge(START, "collect")
    g.add_edge("collect", "select")
    g.add_conditional_edges("select", fan_report, ["report", "verify"])   # 기사 수만큼 report를 펼친다
    g.add_edge("report", "verify")
    g.add_edge("verify", "publish")
    g.add_edge("publish", END)
    return g

INIT = {"hours": 24,
        "collected": [], "picked": [], "drafted": [], "verified": [], "log": []}

def run():
    return build().compile().invoke(INIT)

if __name__ == "__main__":                      # main.py가 import할 때는 실행하지 않는다
    for line in run()["log"]:
        print(line)
