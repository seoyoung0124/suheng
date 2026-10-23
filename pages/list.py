import json
from datetime import date, datetime
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="오늘 할 일 | 하루결", page_icon="✅", layout="wide")

CURRENT_DIR = Path(__file__).resolve().parent
# list.py가 루트에 있거나 pages/ 폴더 안에 있어도 루트의 events.json을 찾는다.
if (CURRENT_DIR / "events.json").exists() or CURRENT_DIR.name != "pages":
    DATA_DIR = CURRENT_DIR
else:
    DATA_DIR = CURRENT_DIR.parent

EVENTS_FILE = DATA_DIR / "events.json"
STATUS_FILE = DATA_DIR / "todo_status.json"

IMPORTANCE_COLORS = {
    "상": "#F87171",
    "중": "#FACC15",
    "하": "#4ADE80",
    "없음": "#C4B5FD",
}
CATEGORY_COLORS = {
    "수행평가": "#FCE7F3",
    "시험": "#FEE2E2",
    "동아리": "#DBEAFE",
    "개인일정": "#E0F2FE",
    "과제": "#FEF3C7",
    "학교행사": "#EDE9FE",
    "기타": "#F3F4F6",
}


def parse_date(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except (ValueError, TypeError):
        try:
            return date.fromisoformat(str(value)[:10])
        except (ValueError, TypeError):
            return None


def load_events():
    if not EVENTS_FILE.exists():
        return []
    try:
        with EVENTS_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(data, list):
        return []

    events = []
    for item in data:
        if not isinstance(item, dict):
            continue
        event_date = parse_date(
            item.get("date") or item.get("start") or item.get("start_date")
        )
        if event_date is None:
            continue

        categories = item.get("categories", [])
        if isinstance(categories, str):
            categories = [categories]
        if not isinstance(categories, list):
            categories = []

        importance = str(item.get("importance", "없음"))
        if importance not in IMPORTANCE_COLORS:
            importance = "없음"

        event_id = str(item.get("id") or "")
        if not event_id:
            event_id = f'{event_date.isoformat()}_{item.get("title", "")}'

        events.append({
            "id": event_id,
            "date": event_date,
            "title": str(item.get("title") or "").strip() or "(제목 없음)",
            "description": str(item.get("description") or "").strip(),
            "importance": importance,
            "categories": [str(c) for c in categories],
        })
    return events


def load_status():
    if not STATUS_FILE.exists():
        return {}
    try:
        with STATUS_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if isinstance(data, dict):
            return {str(k): bool(v) for k, v in data.items()}
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def save_status():
    try:
        with STATUS_FILE.open("w", encoding="utf-8") as file:
            json.dump(st.session_state.todo_status, file, ensure_ascii=False, indent=2)
    except OSError as exc:
        st.error(f"완료 상태를 저장하지 못했습니다: {exc}")


if "todo_status" not in st.session_state:
    st.session_state.todo_status = load_status()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
.stApp { background: #FAF9FF; }
.main .block-container { max-width: 1100px; padding-top: 2rem; padding-bottom: 3rem; }
.page-header { background: linear-gradient(135deg, #EDE9FE, #FDF2F8);
border: 1px solid #E9DFFB; border-radius: 24px; padding: 28px 30px; margin-bottom: 20px; }
.page-title { font-size: 32px; font-weight: 800; color: #514278; margin: 0 0 8px 0; }
.page-subtitle { color: #756B8D; margin: 0; font-size: 15px; }
div.stButton > button { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="page-header">
<div class="page-title">✅ 오늘 할 일</div>
<p class="page-subtitle">캘린더에 등록한 일정이 자동으로 정리됩니다. 완료한 항목은 체크해서 진행 상황을 관리하세요.</p>
</div>
""", unsafe_allow_html=True)

events = load_events()
today = date.today()

if not events:
    st.info("아직 등록된 일정이 없어요. 먼저 캘린더 페이지에서 일정을 추가해 주세요.")
    st.caption("이 페이지는 main.py와 같은 폴더의 events.json 파일을 읽습니다.")
    st.stop()

date_filter = st.radio(
    "표시할 일정",
    ["오늘 이후", "오늘", "전체", "지난 일정"],
    horizontal=True,
    index=0,
)
category_options = sorted({
    category for event in events for category in event["categories"]
})
category_filter = st.selectbox("카테고리 필터", ["전체"] + category_options)
importance_filter = st.selectbox("중요도 필터", ["전체", "상", "중", "하", "없음"])
show_completed = st.checkbox("완료한 일정도 표시", value=True)

filtered = []
for event in events:
    event_date = event["date"]
    if date_filter == "오늘 이후" and event_date < today:
        continue
    if date_filter == "오늘" and event_date != today:
        continue
    if date_filter == "지난 일정" and event_date >= today:
        continue
    if category_filter != "전체" and category_filter not in event["categories"]:
        continue
    if importance_filter != "전체" and event["importance"] != importance_filter:
        continue
    if st.session_state.todo_status.get(event["id"], False) and not show_completed:
        continue
    filtered.append(event)

importance_order = {"상": 0, "중": 1, "하": 2, "없음": 3}
filtered.sort(key=lambda e: (e["date"], importance_order.get(e["importance"], 3), e["title"].casefold()))

all_ids = [event["id"] for event in events]
completed_count = sum(1 for event_id in all_ids if st.session_state.todo_status.get(event_id, False))
total_count = len(events)
remaining_count = total_count - completed_count

m1, m2, m3 = st.columns(3)
m1.metric("전체 일정", f"{total_count}개")
m2.metric("남은 일정", f"{remaining_count}개")
m3.metric("완료한 일정", f"{completed_count}개")
st.progress(completed_count / total_count if total_count else 0.0,
            text=f"전체 일정 완료율 {round(completed_count / total_count * 100) if total_count else 0}%")
st.divider()

left, right = st.columns([3, 1])
with left:
    st.markdown("### 할 일 목록")
    st.caption(f"표시 중인 일정: {len(filtered)}개")
with right:
    if st.button("완료 표시 모두 해제", use_container_width=True):
        for event_id in all_ids:
            st.session_state.todo_status[event_id] = False
        save_status()
        st.rerun()

if not filtered:
    st.warning("선택한 조건에 맞는 일정이 없습니다.")
else:
    grouped = {}
    for event in filtered:
        grouped.setdefault(event["date"], []).append(event)

    for event_date in sorted(grouped):
        day_events = grouped[event_date]
        if event_date == today:
            label = "오늘"
        elif event_date < today:
            label = "지난 일정"
        else:
            label = event_date.strftime("%m월 %d일")

        done_today = sum(
            1 for event in day_events
            if st.session_state.todo_status.get(event["id"], False)
        )
        st.markdown(f"### {label} · {event_date.strftime('%Y-%m-%d')}")
        st.caption(f"{done_today}/{len(day_events)}개 완료")

        for event in day_events:
            event_id = event["id"]
            completed = st.session_state.todo_status.get(event_id, False)
            color = (
                "#7DD3FC" if "개인일정" in event["categories"]
                else IMPORTANCE_COLORS.get(event["importance"], "#C4B5FD")
            )

            with st.container(border=True):
                check_col, detail_col = st.columns([0.08, 0.92])
                with check_col:
                    checked = st.checkbox(
                        "완료", value=completed, key=f"todo_{event_id}",
                        label_visibility="collapsed",
                    )
                if checked != completed:
                    st.session_state.todo_status[event_id] = checked
                    save_status()
                    st.rerun()

                with detail_col:
                    if completed:
                        st.markdown(f'~~**{event["title"]}**~~')
                    else:
                        st.markdown(f'**{event["title"]}**')

                    badges = [
                        f'<span style="background:{color};padding:3px 8px;border-radius:999px;font-size:12px;">중요도 {event["importance"]}</span>'
                    ]
                    for category in event["categories"]:
                        cat_color = CATEGORY_COLORS.get(category, "#F3F4F6")
                        badges.append(
                            f'<span style="background:{cat_color};padding:3px 8px;border-radius:999px;font-size:12px;">{category}</span>'
                        )
                    st.markdown(" &nbsp; ".join(badges), unsafe_allow_html=True)
                    if event["description"]:
                        st.write(event["description"])
        st.write("")

st.divider()
st.caption("일정은 main.py가 저장한 events.json에서 읽고, 완료 체크 상태는 todo_status.json에 별도로 저장합니다.")
st.caption("Streamlit Cloud의 로컬 파일은 재배포나 환경 초기화 후 유지되지 않을 수 있습니다. 장기 보존에는 외부 데이터베이스 연결을 권장합니다.")
