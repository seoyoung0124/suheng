from datetime import date
import streamlit as st
from supabase_utils import get_supabase, current_user_id, sign_out

st.set_page_config(
    page_title="하루결 | 플래너",
    page_icon="🗓️",
    layout="centered",
)

# ---------- 기본 스타일 ----------
st.markdown(
    """
    <style>
    .block-container {
        max-width: 760px;
        padding-top: 2.2rem;
        padding-bottom: 3rem;
    }
    h1, h2, h3 {
        letter-spacing: -0.04em;
    }
    div[data-testid="stMetric"] {
        background: #f7f8fa;
        border: 1px solid #eceef1;
        padding: 14px 16px;
        border-radius: 12px;
    }
    div[data-testid="stCheckbox"] {
        padding-top: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- 로그인 확인 ----------
uid = current_user_id()
if not uid:
    st.title("로그인이 필요해요")
    st.caption("하루결 플래너를 이용하려면 먼저 로그인해 주세요.")
    st.page_link("main.py", label="캘린더로 이동")
    st.stop()

client = get_supabase()

# ---------- 상단 ----------
top_left, top_right = st.columns([5, 1])
with top_left:
    st.title("하루결")
    st.caption("오늘의 계획을 차분하게 정리해 보세요.")
with top_right:
    if st.button("로그아웃", use_container_width=True):
        sign_out()
        st.rerun()

st.divider()

# ---------- 데이터 불러오기 ----------
try:
    rows = (
        client.table("events")
        .select("id,event_date,title,description,importance,categories")
        .eq("user_id", uid)
        .order("event_date")
        .execute()
        .data
        or []
    )
    status_rows = (
        client.table("todo_status")
        .select("event_id,completed")
        .eq("user_id", uid)
        .execute()
        .data
        or []
    )
except Exception as exc:
    st.error("일정을 불러오지 못했습니다.")
    st.caption(str(exc))
    st.info("Supabase의 events와 todo_status 테이블 및 user_id 설정을 확인해 주세요.")
    st.stop()

statuses = {
    str(row["event_id"]): bool(row.get("completed", False))
    for row in status_rows
}
events = [row for row in rows if row.get("event_date")]
events.sort(key=lambda row: (str(row["event_date"]), row.get("title") or ""))

if not events:
    st.info("아직 등록된 일정이 없어요.")
    st.page_link("main.py", label="캘린더에서 첫 일정 추가하기")
    st.stop()

# ---------- 필터 ----------
today = date.today().isoformat()
with st.expander("필터", expanded=False):
    date_filter = st.selectbox(
        "기간",
        ["전체", "오늘", "오늘 이후", "지난 일정"],
        label_visibility="collapsed",
    )
    category_list = sorted({
        category
        for event in events
        for category in (event.get("categories") or [])
        if isinstance(category, str)
    })
    category_filter = st.selectbox("카테고리", ["전체"] + category_list)
    importance_filter = st.selectbox("중요도", ["전체", "상", "중", "하", "없음"])

filtered = []
for event in events:
    event_date = str(event["event_date"])[:10]
    categories = event.get("categories") or []

    if date_filter == "오늘" and event_date != today:
        continue
    if date_filter == "오늘 이후" and event_date < today:
        continue
    if date_filter == "지난 일정" and event_date >= today:
        continue
    if category_filter != "전체" and category_filter not in categories:
        continue
    if importance_filter != "전체" and (event.get("importance") or "없음") != importance_filter:
        continue

    filtered.append(event)

if not filtered:
    st.info("선택한 조건에 해당하는 일정이 없어요.")
    st.stop()

# ---------- 진행 현황 ----------
completed_count = sum(
    1 for event in filtered if statuses.get(str(event["id"]), False)
)
total_count = len(filtered)
remaining_count = total_count - completed_count
progress = completed_count / total_count if total_count else 0

st.subheader("나의 플래너")
st.caption(f"{date.today().strftime('%Y년 %m월 %d일')} 기준")

metric1, metric2, metric3 = st.columns(3)
metric1.metric("전체", f"{total_count}개")
metric2.metric("완료", f"{completed_count}개")
metric3.metric("남은 일", f"{remaining_count}개")

st.progress(progress, text=f"오늘의 진행률이 아닌, 현재 필터에 표시된 일정의 완료율 {progress:.0%}")

st.divider()

# ---------- 일정 목록 ----------
st.subheader("일정")

for event in filtered:
    event_id = str(event["id"])
    is_done = statuses.get(event_id, False)
    title = (event.get("title") or "").strip() or "제목 없는 일정"
    event_date = str(event["event_date"])[:10]
    categories = event.get("categories") or []
    importance = event.get("importance") or "없음"

    with st.container(border=True):
        check_col, text_col = st.columns([0.08, 0.92])
        with check_col:
            checked = st.checkbox(
                "완료",
                value=is_done,
                key=f"planner_done_{event_id}",
                label_visibility="collapsed",
            )
        with text_col:
            if is_done:
                st.markdown(f"~~**{title}**~~")
            else:
                st.markdown(f"**{title}**")
            meta = f"{event_date}  ·  중요도 {importance}"
            if categories:
                meta += f"  ·  {', '.join(categories)}"
            st.caption(meta)
            if event.get("description"):
                st.write(event["description"])

    if checked != is_done:
        try:
            client.table("todo_status").upsert(
                {
                    "event_id": event_id,
                    "user_id": uid,
                    "completed": checked,
                },
                on_conflict="event_id",
            ).execute()
            st.rerun()
        except Exception as exc:
            st.error("완료 상태를 저장하지 못했습니다.")
            st.caption(str(exc))

st.divider()
st.page_link("main.py", label="← 캘린더로 돌아가기")
