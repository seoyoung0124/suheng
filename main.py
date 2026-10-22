import streamlit as st
from streamlit_calendar import calendar
from datetime import datetime, date

# ---------------------------------------------------------
# 1. 페이지 기본 설정 및 스타일 정의
# ---------------------------------------------------------
st.set_page_config(
    page_title="스마트 스케줄러 & 스터디 플래너",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .legend-container {
        display: flex;
        gap: 12px;
        background-color: #F8FAFC;
        padding: 12px 18px;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        margin-bottom: 20px;
        flex-wrap: wrap;
        font-size: 14px;
    }
    .legend-item {
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .color-box {
        width: 14px;
        height: 14px;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">📅 스마트 스케줄러 & 스터디 플래너</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">수행평가, 시험, 동아리, 개인 일정 등 나만의 일정을 체계적으로 관리하세요!</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. 세션 상태(Session State) 초기화
# ---------------------------------------------------------
if "events" not in st.session_state:
    st.session_state.events = [
        {
            "id": "1",
            "title": "[시험] 중간고사 준비",
            "start": date.today().isoformat(),
            "end": date.today().isoformat(),
            "backgroundColor": "#FF4B4B",
            "borderColor": "#FF4B4B",
            "extendedProps": {
                "description": "수학, 영어 개념 정리 및 기출문제 풀이",
                "priority": "상",
                "category": "시험"
            }
        },
        {
            "id": "2",
            "title": "[개인일정] 동아리 회의",
            "start": date.today().isoformat(),
            "end": date.today().isoformat(),
            "backgroundColor": "#17A2B8",
            "borderColor": "#17A2B8",
            "extendedProps": {
                "description": "축제 부스 운영 아이디어 발표",
                "priority": "",
                "category": "개인일정"
            }
        }
    ]

if "show_dialog" not in st.session_state:
    st.session_state.show_dialog = False
if "selected_event" not in st.session_state:
    st.session_state.selected_event = None
if "selected_date" not in st.session_state:
    st.session_state.selected_date = date.today().isoformat()
if "dialog_mode" not in st.session_state:
    st.session_state.dialog_mode = "create"

# ---------------------------------------------------------
# 3. 일정 색상 결정 함수
# ---------------------------------------------------------
def get_color(priority, category):
    if priority == "상":
        return "#FF4B4B"
    elif priority == "중":
        return "#FFC107"
    elif priority == "하":
        return "#28A745"
    elif category == "
