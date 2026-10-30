from datetime import date, timedelta
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
        max-width: 850px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    h1, h2, h3 { letter-spacing: -0.035em; }
    .section-intro {
        color: #64748b;
        font-size: 0.92rem;
        margin-top: -0.45rem;
        margin-bottom: 1rem;
    }
    .stat-heading {
        font-size: 1.05rem;
        font-weight: 700;
        margin: 0.35rem 0 0.7rem 0;
    }
    div[data-testid="stMetric"] {
        background: #f7f8fa;
        border: 1px solid #e6e9ee;
        border-radius: 13px;
        padding: 15px 18px;
        min-height: 105px;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.9rem;
        color: #475569;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.65rem;
        font-weight: 700;
    }
    div[data-testid="stTabs"] button {
        font-size: 1rem;
        font-weight: 650;
        padding-top: 0.65rem;
        padding-bottom: 0.65rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def parse_event_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def get_categories(value):
    if isinstance(value, list):
        return [str(item) for item in value if item]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def summarize_period(period_events, statuses, start_date, end_date):
    selected = [
        event for event in period_events
        if start_date <= event["_date"] <= end_date
    ]
    total = len(selected)
    completed = sum(
        1 for event in selected if statuses.get(str(event["id"]), False)
    )
    remaining = total - completed
    rate = completed / total if total else 0
    return selected, total, completed, remaining, rate


def render_metrics(total, completed, remaining, rate):
    # 4개 지표를 2x2로 배치해 작은 화면에서도 읽기 쉽게 표시
    row1_col1, row1_col2 = st.columns(2)
    row1_col1.metric("전체 일정", f"{total}개")
    row1_col2.metric("완료한 일정", f"{completed}개")
    row2_col1, row2_col2 = st.columns(2)
    row2_col1.metric("남은 일정", f"{remaining}개")
    row2_col2.metric("완료율", f"{rate:.0%}")

    st.progress(rate)
    st.caption(f"전체 {total}개 중 {completed}개 완료 · 미완료 {remaining}개")


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
    st.bar_chart(chart_df, height=280)
    st.caption("막대의 두 항목은 해당 날짜의 완료 일정과 미완료 일정 수를 나타냅니다.")


def render_category_summary(selected, statuses):
    category_counts = {}
    for event in selected:
        categories = get_categories(event.get("categories")) or ["분류 없음"]
        for category in categories:
            if category not in category_counts:
                category_counts[category] = {"전체 일정": 0, "완료": 0}
            category_counts[category]["전체 일정"] += 1
            if statuses.get(str(event["id"]), False):
                category_counts[category]["완료"] += 1

    if not category_counts:
        st.caption("표시할 일정이 없습니다.")
        return

    table_rows = []
    for category, counts in category_counts.items():
        total = counts["전체 일정"]
        completed = counts["완료"]
        table_rows.append({
            "분류": category,
            "전체 일정": total,
            "완료": completed,
            "미완료": total - completed,
            "완료율": completed / total if total else 0,
        })

    summary_df = pd.DataFrame(table_rows).sort_values("분류")
    st.dataframe(
        summary_df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "전체 일정": st.column_config.NumberColumn(format="%d개"),
            "완료": st.column_config.NumberColumn(format="%d개"),
            "미완료": st.column_config.NumberColumn(format="%d개"),
            "완료율": st.column_config.ProgressColumn(
                "완료율", min_value=0, max_value=1, format="%.0f%%"
            ),
        },
    )


def render_period_section(label, selected, total, completed, remaining, rate,
                          start_date, end_date, statuses):
    st.markdown(f'<div class="stat-heading">{label} 요약</div>', unsafe_allow_html=True)
    render_metrics(total, completed, remaining, rate)

    st.divider()
    st.subheader("날짜별 진행 현황")
    st.markdown('<div class="section-intro">날짜마다 완료한 일정과 남은 일정을 비교할 수 있어요.</div>', unsafe_allow_html=True)
    if selected:
        render_daily_chart(selected, statuses, start_date, end_date)
        st.divider()
        st.subheader("분류별 진행 현황")
        st.markdown('<div class="section-intro">어떤 종류의 일정이 얼마나 완료되었는지 확인해 보세요.</div>', unsafe_allow_html=True)
        render_category_summary(selected, statuses)
    else:
        st.info("선택한 기간에는 등록된 일정이 없습니다.")


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
    st.caption("나의 일정 진행 상황을 한눈에 확인하세요.")
with right:
    if st.button("로그아웃", use_container_width=True):
        sign_out()
        st.rerun()

st.divider()
st.header("주간·월간 통계")
st.markdown(
    '<div class="section-intro">기준 날짜를 선택하면 해당 날짜가 포함된 주와 달의 통계를 보여 줍니다.</div>',
    unsafe_allow_html=True,
)

# ---------- 데이터 ----------
try:
    event_rows = (
        client.table("events")
        .select("id,event_date,title,categories,importance")
        .eq("user_id", uid)
        .execute()
        .data or []
    )
    status_rows = (
        client.table("todo_status")
        .select("event_id,completed")
        .eq("user_id", uid)
        .execute()
        .data or []
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
    if parsed_date is not None:
        event = dict(row)
        event["_date"] = parsed_date
        events.append(event)

if not events:
    st.info("통계를 표시할 일정이 아직 없습니다. 캘린더에서 일정을 추가해 보세요.")
    st.page_link("main.py", label="캘린더로 이동")
    st.stop()

reference_date = st.date_input(
    "통계 기준 날짜",
    value=date.today(),
    help="선택한 날짜가 포함된 주간·월간 통계를 보여 줍니다.",
)

week_start = reference_date - timedelta(days=reference_date.weekday())
week_end = week_start + timedelta(days=6)
month_start = reference_date.replace(day=1)
month_end = reference_date.replace(
    day=calendar.monthrange(reference_date.year, reference_date.month)[1]
)

weekly_tab, monthly_tab = st.tabs(["주간 통계", "월간 통계"])

with weekly_tab:
    st.subheader(f"{week_start:%Y.%m.%d} – {week_end:%Y.%m.%d}")
    selected, total, completed, remaining, rate = summarize_period(
        events, statuses, week_start, week_end
    )
    render_period_section(
        "이번 주", selected, total, completed, remaining, rate,
        week_start, week_end, statuses,
    )

with monthly_tab:
    st.subheader(f"{reference_date:%Y년 %m월}")
    selected, total, completed, remaining, rate = summarize_period(
        events, statuses, month_start, month_end
    )
    render_period_section(
        "이번 달", selected, total, completed, remaining, rate,
        month_start, month_end, statuses,
    )

st.divider()
st.page_link("pages/list.py", label="To-do 리스트로 이동")
st.page_link("main.py", label="캘린더로 이동")
