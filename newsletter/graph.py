"""수집 → 선별 → 취재·요약 → 검수 → 발행 순서로 노드를 잇는다."""

from langgraph.graph import END, START, StateGraph

from newsletter.nodes import collect, publish, report, select, verify
from newsletter.state import NewsletterState


def build_graph():
    graph = StateGraph(NewsletterState)

    graph.add_node("collect", collect)
    graph.add_node("select", select)
    graph.add_node("report", report)
    graph.add_node("verify", verify)
    graph.add_node("publish", publish)

    graph.add_edge(START, "collect")
    graph.add_edge("collect", "select")
    graph.add_edge("select", "report")
    graph.add_edge("report", "verify")
    graph.add_edge("verify", "publish")
    graph.add_edge("publish", END)

    return graph.compile()
