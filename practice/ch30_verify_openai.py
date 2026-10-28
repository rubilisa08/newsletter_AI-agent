# 30장 실습 · 검수 노드를 채우고 다시 돌리기 (강의 원본 · OpenAI 유료 호출: 초안 수만큼)
#   uv run python practice/ch30_verify_openai.py
# ⚠ .env 의 OPENAI_API_KEY 로 호출하므로 실행하면 OpenAI 계정에 요금이 청구된다.
#   graph.py 에는 같은 구조(Verdict · verified 칸 · verify)에 check 만 무료로 바꾼 버전이 들어 있다.
#   Brief 의 verified 칸과 INIT 은 graph.py 에 이미 더해 두었다.
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import graph

load_dotenv(ROOT / ".env")
client = OpenAI(default_headers={"Accept-Encoding": "gzip, deflate"})

class Verdict(BaseModel):
    ok:       bool      = Field(description="요약이 원문에 근거하면 true")
    problems: list[str] = Field(description="근거 없는 부분. 없으면 빈 목록")

SYS_CHECK = ("요약이 원문에서 뒷받침되는지 판정하세요.\n"
             "헤드라인과 요약만 보고 판단하고, 번역이나 단위 환산은 문제가 아닙니다.")

def check(d):
    user = (f"[원문]\n{d['body'][:5000]}\n\n"
            f"[헤드라인]\n{d['headline']}\n\n[요약]\n{d['summary']}")
    return client.chat.completions.parse(
        model="gpt-4.1-mini", temperature=0,
        messages=[{"role": "system", "content": SYS_CHECK},
                  {"role": "user", "content": user}],
        response_format=Verdict).choices[0].message.parsed

def verify(s: dict) -> dict:                  # ④ 검수 — 빈 노드를 갈아 끼운다
    kept, dropped = [], []
    for d in s["drafted"]:
        (kept if check(d).ok else dropped).append(d)
    return {"verified": kept,                  # 리듀서 없는 새 칸에 담는다
            "log": [f"④ 검수   {len(s['drafted'])} → {len(kept)}건"
                    + (f" · 불합격 {[x['source'] for x in dropped]}" if dropped else "")]}

graph.verify = verify                       # 노드를 갈아 끼운다

for line in graph.run()["log"]:
    print(line)
