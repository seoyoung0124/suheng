import uuid
from datetime import date, datetime

import streamlit as st
from streamlit_calendar import calendar

from supabase_utils import get_supabase, current_user_id, sign_out

st.set_page_config(page_title="하루결 | 일정 관리", page_icon="🗓️", layout="wide")

CATEGORIES = ["수행평가", "시험", "동아리", "개인일정", "과제", "학교행사", "기타"]
COLORS = {"상": "#F87171", "중": "#FACC15", "하": "#4ADE80", "없음": "#C4B5FD"}
PERSONAL_COLOR = "#7DD3FC"


def fetch_events(client, uid):
    rows = (
        client.table("events")
        .select("*")
        .eq("user_id", uid)
        .order("event_date")
        .execute()
        .data
        or []
    )
    result = []
    for row in rows:
        if not row.get("event_date"):
            continue
        cats = row.get("categories") or []
        if isinstance(cats, str):
            cats = [cats]
        result.append({
            "id": str(row["id"]),
            "date": str(row["event_date"])[:10],
            "title": row.get("title") or "",
            "description": row.get("description") or "",
            "importance": row.get("importance") if row.get("importance") in COLORS else "없음",
            "categories": [item for item in cats if item in CATEGORIES],
        })
    return result


def write_event(client, uid, event):
    client.table("events").upsert({
        "id": event["id"],
        "user_id": uid,
        "event_date": event["date"],
        "title": event["title"],
        "description": event["description"],
        "importance": event["importance"],
        "categories": event["categories"],
    }).execute()


