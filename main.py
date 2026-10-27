import uuid
from datetime import date, datetime
import streamlit as st
from streamlit_calendar import calendar
from supabase_utils import get_supabase, store_auth_session, current_user_id, sign_out

st.set_page_config(page_title="하루결 | 일정 관리", page_icon="🗓️", layout="wide")
CATEGORIES = ["수행평가", "시험", "동아리", "개인일정", "과제", "학교행사", "기타"]
COLORS = {"상": "#F87171", "중": "#FACC15", "하": "#4ADE80", "없음": "#C4B5FD"}
PERSONAL_COLOR = "#7DD3FC"

def auth_page():
    st.title("🗓️ 하루결")
    st.write("회원가입 또는 로그인하면 나만의 캘린더를 사용할 수 있어요.")
    client = get_supabase()
    login, signup = st.tabs(["로그인", "회원가입"])
    with login:
        with st.form("login_form"):
            email = st.text_input("이메일", key="login_email")
            password = st.text_input("비밀번호", type="password", key="login_password")
            submit = st.form_submit_button("로그인", type="primary", use_container_width=True)
        if submit:
            try:
                response = client.auth.sign_in_with_password({"email": email.strip(), "password": password})
                if store_auth_session(client, response):
                    st.rerun()
                st.error("로그인 세션을 만들지 못했습니다. 이메일 인증 여부를 확인해 주세요.")
            except Exception:
                st.error("로그인에 실패했습니다. 이메일·비밀번호 또는 이메일 인증 상태를 확인해 주세요.")
    with signup:
        with st.form("signup_form"):
            email = st.text_input("이메일 주소", key="signup_email")
            password = st.text_input("비밀번호", type="password", key="signup_password")
            confirm = st.text_input("비밀번호 확인", type="password", key="signup_confirm")
            submit = st.form_submit_button("회원가입", type="primary", use_container_width=True)
        if submit:
            if not email.strip() or not password:
                st.warning("이메일과 비밀번호를 입력해 주세요.")
            elif password != confirm:
                st.warning("비밀번호가 일치하지 않습니다.")
            elif len(password) < 6:
                st.warning("비밀번호를 6자 이상 입력해 주세요.")
            else:
                try:
                    response = client.auth.sign_up({"email": email.strip(), "password": password})
                    if store_auth_session(client, response):
                        st.success("회원가입이 완료되었습니다.")
                        st.rerun()
                    else:
                        st.success("가입 요청이 완료되었습니다. 이메일 인증이 설정되어 있다면 이메일 인증 후 로그인해 주세요.")
                except Exception:
                    st.error("회원가입에 실패했습니다. 이메일 형식과 Supabase Authentication 설정을 확인해 주세요.")

def fetch_events(client, uid):
    rows = client.table("events").select("*").eq("user_id", uid).order("event_date").execute().data or []
    result = []
    for r in rows:
        if not r.get("event_date"):
            continue
        cats = r.get("categories") or []
        if isinstance(cats, str):
            cats = [cats]
        result.append({
            "id": str(r["id"]), "date": str(r["event_date"])[:10],
            "title": r.get("title") or "", "description": r.get("description") or "",
            "importance": r.get("importance") if r.get("importance") in COLORS else "없음",
            "categories": [x for x in cats if x in CATEGORIES]
        })
    return result

def write_event(client, uid, event):
    client.table("events").upsert({
        "id": event["id"], "user_id": uid, "event_date": event["date"],
        "title": event["title"], "description": event["description"],
        "importance": event["importance"], "categories": event["categories"]
    }).execute()

