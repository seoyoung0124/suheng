# 주간·월간 일정 수와 완료율 등 통계 화면을 담당한다.
import calendar as pycal
import math
from datetime import date, timedelta

import streamlit as st

import theme

st.set_page_config(
    page_title="Daily Planner | Stats",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

client, uid = theme.page_setup("stats")

esc = theme.esc
today = theme.today_kst()
pal = theme.palette()
WD = theme.WEEKDAYS_KR

# 카테고리별 색 (어떤 테마에서도 잘 보이는 파스텔)
CAT_COLOR = {
    "수행평가": "#C4A8F5",
    "시험": "#FBD680",
    "동아리": "#8FDDBE",
    "개인일정": "#A9D4FA",
    "과제": "#F6A9C8",
    "학교행사": "#F9B88F",
    "기타": "#CFD2E0",
    "미분류": "#E1E3EC",
}
CAT_ORDER = {name: i for i, name in enumerate(theme.CATEGORIES)}
MAJOR_SHOW = 5  # '주요 일정'에 보여 줄 최대 개수


# ==========================================
# 1. 날짜 / 문구 도우미
# ==========================================

def add_months(d, n):
    index = d.year * 12 + (d.month - 1) + n
    return date(index // 12, index % 12 + 1, 1)


def month_bounds(anchor):
    start = anchor.replace(day=1)
    return start, add_months(start, 1) - timedelta(days=1)


def week_bounds(anchor):
    start = anchor - timedelta(days=anchor.weekday())
    return start, start + timedelta(days=6)


def kr_date(d):
    return f"{d.month}월 {d.day}일 ({WD[d.weekday()]})"


def has_batchim(word):
    ch = str(word).strip()[-1:]
    return bool(ch) and "가" <= ch <= "힣" and (ord(ch) - 0xAC00) % 28 != 0


def eun_neun(word):
    return "은" if has_batchim(word) else "는"


def cat_color(name):
    return CAT_COLOR.get(name, "#CFD2E0")


def primary_cat(event):
    return event["categories"][0] if event["categories"] else "미분류"


# ==========================================
# 2. 일정 불러오기 / 통계 계산
# ==========================================

def fetch_events(client, uid, start, end):
    rows = (
        client.table("events")
        .select("*")
        .eq("user_id", uid)
        .gte("event_date", start.isoformat())
        .lte("event_date", end.isoformat())
        .order("event_date")
        .execute()
        .data or []
    )

    result = []

    for r in rows:
        if not r.get("event_date"):
            continue

        cats = r.get("categories") or []

        if isinstance(cats, str):
            cats = [cats]

        importance = r.get("importance")

        result.append({
            "id": str(r["id"]),
            "date": str(r["event_date"])[:10],
            "title": r.get("title") or "(제목 없음)",
            "importance": (
                importance if importance in theme.IMPORTANCE_ORDER else "없음"
            ),
            "categories": [x for x in cats if x in theme.CATEGORIES],
            "done": bool(r.get("done"))
        })

    return result


def summarize(items):
    total = len(items)
    done = sum(1 for e in items if e["done"])
    rate = done / total * 100 if total else 0.0

    counts = {}

    for e in items:
        for c in (e["categories"] or ["미분류"]):
            counts[c] = counts.get(c, 0) + 1

    cats = sorted(counts.items(), key=lambda kv: (-kv[1], CAT_ORDER.get(kv[0], 99)))

    return {
        "total": total,
        "done": done,
        "rate": rate,
        "cats": cats,
        "tags": sum(counts.values()),
    }


def group_by_date(items):
    by_date = {}

    for e in items:
        by_date.setdefault(e["date"], []).append(e)

    return by_date


# ==========================================
# 3. 상태 (주간/월간, 기간 이동)
# ==========================================

st.session_state.setdefault("stats_mode", "week")
st.session_state.setdefault("stats_anchor", today)


def set_mode(mode):
    st.session_state.stats_mode = mode
    st.session_state.stats_anchor = theme.today_kst()


def shift_period(delta):
    anchor = st.session_state.stats_anchor

    if st.session_state.stats_mode == "month":
        st.session_state.stats_anchor = add_months(anchor, delta)
    else:
        st.session_state.stats_anchor = anchor + timedelta(days=7 * delta)


mode = st.session_state.stats_mode if st.session_state.stats_mode in ("week", "month") else "week"
anchor = st.session_state.stats_anchor

if not isinstance(anchor, date):
    anchor = today

if mode == "month":
    start, end = month_bounds(anchor)
    prev_start, prev_end = month_bounds(add_months(start, -1))
else:
    start, end = week_bounds(anchor)
    prev_start, prev_end = start - timedelta(days=7), start - timedelta(days=1)

is_current = start <= today <= end

try:
    all_events = fetch_events(client, uid, prev_start, end)
except Exception as exc:
    st.error(f"일정을 불러오지 못했습니다: {exc}")
    st.info("Supabase events 테이블과 done 컬럼을 확인해 주세요. (schema.sql 실행)")
    st.stop()

cur_events = [e for e in all_events if start.isoformat() <= e["date"] <= end.isoformat()]
prev_events = [e for e in all_events if prev_start.isoformat() <= e["date"] <= prev_end.isoformat()]

cur = summarize(cur_events)
prev = summarize(prev_events)
by_date = group_by_date(cur_events)

total_delta = cur["total"] - prev["total"]
done_delta = cur["done"] - prev["done"]

if mode == "month":
    cur_name = "이번 달" if is_current else f"{start.month}월"
    prev_name = "지난달" if is_current else f"{prev_start.month}월"
else:
    cur_name = "이번 주" if is_current else "이 주"
    prev_name = "지난주" if is_current else "그 전주"


# ==========================================
# 4. HTML 조각 (카드, 도넛, 파이, 막대, 달력)
# ==========================================

def diff_html(delta, good=False):
    if delta > 0:
        css = "diff-good" if good else "diff-up"
        return f'<span class="kpi-diff {css}">▲ +{delta}개</span>'

    if delta < 0:
        return f'<span class="kpi-diff diff-down">▼ {delta}개</span>'

    return '<span class="kpi-diff diff-flat">－ 변동 없음</span>'


def kpi_card(icon, icon_bg, label, value, extra=""):
    return (
        '<div class="stat-card kpi">'
        f'<div class="kpi-ic" style="background:{icon_bg}">{icon}</div>'
        f'<div><div class="kpi-label">{esc(label)}</div>'
        f'<div class="kpi-val">{value}{extra}</div></div>'
        '</div>'
    )


def donut_style(rate):
    return (
        f"background:conic-gradient({pal['accent']} 0 {rate:.2f}%, "
        f"{pal['rail']} {rate:.2f}% 100%)"
    )


def donut_card_month():
    return (
        '<div class="stat-card kpi">'
        f'<div class="donut sm" style="{donut_style(cur["rate"])}"></div>'
        '<div><div class="kpi-label">일정 완료율</div>'
        f'<div class="kpi-val">{cur["rate"]:.1f}%</div>'
        f'<div class="kpi-note">({cur["done"]} / {cur["total"]})</div></div>'
        '</div>'
    )


def donut_card_week():
    return (
        '<div class="stat-card kpi">'
        f'<div class="donut" style="{donut_style(cur["rate"])}">'
        f'<span>{cur["rate"]:.1f}%</span></div>'
        '<div><div class="kpi-label big">일정 완료율</div>'
        f'<div class="kpi-note big">완료 {cur["done"]}개 / 전체 {cur["total"]}개</div></div>'
        '</div>'
    )


def top_category_card():
    if cur["cats"]:
        name, count = cur["cats"][0]
        pct = round(count / cur["tags"] * 100)
        value = (
            f'<span style="font-size:1.55rem">{esc(name)}</span>'
            f'<span class="kpi-note"> ({pct}%)</span>'
        )
    else:
        value = '<span class="kpi-note">-</span>'

    return kpi_card("⭐", "#FFF0DD", "가장 많은 카테고리", value)


def pie_card():
    if cur["cats"]:
        stops, acc = [], 0.0

        for name, count in cur["cats"]:
            nxt = acc + count / cur["tags"] * 100
            stops.append(f"{cat_color(name)} {acc:.2f}% {nxt:.2f}%")
            acc = nxt

        pie_style = "background:conic-gradient(" + ",".join(stops) + ")"
        body = (
            '<div class="pie-wrap">'
            f'<div class="pie" style="{pie_style}"></div>'
            f'<div class="cat-list">{cat_rows_html()}</div>'
            '</div>'
        )
    else:
        body = '<div class="stat-empty">아직 분류된 일정이 없어요.</div>'

    return (
        '<div class="stat-card">'
        '<div class="stat-title"><span class="stat-ic">🥧</span>카테고리별 현황</div>'
        f'{body}</div>'
    )


def cat_rows_html():
    rows = []

    for name, count in cur["cats"]:
        pct = round(count / cur["tags"] * 100)
        rows.append(
            '<div class="cat-row">'
            f'<span class="cat-dot" style="background:{cat_color(name)}"></span>'
            f'<span class="cat-name">{esc(name)}</span>'
            f'<span class="cat-val">{count}개 ({pct}%)</span>'
            '</div>'
        )

    return "".join(rows)


def category_card_week():
    if cur["cats"]:
        name = cur["cats"][0][0]
        tip = (
            "분류하지 않은 일정이 가장 많아요!"
            if name == "미분류"
            else f"{cur_name}에는 {esc(name)} 일정이 가장 많아요!"
        )
        body = f'<div class="cat-list">{cat_rows_html()}</div><div class="stat-tip">💡 {tip}</div>'
    else:
        body = '<div class="stat-empty">아직 분류된 일정이 없어요.</div>'

    return (
        '<div class="stat-card">'
        '<div class="stat-title"><span class="stat-ic">🥧</span>카테고리별 현황</div>'
        f'{body}</div>'
    )


def month_calendar_html():
    weeks = pycal.Calendar(firstweekday=0).monthdayscalendar(start.year, start.month)

    head = "".join(f'<div class="mc-h">{name}</div>' for name in WD)
    cells = []

    for week in weeks:
        for number in week:
            if number == 0:
                cells.append('<div class="mc-d empty"></div>')
                continue

            d = date(start.year, start.month, number)
            events = by_date.get(d.isoformat(), [])

            style, dots = "", ""

            if events:
                style = f' style="background:{cat_color(primary_cat(events[0]))}33"'
                dots = '<div class="mc-dots">' + "".join(
                    f'<i style="background:{cat_color(primary_cat(e))}"></i>'
                    for e in events[:3]
                ) + "</div>"

            css = "mc-d today" if d == today else "mc-d"
            cells.append(f'<div class="{css}"{style}><span>{number}</span>{dots}</div>')

    legend = "".join(
        f'<span><i style="background:{cat_color(name)}"></i>{esc(name)}</span>'
        for name, _ in cur["cats"]
    )

    return (
        f'<div class="mini-cal">{head}{"".join(cells)}</div>'
        f'<div class="legend">{legend}</div>'
    )


def week_chart_html():
    days = [start + timedelta(days=i) for i in range(7)]
    counts = [len(by_date.get(d.isoformat(), [])) for d in days]
    dones = [sum(1 for e in by_date.get(d.isoformat(), []) if e["done"]) for d in days]

    top = max(counts) if counts else 0
    step = 1 if top <= 4 else math.ceil(top / 4)
    ymax = step * 4

    lines = "".join(
        f'<div class="bc-line" style="bottom:{t / ymax * 100:.2f}%"><span>{t}</span></div>'
        for t in range(0, ymax + 1, step)
    )

    cols, labels = [], []

    for d, count, done in zip(days, counts, dones):
        bar = ""

        if count:
            bar = (
                f'<div class="bar" style="height:{count / ymax * 100:.2f}%">'
                f'<div class="bar-done" style="height:{done / count * 100:.2f}%"></div></div>'
            )

        cols.append(f'<div class="bc-col"><div class="bc-val">{count}</div>{bar}</div>')

        css = "bc-lab bc-today" if d == today else "bc-lab"
        labels.append(
            f'<div class="{css}">{WD[d.weekday()]}<br><small>({d.day}일)</small></div>'
        )

    return (
        '<div class="bc">'
        f'<div class="bc-plot">{lines}<div class="bc-cols">{"".join(cols)}</div></div>'
        f'<div class="bc-labels">{"".join(labels)}</div>'
        '</div>'
        '<div class="legend"><span><i style="background:' + pal["accent"] + '"></i>완료</span>'
        '<span><i style="background:' + pal["ring_a"] + '"></i>전체</span></div>'
    )


def insight_text():
    if cur["total"] == 0 and prev["total"] == 0:
        return f"{cur_name}에는 아직 등록된 일정이 없어요. 캘린더에서 일정을 추가해 보세요."

    subject = f"{cur_name}{eun_neun(cur_name)} {prev_name}보다"
    gap = abs(total_delta)

    if total_delta > 0:
        tail = "일정이 더 추가되었어요!" if mode == "month" else "일정을 더 추가했어요!"
        return f"{subject} {gap}개의 {tail}"

    if total_delta < 0:
        return f"{subject} 일정이 {gap}개 줄었어요."

    return f"{cur_name}의 일정 수는 {prev_name}과 같아요!"


# ==========================================
# 5. 상단: 제목 + 주간/월간 토글
# ==========================================

if mode == "month":
    page_title = "월간 통계"
    page_sub = (
        "이번 달의 일정을 한눈에 확인해보세요!" if is_current
        else f"{start.year}년 {start.month}월의 일정을 한눈에 확인해보세요!"
    )
else:
    page_title = "주간 통계"
    page_sub = (
        "이번 주 나의 일정을 한눈에 확인해보세요!" if is_current
        else "선택한 주의 일정을 한눈에 확인해보세요!"
    )

h_title, h_toggle = st.columns([5, 2.6], vertical_alignment="center")

with h_title:
    st.markdown(
        '<div class="stat-head">'
        '<div class="bars"><i style="height:22px"></i><i style="height:34px"></i><i style="height:48px"></i></div>'
        f'<div><div class="stat-h1">{page_title}</div><div class="stat-sub">{esc(page_sub)}</div></div>'
        '</div>',
        unsafe_allow_html=True
    )

with h_toggle:
    with st.container(key="stats_toggle"):
        t_week, t_month = st.columns(2)

        with t_week:
            st.button(
                "주간 통계", key="stats_tab_week",
                type="primary" if mode == "week" else "secondary",
                on_click=set_mode, args=("week",), use_container_width=True
            )

        with t_month:
            st.button(
                "월간 통계", key="stats_tab_month",
                type="primary" if mode == "month" else "secondary",
                on_click=set_mode, args=("month",), use_container_width=True
            )

st.write("")


# ==========================================
# 6. KPI 카드
# ==========================================

if mode == "month":
    k1, k2, k3, k4 = st.columns(4)

    with k1:
        st.markdown(
            kpi_card("📅", pal["tile1"], f"{cur_name} 일정 수", f'{cur["total"]}개', diff_html(total_delta)),
            unsafe_allow_html=True
        )

    with k2:
        st.markdown(
            kpi_card("✅", "#DDF5EA", "완료한 일정", f'{cur["done"]}개', diff_html(done_delta, good=True)),
            unsafe_allow_html=True
        )

    with k3:
        st.markdown(donut_card_month(), unsafe_allow_html=True)

    with k4:
        st.markdown(top_category_card(), unsafe_allow_html=True)
else:
    k1, k2, k3 = st.columns([1.3, 1, 1])

    with k1:
        st.markdown(donut_card_week(), unsafe_allow_html=True)

    with k2:
        st.markdown(
            kpi_card("📅", pal["tile1"], f"{cur_name} 일정 수", f'{cur["total"]}개', diff_html(total_delta)),
            unsafe_allow_html=True
        )

    with k3:
        st.markdown(
            kpi_card("✅", "#DDF5EA", "완료한 일정", f'{cur["done"]}개', diff_html(done_delta, good=True)),
            unsafe_allow_html=True
        )

st.write("")


# ==========================================
# 7. 본문: 일정 현황(달력/막대) + 카테고리 / 주요 일정
# ==========================================

if mode == "month":
    panel_title = f"{cur_name} 일정 현황"
    range_label = f"{start.year}년 {start.month}월"
else:
    panel_title = f"{cur_name} 일정 현황"
    range_label = f"{kr_date(start)} - {kr_date(end)}"

col_main, col_side = st.columns([5, 3.2])

with col_main:
    with st.container(key="stats_main_panel"):
        p_title, p_nav = st.columns([3, 3.2], vertical_alignment="center")

        with p_title:
            st.markdown(
                f'<div class="stat-title"><span class="stat-ic">📅</span>{esc(panel_title)}</div>',
                unsafe_allow_html=True
            )

        with p_nav:
            n_prev, n_label, n_next = st.columns([0.7, 3, 0.7], vertical_alignment="center")

            with n_prev:
                st.button("‹", key="stats_prev", on_click=shift_period, args=(-1,))

            with n_label:
                st.markdown(
                    f'<div class="stat-range">{esc(range_label)}</div>',
                    unsafe_allow_html=True
                )

            with n_next:
                st.button("›", key="stats_next", on_click=shift_period, args=(1,))

        st.markdown(
            month_calendar_html() if mode == "month" else week_chart_html(),
            unsafe_allow_html=True
        )

with col_side:
    if mode == "month":
        st.markdown(pie_card(), unsafe_allow_html=True)

        major = sorted(
            [e for e in cur_events if e["importance"] == "상"],
            key=lambda e: (e["date"], e["title"])
        )

        with st.container(key="stats_major"):
            m_title, m_more = st.columns([3, 1.4], vertical_alignment="center")

            with m_title:
                st.markdown(
                    f'<div class="stat-title"><span class="stat-ic">⭐</span>{esc(cur_name)} 주요 일정</div>',
                    unsafe_allow_html=True
                )

            with m_more:
                try:
                    st.page_link("pages/search.py", label="더보기 ›")
                except Exception:
                    pass

            if major:
                rows = [
                    '<div class="major-row">'
                    f'<span class="cat-dot" style="background:{cat_color(primary_cat(e))}"></span>'
                    f'<span class="major-date">{kr_date(date.fromisoformat(e["date"]))}</span>'
                    f'<span class="major-title">{esc(e["title"])}</span>'
                    '</div>'
                    for e in major[:MAJOR_SHOW]
                ]

                if len(major) > MAJOR_SHOW:
                    rows.append(f'<div class="stat-empty">외 {len(major) - MAJOR_SHOW}개</div>')

                st.markdown("".join(rows), unsafe_allow_html=True)
            else:
                st.markdown(
                    '<div class="stat-empty">중요도 ‘상’인 일정이 없어요.</div>',
                    unsafe_allow_html=True
                )
    else:
        st.markdown(category_card_week(), unsafe_allow_html=True)

st.write("")


# ==========================================
# 8. 하단 인사이트 배너
# ==========================================

st.markdown(
    '<div class="stat-banner">'
    f'<span>{"💡" if mode == "month" else "⭐"}</span>'
    f'<span>{esc(insight_text())}</span>'
    '<span class="deco">📅</span>'
    '</div>',
    unsafe_allow_html=True
)
