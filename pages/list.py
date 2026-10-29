from datetime import date
import streamlit as st
from supabase_utils import get_supabase, current_user_id, sign_out

st.set_page_config(page_title="하루결 | To-do 목록", page_icon="✅", layout="wide")

if not current_user_id():
    st.title("🔐 로그인이 필요해요")
    st.info("먼저 메인 페이지에서 회원가입하거나 로그인해 주세요.")
    st.page_link("main.py", label="캘린더 / 로그인으로 이동", icon="🗓️")
    st.stop()

client = get_supabase()
uid = current_user_id()
left, right = st.columns([5, 1])
with left:
    st.title("✅ 나의 To-do 목록")
    st.caption(f"로그인 계정: {st.session_state.get('user_email', '')}")
with right:
    if st.button("로그아웃", use_container_width=True):
        sign_out()
        st.rerun()

try:
    rows = client.table("events").select(
        "id,event_date,title,description,importance,categories"
    ).eq("user_id", uid).order("event_date").execute().data or []
    status_rows = client.table("todo_status").select(
        "event_id,completed"
    ).eq("user_id", uid).execute().data or []
except Exception as exc:
    st.error(f"데이터를 불러오지 못했습니다: {exc}")
    st.info("Supabase SQL을 실행했고 두 테이블에 user_id 컬럼이 있는지 확인해 주세요.")
    st.stop()

statuses = {str(r["event_id"]): bool(r.get("completed", False)) for r in status_rows}
events = [r for r in rows if r.get("event_date")]
events.sort(key=lambda r: (str(r["event_date"]), r.get("title") or ""))

if not events:
    st.info("등록된 일정이 없습니다. 캘린더에서 먼저 일정을 추가해 주세요.")
    st.page_link("main.py", label="캘린더로 이동", icon="🗓️")
    st.stop()

with st.expander("목록 필터", expanded=True):
    date_filter = st.selectbox("기간", ["전체", "오늘", "오늘 이후", "지난 일정"])
    category_list = sorted({c for e in events for c in (e.get("categories") or []) if isinstance(c, str)})
    category_filter = st.selectbox("카테고리", ["전체"] + category_list)
    importance_filter = st.selectbox("중요도", ["전체", "상", "중", "하", "없음"])

today = date.today().isoformat()
filtered = []
for e in events:
    d = str(e["event_date"])[:10]
    cats = e.get("categories") or []
    if date_filter == "오늘" and d != today:
        continue
    if date_filter == "오늘 이후" and d < today:
        continue
    if date_filter == "지난 일정" and d >= today:
        continue
    if category_filter != "전체" and category_filter not in cats:
        continue
    if importance_filter != "전체" and (e.get("importance") or "없음") != importance_filter:
        continue
    filtered.append(e)

if not filtered:
    st.info("선택한 조건에 맞는 일정이 없습니다.")
    st.stop()

st.caption("체크 상태는 로그인한 계정에 저장됩니다.")
for e in filtered:
    eid = str(e["id"])
    done = statuses.get(eid, False)
    with st.container(border=True):
        col1, col2 = st.columns([0.08, 0.92])
        with col1:
            checked = st.checkbox("완료", value=done, key=f"done_{eid}", label_visibility="collapsed")
        with col2:
            st.markdown(f"**{str(e['event_date'])[:10]} · {(e.get('title') or '').strip() or '(제목 없음)'}**")
            cats = e.get("categories") or []
            st.caption(f"중요도: {e.get('importance') or '없음'}　|　카테고리: {', '.join(cats) if cats else '없음'}")
            if e.get("description"):
                st.write(e["description"])
    if checked != done:
        try:
            client.table("todo_status").upsert(
                {"event_id": eid, "user_id": uid, "completed": checked},
                on_conflict="event_id"
            ).execute()
            st.rerun()
        except Exception as exc:
            st.error(f"완료 상태를 저장하지 못했습니다: {exc}")

completed_count = sum(1 for e in filtered if statuses.get(str(e["id"]), False))
st.divider()
a, b, c = st.columns(3)
a.metric("표시된 일정", f"{len(filtered)}개")
b.metric("완료", f"{completed_count}개")
c.metric("남은 일정", f"{len(filtered)-completed_count}개")
st.page_link("main.py", label="캘린더로 돌아가기", icon="🗓️")
