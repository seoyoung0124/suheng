import json
import uuid
from datetime import date, datetime
from pathlib import Path

import streamlit as st
from streamlit_calendar import calendar


# =========================================================
# 기본 설정
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
    "상": "#F87171",
    "중": "#FACC15",
    "하": "#4ADE80",
    "없음": "#C4B5FD",
}
PERSONAL_COLOR = "#7DD3FC"


# =========================================================
# 날짜 및 일정 데이터 처리
# =========================================================
def normalize_date(value):
    """날짜 문자열을 YYYY-MM-DD 형식으로 변환한다."""
    if not value:
        return None

    try:
        text = str(value).strip()
        # ISO 날짜/시간 문자열을 우선 처리
        return datetime.fromisoformat(
            text.replace("Z", "+00:00")
        ).date().isoformat()
    except (ValueError, TypeError):
        try:
            return date.fromisoformat(str(value)[:10]).isoformat()
        except (ValueError, TypeError):
            return None


def normalize_event(raw):
    """필드가 빠졌거나 구형 형식인 일정 데이터를 안전하게 변환한다."""
    if not isinstance(raw, dict):
        return None

    event_date = normalize_date(
        raw.get("date")
        or raw.get("start")
        or raw.get("start_date")
    )
    if event_date is None:
        return None

    raw_categories = raw.get("categories", [])
    if isinstance(raw_categories, str):
        raw_categories = [raw_categories]
    if not isinstance(raw_categories, list):
        raw_categories = []

    categories = []
    for category in raw_categories:
        category_text = str(category)
        if category_text in CATEGORIES and category_text not in categories:
            categories.append(category_text)

    importance = str(raw.get("importance", "없음"))
    if importance not in IMPORTANCE_COLORS:
        importance = "없음"

    return {
        "id": str(raw.get("id") or uuid.uuid4()),
        "date": event_date,
        "title": str(raw.get("title") or ""),
        "description": str(raw.get("description") or ""),
        "importance": importance,
        "categories": categories,
    }


def load_events():
    """JSON 파일에서 유효한 일정만 불러온다."""
    if not DATA_FILE.exists():
        return []

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            return []

        events = []
        for raw in data:
            event = normalize_event(raw)
            if event is not None:
                events.append(event)

        return events

    except (json.JSONDecodeError, OSError):
        return []


def save_events():
    """일정을 JSON 파일에 저장한다."""
    try:
        with DATA_FILE.open("w", encoding="utf-8") as file:
            json.dump(
                st.session_state.events,
                file,
                ensure_ascii=False,
                indent=2,
            )
    except OSError as exc:
        st.error(f"일정을 저장하지 못했습니다: {exc}")


def find_event(event_id):
    if not event_id:
        return None

    for event in st.session_state.events:
        if event.get("id") == event_id:
            return event

    return None


def get_event_color(event):
    if "개인일정" in event.get("categories", []):
        return PERSONAL_COLOR

    return IMPORTANCE_COLORS.get(
        event.get("importance", "없음"),
        IMPORTANCE_COLORS["없음"],
    )


def get_calendar_events():
    """캘린더에서 사용할 일정 목록을 만든다."""
    result = []

    for raw in st.session_state.events:
        event = normalize_event(raw)
        if event is None:
            continue

        color = get_event_color(event)
        title = event["title"].strip() or "(제목 없음)"

        result.append({
            "id": event["id"],
            "title": title,
            "start": event["date"],
            "allDay": True,
            "backgroundColor": color,
            "borderColor": color,
            "textColor": "#263238",
            "extendedProps": {
                "description": event["description"],
                "importance": event["importance"],
                "categories": event["categories"],
            },
        })

    return result


# =========================================================
# 세션 상태 초기화
# =========================================================
if "events" not in st.session_state:
    st.session_state.events = load_events()

if "pending_action" not in st.session_state:
    st.session_state.pending_action = None

