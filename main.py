import streamlit as st
from streamlit_calendar import calendar
from datetime import datetime, date

# ---------------------------------------------------------
# 1. 페이지 기본 설정 및 제목
# ---------------------------------------------------------
st.set_page_config(
    page_title="스마트 스케줄러 & 스터디 플래너",
    page_icon="📅",
    layout="wide"
)

# 메인 제목 및 설명
st.title("📅 스마트 스케줄러 & 스터디 플래너")
st.caption("수행평가, 시험, 동아리, 개인 일정 등 나만의 일정을 체계적으로 관리하세요!")

# ---------------------------------------------------------
# 2. 세션 상태(Session State) 초기화
# ---------------------------------------------------------
if "events" not in st.session_state:
    # 기본 예시 데이터
    st.session_state.events = [
        {
            "id": "1",
            "title": "[시험] 중간고사",
            "start": date.today().isoformat(),
            "end": date.today().isoformat(),
            "backgroundColor": "#FF4B4B",  # 빨간색 (중요도 상)
            "borderColor": "#FF4B4B",
            "extendedProps": {
                "description": "수학, 영어 시험 대비",
                "priority": "상",
                "category": "시험"
            }
        }
    ]

# 팝업 상태 관리
if "show_dialog" not in st.session_state:
    st.session_state.show_dialog = False
if "selected_event" not in st.session_state:
    st.session_state.selected_event = None
if "selected_date" not in st.session_state:
    st.session_state.selected_date = date.today().isoformat()
if "dialog_mode" not in st.session_state:
    st.session_state.dialog_mode = "create"  # "create" 또는 "view"

