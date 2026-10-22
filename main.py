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
    "수행평가", "시험", "동아리", "개인일정",
    "과제", "학교행사", "기타",
]

IMPORTANCE_COLORS = {
    "상": "#F87171",
    "중": "#FACC15",
    "하": "#4ADE80",
    "없음": "#C4B5FD",
}
PERSONAL_COLOR = "#7DD3FC"


# =========================================================
# 데이터 검증 및 저장
# =========================================================
def normalize_date(value):
    """YYYY-MM-DD 또는 ISO 날짜/시간 문자열을 날짜로 정규화한다."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date().isoformat()
    except (ValueError, TypeError):
        try:
            return date.fromisoformat(str(value)[:10]).isoformat()
        except (ValueError, TypeError):
            return None


def normalize_event(raw):
    """오래된 형식이나 일부 필드가 빠진 일정도 안전한 형식으로 변환한다."""
    if not isinstance(raw, dict):
        return None

    # 예전 데이터가 date 대신 start 또는 start_date를 썼을 경우도 처리
    event_date = normalize_date(
        raw.get("date") or raw.get("start") or raw.get("start_date")
    )
    if not event_date:
        return None

    raw_categories = raw.get("categories", [])
    if isinstance(raw_categories, str):
        raw_categories = [raw_categories]
    if not isinstance(raw_categories, list):
        raw_categories = []

    categories = [
        str(category) for category in raw_categories
        if str(category) in CATEGORIES
    ]

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
    if not DATA_FILE.exists():
        return []

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, list):
            return []
        return [
            event for raw in data
            if (event := normalize_event(raw)) is not None
        ]
    except (json.JSONDecodeError, OSError):
        return []


def save_events():
    """현재 세션의 일정을 JSON 파일에 저장한다."""
    try:
        with DATA_FILE.open("w", encoding="utf-8") as file:
            json.dump(
                st.session_state.events,
                file,
                ensure_ascii=False,
                indent=2,
            )
    except OSError as exc:
        st.error(f"일정을 파일에 저장하지 못했습니다: {exc}")


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
    """date 필드가 없는 일정이 캘린더를 중단시키지 않도록 재검증한다."""
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
# 세션 상태
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
# 디자인
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
.stApp { background-color: #FAF9FF; }
.main .block-container { max-width: 1450px; padding-top: 2rem; padding-bottom: 3rem; }
.app-header {
    background: linear-gradient(135deg, #EDE9FE, #FDF2F8);
    padding: 30px 32px; border-radius: 24px; margin-bottom: 22px;
    border: 1px solid #E9DFFB;
}
.app-title { font-size: 34px; font-weight: 800; color: #514278; margin-bottom: 8px; }
.app-subtitle { font-size: 15px; color: #756B8D; margin: 0; }
.section-title { color: #514278; font-size: 20px; font-weight: 700; margin: 10px 0 12px; }
.legend-item { display: inline-flex; align-items: center; gap: 6px; margin-right: 16px; margin-bottom: 8px; color: #625B70; font-size: 13px; }
.legend-dot { width: 11px; height: 11px; border-radius: 50%; display: inline-block; }
div.stButton > button { border-radius: 12px; min-height: 42px; font-weight: 600; }
.fc { font-family: 'Noto Sans KR', sans-serif; background: white; border-radius: 16px; padding: 12px; }
.fc .fc-toolbar-title { font-size: 23px !important; font-weight: 700; color: #514278; }
.fc .fc-button { background-color: #8B7AC8 !important; border-color: #8B7AC8 !important; border-radius: 8px !important; }
.fc .fc-daygrid-day-number { color: #514278; text-decoration: none; padding: 8px; }
.fc .fc-col-header-cell-cushion { color: #74688E; text-decoration: none; padding: 10px; }
.fc .fc-event { border-radius: 5px; padding: 2px 4px; cursor: pointer; }
@media (max-width: 768px) {
  .app-title { font-size: 27px; }
  .app-header { padding: 22px; }
  .fc .fc-toolbar-title { font-size: 18px !important; }
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="app-header">
  <div class="app-title">🗓️ 하루결</div>
  <p class="app-subtitle">하루의 일정을 차곡차곡 기록하고, 중요한 순간을 놓치지 마세요.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="margin-bottom:18px;">
  <span class="legend-item"><span class="legend-dot" style="background:#F87171;"></span>중요도 상</span>
  <span class="legend-item"><span class="legend-dot" style="background:#FACC15;"></span>중요도 중</span>
  <span class="legend-item"><span class="legend-dot" style="background:#4ADE80;"></span>중요도 하</span>
  <span class="legend-item"><span class="legend-dot" style="background:#7DD3FC;"></span>개인일정</span>
  <span class="legend-item"><span class="legend-dot" style="background:#C4B5FD;"></span>중요도 미설정</span>
</div>
""", unsafe_allow_html=True)


# =========================================================
# 캘린더
# =========================================================
st.markdown('<div class="section-title">나의 월간 캘린더</div>', unsafe_allow_html=True)

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
    "buttonText": {"today": "오늘", "month": "월"},
    "dayHeaderFormat": {"weekday": "short"},
    "displayEventTime": False,
    "eventDisplay": "block",
    "fixedWeekCount": False,
}

