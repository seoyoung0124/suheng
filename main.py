
import json
import os
import uuid
from datetime import date
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from streamlit_calendar import calendar


# =========================================================
# 1. 기본 설정
# =========================================================

st.set_page_config(
    page_title="하루결 | 일정 관리",
    page_icon="🗓️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DATA_FILE = Path("events.json")

CATEGORIES = [
    "수행평가",
    "시험",
    "동아리",
    "개인일정",
    "과제",
    "학교행사",
    "기타",
]

IMPORTANCE_COLORS = {
    "상": "#F87171",  # 빨강
    "중": "#FACC15",  # 노랑
    "하": "#4ADE80",  # 초록
    "없음": "#C4B5FD",  # 연보라
}

PERSONAL_COLOR = "#7DD3FC"  # 하늘색


# =========================================================
# 2. 일정 데이터 관리
# =========================================================

def load_events():
    """JSON 파일에서 일정 불러오기"""
    if not DATA_FILE.exists():
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

        return []

    except (json.JSONDecodeError, OSError):
        return []


def save_events():
    """현재 일정을 JSON 파일에 저장하기"""
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(
            st.session_state.events,
            file,
            ensure_ascii=False,
            indent=2,
        )


def get_event_color(event):
    """
    색상 우선순위:
    1. 개인일정: 하늘색
    2. 중요도 상: 빨강
    3. 중요도 중: 노랑
    4. 중요도 하: 초록
    5. 중요도 미설정: 연보라
    """
    categories = event.get("categories", [])

    if "개인일정" in categories:
        return PERSONAL_COLOR

    importance = event.get("importance", "없음")

    return IMPORTANCE_COLORS.get(
        importance,
        IMPORTANCE_COLORS["없음"],
    )


def find_event(event_id):
    """ID로 일정 찾기"""
    for event in st.session_state.events:
        if event["id"] == event_id:
            return event

    return None


def get_calendar_events():
    """캘린더에 표시할 형식으로 일정 변환"""
    result = []

    for event in st.session_state.events:
        color = get_event_color(event)

        # 제목이 없어도 캘린더에서 일정을 구별할 수 있도록 표시
        title = event.get("title", "").strip() or "(제목 없음)"

        result.append(
            {
                "id": event["id"],
                "title": title,
                "start": event["date"],
                "allDay": True,
                "backgroundColor": color,
                "borderColor": color,
                "textColor": "#263238",
                "extendedProps": {
                    "description": event.get("description", ""),
                    "importance": event.get("importance", "없음"),
                    "categories": event.get("categories", []),
                },
            }
        )

    return result


# =========================================================
# 3. 세션 상태 초기화
# =========================================================

if "events" not in st.session_state:
    st.session_state.events = load_events()

if "pending_action" not in st.session_state:
    st.session_state.pending_action = None

if "selected_date" not in st.session_state:
    st.session_state.selected_date = date.today().isoformat()

if "selected_event_id" not in st.session_state:
    st.session_state.selected_event_id = None

if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

if "form_version" not in st.session_state:
    st.session_state.form_version = 0


# =========================================================
# 4. 공통 스타일
# =========================================================

st.markdown(
    """
    <style>
    @import url(
        'https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap'
    );

    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', sans-serif;
    }

    .stApp {
        background-color: #FAF9FF;
    }

    .main .block-container {
        max-width: 1450px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .app-header {
        background: linear-gradient(135deg, #EDE9FE, #FDF2F8);
        padding: 30px 32px;
        border-radius: 24px;
        margin-bottom: 22px;
        border: 1px solid #E9DFFB;
    }

    .app-title {
        font-size: 34px;
        font-weight: 800;
        color: #514278;
        margin-bottom: 8px;
    }

    .app-subtitle {
        font-size: 15px;
        color: #756B8D;
        margin: 0;
    }

    .section-title {
        color: #514278;
        font-size: 20px;
        font-weight: 700;
        margin: 10px 0 12px 0;
    }

    .legend-item {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        margin-right: 16px;
        margin-bottom: 8px;
        color: #625B70;
        font-size: 13px;
    }

    .legend-dot {
        width: 11px;
        height: 11px;
        border-radius: 50%;
        display: inline-block;
    }

    div.stButton > button {
        border-radius: 12px;
        min-height: 42px;
        font-weight: 600;
    }

    div[data-testid="stDialog"] {
        border-radius: 20px;
    }

    /* 캘린더 월간 화면 */
    .fc {
        font-family: 'Noto Sans KR', sans-serif;
        background: white;
        border-radius: 16px;
        padding: 12px;
    }

    .fc .fc-toolbar-title {
        font-size: 23px !important;
        font-weight: 700;
        color: #514278;
    }

    .fc .fc-button {
        background-color: #8B7AC8 !important;
        border-color: #8B7AC8 !important;
        border-radius: 8px !important;
    }

    .fc .fc-daygrid-day-number {
        color: #514278;
        text-decoration: none;
        padding: 8px;
    }

    .fc .fc-col-header-cell-cushion {
        color: #74688E;
        text-decoration: none;
        padding: 10px;
    }

    .fc .fc-event {
        border-radius: 5px;
        padding: 2px 4px;
        cursor: pointer;
    }

    .fc .fc-daygrid-day {
        min-height: 105px;
    }

    @media (max-width: 768px) {
        .app-title {
            font-size: 27px;
        }

        .app-header {
            padding: 22px;
        }

        .fc .fc-toolbar-title {
            font-size: 18px !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 5. 상단 제목 및 안내
# =========================================================

st.markdown(
    """
    <div class="app-header">
        <div class="app-title">🗓️ 하루결</div>
        <p class="app-subtitle">
            하루의 일정을 차곡차곡 기록하고,
            중요한 순간을 놓치지 마세요.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 6. 색상 범례
# =========================================================

st.markdown(
    """
    <div style="margin-bottom: 18px;">
        <span class="legend-item">
            <span class="legend-dot" style="background:#F87171;"></span>
            중요도 상
        </span>
        <span class="legend-item">
            <span class="legend-dot" style="background:#FACC15;"></span>
            중요도 중
        </span>
        <span class="legend-item">
            <span class="legend-dot" style="background:#4ADE80;"></span>
            중요도 하
        </span>
        <span class="legend-item">
            <span class="legend-dot" style="background:#7DD3FC;"></span>
            개인일정
        </span>
        <span class="legend-item">
            <span class="legend-dot" style="background:#C4B5FD;"></span>
            중요도 미설정
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 7. 캘린더 표시
# =========================================================

st.markdown(
    '<div class="section-title">나의 월간 캘린더</div>',
    unsafe_allow_html=True,
)

calendar_options = {
    "initialView": "dayGridMonth",
    "locale": "ko",
    "timeZone": "local",
    "height": 760,
    "contentHeight": 720,
    "expandRows": True,
    "dayMaxEvents": 4,
    "selectable": True,
    "dateClick": True,
    "eventClick": True,
    "editable": False,
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "",
    },
    "buttonText": {
        "today": "오늘",
        "month": "월",
    },
    "dayHeaderFormat": {
        "weekday": "short",
    },
    "displayEventTime": False,
    "eventDisplay": "block",
    "fixedWeekCount": False,
}

calendar_state = calendar(
    events=get_calendar_events(),
    options=calendar_options,
    custom_css="""
        .fc-daygrid-day-number {
            font-weight: 500;
        }
        .fc-event-title {
            font-weight: 600;
            white-space: normal;
        }
    """,
    key="main_calendar",
)


# =========================================================
# 8. 날짜 및 일정 클릭 처리
# =========================================================

if calendar_state:
    # 날짜를 클릭하면 해당 날짜의 일정 추가 창 열기
    date_click = calendar_state.get("dateClick")

    if date_click:
        clicked_date = date_click.get("dateStr")

        if clicked_date:
            st.session_state.selected_date = clicked_date[:10]
            st.session_state.selected_event_id = None
            st.session_state.edit_mode = False
            st.session_state.pending_action = "add"

    # 기존 일정을 클릭하면 일정 상세 창 열기
    event_click = calendar_state.get("eventClick")

    if event_click:
        clicked_event = event_click.get("event", {})
        clicked_id = clicked_event.get("id")

        if clicked_id and find_event(str(clicked_id)):
            st.session_state.selected_event_id = str(clicked_id)
            st.session_state.pending_action = "view"
            st.session_state.edit_mode = False


# =========================================================
# 9. 일정 입력 / 수정 창
# =========================================================

@st.dialog("일정 입력", width="large")
def event_form_dialog(event_id=None):
    existing_event = find_event(event_id) if event_id else None

    is_edit = existing_event is not None

    st.markdown(
        f"**날짜:** {st.session_state.selected_date}"
    )

    if is_edit:
        st.caption("기존 일정을 수정하고 설정 완료를 눌러 저장하세요.")
    else:
        st.caption("입력하지 않은 항목은 비워 두어도 됩니다.")

    # 위젯 키에 버전을 넣어 새 일정 입력 시 이전 입력값이 남지 않도록 처리
    version = st.session_state.form_version
    prefix = f"form_{version}_{event_id or 'new'}"

    with st.form(f"event_form_{prefix}"):
        title = st.text_input(
            "일정 제목",
            value=existing_event.get("title", "") if is_edit else "",
            placeholder="예: 수학 수행평가",
            key=f"{prefix}_title",
        )

        description = st.text_area(
            "부가 설명",
            value=existing_event.get("description", "") if is_edit else "",
            placeholder="준비물, 제출 방법, 기억할 내용 등을 입력하세요.",
            height=120,
            key=f"{prefix}_description",
        )

        st.markdown("**중요도**")
        st.caption("하나만 선택하거나, 선택하지 않아도 됩니다.")

        importance_options = ["없음", "상", "중", "하"]
        old_importance = (
            existing_event.get("importance", "없음")
            if is_edit
            else "없음"
        )

        importance = st.radio(
            "중요도 선택",
            options=importance_options,
            index=(
                importance_options.index(old_importance)
                if old_importance in importance_options
                else 0
            ),
            horizontal=True,
            label_visibility="collapsed",
            key=f"{prefix}_importance",
        )

        st.markdown("**카테고리**")
        st.caption("여러 항목을 동시에 선택할 수 있습니다.")

        old_categories = (
            existing_event.get("categories", [])
            if is_edit
            else []
        )

        selected_categories = []

        category_columns = st.columns(3)

        for index, category in enumerate(CATEGORIES):
            with category_columns[index % 3]:
                checked = st.checkbox(
                    category,
                    value=category in old_categories,
                    key=f"{prefix}_category_{category}",
                )

                if checked:
                    selected_categories.append(category)

        submitted = st.form_submit_button(
            "설정 완료",
            use_container_width=True,
            type="primary",
        )

    if submitted:
        # 제목이나 설명이 없어도 일정 저장 가능
        if is_edit:
            for event in st.session_state.events:
                if event["id"] == event_id:
                    event["title"] = title.strip()
                    event["description"] = description.strip()
                    event["importance"] = importance
                    event["categories"] = selected_categories
                    break
        else:
            new_event = {
                "id": str(uuid.uuid4()),
                "date": st.session_state.selected_date,
                "title": title.strip(),
                "description": description.strip(),
                "importance": importance,
                "categories": selected_categories,
            }

            st.session_state.events.append(new_event)

        save_events()

        st.session_state.pending_action = None
        st.session_state.selected_event_id = None
        st.session_state.edit_mode = False
        st.session_state.form_version += 1

        st.success("일정이 저장되었습니다.")
        st.rerun()


# =========================================================
# 10. 일정 상세 창
# =========================================================

@st.dialog("일정 상세", width="large")
def event_detail_dialog(event_id):
    event = find_event(event_id)

    if event is None:
        st.warning("해당 일정을 찾을 수 없습니다.")
        if st.button("닫기", use_container_width=True):
            st.session_state.pending_action = None
            st.rerun()
        return

    color = get_event_color(event)

    st.markdown(
        f"""
        <div style="
            background:{color};
            padding:12px 16px;
            border-radius:12px;
            margin-bottom:16px;
        ">
            <span style="font-size:13px;">일정 날짜</span><br>
            <strong style="font-size:19px;">{event["date"]}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### 일정 제목")
    st.write(event.get("title", "").strip() or "(제목 없음)")

    st.markdown("#### 부가 설명")
    st.write(event.get("description", "").strip() or "입력된 설명이 없습니다.")

    st.markdown("#### 중요도")
    st.write(event.get("importance", "없음"))

    st.markdown("#### 카테고리")
    categories = event.get("categories", [])
    st.write(", ".join(categories) if categories else "설정된 카테고리가 없습니다.")

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("✏️ 수정", use_container_width=True):
            st.session_state.pending_action = "edit"
            st.session_state.selected_event_id = event_id
            st.rerun()

    with col2:
        if st.button("🗑️ 삭제", use_container_width=True):
            st.session_state.pending_action = "confirm_delete"
            st.rerun()

    with col3:
        if st.button("＋ 추가", use_container_width=True):
            st.session_state.selected_date = event["date"]
            st.session_state.selected_event_id = None
            st.session_state.pending_action = "add"
            st.session_state.form_version += 1
            st.rerun()


# =========================================================
# 11. 일정 삭제 확인 창
# =========================================================

@st.dialog("일정 삭제 확인")
def delete_confirm_dialog(event_id):
    event = find_event(event_id)

    if event is None:
        st.warning("삭제할 일정을 찾을 수 없습니다.")
        if st.button("닫기", use_container_width=True):
            st.session_state.pending_action = None
            st.rerun()
        return

    event_title = event.get("title", "").strip() or "(제목 없음)"

    st.write(f"**{event_title}** 일정을 삭제할까요?")
    st.caption("삭제한 일정은 현재 저장된 일정 목록에서 제거됩니다.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "삭제하기",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.events = [
                item
                for item in st.session_state.events
                if item["id"] != event_id
            ]

            save_events()

            st.session_state.pending_action = None
            st.session_state.selected_event_id = None

            st.success("일정이 삭제되었습니다.")
            st.rerun()

    with col2:
        if st.button("취소", use_container_width=True):
            st.session_state.pending_action = "view"
            st.rerun()


# =========================================================
# 12. 선택한 동작에 따라 창 표시
# =========================================================

action = st.session_state.pending_action
selected_id = st.session_state.selected_event_id

if action == "add":
    event_form_dialog()

elif action == "view" and selected_id:
    event_detail_dialog(selected_id)

elif action == "edit" and selected_id:
    event_form_dialog(selected_id)

elif action == "confirm_delete" and selected_id:
    delete_confirm_dialog(selected_id)


# =========================================================
# 13. 하단 일정 요약
# =========================================================

st.divider()

st.markdown(
    '<div class="section-title">전체 일정 요약</div>',
    unsafe_allow_html=True,
)

total_events = len(st.session_state.events)

today_string = date.today().isoformat()

today_events = [
    event
    for event in st.session_state.events
    if event.get("date") == today_string
]

upcoming_events = [
    event
    for event in st.session_state.events
    if event.get("date", "") >= today_string
]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("전체 일정", f"{total_events}개")

with col2:
    st.metric("오늘의 일정", f"{len(today_events)}개")

with col3:
    st.metric("오늘 이후 일정", f"{len(upcoming_events)}개")


# =========================================================
# 14. 날짜순 일정 목록
# =========================================================

with st.expander("📋 전체 일정 목록 보기", expanded=False):
    if not st.session_state.events:
        st.info("아직 등록된 일정이 없습니다. 캘린더에서 날짜를 눌러 추가해 보세요.")
    else:
        sorted_events = sorted(
            st.session_state.events,
            key=lambda event: (
                event.get("date", ""),
                event.get("title", ""),
            ),
        )

        for event in sorted_events:
            color = get_event_color(event)
            title = event.get("title", "").strip() or "(제목 없음)"
            categories = ", ".join(event.get("categories", [])) or "카테고리 없음"

            st.markdown(
                f"""
                <div style="
                    border-left:6px solid {color};
                    background:white;
                    padding:12px 16px;
                    border-radius:8px;
                    margin-bottom:10px;
                ">
                    <strong>{event.get("date", "")} · {title}</strong><br>
                    <span style="color:#756B8D;font-size:13px;">
                        중요도: {event.get("importance", "없음")}
                        &nbsp;|&nbsp; {categories}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
