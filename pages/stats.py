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

# 기준 날짜에서 지정한 개월 수만큼 이동한 날짜를 계산한다.
def add_months(d, n):
    index = d.year * 12 + (d.month - 1) + n
    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return date(index // 12, index % 12 + 1, 1)


# 기준 월의 첫날과 마지막 날을 구한다.
def month_bounds(anchor):
    start = anchor.replace(day=1)
    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return start, add_months(start, 1) - timedelta(days=1)


# 기준 날짜가 포함된 주의 시작일과 마지막 날을 구한다.
def week_bounds(anchor):
    start = anchor - timedelta(days=anchor.weekday())
    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return start, start + timedelta(days=6)


# 날짜를 월·일과 한국어 요일 형식으로 바꾼다.
def kr_date(d):
    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return f"{d.month}월 {d.day}일 ({WD[d.weekday()]})"


# 한글 단어 마지막 글자에 받침이 있는지 판별한다.
def has_batchim(word):
    ch = str(word).strip()[-1:]
    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return bool(ch) and "가" <= ch <= "힣" and (ord(ch) - 0xAC00) % 28 != 0


# 받침 여부에 따라 자연스러운 조사 은 또는 는을 반환한다.
def eun_neun(word):
    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return "은" if has_batchim(word) else "는"


# 카테고리에 지정된 색상을 반환한다.
def cat_color(name):
    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return CAT_COLOR.get(name, "#CFD2E0")


# 일정에 지정된 첫 번째 카테고리를 대표 카테고리로 반환한다.
def primary_cat(event):
    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return event["categories"][0] if event["categories"] else "미분류"


# ==========================================
# 2. 일정 불러오기 / 통계 계산
# ==========================================

# 현재 사용자에게 저장된 일정 데이터를 조회해 화면에서 사용할 형태로 정리한다.
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

    # 목록의 항목을 하나씩 확인하며 필요한 처리를 반복한다.
    for r in rows:
        # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
        if not r.get("event_date"):
            continue

        cats = r.get("categories") or []

        # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
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

    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return result


# 일정 개수, 완료 수, 완료율 및 카테고리별 개수를 계산한다.
def summarize(items):
    total = len(items)
    done = sum(1 for e in items if e["done"])
    rate = done / total * 100 if total else 0.0

    counts = {}

    # 목록의 항목을 하나씩 확인하며 필요한 처리를 반복한다.
    for e in items:
        # 목록의 항목을 하나씩 확인하며 필요한 처리를 반복한다.
        for c in (e["categories"] or ["미분류"]):
            counts[c] = counts.get(c, 0) + 1

    cats = sorted(counts.items(), key=lambda kv: (-kv[1], CAT_ORDER.get(kv[0], 99)))

    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return {
        "total": total,
        "done": done,
        "rate": rate,
        "cats": cats,
        "tags": sum(counts.values()),
    }


# 일정 목록을 날짜별로 묶어 딕셔너리로 반환한다.
def group_by_date(items):
    by_date = {}

    # 목록의 항목을 하나씩 확인하며 필요한 처리를 반복한다.
    for e in items:
        by_date.setdefault(e["date"], []).append(e)

    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return by_date


# ==========================================
# 3. 상태 (주간/월간, 기간 이동)
# ==========================================

# 페이지가 다시 실행되어도 필요한 값을 유지하도록 세션 상태를 갱신한다.
st.session_state.setdefault("stats_mode", "week")
# 페이지가 다시 실행되어도 필요한 값을 유지하도록 세션 상태를 갱신한다.
st.session_state.setdefault("stats_anchor", today)


# 통계 화면을 주간 또는 월간 모드로 바꾸고 기준 날짜를 오늘로 설정한다.
def set_mode(mode):
    st.session_state.stats_mode = mode
    st.session_state.stats_anchor = theme.today_kst()


# 현재 통계 모드에 맞춰 이전 기간 또는 다음 기간으로 이동한다.
def shift_period(delta):
    anchor = st.session_state.stats_anchor

    # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
    if st.session_state.stats_mode == "month":
        st.session_state.stats_anchor = add_months(anchor, delta)
    # 앞의 조건에 해당하지 않을 때 실행할 작업을 처리한다.
    else:
        st.session_state.stats_anchor = anchor + timedelta(days=7 * delta)


mode = st.session_state.stats_mode if st.session_state.stats_mode in ("week", "month") else "week"
anchor = st.session_state.stats_anchor

# 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
if not isinstance(anchor, date):
    anchor = today

# 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
if mode == "month":
    start, end = month_bounds(anchor)
    prev_start, prev_end = month_bounds(add_months(start, -1))
# 앞의 조건에 해당하지 않을 때 실행할 작업을 처리한다.
else:
    start, end = week_bounds(anchor)
    prev_start, prev_end = start - timedelta(days=7), start - timedelta(days=1)

is_current = start <= today <= end

# 오류가 발생할 수 있는 작업을 실행하고 예외 상황에 대비한다.
try:
    all_events = fetch_events(client, uid, prev_start, end)
# 앞선 작업에서 오류가 발생했을 때 예외 처리를 수행한다.
except Exception as exc:
    st.error(f"일정을 불러오지 못했습니다: {exc}")
    st.info("Supabase events 테이블과 done 컬럼을 확인해 주세요. (schema.sql 실행)")
    # 현재 실행을 중단해 이후 화면 처리가 진행되지 않도록 한다.
    st.stop()

cur_events = [e for e in all_events if start.isoformat() <= e["date"] <= end.isoformat()]
prev_events = [e for e in all_events if prev_start.isoformat() <= e["date"] <= prev_end.isoformat()]

cur = summarize(cur_events)
prev = summarize(prev_events)
by_date = group_by_date(cur_events)

total_delta = cur["total"] - prev["total"]
done_delta = cur["done"] - prev["done"]

# 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
if mode == "month":
    cur_name = "이번 달" if is_current else f"{start.month}월"
    prev_name = "지난달" if is_current else f"{prev_start.month}월"
# 앞의 조건에 해당하지 않을 때 실행할 작업을 처리한다.
else:
    cur_name = "이번 주" if is_current else "이 주"
    prev_name = "지난주" if is_current else "그 전주"


# ==========================================
# 4. HTML 조각 (카드, 도넛, 파이, 막대, 달력)
# ==========================================

# 현재 기간과 이전 기간의 수치 차이를 나타내는 HTML을 만든다.
def diff_html(delta, good=False):
    # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
    if delta > 0:
        css = "diff-good" if good else "diff-up"
        # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
        return f'<span class="kpi-diff {css}">▲ +{delta}개</span>'

    # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
    if delta < 0:
        # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
        return f'<span class="kpi-diff diff-down">▼ {delta}개</span>'

    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return '<span class="kpi-diff diff-flat">－ 변동 없음</span>'


# 아이콘과 제목, 수치로 구성된 통계 요약 카드를 만든다.
def kpi_card(icon, icon_bg, label, value, extra=""):
    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return (
        '<div class="stat-card kpi">'
        f'<div class="kpi-ic" style="background:{icon_bg}">{icon}</div>'
        f'<div><div class="kpi-label">{esc(label)}</div>'
        f'<div class="kpi-val">{value}{extra}</div></div>'
        '</div>'
    )


# 완료율에 맞춰 도넛 그래프의 색상 비율을 CSS로 만든다.
def donut_style(rate):
    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return (
        f"background:conic-gradient({pal['accent']} 0 {rate:.2f}%, "
        f"{pal['rail']} {rate:.2f}% 100%)"
    )


# 월간 일정 완료율을 도넛 그래프 카드로 구성한다.
def donut_card_month():
    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return (
        '<div class="stat-card kpi">'
        f'<div class="donut sm" style="{donut_style(cur["rate"])}"></div>'
        '<div><div class="kpi-label">일정 완료율</div>'
        f'<div class="kpi-val">{cur["rate"]:.1f}%</div>'
        f'<div class="kpi-note">({cur["done"]} / {cur["total"]})</div></div>'
        '</div>'
    )


# 주간 일정 완료율을 도넛 그래프 카드로 구성한다.
def donut_card_week():
    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return (
        '<div class="stat-card kpi">'
        f'<div class="donut" style="{donut_style(cur["rate"])}">'
        f'<span>{cur["rate"]:.1f}%</span></div>'
        '<div><div class="kpi-label big">일정 완료율</div>'
        f'<div class="kpi-note big">완료 {cur["done"]}개 / 전체 {cur["total"]}개</div></div>'
        '</div>'
    )


# 현재 기간에 가장 많이 등록된 카테고리를 카드로 표시한다.
def top_category_card():
    # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
    if cur["cats"]:
        name, count = cur["cats"][0]
        pct = round(count / cur["tags"] * 100)
        value = (
            f'<span style="font-size:1.55rem">{esc(name)}</span>'
            f'<span class="kpi-note"> ({pct}%)</span>'
        )
    # 앞의 조건에 해당하지 않을 때 실행할 작업을 처리한다.
    else:
        value = '<span class="kpi-note">-</span>'

    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return kpi_card("⭐", "#FFF0DD", "가장 많은 카테고리", value)


# 카테고리별 일정 비율을 파이 차트와 목록으로 표시한다.
def pie_card():
    # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
    if cur["cats"]:
        stops, acc = [], 0.0

        # 목록의 항목을 하나씩 확인하며 필요한 처리를 반복한다.
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
    # 앞의 조건에 해당하지 않을 때 실행할 작업을 처리한다.
    else:
        body = '<div class="stat-empty">아직 분류된 일정이 없어요.</div>'

    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return (
        '<div class="stat-card">'
        '<div class="stat-title"><span class="stat-ic">🥧</span>카테고리별 현황</div>'
        f'{body}</div>'
    )


# 카테고리별 일정 수와 비율을 목록 HTML로 만든다.
def cat_rows_html():
    rows = []

    # 목록의 항목을 하나씩 확인하며 필요한 처리를 반복한다.
    for name, count in cur["cats"]:
        pct = round(count / cur["tags"] * 100)
        rows.append(
            '<div class="cat-row">'
            f'<span class="cat-dot" style="background:{cat_color(name)}"></span>'
            f'<span class="cat-name">{esc(name)}</span>'
            f'<span class="cat-val">{count}개 ({pct}%)</span>'
            '</div>'
        )

    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return "".join(rows)


# 주간 카테고리별 일정 현황과 간단한 안내 문구를 표시한다.
def category_card_week():
    # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
    if cur["cats"]:
        name = cur["cats"][0][0]
        tip = (
            "분류하지 않은 일정이 가장 많아요!"
            # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
            if name == "미분류"
            else f"{cur_name}에는 {esc(name)} 일정이 가장 많아요!"
        )
        body = f'<div class="cat-list">{cat_rows_html()}</div><div class="stat-tip">💡 {tip}</div>'
    # 앞의 조건에 해당하지 않을 때 실행할 작업을 처리한다.
    else:
        body = '<div class="stat-empty">아직 분류된 일정이 없어요.</div>'

    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return (
        '<div class="stat-card">'
        '<div class="stat-title"><span class="stat-ic">🥧</span>카테고리별 현황</div>'
        f'{body}</div>'
    )


# 월간 날짜별 일정 유무와 카테고리 색상을 달력 HTML로 만든다.
def month_calendar_html():
    weeks = pycal.Calendar(firstweekday=0).monthdayscalendar(start.year, start.month)

    head = "".join(f'<div class="mc-h">{name}</div>' for name in WD)
    cells = []

    # 목록의 항목을 하나씩 확인하며 필요한 처리를 반복한다.
    for week in weeks:
        # 목록의 항목을 하나씩 확인하며 필요한 처리를 반복한다.
        for number in week:
            # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
            if number == 0:
                cells.append('<div class="mc-d empty"></div>')
                continue

            d = date(start.year, start.month, number)
            events = by_date.get(d.isoformat(), [])

            style, dots = "", ""

            # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
            if events:
                style = f' style="background:{cat_color(primary_cat(events[0]))}33"'
                dots = '<div class="mc-dots">' + "".join(
                    f'<i style="background:{cat_color(primary_cat(e))}"></i>'
                    # 목록의 항목을 하나씩 확인하며 필요한 처리를 반복한다.
                    for e in events[:3]
                ) + "</div>"

            css = "mc-d today" if d == today else "mc-d"
            cells.append(f'<div class="{css}"{style}><span>{number}</span>{dots}</div>')

    legend = "".join(
        f'<span><i style="background:{cat_color(name)}"></i>{esc(name)}</span>'
        # 목록의 항목을 하나씩 확인하며 필요한 처리를 반복한다.
        for name, _ in cur["cats"]
    )

    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return (
        f'<div class="mini-cal">{head}{"".join(cells)}</div>'
        f'<div class="legend">{legend}</div>'
    )


# 요일별 전체 일정 수와 완료 수를 막대그래프로 표현한다.
def week_chart_html():
    days = [start + timedelta(days=i) for i in range(7)]
    counts = [len(by_date.get(d.isoformat(), [])) for d in days]
    dones = [sum(1 for e in by_date.get(d.isoformat(), []) if e["done"]) for d in days]

    top = max(counts) if counts else 0
    step = 1 if top <= 4 else math.ceil(top / 4)
    ymax = step * 4

    lines = "".join(
        f'<div class="bc-line" style="bottom:{t / ymax * 100:.2f}%"><span>{t}</span></div>'
        # 목록의 항목을 하나씩 확인하며 필요한 처리를 반복한다.
        for t in range(0, ymax + 1, step)
    )

    cols, labels = [], []

    # 목록의 항목을 하나씩 확인하며 필요한 처리를 반복한다.
    for d, count, done in zip(days, counts, dones):
        bar = ""

        # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
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

    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return (
        '<div class="bc">'
        f'<div class="bc-plot">{lines}<div class="bc-cols">{"".join(cols)}</div></div>'
        f'<div class="bc-labels">{"".join(labels)}</div>'
        '</div>'
        '<div class="legend"><span><i style="background:' + pal["accent"] + '"></i>완료</span>'
        '<span><i style="background:' + pal["ring_a"] + '"></i>전체</span></div>'
    )


# 현재 기간과 이전 기간의 일정 수를 비교해 요약 문구를 만든다.
def insight_text():
    # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
    if cur["total"] == 0 and prev["total"] == 0:
        # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
        return f"{cur_name}에는 아직 등록된 일정이 없어요. 캘린더에서 일정을 추가해 보세요."

    subject = f"{cur_name}{eun_neun(cur_name)} {prev_name}보다"
    gap = abs(total_delta)

    # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
    if total_delta > 0:
        tail = "일정이 더 추가되었어요!" if mode == "month" else "일정을 더 추가했어요!"
        # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
        return f"{subject} {gap}개의 {tail}"

    # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
    if total_delta < 0:
        # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
        return f"{subject} 일정이 {gap}개 줄었어요."

    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return f"{cur_name}의 일정 수는 {prev_name}과 같아요!"


# ==========================================
# 5. 상단: 제목 + 주간/월간 토글
# ==========================================

# 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
if mode == "month":
    page_title = "월간 통계"
    page_sub = (
        "이번 달의 일정을 한눈에 확인해보세요!" if is_current
        else f"{start.year}년 {start.month}월의 일정을 한눈에 확인해보세요!"
    )
# 앞의 조건에 해당하지 않을 때 실행할 작업을 처리한다.
else:
    page_title = "주간 통계"
    page_sub = (
        "이번 주 나의 일정을 한눈에 확인해보세요!" if is_current
        else "선택한 주의 일정을 한눈에 확인해보세요!"
    )

h_title, h_toggle = st.columns([5, 2.6], vertical_alignment="center")

with h_title:
    # 화면에 입력 요소 또는 안내 내용을 표시한다.
    st.markdown(
        '<div class="stat-head">'
        '<div class="bars"><i style="height:22px"></i><i style="height:34px"></i><i style="height:48px"></i></div>'
        f'<div><div class="stat-h1">{page_title}</div><div class="stat-sub">{esc(page_sub)}</div></div>'
        '</div>',
        unsafe_allow_html=True
    )

with h_toggle:
    # 관련 화면 요소를 하나의 영역으로 묶는다.
    with st.container(key="stats_toggle"):
        t_week, t_month = st.columns(2)

        with t_week:
            # 화면에 입력 요소 또는 안내 내용을 표시한다.
            st.button(
                "주간 통계", key="stats_tab_week",
                type="primary" if mode == "week" else "secondary",
                on_click=set_mode, args=("week",), use_container_width=True
            )

        with t_month:
            # 화면에 입력 요소 또는 안내 내용을 표시한다.
            st.button(
                "월간 통계", key="stats_tab_month",
                type="primary" if mode == "month" else "secondary",
                on_click=set_mode, args=("month",), use_container_width=True
            )

# 화면에 입력 요소 또는 안내 내용을 표시한다.
st.write("")


# ==========================================
# 6. KPI 카드
# ==========================================

# 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
if mode == "month":
    k1, k2, k3, k4 = st.columns(4)

    with k1:
        # 화면에 입력 요소 또는 안내 내용을 표시한다.
        st.markdown(
            kpi_card("📅", pal["tile1"], f"{cur_name} 일정 수", f'{cur["total"]}개', diff_html(total_delta)),
            unsafe_allow_html=True
        )

    with k2:
        # 화면에 입력 요소 또는 안내 내용을 표시한다.
        st.markdown(
            kpi_card("✅", "#DDF5EA", "완료한 일정", f'{cur["done"]}개', diff_html(done_delta, good=True)),
            unsafe_allow_html=True
        )

    with k3:
        # 화면에 입력 요소 또는 안내 내용을 표시한다.
        st.markdown(donut_card_month(), unsafe_allow_html=True)

    with k4:
        # 화면에 입력 요소 또는 안내 내용을 표시한다.
        st.markdown(top_category_card(), unsafe_allow_html=True)
# 앞의 조건에 해당하지 않을 때 실행할 작업을 처리한다.
else:
    k1, k2, k3 = st.columns([1.3, 1, 1])

    with k1:
        # 화면에 입력 요소 또는 안내 내용을 표시한다.
        st.markdown(donut_card_week(), unsafe_allow_html=True)

    with k2:
        # 화면에 입력 요소 또는 안내 내용을 표시한다.
        st.markdown(
            kpi_card("📅", pal["tile1"], f"{cur_name} 일정 수", f'{cur["total"]}개', diff_html(total_delta)),
            unsafe_allow_html=True
        )

    with k3:
        # 화면에 입력 요소 또는 안내 내용을 표시한다.
        st.markdown(
            kpi_card("✅", "#DDF5EA", "완료한 일정", f'{cur["done"]}개', diff_html(done_delta, good=True)),
            unsafe_allow_html=True
        )

# 화면에 입력 요소 또는 안내 내용을 표시한다.
st.write("")


# ==========================================
# 7. 본문: 일정 현황(달력/막대) + 카테고리 / 주요 일정
# ==========================================

# 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
if mode == "month":
    panel_title = f"{cur_name} 일정 현황"
    range_label = f"{start.year}년 {start.month}월"
# 앞의 조건에 해당하지 않을 때 실행할 작업을 처리한다.
else:
    panel_title = f"{cur_name} 일정 현황"
    range_label = f"{kr_date(start)} - {kr_date(end)}"

col_main, col_side = st.columns([5, 3.2])

with col_main:
    # 관련 화면 요소를 하나의 영역으로 묶는다.
    with st.container(key="stats_main_panel"):
        p_title, p_nav = st.columns([3, 3.2], vertical_alignment="center")

        with p_title:
            # 화면에 입력 요소 또는 안내 내용을 표시한다.
            st.markdown(
                f'<div class="stat-title"><span class="stat-ic">📅</span>{esc(panel_title)}</div>',
                unsafe_allow_html=True
            )

        with p_nav:
            n_prev, n_label, n_next = st.columns([0.7, 3, 0.7], vertical_alignment="center")

            with n_prev:
                # 화면에 입력 요소 또는 안내 내용을 표시한다.
                st.button("‹", key="stats_prev", on_click=shift_period, args=(-1,))

            with n_label:
                # 화면에 입력 요소 또는 안내 내용을 표시한다.
                st.markdown(
                    f'<div class="stat-range">{esc(range_label)}</div>',
                    unsafe_allow_html=True
                )

            with n_next:
                # 화면에 입력 요소 또는 안내 내용을 표시한다.
                st.button("›", key="stats_next", on_click=shift_period, args=(1,))

        # 화면에 입력 요소 또는 안내 내용을 표시한다.
        st.markdown(
            month_calendar_html() if mode == "month" else week_chart_html(),
            unsafe_allow_html=True
        )

with col_side:
    # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
    if mode == "month":
        # 화면에 입력 요소 또는 안내 내용을 표시한다.
        st.markdown(pie_card(), unsafe_allow_html=True)

        major = sorted(
            [e for e in cur_events if e["importance"] == "상"],
            key=lambda e: (e["date"], e["title"])
        )

        # 관련 화면 요소를 하나의 영역으로 묶는다.
        with st.container(key="stats_major"):
            m_title, m_more = st.columns([3, 1.4], vertical_alignment="center")

            with m_title:
                # 화면에 입력 요소 또는 안내 내용을 표시한다.
                st.markdown(
                    f'<div class="stat-title"><span class="stat-ic">⭐</span>{esc(cur_name)} 주요 일정</div>',
                    unsafe_allow_html=True
                )

            with m_more:
                # 오류가 발생할 수 있는 작업을 실행하고 예외 상황에 대비한다.
                try:
                    # 화면에 입력 요소 또는 안내 내용을 표시한다.
                    st.page_link("pages/search.py", label="더보기 ›")
                # 앞선 작업에서 오류가 발생했을 때 예외 처리를 수행한다.
                except Exception:
                    pass

            # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
            if major:
                rows = [
                    '<div class="major-row">'
                    f'<span class="cat-dot" style="background:{cat_color(primary_cat(e))}"></span>'
                    f'<span class="major-date">{kr_date(date.fromisoformat(e["date"]))}</span>'
                    f'<span class="major-title">{esc(e["title"])}</span>'
                    '</div>'
                    # 목록의 항목을 하나씩 확인하며 필요한 처리를 반복한다.
                    for e in major[:MAJOR_SHOW]
                ]

                # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
                if len(major) > MAJOR_SHOW:
                    rows.append(f'<div class="stat-empty">외 {len(major) - MAJOR_SHOW}개</div>')

                # 화면에 입력 요소 또는 안내 내용을 표시한다.
                st.markdown("".join(rows), unsafe_allow_html=True)
            # 앞의 조건에 해당하지 않을 때 실행할 작업을 처리한다.
            else:
                # 화면에 입력 요소 또는 안내 내용을 표시한다.
                st.markdown(
                    '<div class="stat-empty">중요도 ‘상’인 일정이 없어요.</div>',
                    unsafe_allow_html=True
                )
    # 앞의 조건에 해당하지 않을 때 실행할 작업을 처리한다.
    else:
        # 화면에 입력 요소 또는 안내 내용을 표시한다.
        st.markdown(category_card_week(), unsafe_allow_html=True)

# 화면에 입력 요소 또는 안내 내용을 표시한다.
st.write("")


# ==========================================
# 8. 하단 인사이트 배너
# ==========================================

# 화면에 입력 요소 또는 안내 내용을 표시한다.
st.markdown(
    '<div class="stat-banner">'
    f'<span>{"💡" if mode == "month" else "⭐"}</span>'
    f'<span>{esc(insight_text())}</span>'
    '<span class="deco">📅</span>'
    '</div>',
    unsafe_allow_html=True
)