def date_from(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        try:
            return date.fromisoformat(str(value)[:10]).isoformat()
        except ValueError:
            return None

if not current_user_id():
    auth_page()
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
        st.rerun()

try:
    events = fetch_events(client, uid)
except Exception as exc:
    st.error(f"일정을 불러오지 못했습니다: {exc}")
    st.info("SQL Editor에서 테이블과 RLS 정책을 설정했는지, events 테이블에 user_id 및 event_date 컬럼이 있는지 확인해 주세요.")
    st.stop()

cal_events = []
for e in events:
    color = PERSONAL_COLOR if "개인일정" in e["categories"] else COLORS[e["importance"]]
    cal_events.append({"id": e["id"], "title": e["title"] or "(제목 없음)", "start": e["date"],
                       "allDay": True, "backgroundColor": color, "borderColor": color,
                       "textColor": "#263238"})

st.subheader("나의 월간 캘린더")
state = calendar(
    events=cal_events,
    options={
        "initialView": "dayGridMonth", "locale": "ko", "timeZone": "local",
        "height": 680, "contentHeight": 650, "expandRows": True, "dayMaxEvents": 4,
        "dateClick": True, "eventClick": True, "selectable": True, "editable": False,
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
        "buttonText": {"today": "오늘"}, "displayEventTime": False, "fixedWeekCount": False
    },
    callbacks=["dateClick", "eventClick"], key="main_calendar"
)

# Calendar callback support differs by streamlit-calendar version.
if isinstance(state, dict):
    callback = state.get("callback")
    dc = state.get("dateClick")
    ec = state.get("eventClick")
    if callback == "dateClick" or (callback is None and isinstance(dc, dict)):
        picked = date_from((dc or {}).get("date") or (dc or {}).get("dateStr"))
        if picked:
            st.session_state.selected_date = picked
            st.session_state.edit_event_id = None
            st.session_state.show_event_form = True
            st.rerun()
    elif callback == "eventClick" or (callback is None and isinstance(ec, dict)):
        event_data = (ec or {}).get("event") or {}
        if event_data.get("id"):
            st.session_state.view_event_id = str(event_data["id"])
            st.rerun()

with st.expander("날짜를 직접 선택해 일정 추가", expanded=False):
    fallback = st.date_input("일정 날짜", value=date.today(), key="fallback_date")
    if st.button("＋ 이 날짜에 일정 추가"):
        st.session_state.selected_date = fallback.isoformat()
        st.session_state.edit_event_id = None
        st.session_state.show_event_form = True
        st.rerun()

# Event details and actions
view_id = st.session_state.get("view_event_id")
view_event = next((e for e in events if e["id"] == view_id), None)
if view_event:
    with st.container(border=True):
        st.subheader(view_event["title"] or "(제목 없음)")
        st.write(f"날짜: {view_event['date']}")
        st.write(view_event["description"] or "설명 없음")
        st.write(f"중요도: {view_event['importance']}")
        st.write("카테고리: " + (", ".join(view_event["categories"]) or "없음"))
        c1, c2, c3 = st.columns(3)
        if c1.button("수정", key="view_edit"):
            st.session_state.edit_event_id = view_id
            st.session_state.selected_date = view_event["date"]
            st.session_state.show_event_form = True
            st.session_state.view_event_id = None
            st.rerun()
        if c2.button("삭제", key="view_delete"):
            try:
                client.table("events").delete().eq("id", view_id).eq("user_id", uid).execute()
                client.table("todo_status").delete().eq("event_id", view_id).eq("user_id", uid).execute()
                st.session_state.view_event_id = None
                st.success("일정을 삭제했습니다.")
                st.rerun()
            except Exception as exc:
                st.error(f"삭제 실패: {exc}")
        if c3.button("닫기", key="view_close"):
            st.session_state.view_event_id = None
            st.rerun()

if st.session_state.get("show_event_form", False):
    edit_id = st.session_state.get("edit_event_id")
    existing = next((e for e in events if e["id"] == edit_id), None) if edit_id else None
    picked_date = st.session_state.get("selected_date", date.today().isoformat())
    st.divider()
    st.subheader("일정 수정" if existing else "일정 추가")
    st.caption(f"선택한 날짜: {picked_date}")
    with st.form("event_editor"):
        title = st.text_input("일정 제목", value=existing["title"] if existing else "")
        description = st.text_area("부가 설명", value=existing["description"] if existing else "")
        imp_options = ["없음", "상", "중", "하"]
        importance = st.radio("중요도", imp_options, index=imp_options.index(existing["importance"] if existing else "없음"), horizontal=True)
        categories = st.multiselect("카테고리", CATEGORIES, default=existing["categories"] if existing else [])
        save = st.form_submit_button("저장", type="primary")
    c1, c2 = st.columns(2)
    with c1:
        if save:
            event = {"id": edit_id or str(uuid.uuid4()), "date": picked_date, "title": title.strip(),
                     "description": description.strip(), "importance": importance, "categories": categories}
            try:
                write_event(client, uid, event)
                st.session_state.show_event_form = False
                st.session_state.edit_event_id = None
                st.success("일정을 저장했습니다.")
                st.rerun()
            except Exception as exc:
                st.error(f"저장 실패: {exc}")
    with c2:
        if st.button("취소", key="cancel_event_form"):
            st.session_state.show_event_form = False
            st.session_state.edit_event_id = None
            st.rerun()

st.divider()
today = date.today().isoformat()
a, b, c = st.columns(3)
a.metric("전체 일정", f"{len(events)}개")
b.metric("오늘 일정", f"{sum(e['date'] == today for e in events)}개")
c.metric("오늘 이후 일정", f"{sum(e['date'] >= today for e in events)}개")
