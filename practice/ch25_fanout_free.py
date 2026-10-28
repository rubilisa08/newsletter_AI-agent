# 25장 실습 · 무료판 — skeleton.py 그래프에서 report가 기사 수만큼 펼쳐지는 모습을 본다
#   uv run python practice/ch25_fanout_free.py
#
# invoke()는 마지막 State만 돌려주지만, stream()은 노드가 끝날 때마다 하나씩 알려 준다.
# select 다음에 report가 고른 기사 수만큼 따로 실행되고, verify는 그 워커들이 다 끝난 뒤 한 번 돈다.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from skeleton import INIT, build

graph = build().compile()

print("그래프 모양 — select 뒤 엣지가 점선(-.->, 조건부 · Send)으로 바뀐다")
for line in graph.get_graph().draw_mermaid().splitlines():
    if "-->" in line or "-.->" in line:         # 엣지 줄만 보여 준다
        print("  " + line.strip())

print("실행 순서")
workers = 0
for step in graph.stream(INIT, stream_mode="updates"):
    for node, update in step.items():
        if node == "report":
            workers += 1
            got = update.get("drafted") or []
            what = f"초안 {got[0]['source']}" if got else (update.get("log") or [""])[0].strip()
            print(f"  report 워커 {workers}  → {what}")
        else:
            print(f"  {node}")
print(f"\nreport 워커 {workers}개가 따로 돌았고, drafted 칸에는 리듀서(operator.add)로 이어 붙었다")