# ---------------------------------------------------------
# 3. 일정 색상 결정 함수
# ---------------------------------------------------------
def get_color(priority, category):
    """
    조건에 따른 일정 색상 반환:
    1. 중요도 '상': 빨간색 (#FF4B4B)
    2. 중요도 '중': 노란색 (#FFC107)
    3. 중요도 '하': 초록색 (#28A745)
    4. 개인일정: 하늘색 (#17A2B8)
    5. 지정 없음: 연보라색 (#9C27B0 / #B39DDB)
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
        return "#B39DDB"  # 연보라색

# ---------------------------------------------------------
# 4. 일정 추가/수정/삭제 대화상자 (Modal)
# ---------------------------------------------------------
@st.dialog("일정 상세 / 입력")
def manage_event_dialog():
    mode = st.session_state.dialog_mode
    event_data = st.session_state.selected_event or {}
    
    # -----------------------------------------------------
    # [A] 기존 일정 조회 및 수정/삭제 모드
    # -----------------------------------------------------
    if mode == "view":
        st.subheader("📌 일정 상세보기")
        props = event_data.get("extendedProps", {})
        
        st.write(**제목:** {event_data.get('title', '제목 없음')}`)
        st.write(f"📅 **날짜:** {event_data.get('start')}")
        st.write(f"🏷️ **카테고리:** {props.get('category', '미선택')}")
        st.write(f"🚨 **중요도:** {props.get('priority', '미선택')}")
        st.write(f"📝 **설명:** {props.get('description', '내용 없음')}")
        
        st.divider()
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✏️ 수정", use_container_width=True):
                st.session_state.dialog_mode = "edit"
                st.rerun()
                
        with col2:
            if st.button("🗑️ 삭제", type="primary", use_container_width=True):
                # 일정 삭제 처리
                st.session_state.events = [
                    e for e in st.session_state.events if e["id"] != event_data["id"]
                ]
                st.session_state.show_dialog = False
                st.success("일정이 삭제되었습니다.")
                st.rerun()
                
        with col3:
            if st.button("➕ 새 일정 추가", use_container_width=True):
                st.session_state.selected_date = event_data.get("start")
                st.session_state.dialog_mode = "create"
                st.session_state.selected_event = None
                st.rerun()

    # -----------------------------------------------------
    # [B] 일정 생성 및 수정 모드
    # -----------------------------------------------------
    else:
        is_edit = (mode == "edit")
        st.subheader("✏️ 일정 수정" if is_edit else "➕ 새 일정 추가")
        
        props = event_data.get("extendedProps", {}) if is_edit else {}
        
        # 1. 제목 및 설명
        default_title = event_data.get("title", "") if is_edit else ""
        title = st.text_input("일정 제목", value=default_title, placeholder="예: 수학 수행평가 제출")
        
        default_desc = props.get("description", "") if is_edit else ""
        description = st.text_area("부가 설명", value=default_desc, placeholder="상세 내용을 입력하세요.")
        
        # 2. 카테고리 설정 (단일 선택 체크박스형)
        st.write("🏷️ **카테고리 설정** (선택 사항)")
        categories = ["수행평가", "시험", "동아리", "개인일정", "기타"]
        current_cat = props.get("category", "") if is_edit else ""
        selected_category = ""
        
        cat_cols = st.columns(len(categories))
        for idx, cat in enumerate(categories):
            with cat_cols[idx]:
                checked = st.checkbox(cat, value=(current_cat == cat), key=f"cat_{cat}")
                if checked:
                    selected_category = cat
                    
        # 3. 중요도 설정 (단일 선택 체크박스형)
        st.write("🚨 **중요도 설정** (선택 사항)")
        priorities = ["상", "중", "하"]
        current_prio = props.get("priority", "") if is_edit else ""
        selected_priority = ""
        
        prio_cols = st.columns(3)
        for idx, prio in enumerate(priorities):
            with prio_cols[idx]:
                checked = st.checkbox(f"중요도 {prio}", value=(current_prio == prio), key=f"prio_{prio}")
                if checked:
                    selected_priority = prio

        # 저장 / 설정 완료 버튼
        st.divider()
        if st.button("💾 설정 완료", type="primary", use_container_width=True):
            color = get_color(selected_priority, selected_category)
            target_date = event_data.get("start", st.session_state.selected_date) if is_edit else st.session_state.selected_date

            if is_edit:
                # 기존 일정 업데이트
                for e in st.session_state.events:
                    if e["id"] == event_data["id"]:
                        e["title"] = title if title else "제목 없음"
                        e["backgroundColor"] = color
                        e["borderColor"] = color
                        e["extendedProps"] = {
                            "description": description,
                            "priority": selected_priority,
                            "category": selected_category
                        }
            else:
                # 새 일정 추가
                new_event = {
                    "id": str(datetime.now().timestamp()),
                    "title": title if title else "제목 없음",
                    "start": target_date,
                    "end": target_date,
                    "backgroundColor": color,
                    "borderColor": color,
                    "extendedProps": {
                        "description": description,
                        "priority": selected_priority,
                        "category": selected_category
                    }
                }
                st.session_state.events.append(new_event)
            
            st.session_state.show_dialog = False
            st.rerun()

# ---------------------------------------------------------
# 5. 캘린더 옵션 및 출력
# ---------------------------------------------------------
calendar_options = {
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth,timeGridWeek"
    },
    "initialView": "dayGridMonth",
    "selectable": True,
    "editable": False,
    "height": "700px"  # 캘린더 크기 크게 설정
}

# 범례(Legend) 안내 표시
st.markdown("""
<div style="display: flex; gap: 15px; margin-bottom: 15px; align-items: center; font-size: 14px;">
    <b>🎨 색상 안내:</b>
    <span>🔴 상 (빨강)</span>
    <span>🟡 중 (노랑)</span>
    <span>🟢 하 (초록)</span>
    <span>🔵 개인일정 (하늘색)</span>
    <span>🟣 기타/미지정 (연보라)</span>
</div>
""", unsafe_allow_html=True)

# FullCalendar 생성
state = calendar(
    events=st.session_state.events,
    options=calendar_options,
    key="calendar"
)

# ---------------------------------------------------------
# 6. 클릭 이벤트 핸들링 (날짜 클릭 및 일정 클릭)
# ---------------------------------------------------------
if state.get("callback") == "dateClick":
    # 날짜 클릭 시 -> 새 일정 작성 모드
    st.session_state.selected_date = state["dateClick"]["dateStr"].split("T")[0]
    st.session_state.selected_event = None
    st.session_state.dialog_mode = "create"
    st.session_state.show_dialog = True
    st.rerun()

elif state.get("callback") == "eventClick":
    # 일정 클릭 시 -> 일정 보기 모드
    click_event = state["eventClick"]["event"]
    # session_state에 저장된 원본 event 객체 탐색
    for event in st.session_state.events:
        if str(event["id"]) == str(click_event["id"]):
            st.session_state.selected_event = event
            break
    st.session_state.dialog_mode = "view"
    st.session_state.show_dialog = True
    st.rerun()

# 대화상자 띄우기
if st.session_state.show_dialog:
    manage_event_dialog()
