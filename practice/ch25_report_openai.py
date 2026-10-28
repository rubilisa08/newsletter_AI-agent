# 25장 실습 · 취재 노드를 채우고 기사 수만큼 펼치기 (강의 원본 · OpenAI 유료 호출: 고른 기사 수만큼)
#   uv run python practice/ch25_report_openai.py
# ⚠ .env 의 OPENAI_API_KEY 로 호출하므로 실행하면 OpenAI 계정에 요금이 청구된다.
#   graph.py 에는 같은 구조(Send · ReportIn · fan_report)에 draft 만 무료로 바꾼 버전이 들어 있다.
import sys
from pathlib import Path
from typing import TypedDict

import trafilatura
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from openai import OpenAI
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import graph
from graph import Brief

load_dotenv(ROOT / ".env")
client = OpenAI(default_headers={"Accept-Encoding": "gzip, deflate"})

# ── 24장 셀에서 만든 Draft · SYS ──
class Draft(BaseModel):
    headline: str = Field(description="20자 내외의 한국어 헤드라인")
    summary:  str = Field(description="세 문장 요약. ~합니다체, 과장 없이 건조하게")
    why:      str = Field(description="국내 개발팀에게 왜 중요한지 한 문장")

SYS = ("당신은 국내 개발팀을 위한 AI 뉴스레터 기자입니다.\n"
       "아래 기사 본문을 읽고 헤드라인·요약·왜 중요한지를 쓰세요.\n"
       "'주목된다·기대를 모은다' 같은 기자체 표현은 쓰지 마세요.")

# ── 25장 ──
class ReportIn(TypedDict):                     # 워커가 받는 것은 기사 하나뿐
    item: dict

def extract_body(url):
    d = trafilatura.fetch_url(url)
    return trafilatura.extract(d) if d else None

def draft(body):
    return client.chat.completions.parse(
        model="gpt-4.1-mini", temperature=0,
        messages=[{"role": "system", "content": SYS},
                  {"role": "user", "content": body[:6000]}],
        response_format=Draft).choices[0].message.parsed

def fan_report(s: dict):                      # 기사 수만큼 워커를 펼친다
    return [Send("report", {"item": it}) for it in s["picked"]]

def report(s: ReportIn) -> dict:               # ③ 요약 — 기사 한 건을 맡는다
    it = s["item"]
    body = extract_body(it["url"])
    if not body or len(body) < 600:            # ← 섹션 3에서 정한 G1 기준선
        return {"drafted": [],
                "log": [f"   취재 제외 {it['source']} · 본문 {len(body or '')}자"]}
    d = draft(body)
    return {"drafted": [{**it, "body": body[:6000], **d.model_dump()}]}

def build():                                   # 엣지 한 줄이 팬아웃으로 바뀐다
    g = StateGraph(Brief)
    nodes = {"collect": graph.collect, "select": graph.select, "report": report,
             "verify": graph.verify, "publish": graph.publish}
    for name in ("collect", "select", "report", "verify", "publish"):
        g.add_node(name, nodes[name])
    g.add_edge(START, "collect")
    g.add_edge("collect", "select")
    g.add_conditional_edges("select", fan_report, ["report"])   # ← 고정 엣지가 아니라
    g.add_edge("report", "verify")
    g.add_edge("verify", "publish")
    g.add_edge("publish", END)
    return g

for line in build().compile().invoke(graph.INIT)["log"]:
    print(line)
