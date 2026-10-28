# 20장 실습 · 선별 노드를 채우고 그래프를 다시 돌리기 (강의 원본 · OpenAI 유료 호출: 예선 묶음 수 + 본선 1번)
#   uv run python practice/ch20_select_openai.py
# ⚠ .env 의 OPENAI_API_KEY 로 호출하므로 실행하면 OpenAI 계정에 요금이 청구된다.
#   skeleton.py 에는 같은 구조에 ask_picks 만 무료(키워드 점수)로 바꾼 버전이 들어 있다.
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import skeleton
from skeleton import Shortlist                  # 19장 스키마 (Pick · Shortlist)

load_dotenv(ROOT / ".env")
client = OpenAI(default_headers={"Accept-Encoding": "gzip, deflate"})

BATCH, TARGET = 40, 5          # 예선 묶음 크기, 최종 발행 건수

CRITERIA = ("독자는 AI를 실제 제품에 붙이는 국내 개발팀입니다.\n"
            "- 이번 주 일하는 방식이 바뀔 만한가\n"
            "- 지금 쓰는 도구·API의 가격·한도·정책이 실제로 변했나\n"
            "버릴 것: 발표 예정·로드맵만 있는 것, MOU·투자유치·수상 같은 홍보성 소식")

def ask_picks(items, n):
    listing = "\n".join(f"{i}. [{it['source']}] {it['title']}" for i, it in enumerate(items))
    sys = (f"{CRITERIA}\n\n아래 목록에서 중요한 순서대로 {n}건을 고르세요.\n"
           "같은 사건을 다룬 기사에는 같은 event 라벨을 붙이세요.")
    out = client.chat.completions.parse(
        model="gpt-4.1-mini", temperature=0,
        messages=[{"role": "system", "content": sys},
                  {"role": "user", "content": listing}],
        response_format=Shortlist).choices[0].message.parsed
    return [p for p in out.picks if 0 <= p.index < len(items)]      # 없는 번호는 버린다

def select(s: dict) -> dict:                   # ② 중요도 선별 — 빈 노드를 갈아 끼운다
    items = s["collected"]
    survivors = []
    for i in range(0, len(items), BATCH):       # 예선 — 묶음마다 여덟 건
        chunk = items[i:i + BATCH]
        survivors += [chunk[p.index] for p in ask_picks(chunk, 8)]
    finals = ask_picks(survivors, TARGET)       # 본선 — 한 화면에 놓고 다섯 건
    return {"picked": [survivors[p.index] for p in finals],
            "log": [f"② 선별   {len(items)} → 예선 {len(survivors)} → {len(finals)}건"]}

skeleton.select = select                        # 노드를 갈아 끼운다

for line in skeleton.run()["log"]:
    print(line)
