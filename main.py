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

# 메인 제목 및 패널 디자인 Custom CSS
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
                "priority": "None",
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
    """
    일정 색상 결정 로직:
    1. 중요도 '상': 빨간색 (#FF4B4B)
    2. 중요도 '중': 노란색 (#FFC107)
    3. 중요도 '하': 초록색 (#28A745)
    4. 중요도 미설정 & '개인일정': 하늘색 (#17A2B8)
    5. 모두 미설정 / 기타: 연보라색 (#9C27B0)
    """
    if priority == "상":
        return "#FF4B4B"
    elif priority == "중":
        return "#FFC107"
    elif priority == "하":
        return "#28A745"
    elif category == "개인일정":
        return "#17A2B8"
    else:
        return "#9C27B0"  # 연보라색

# ---------------------------------------------------------
# 4. 일정 추가/수정/삭제 대화상자 (Modal)
# ---------------------------------------------------------
@st.dialog("📋 일정 등록 / 상세 관리")
def manage_event_dialog():
    mode = st.session_state.dialog_mode
    event_data = st.session_state.selected_event or {}
    
    # -----------------------------------------------------
    # [A] 기존 일정 조회 모드
    # -----------------------------------------------------
    if mode == "view":
        st.subheader("📌 일정 상세정보")
        props = event_data.get("extendedProps", {})
        
        st.markdown(f"**제목:** `{event_data.get('title', '제목 없음')}`")
        st.markdown(f"📅 **날짜:** {event_data.get('start')}")
        st.markdown(f"🏷️ **카테고리:** {props.get('category') or '미선택'}")
        
        prio_display = props.get('priority')
        prio_text = f"중요도 {prio_display}" if prio_display in ["상", "중", "하"] else "미설정"
        st.markdown(f"🚨 **중요도:** {prio_text}")
        
        desc = props.get('description', '').strip()
        st.markdown(f"📝 **부가 설명:**\n{desc if desc else '입력된 설명이 없습니다.'}")
        
        st.divider()
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✏️ 수정하기", use_container_width=True):
                st.session_state.dialog_mode = "edit"
                st.rerun()
                
        with col2:
            if st.button("🗑️ 삭제하기", type="primary", use_container_width=True):
                st.session_state.events = [
                    e for e in st.session_state.events if str(e["id"]) != str(event_data["id"])
                ]
                st.session_state.show_dialog = False
                st.toast("일정이 삭제되었습니다.", icon="🗑️")
                st.rerun()
                
        with col3:
            if st.button("➕ 같은 날에 추가", use_container_width=True):
                st.session_state.selected_date = event_data.get("start")
                st.session_state.dialog_mode = "create"
                st.session_state.selected_event = None
                st.rerun()

    # -----------------------------------------------------
    # [B] 일정 입력 및 수정 모드
    # -----------------------------------------------------
    else:
        is_edit = (mode == "edit")
        st.subheader("✏️ 일정 수정" if is_edit else f"➕ 새 일정 추가 ({st.session_state.selected_date})")
        
        props = event_data.get("extendedProps", {}) if is_edit else {}
        
        # 1. 일정 제목 및 부가 설명
        default_title = event_data.get("title", "") if is_edit else ""
        title = st.text_input("일정 제목", value=default_title, placeholder="예: 수학 수행평가 제출, 동아리 회의")
        
        default_desc = props.get("description", "") if is_edit else ""
        description = st.text_area("부가 설명 (선택)", value=default_desc, placeholder="상세 내용이나 메모할 항목을 적어주세요.")
        
        st.markdown("---")
        
        # 2. 카테고리 선택 (체크박스 스타일 구현)
        st.markdown("**🏷️ 카테고리 선택 (선택 사항)**")
        categories = ["수행평가", "시험", "동아리", "개인일정", "기타"]
        current_cat = props.get("category", "") if is_edit else ""
        
        cat_cols = st.columns(len(categories))
        selected_category = ""
        for idx, cat in enumerate(categories):
            with cat_cols[idx]:
                is_checked = st.checkbox(cat, value=(current_cat == cat), key=f"dialog_cat_{cat}")
                if is_checked:
                    selected_category = cat

        st.markdown("---")

        # 3. 중요도 설정 (체크박스 스타일 구현)
        st.markdown("**🚨 중요도 설정 (선택 사항)**")
        priorities = ["상", "중", "하"]
        current_prio = props.get("priority", "") if is_edit else ""
        
        prio_cols = st.columns(3)
        selected_priority = ""
        for idx, prio in enumerate(priorities):
            with prio_cols[idx]:
                is_checked = st.checkbox(f"중요도 {prio}", value=(current_prio == prio), key=f"dialog_prio_{prio}")
                if is_checked:
                    selected_priority = prio

        st.divider()
        
        col_submit, col_cancel = st.columns([2, 1])
        with col_submit:
            if st.button("💾 설정 완료 및 저장", type="primary", use_container_width=True):
                color = get_color(selected_priority, selected_category)
                target_date = event_data.get("start", st.session_state.selected_date) if is_edit else st.session_state.selected_date

                final_title = title.
