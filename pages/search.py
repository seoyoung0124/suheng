import re
from datetime import date

import streamlit as st

import theme

st.set_page_config(
    page_title="Daily Planner | Search",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

client, uid = theme.page_setup("search")

esc = theme.esc
today = theme.today_kst()

MAX_PER_GROUP = 30  # 한 번에 보여 줄 최대 결과 수 (다가오는 일정 / 지난 일정 각각)
STATUS_OPTIONS = ["전체", "진행 전", "완료"]


# ==========================================
# 1. 일정 불러오기
# ==========================================

# 현재 사용자에게 저장된 일정 데이터를 조회해 화면에서 사용할 형태로 정리한다.
def fetch_events(client, uid):
    rows = (
        client.table("events")
        .select("*")
        .eq("user_id", uid)
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
            "title": r.get("title") or "",
            "description": r.get("description") or "",
            "importance": (
                importance if importance in theme.IMPORTANCE_ORDER else "없음"
            ),
            "categories": [x for x in cats if x in theme.CATEGORIES],
            "done": bool(r.get("done"))
        })

    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return result


# ==========================================
# 2. 검색 / 표시 도우미
# ==========================================

# 검색어 토큰이 일정의 제목이나 설명 등에 포함되는지 확인한다.
def matches(event, tokens):
    """검색어를 공백으로 나눈 모든 단어가 제목·설명·카테고리 어딘가에 있으면 일치."""
    haystack = " ".join(
        [event["title"], event["description"], " ".join(event["categories"])]
    ).lower()

    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return all(token in haystack for token in tokens)


# 검색어가 포함된 부분을 강조 표시할 HTML 문자열로 만든다.
def highlight(text, tokens):
    """검색어와 일치하는 부분을 <mark>로 감싼다. (HTML은 모두 이스케이프)"""
    if not tokens:
        # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
        return esc(text)

    pattern = re.compile(
        "(" + "|".join(
            re.escape(t) for t in sorted(tokens, key=len, reverse=True)
        ) + ")",
        re.IGNORECASE
    )

    parts = pattern.split(text)

    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return "".join(
        f"<mark>{esc(part)}</mark>" if i % 2 == 1 else esc(part)
        # 목록의 항목을 하나씩 확인하며 필요한 처리를 반복한다.
        for i, part in enumerate(parts)
    )


# 일정의 완료 상태와 중요도에 맞는 색상을 반환한다.
def event_color(event):
    # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
    if event["done"]:
        # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
        return theme.DONE_COLOR
    # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
    if "개인일정" in event["categories"]:
        # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
        return theme.PERSONAL_COLOR
    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return theme.IMPORTANCE_COLOR[event["importance"]]


# 일정 날짜와 오늘 날짜의 차이를 D-day 형식으로 표시한다.
def d_label(day):
    diff = (day - today).days

    # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
    if diff == 0:
        # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
        return "오늘"
    # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
    if diff > 0:
        # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
        return f"D-{diff}"
    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return f"D+{-diff}"


# 일정 하나의 날짜, 제목, 설명 및 상태를 검색 결과로 표시한다.
def render_result(event, tokens):
    day = date.fromisoformat(event["date"])

    chips = []

    # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
    if event["importance"] != "없음":
        chips.append(f"중요도 {event['importance']}")

    chips += event["categories"]

    # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
    if event["done"]:
        chips.append("✅ 완료")

    chips_html = "".join(f'<span class="chip">{esc(c)}</span>' for c in chips)

    desc = event["description"]
    desc_html = (
        f'<div class="res-desc">{highlight(desc[:90] + ("…" if len(desc) > 90 else ""), tokens)}</div>'
        # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
        if desc else ""
    )

    title = event["title"] or "(제목 없음)"

    # 관련 화면 요소를 하나의 영역으로 묶는다.
    with st.container(key=f"res_{event['id']}"):
        c_info, c_plan, c_cal = st.columns([6, 1.4, 1.4], vertical_alignment="center")

        with c_info:
            # 화면에 입력 요소 또는 안내 내용을 표시한다.
            st.markdown(
                '<div class="res-top">'
                f'<span class="up-dot" style="background:{event_color(event)}"></span>'
                f'<span class="res-title">{highlight(title, tokens)}</span>'
                f'<span class="res-date">{day.year}.{day.month:02d}.{day.day:02d} '
                f'({theme.WEEKDAYS_KR[day.weekday()]}) · {d_label(day)}</span>'
                '</div>'
                f'{desc_html}'
                f'<div class="res-chips">{chips_html}</div>',
                unsafe_allow_html=True
            )

        with c_plan:
            # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
            if st.button(
                "플래너", key=f"go_plan_{event['id']}",
                icon=":material/task_alt:", use_container_width=True
            ):
                st.session_state.planner_picker = day
                st.switch_page("pages/list.py")

        with c_cal:
            # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
            if st.button(
                "캘린더", key=f"go_cal_{event['id']}",
                icon=":material/calendar_month:", use_container_width=True
            ):
                st.session_state.cal_start_date = day.replace(day=1).isoformat()
                st.session_state.cal_ver = st.session_state.get("cal_ver", 0) + 1
                st.session_state.view_event_id = event["id"]
                st.switch_page("main.py")