calendar_state = calendar(
    events=get_calendar_events(),
    options=calendar_options,
    custom_css="""
      .fc-daygrid-day-number { font-weight: 500; }
      .fc-event-title { font-weight: 600; white-space: normal; }
    """,
    key="main_calendar",
)

if isinstance(calendar_state, dict):
    date_click = calendar_state.get("dateClick")
    if isinstance(date_click, dict):
        clicked_date = normalize_date(date_click.get("dateStr"))
        if clicked_date:
            st.session_state.selected_date = clicked_date
            st.session_state.selected_event_id = None
            st.session_state.pending_action = "add"

    event_click = calendar_state.get("eventClick")
    if isinstance(event_click, dict):
        clicked_event = event_click.get("event") or {}
        clicked_id = clicked_event.get("id")
        if clicked_id and find_event(str(clicked_id)):
            st.session_state.selected_event_id = str(clicked_id)
            st.session_state.pending_action = "view"


# =========================================================
# 일정 추가/수정 창
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
            importance_options,
            index=importance_options.index(old_importance),
            horizontal=True,
            label_visibility="collapsed",
            key=f"{prefix}_importance",
        )

        st.markdown("**카테고리**")
        st.caption("여러 항목을 동시에 선택할 수 있습니다.")
        old_categories = existing["categories"] if is_edit else []
        selected_categories = []
        columns = st.columns(3)

        for i, category in enumerate(CATEGORIES):
            with columns[i % 3]:
                if st.checkbox(
                    category,
                    value=category in old_categories,
                    key=f"{prefix}_category_{category}",
                ):
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
        f"""<div style="background:{color};padding:12px 16px;border-radius:12px;margin-bottom:16px;">
        <span style="font-size:13px;">일정 날짜</span><br>
        <strong style="font-size:19px;">{event["date"]}</strong></div>""",
        unsafe_allow_html=True,
    )
    st.markdown("#### 일정 제목")
    st.write(event["title"].strip() or "(제목 없음)")
    st.markdown("#### 부가 설명")
    st.write(event["description"].strip() or "입력된 설명이 없습니다.")
    st.markdown("#### 중요도")
    st.write(event["importance"])
    st.markdown("#### 카테고리")
    st.write(", ".join(event["categories"]) or "설정된 카테고리가 없습니다.")
    st.divider()

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("✏️ 수정", use_container_width=True):
            st.session_state.pending_action = "edit"
            st.session_state.selected_event_id = event_id
            st.rerun()
    with c2:
        if st.button("🗑️ 삭제", use_container_width=True):
            st.session_state.pending_action = "confirm_delete"
            st.rerun()
    with c3:
        if st.button("＋ 추가", use_container_width=True):
            st.session_state.selected_date = event["date"]
            st.session_state.selected_event_id = None
            st.session_state.pending_action = "add"
            st.session_state.form_version += 1
            st.rerun()


# =========================================================
# 삭제 확인 창
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

    title = event["title"].strip() or "(제목 없음)"
    st.write(f"**{title}** 일정을 삭제할까요?")
    st.caption("삭제하면 현재 일정 목록에서 제거됩니다.")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("삭제하기", type="primary", use_container_width=True):
            st.session_state.events = [
                item for item in st.session_state.events
                if item["id"] != event_id
            ]
            save_events()
            st.session_state.pending_action = None
            st.session_state.selected_event_id = None
            st.rerun()
    with c2:
        if st.button("취소", use_container_width=True):
            st.session_state.pending_action = "view"
            st.rerun()


# =========================================================
# 선택된 창 표시
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
# 일정 요약 및 목록
# =========================================================
st.divider()
st.markdown('<div class="section-title">전체 일정 요약</div>', unsafe_allow_html=True)

today_string = date.today().isoformat()
total_events = len(st.session_state.events)
today_events = [e for e in st.session_state.events if e["date"] == today_string]
upcoming_events = [e for e in st.session_state.events if e["date"] >= today_string]

c1, c2, c3 = st.columns(3)
c1.metric("전체 일정", f"{total_events}개")
c2.metric("오늘의 일정", f"{len(today_events)}개")
c3.metric("오늘 이후 일정", f"{len(upcoming_events)}개")

with st.expander("📋 전체 일정 목록 보기", expanded=False):
    if not st.session_state.events:
        st.info("아직 등록된 일정이 없습니다. 캘린더에서 날짜를 눌러 추가해 보세요.")
    else:
        for event in sorted(
            st.session_state.events,
            key=lambda e: (e["date"], e["title"]),
        ):
            color = get_event_color(event)
            title = event["title"].strip() or "(제목 없음)"
            categories = ", ".join(event["categories"]) or "카테고리 없음"
            st.markdown(
                f"""<div style="border-left:6px solid {color};background:white;
                padding:12px 16px;border-radius:8px;margin-bottom:10px;">
                <strong>{event["date"]} · {title}</strong><br>
                <span style="color:#756B8D;font-size:13px;">
                중요도: {event["importance"]} &nbsp;|&nbsp; {categories}
                </span></div>""",
                unsafe_allow_html=True,
            )
