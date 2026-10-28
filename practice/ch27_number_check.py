# 27장 실습 · 숫자를 글자로 맞춰 보면 정확한 요약도 떨어져요 (OpenAI 호출 없음 · 무료)
#   uv run python practice/ch27_number_check.py
import re

# 섹션 6에서 만든 요약과 그 원문을 그대로 쓴다
summary = ("휴머노이드 로봇 훈련을 위한 인간 동작 데이터 수집 및 분석 스타트업 Mecka AI가 "
           "세쿼이아 캐피털이 주도하는 신규 투자 라운드를 진행 중이며, 기업 가치는 약 5억 "
           "달러에 달한다. 이번 투자 유치는 지난 3개월 전 6000만 달러 규모의 투자 이후 "
           "빠른 성장세를 반영한다.")
body = ("Mecka is nearing a new round led by Sequoia Capital at a valuation of about "
        "$500 million, according to two people with knowledge of the deal. "
        "The new financing comes just three months after Mecka announced that it "
        "raised $60 million in a round led by Framework Ventures.")

nums = sorted(set(re.findall(r"\d[\d,\.]*", summary)))
missing = [n for n in nums if n.replace(",", "") not in body.replace(",", "")]

print("요약에 등장한 숫자 :", nums)
print("원문에 없는 숫자   :", missing)
print("판정               :", "불합격 — 환각 의심" if missing else "합격")