if "selected_date" not in st.session_state:
    st.session_state.selected_date = date.today().isoformat()

if "selected_event_id" not in st.session_state:
    st.session_state.selected_event_id = None

if "form_version" not in st.session_state:
    st.session_state.form_version = 0


# =========================================================
# 화면 디자인
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');

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
    margin: 10px 0 12px;
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
""", unsafe_allow_html=True)

st.markdown("""
<div class="app-header">
    <div class="app-title">🗓️ 하루결</div>
    <p class="app-subtitle">
        하루의 일정을 차곡차곡 기록하고,
        중요한 순간을 놓치지 마세요.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="margin-bottom:18px;">
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
""", unsafe_allow_html=True)


# =========================================================
# 월간 캘린더
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
    callbacks=["dateClick", "eventClick"],
    key="main_calendar",
)

# 날짜 클릭 이벤트가 전달되지 않는 경우를 위한 직접 날짜 선택 기능
st.markdown("#### 일정 추가")
add_col1, add_col2 = st.columns([2, 1])
with add_col1:
    manual_date = st.date_input(
        "일정을 추가할 날짜",
        value=date.fromisoformat(st.session_state.selected_date),
        key="manual_add_date",
    )
with add_col2:
    st.write("")
    st.write("")
    if st.button("＋ 선택한 날짜에 일정 추가", use_container_width=True):
        st.session_state.selected_date = manual_date.isoformat()
        st.session_state.selected_event_id = None
        st.session_state.pending_action = "add"
        st.session_state.form_version += 1
        st.rerun()


# 캘린더 클릭 결과 처리
# streamlit-calendar 버전에 따라 콜백 데이터 구조가 다를 수 있어
# callback 이름과 실제 데이터 키를 함께 확인한다.
if isinstance(calendar_state, dict):
    callback_name = calendar_state.get("callback")
    date_click = calendar_state.get("dateClick")
    event_click = calendar_state.get("eventClick")

    if callback_name == "dateClick" or (
        callback_name is None and isinstance(date_click, dict)
    ):
        if isinstance(date_click, dict):
            clicked_date = normalize_date(
                date_click.get("date")
                or date_click.get("dateStr")
                or date_click.get("start")
            )
        else:
            clicked_date = normalize_date(date_click)

        if clicked_date:
            st.session_state.selected_date = clicked_date
            st.session_state.selected_event_id = None
            st.session_state.pending_action = "add"
            st.session_state.form_version += 1

    elif callback_name == "eventClick" or (
        callback_name is None and isinstance(event_click, dict)
    ):
        if isinstance(event_click, dict):
            clicked_event = event_click.get("event") or {}
            clicked_id = clicked_event.get("id")
            if clicked_id and find_event(str(clicked_id)):
                st.session_state.selected_event_id = str(clicked_id)
                st.session_state.pending_action = "view"


# =========================================================
# 일정 입력 및 수정 창
# =========================================================
@st.dialog("일정 입력", width="large")
def event_form_dialog(event_id=None):
    existing = find_event(event_id) if event_id else None
    is_edit = existing is not None

    st.write(f"**날짜:** {st.session_state.selected_date}")
    st.caption("입력하지 않은 항목은 비워 두어도 됩니다.")

    version = st.session_state.form_version
    prefix = f"event_{version}_{event_id or 'new'}"

    with st.form(f"event_form_{prefix}"):
        title = st.text_input(
            "일정 제목",
            value=existing["title"] if is_edit else "",
            placeholder="예: 수학 수행평가",
            key=f"{prefix}_title",
        )

        description = st.text_area(
            "부가 설명",
            value=existing["description"] if is_edit else "",
            placeholder="준비물, 제출 방법, 기억할 내용 등을 입력하세요.",
            height=120,
            key=f"{prefix}_description",
        )

        st.markdown("**중요도**")
        importance_options = ["없음", "상", "중", "하"]
        old_importance = existing["importance"] if is_edit else "없음"

        importance = st.radio(
            "중요도 선택",
            options=importance_options,
            index=importance_options.index(old_importance),
            horizontal=True,
            label_visibility="collapsed",
            key=f"{prefix}_importance",
        )

        st.markdown("**카테고리**")
        st.caption("여러 항목을 동시에 선택할 수 있습니다.")

        old_categories = existing["categories"] if is_edit else []
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
        if is_edit:
            for item in st.session_state.events:
                if item["id"] == event_id:
                    item.update({
                        "date": st.session_state.selected_date,
                        "title": title.strip(),
                        "description": description.strip(),
                        "importance": importance,
                        "categories": selected_categories,
                    })
                    break
        else:
            st.session_state.events.append({
                "id": str(uuid.uuid4()),
                "date": st.session_state.selected_date,
                "title": title.strip(),
                "description": description.strip(),
                "importance": importance,
                "categories": selected_categories,
            })

        save_events()
        st.session_state.pending_action = None
        st.session_state.selected_event_id = None
        st.session_state.form_version += 1
        st.rerun()


# =========================================================
# 일정 상세 창
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
    st.write(event["title"].strip() or "(제목 없음)")

    st.markdown("#### 부가 설명")
    st.write(event["description"].strip() or "입력된 설명이 없습니다.")

    st.markdown("#### 중요도")
    st.write(event["importance"])

    st.markdown("#### 카테고리")
    st.write(
        ", ".join(event["categories"])
        if event["categories"]
        else "설정된 카테고리가 없습니다."
    )

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
# 일정 삭제 확인 창
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

    event_title = event["title"].strip() or "(제목 없음)"
    st.write(f"**{event_title}** 일정을 삭제할까요?")
    st.caption("삭제하면 현재 저장된 일정 목록에서 제거됩니다.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "삭제하기",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.events = [
                item for item in st.session_state.events
                if item["id"] != event_id
            ]
            save_events()
            st.session_state.pending_action = None
            st.session_state.selected_event_id = None
            st.rerun()

    with col2:
        if st.button("취소", use_container_width=True):
            st.session_state.pending_action = "view"
            st.rerun()


# =========================================================
# 현재 동작에 맞는 창 표시
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
# 일정 요약
# =========================================================
st.divider()
st.markdown(
    '<div class="section-title">전체 일정 요약</div>',
    unsafe_allow_html=True,
)

today_string = date.today().isoformat()
total_events = len(st.session_state.events)

today_events = [
    event for event in st.session_state.events
    if event["date"] == today_string
]

upcoming_events = [
    event for event in st.session_state.events
    if event["date"] >= today_string
]

col1, col2, col3 = st.columns(3)
col1.metric("전체 일정", f"{total_events}개")
col2.metric("오늘의 일정", f"{len(today_events)}개")
col3.metric("오늘 이후 일정", f"{len(upcoming_events)}개")


# =========================================================
# 전체 일정 목록
# =========================================================
with st.expander("📋 전체 일정 목록 보기", expanded=False):
    if not st.session_state.events:
        st.info(
            "아직 등록된 일정이 없습니다. "
            "캘린더에서 날짜를 눌러 추가해 보세요."
        )
    else:
        sorted_events = sorted(
            st.session_state.events,
            key=lambda event: (
                event["date"],
                event["title"],
            ),
        )

        for event in sorted_events:
            color = get_event_color(event)
            title = event["title"].strip() or "(제목 없음)"
            categories = (
                ", ".join(event["categories"])
                if event["categories"]
                else "카테고리 없음"
            )

            st.markdown(
                f"""
                <div style="
                    border-left:6px solid {color};
                    background:white;
                    padding:12px 16px;
                    border-radius:8px;
                    margin-bottom:10px;
                ">
                    <strong>{event["date"]} · {title}</strong><br>
                    <span style="color:#756B8D;font-size:13px;">
                        중요도: {event["importance"]}
                        &nbsp;|&nbsp; {categories}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
