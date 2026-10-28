"""그래프 전체가 공유하는 상태(State).

각 노드는 자기가 맡은 필드만 채워서 반환하고, LangGraph가 이를 상태에 합쳐 다음 노드로 넘긴다.

    collect  -> candidates   (오늘 수집한 AI 소식 후보 전체)
    select   -> selected     (개발팀이 알아야 할 5건)
    report   -> reports      (5건 각각의 취재·요약 결과)
    verify   -> verified, issues
    publish  -> published
"""

from typing import TypedDict


class Article(TypedDict, total=False):
    title: str
    url: str
    source: str
    published_at: str
    summary: str


class NewsletterState(TypedDict, total=False):
    run_date: str  # 실행 기준 날짜 (YYYY-MM-DD)
    candidates: list[Article]
    selected: list[Article]
    reports: list[Article]
    verified: bool
    issues: list[str]
    published: bool
