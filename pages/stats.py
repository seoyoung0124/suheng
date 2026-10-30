from datetime import date, datetime, timedelta
import calendar

import pandas as pd
import streamlit as st

from supabase_utils import get_supabase, current_user_id, sign_out


st.set_page_config(
    page_title="하루결 | 통계",
    page_icon="📊",
    layout="centered",
)

# ---------- 디자인 ----------
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
    </style>
    """,
    unsafe_allow_html=True,
)


def parse_event_date(value):
    """Supabase 날짜 값을 date 객체로 변환한다."""
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def get_categories(value):
    """categories JSONB 값을 안전하게 목록으로 변환한다."""
    if isinstance(value, list):
        return [str(item) for item in value if item]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def summarize_period(period_events, statuses, start_date, end_date):
    selected = [
        event for event in period_events
        if event["_date"] is not None and start_date <= event["_date"] <= end_date
    ]

    total = len(selected)
    completed = sum(
        1 for event in selected
        if statuses.get(str(event["id"]), False)
    )
    remaining = total - completed
    rate = completed / total if total else 0

    return selected, total, completed, remaining, rate


def render_metrics(total, completed, remaining, rate):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("전체 일정", f"{total}개")
    c2.metric("완료", f"{completed}개")
    c3.metric("미완료", f"{remaining}개")
    c4.metric("완료율", f"{rate:.0%}")


def render_daily_chart(selected, statuses, start_date, end_date):
    day_count = (end_date - start_date).days + 1
    days = [start_date + timedelta(days=i) for i in range(day_count)]

    rows = []
    for day in days:
        day_events = [event for event in selected if event["_date"] == day]
        done = sum(
            1 for event in day_events
            if statuses.get(str(event["id"]), False)
        )
        rows.append({
            "날짜": day.strftime("%m/%d"),
            "완료": done,
            "미완료": len(day_events) - done,
        })

    chart_df = pd.DataFrame(rows).set_index("날짜")
    st.bar_chart(chart_df, height=250)


def render_category_summary(selected, statuses):
    category_counts = {}
    for event in selected:
        categories = get_categories(event.get("categories"))
        if not categories:
            categories = ["분류 없음"]

        for category in categories:
            if category not in category_counts:
                category_counts[category] = {"전체": 0, "완료": 0}
            category_counts[category]["전체"] += 1
            if statuses.get(str(event["id"]), False):
                category_counts[category]["완료"] += 1

    if not category_counts:
        st.caption("표시할 일정이 없습니다.")
        return

    table_rows = []
    for category, counts in sorted(category_counts.items()):
        total = counts["전체"]
        completed = counts["완료"]
        rate = completed / total if total else 0
        table_rows.append({
            "분류": category,
            "전체": total,
            "완료": completed,
            "완료율": f"{rate:.0%}",
        })

    st.dataframe(
        pd.DataFrame(table_rows),
        hide_index=True,
        use_container_width=True,
    )


# ---------- 로그인 ----------
uid = current_user_id()
if not uid:
    st.title("로그인이 필요해요")
    st.caption("통계를 확인하려면 먼저 로그인해 주세요.")
    st.page_link("main.py", label="캘린더로 이동")
    st.stop()

client = get_supabase()

# ---------- 상단 ----------
left, right = st.columns([5, 1])
with left:
    st.title("하루결")
    st.caption("기록을 돌아보고 계획을 점검해 보세요.")
with right:
    if st.button("로그아웃", use_container_width=True):
        sign_out()
        st.rerun()

st.divider()
st.header("주간·월간 통계")

# ---------- 데이터 ----------
try:
    event_rows = (
        client.table("events")
        .select("id,event_date,title,categories,importance")
        .eq("user_id", uid)
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
    st.error("통계 데이터를 불러오지 못했습니다.")
    st.caption(str(exc))
    st.info("Supabase의 events와 todo_status 테이블 및 user_id 설정을 확인해 주세요.")
    st.stop()

statuses = {
    str(row["event_id"]): bool(row.get("completed", False))
    for row in status_rows
}

events = []
for row in event_rows:
    parsed_date = parse_event_date(row.get("event_date"))
    if parsed_date is None:
        continue
    event = dict(row)
    event["_date"] = parsed_date
    events.append(event)

if not events:
    st.info("통계를 표시할 일정이 아직 없습니다. 캘린더에서 일정을 추가해 보세요.")
    st.page_link("main.py", label="캘린더로 이동")
    st.stop()

# 기준 날짜를 선택해 해당 날짜가 포함된 주와 월을 조회
reference_date = st.date_input(
    "기준 날짜",
    value=date.today(),
    help="선택한 날짜가 포함된 주간·월간 통계를 보여 줍니다.",
)

week_start = reference_date - timedelta(days=reference_date.weekday())
week_end = week_start + timedelta(days=6)

month_start = reference_date.replace(day=1)
month_last_day = calendar.monthrange(reference_date.year, reference_date.month)[1]
month_end = reference_date.replace(day=month_last_day)

weekly_tab, monthly_tab = st.tabs(["주간 통계", "월간 통계"])

# ---------- 주간 ----------
with weekly_tab:
    st.subheader(f"{week_start:%Y년 %m월 %d일} – {week_end:%m월 %d일}")
    selected, total, completed, remaining, rate = summarize_period(
        events, statuses, week_start, week_end
    )

    render_metrics(total, completed, remaining, rate)
    st.progress(rate, text=f"이번 주 완료율 {rate:.0%}")

    st.markdown("#### 날짜별 일정")
    if selected:
        render_daily_chart(selected, statuses, week_start, week_end)
        st.markdown("#### 분류별 현황")
        render_category_summary(selected, statuses)
    else:
        st.info("선택한 주에는 등록된 일정이 없습니다.")

# ---------- 월간 ----------
with monthly_tab:
    st.subheader(f"{reference_date:%Y년 %m월}")
    selected, total, completed, remaining, rate = summarize_period(
        events, statuses, month_start, month_end
    )

    render_metrics(total, completed, remaining, rate)
    st.progress(rate, text=f"이번 달 완료율 {rate:.0%}")

    st.markdown("#### 날짜별 일정")
    if selected:
        render_daily_chart(selected, statuses, month_start, month_end)
        st.markdown("#### 분류별 현황")
        render_category_summary(selected, statuses)
    else:
        st.info("선택한 달에는 등록된 일정이 없습니다.")

st.divider()
st.page_link("pages/list.py", label="플래너로 돌아가기")
st.page_link("main.py", label="캘린더로 돌아가기")
