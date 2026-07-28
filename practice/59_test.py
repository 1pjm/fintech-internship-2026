import streamlit as st

st.markdown("# 안녕하세요")
st.write("언뇽허삽나까")

my_long_text = """
| # | 지표 | 엑셀 계산식 | 무엇과 비교? | 나빠지면 제일 먼저 할 일 |
| --- | --- | --- | --- | --- |
| *예* | *월간 이탈률* | *=이탈고객수/전체고객수* | *지난달과 비교* | *어느 그룹에서 늘었는지 쪼개 보기* |
| 1 | 신규 / 이탈 / 순증 | 상태별 COUNTIFS · 신규−이탈 | 상태별 COUNTIFS/신규-이탈 | 신규 감소인지 이탈 증가인지 구분한 후, 플랜·가입 채널별로 원인 확인 |
| 2 | 플랜별 이탈률 | =해당플랜_이탈고객수/해당플랜_전체고객수 | 전체 평균 및 다른 플랜과 비교 | 이탈률이 가장 높은 플랜의 가격·혜택·이용 조건 분석 |
| 3 | 기말 회원수 | COUNTIFS(기준월, 월) | 지난달 기말 회원수 및 목표 회원수와 비교 | 신규와 이탈 중 어느 쪽이 회원 감소에 더 크게 영향을 주었는지 확인 |
| 4 | 이탈률 | 이탈 ÷ 회원 | 지난달 및 목표 이탈률과 비교 | 이탈이 증가한 플랜·가입 기간·고객 그룹부터 세분화하여 확인 |
| 5 | MRR | SUMIFS(월요금, 기준월, 월) | 지난달 MRR 및 월간 매출 목표와 비교 | MRR 감소가 회원 이탈 때문인지, 저가 플랜 이동 때문인지 확인 |
| 6 | 코호트 잔존율 | 가입월 X 경과월 교차표 | 이전 가입 코호트의 같은 경과월 잔존율과 비교 | 잔존율이 급감하는 시점을 찾아 온보딩·혜택·프로모션 개선 |
"""
st.markdown(my_long_text)

col1, col2 = st.columns(2)
with col1:
    st.write("왼쪽")
    st.write("반갑습니다")

with col2:
    st.write("오른쪽")
    st.write("안녕하신가")

st.set_page_config(
    initial_sidebar_state="collapsed", page_icon="🍇", page_title="기초 스트림릿 실습")

with st.sidebar:
    st.write("홈")
    st.write("데이터")

my_button = st.button("이건 버튼")
st.write(my_button)

if my_button == True:
    st.write("냐냐냥🐱")
    col1, col2, _ = st.columns([2, 2, 7])
    with col1:
        st.link_button("이건 클릭이야", "https://github.com/1pjm")

    with col2:
        st.link_button(
            "이쪼이쪼", "https://docs.streamlit.io/develop/api-reference/widgets")


text_input = st.text_input("입력하세요")
st.write(text_input)

if text_input == True:
    st.write("사용자가 입력한 내용은" + text_input)

option = st.selectbox("선택해주세요", ["낑", "깽", "깡"])
st.write(option + "🐾")