def date_from(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date().isoformat()
    except (ValueError, TypeError):
        try:
            return date.fromisoformat(str(value)[:10]).isoformat()
        except (ValueError, TypeError):
            return None


# 로그인 UI는 pages/login.py에서만 표시합니다.
if not current_user_id():
    st.title("🗓️ 하루결")
    st.info("캘린더를 사용하려면 먼저 로그인해 주세요.")
    st.page_link("pages/login.py", label="로그인 / 회원가입 페이지로 이동", icon="🔐")
    st.stop()

client = get_supabase()
uid = current_user_id()

head, logout_col = st.columns([5, 1])
with head:
    st.title("🗓️ 하루결")
    st.caption(f"로그인 계정: {st.session_state.get('user_email', '')}")
with logout_col:
    if st.button("로그아웃", use_container_width=True):
        sign_out()
        st.switch_page("pages/login.py")

try:
    events = fetch_events(client, uid)
except Exception as exc:
    st.error(f"일정을 불러오지 못했습니다: {exc}")
    st.info("Supabase 테이블과 RLS 정책, events 테이블의 user_id 및 event_date 컬럼을 확인해 주세요.")
    st.stop()

calendar_events = []
for event in events:
    color = PERSONAL_COLOR if "개인일정" in event["categories"] else COLORS[event["importance"]]
    calendar_events.append({
        "id": event["id"],
        "title": event["title"] or "(제목 없음)",
        "start": event["date"],
        "allDay": True,
        "backgroundColor": color,
        "borderColor": color,
        "textColor": "#263238",
    })

st.subheader("나의 월간 캘린더")
calendar_state = calendar(
    events=calendar_events,
    options={
        "initialView": "dayGridMonth",
        "locale": "ko",
        "timeZone": "local",
        "height": 680,
        "contentHeight": 650,
        "expandRows": True,
        "dayMaxEvents": 4,
        "dateClick": True,
        "eventClick": True,
        "selectable": True,
        "editable": False,
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
        "buttonText": {"today": "오늘"},
        "displayEventTime": False,
        "fixedWeekCount": False,
    },
    callbacks=["dateClick", "eventClick"],
    key="main_calendar",
)

# streamlit-calendar 버전에 따라 콜백 반환 형태가 다를 수 있습니다.
if isinstance(calendar_state, dict):
    callback = calendar_state.get("callback")
    date_click = calendar_state.get("dateClick")
    event_click = calendar_state.get("eventClick")

    if callback == "dateClick" or (callback is None and isinstance(date_click, dict)):
        picked = date_from((date_click or {}).get("date") or (date_click or {}).get("dateStr"))
        if picked:
            st.session_state.selected_date = picked
            st.session_state.edit_event_id = None
            st.session_state.show_event_form = True
            st.rerun()
    elif callback == "eventClick" or (callback is None and isinstance(event_click, dict)):
        event_data = (event_click or {}).get("event") or {}
        if event_data.get("id"):
            st.session_state.view_event_id = str(event_data["id"])
            st.rerun()

with st.expander("날짜를 직접 선택해 일정 추가", expanded=False):
    fallback_date = st.date_input("일정 날짜", value=date.today(), key="fallback_date")
    if st.button("＋ 이 날짜에 일정 추가"):
        st.session_state.selected_date = fallback_date.isoformat()
        st.session_state.edit_event_id = None
        st.session_state.show_event_form = True
        st.rerun()

# 일정 상세 보기 및 수정/삭제
view_id = st.session_state.get("view_event_id")
view_event = next((event for event in events if event["id"] == view_id), None)

if view_event:
    with st.container(border=True):
        st.subheader(view_event["title"] or "(제목 없음)")
        st.write(f"날짜: {view_event['date']}")
        st.write(view_event["description"] or "설명 없음")
        st.write(f"중요도: {view_event['importance']}")
        st.write("카테고리: " + (", ".join(view_event["categories"]) or "없음"))
        col1, col2, col3 = st.columns(3)

        if col1.button("수정", key="view_edit"):
            st.session_state.edit_event_id = view_id
            st.session_state.selected_date = view_event["date"]
            st.session_state.show_event_form = True
            st.session_state.view_event_id = None
            st.rerun()

        if col2.button("삭제", key="view_delete"):
            try:
                client.table("events").delete().eq("id", view_id).eq("user_id", uid).execute()
                client.table("todo_status").delete().eq("event_id", view_id).eq("user_id", uid).execute()
                st.session_state.view_event_id = None
                st.success("일정을 삭제했습니다.")
                st.rerun()
            except Exception as exc:
                st.error(f"삭제 실패: {exc}")

        if col3.button("닫기", key="view_close"):
            st.session_state.view_event_id = None
            st.rerun()

# 일정 추가/수정 폼
if st.session_state.get("show_event_form", False):
    edit_id = st.session_state.get("edit_event_id")
    existing = next((event for event in events if event["id"] == edit_id), None) if edit_id else None
    picked_date = st.session_state.get("selected_date", date.today().isoformat())

    st.divider()
    st.subheader("일정 수정" if existing else "일정 추가")
    st.caption(f"선택한 날짜: {picked_date}")

    with st.form("event_editor"):
        title = st.text_input("일정 제목", value=existing["title"] if existing else "")
        description = st.text_area("부가 설명", value=existing["description"] if existing else "")
        importance_options = ["없음", "상", "중", "하"]
        current_importance = existing["importance"] if existing else "없음"
        importance = st.radio(
            "중요도",
            importance_options,
            index=importance_options.index(current_importance),
            horizontal=True,
        )
        categories = st.multiselect(
            "카테고리",
            CATEGORIES,
            default=existing["categories"] if existing else [],
        )
        save = st.form_submit_button("저장", type="primary")

    cancel_col, _ = st.columns(2)
    if save:
        event = {
            "id": edit_id or str(uuid.uuid4()),
            "date": picked_date,
            "title": title.strip(),
            "description": description.strip(),
            "importance": importance,
            "categories": categories,
        }
        try:
            write_event(client, uid, event)
            st.session_state.show_event_form = False
            st.session_state.edit_event_id = None
            st.success("일정을 저장했습니다.")
            st.rerun()
        except Exception as exc:
            st.error(f"저장 실패: {exc}")

    if cancel_col.button("취소", key="cancel_event_form"):
        st.session_state.show_event_form = False
        st.session_state.edit_event_id = None
        st.rerun()

st.divider()
today = date.today().isoformat()
metric1, metric2, metric3 = st.columns(3)
metric1.metric("전체 일정", f"{len(events)}개")
metric2.metric("오늘 일정", f"{sum(event['date'] == today for event in events)}개")
metric3.metric("오늘 이후 일정", f"{sum(event['date'] >= today for event in events)}개")
