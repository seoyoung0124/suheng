from datetime import date, datetime, timedelta, timezone

import streamlit as st


# ==========================================
# 1. 기본 설정
# ==========================================

st.set_page_config(
    page_title="하루결 | 플래너",
    page_icon="📒",
    layout="centered"
)

KST = timezone(timedelta(hours=9))
WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]

CATEGORIES = [
    "수행평가", "시험", "동아리",
    "개인일정", "과제", "학교행사", "기타"
]

IMPORTANCE_ICON = {"상": "🔴", "중": "🟡", "하": "🟢", "없음": "🟣"}
IMPORTANCE_ORDER = {"상": 0, "중": 1, "하": 2, "없음": 3}
PERSONAL_ICON = "🔵"


def today_kst():
    # 서버가 UTC여도 한국 시간 기준으로 오늘 날짜를 구한다
    return datetime.now(KST).date()


# ==========================================
# 2. 로그인 확인 (main.py에서 로그인한 세션을 그대로 사용)
# ==========================================

client = st.session_state.get("supabase_client")
uid = st.session_state.get("user_id")

if not client or not uid:
    st.title("📒 오늘의 플래너")
    st.info("먼저 캘린더 화면에서 로그인해 주세요.")

    try:
        st.page_link("main.py", label="로그인하러 가기", icon="🗓️")
    except Exception:
        pass

    st.stop()


# ==========================================
# 3. 선택한 날짜의 일정 불러오기 / 완료 상태 저장
# ==========================================

def fetch_day_events(client, uid, day):
    rows = (
        client.table("events")
        .select("*")
        .eq("user_id", uid)
        .eq("event_date", day.isoformat())
        .execute()
        .data or []
    )

    result = []

    for r in rows:
        cats = r.get("categories") or []

        if isinstance(cats, str):
            cats = [cats]

        importance = r.get("importance")

        result.append({
            "id": str(r["id"]),
            "title": r.get("title") or "(제목 없음)",
            "description": r.get("description") or "",
            "importance": importance if importance in IMPORTANCE_ORDER else "없음",
            "categories": [x for x in cats if x in CATEGORIES],
            "done": bool(r.get("done"))
        })

    # 중요한 일정이 위로 오도록 정렬
    result.sort(key=lambda e: (IMPORTANCE_ORDER[e["importance"]], e["title"]))
    return result


def toggle_done(event_id):
    key = f"done_{event_id}"
    new_value = bool(st.session_state.get(key, False))

    try:
        st.session_state.supabase_client.table("events").update(
            {"done": new_value}
        ).eq("id", event_id).eq(
            "user_id", st.session_state.user_id
        ).execute()
    except Exception as exc:
        st.session_state[key] = not new_value
        st.toast(f"완료 상태를 저장하지 못했습니다: {exc}")


def day_label(day):
    diff = (day - today_kst()).days

    if diff == 0:
        return "오늘"
    if diff > 0:
        return f"D-{diff}"
    return f"D+{-diff}"


# ==========================================
# 4. 날짜 이동 (화살표 / 날짜 선택 / 오늘 버튼)
# ==========================================

if "planner_picker" not in st.session_state:
    st.session_state.planner_picker = today_kst()


def shift_day(delta):
    st.session_state.planner_picker += timedelta(days=delta)


def go_today():
    st.session_state.planner_picker = today_kst()


st.title("📒 플래너")

_, pick_col, today_col, _ = st.columns([1, 3, 1.2, 1], vertical_alignment="bottom")

with pick_col:
    day = st.date_input("날짜 선택", key="planner_picker", format="YYYY-MM-DD")

with today_col:
    st.button("오늘", on_click=go_today, use_container_width=True, key="go_today")


# ==========================================
# 5. 플래너 (가운데) + 전날/다음날 화살표 (양 옆)
# ==========================================

left, center, right = st.columns([1, 6, 1], vertical_alignment="center")

with left:
    st.button(
        "◀", on_click=shift_day, args=(-1,),
        use_container_width=True, key="prev_day", help="전날"
    )

with right:
    st.button(
        "▶", on_click=shift_day, args=(1,),
        use_container_width=True, key="next_day", help="다음날"
    )

with center:
    try:
        day_events = fetch_day_events(client, uid, day)
    except Exception as exc:
        st.error(f"일정을 불러오지 못했습니다: {exc}")
        st.info("Supabase events 테이블에 done 컬럼이 있는지 확인해 주세요.")
        st.stop()

    total = len(day_events)
    done_count = sum(e["done"] for e in day_events)

    with st.container(border=True):
        st.caption(f"{day_label(day)} · 일정 {total}개 · 완료 {done_count}/{total}")
        st.subheader(
            f"{day.year}년 {day.month}월 {day.day}일 ({WEEKDAYS[day.weekday()]})"
        )

        if total:
            st.progress(done_count / total)

        st.divider()

        if not day_events:
            st.write("이 날은 등록된 일정이 없어요.")

        for e in day_events:
            icon = (
                PERSONAL_ICON
                if "개인일정" in e["categories"]
                else IMPORTANCE_ICON[e["importance"]]
            )

            title = f"~~{e['title']}~~" if e["done"] else f"**{e['title']}**"

            st.checkbox(
                f"{icon} {title}",
                value=e["done"],
                key=f"done_{e['id']}",
                on_change=toggle_done,
                args=(e["id"],)
            )

            info = []
            if e["importance"] != "없음":
                info.append(f"중요도 {e['importance']}")
            if e["categories"]:
                info.append(", ".join(e["categories"]))
            if info:
                st.caption(" · ".join(info))

            if e["description"]:
                st.write(e["description"])


# ==========================================
# 6. 캘린더로 돌아가기
# ==========================================

st.divider()

try:
    st.page_link("main.py", label="캘린더로 돌아가기", icon="🗓️")
except Exception:
    pass