# 여러 일정을 하나의 그룹으로 묶어 검색 결과에 표시한다.
def render_group(title, items, tokens):
    # 화면에 입력 요소 또는 안내 내용을 표시한다.
    st.markdown(
        f'<div class="section-title">{esc(title)} '
        f'<span class="muted">({len(items)})</span></div>',
        unsafe_allow_html=True
    )

    # 목록의 항목을 하나씩 확인하며 필요한 처리를 반복한다.
    for event in items[:MAX_PER_GROUP]:
        render_result(event, tokens)

    # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
    if len(items) > MAX_PER_GROUP:
        # 화면에 입력 요소 또는 안내 내용을 표시한다.
        st.caption(
            f"{len(items)}개 중 {MAX_PER_GROUP}개만 보여 드려요. 검색어를 더 구체적으로 입력해 보세요."
        )


# ==========================================
# 3. 검색창 / 필터
# ==========================================

# 화면에 입력 요소 또는 안내 내용을 표시한다.
st.markdown('<div class="page-title">Search</div>', unsafe_allow_html=True)
# 화면에 입력 요소 또는 안내 내용을 표시한다.
st.caption("제목, 설명, 카테고리로 일정을 찾아요. 여러 단어를 띄어 쓰면 모두 포함된 일정만 나와요.")

query = st.text_input(
    "검색", key="search_q",
    placeholder="예: 수학 시험",
    label_visibility="collapsed"
)

f_cat, f_status = st.columns([3, 2], vertical_alignment="bottom")

with f_cat:
    chosen_cats = st.multiselect(
        "카테고리", theme.CATEGORIES, key="search_cats",
        placeholder="카테고리 선택 (선택 안 하면 전체)"
    )

with f_status:
    status = st.radio(
        "상태", STATUS_OPTIONS, key="search_status", horizontal=True
    )


# ==========================================
# 4. 결과
# ==========================================

# 오류가 발생할 수 있는 작업을 실행하고 예외 상황에 대비한다.
try:
    events = fetch_events(client, uid)
# 앞선 작업에서 오류가 발생했을 때 예외 처리를 수행한다.
except Exception as exc:
    st.error(f"일정을 불러오지 못했습니다: {exc}")
    st.info("Supabase events 테이블과 done 컬럼을 확인해 주세요. (schema.sql 실행)")
    # 현재 실행을 중단해 이후 화면 처리가 진행되지 않도록 한다.
    st.stop()

tokens = [t.lower() for t in (query or "").split() if t.strip()]
has_filter = bool(tokens) or bool(chosen_cats) or status != "전체"

# 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
if not events:
    # 화면에 입력 요소 또는 안내 내용을 표시한다.
    st.markdown(
        '<div class="up-empty">등록된 일정이 없어요. 캘린더에서 일정을 추가해 보세요.</div>',
        unsafe_allow_html=True
    )
    # 현재 실행을 중단해 이후 화면 처리가 진행되지 않도록 한다.
    st.stop()

# 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
if not has_filter:
    # 화면에 입력 요소 또는 안내 내용을 표시한다.
    st.markdown(
        '<div class="up-empty">검색어를 입력하거나 필터를 골라 보세요.<br>'
        f'<small>등록된 일정은 모두 {len(events)}개예요.</small></div>',
        unsafe_allow_html=True
    )
    # 현재 실행을 중단해 이후 화면 처리가 진행되지 않도록 한다.
    st.stop()

found = [
    e for e in events
    # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
    if matches(e, tokens)
    and (not chosen_cats or any(c in e["categories"] for c in chosen_cats))
    and (
        status == "전체"
        or (status == "완료" and e["done"])
        or (status == "진행 전" and not e["done"])
    )
]

# 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
if not found:
    shown = esc(query.strip()) if tokens else "선택한 조건"
    # 화면에 입력 요소 또는 안내 내용을 표시한다.
    st.markdown(
        f'<div class="up-empty">‘{shown}’에 맞는 일정이 없어요.</div>',
        unsafe_allow_html=True
    )
    # 현재 실행을 중단해 이후 화면 처리가 진행되지 않도록 한다.
    st.stop()

# 화면에 입력 요소 또는 안내 내용을 표시한다.
st.markdown(
    f'<div class="res-count">검색 결과 {len(found)}개</div>',
    unsafe_allow_html=True
)

today_str = today.isoformat()

# 다가오는 일정은 가까운 날짜부터, 지난 일정은 최근 날짜부터
upcoming = sorted(
    [e for e in found if e["date"] >= today_str],
    key=lambda e: (e["date"], theme.IMPORTANCE_ORDER[e["importance"]])
)
past = sorted(
    [e for e in found if e["date"] < today_str],
    key=lambda e: e["date"], reverse=True
)

# 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
if upcoming:
    render_group("오늘 · 다가오는 일정", upcoming, tokens)

# 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
if past:
    render_group("지난 일정", past, tokens)
