from datetime import timedelta

import streamlit as st

import theme

st.set_page_config(
    page_title="하루결 | My Planner",
    page_icon="📒",
    layout="wide"
)

client, uid = theme.page_setup("planner")

esc = theme.esc
ORDER = theme.IMPORTANCE_ORDER
today = theme.today_kst()


# ==========================================
# 1. 일정 불러오기 / 완료 상태 저장
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
            "importance": importance if importance in ORDER else "없음",
            "categories": [x for x in cats if x in theme.CATEGORIES],
            "done": bool(r.get("done"))
        })

    # 중요한 일정이 위. 완료 여부로는 정렬하지 않아서 체크해도 줄이 움직이지 않는다
    result.sort(key=lambda e: (ORDER[e["importance"]], e["title"]))
    return result


def fetch_week_counts(client, uid, start, end):
    rows = (
        client.table("events")
        .select("event_date,done")
        .eq("user_id", uid)
        .gte("event_date", start.isoformat())
        .lte("event_date", end.isoformat())
        .execute()
        .data or []
    )

    counts = {}

    for r in rows:
        key = str(r["event_date"])[:10]
        total, done = counts.get(key, (0, 0))
        counts[key] = (total + 1, done + (1 if r.get("done") else 0))

    return counts


def toggle_done(event_id, new_value):
    try:
        st.session_state.supabase_client.table("events").update(
            {"done": new_value}
        ).eq("id", event_id).eq(
            "user_id", st.session_state.user_id
        ).execute()
    except Exception as exc:
        st.toast(f"완료 상태를 저장하지 못했습니다: {exc}")


# ==========================================
# 2. 날짜 이동 (화살표 / 날짜 선택 / 주간 보기)
# ==========================================

if "planner_picker" not in st.session_state:
    st.session_state.planner_picker = today

st.session_state.setdefault("show_week", False)


def shift_day(delta):
    st.session_state.planner_picker += timedelta(days=delta)


def go_today():
    st.session_state.planner_picker = theme.today_kst()


def pick_day(day):
    st.session_state.planner_picker = day


def toggle_week():
    st.session_state.show_week = not st.session_state.show_week


# ==========================================
# 3. 상단: 날짜 선택 / 날짜 표시 / 주간 보기 버튼
# ==========================================

h_pick, h_date, h_week = st.columns([1.7, 5, 1.8], vertical_alignment="center")

with h_pick:
    day = st.date_input(
        "날짜 선택", key="planner_picker",
        format="YYYY-MM-DD", label_visibility="collapsed"
    )

week_start = day - timedelta(days=day.weekday())
week_end = week_start + timedelta(days=6)
same_week = week_start <= today <= week_end

with h_date:
    st.markdown(
        '<div class="date-head"><span class="line"></span>'
        f'<span class="date-chip">🗓 {theme.WEEKDAYS_EN[day.weekday()]}, '
        f'{theme.MONTHS_EN[day.month - 1]} {day.day}</span>'
        '<span class="line"></span></div>',
        unsafe_allow_html=True
    )

with h_week:
    if st.session_state.show_week:
        week_label = "주간 보기 닫기"
    else:
        week_label = "이번 주 보기" if same_week else "이 주 보기"

    st.button(
        week_label, key="week_toggle", icon=":material/bar_chart:",
        on_click=toggle_week, use_container_width=True
    )


# ==========================================
# 4. 플래너 카드 (가운데) + 전날 / 다음날 화살표 (양 옆)
# ==========================================

try:
    day_events = fetch_day_events(client, uid, day)
except Exception as exc:
    st.error(f"일정을 불러오지 못했습니다: {exc}")
    st.info("Supabase events 테이블에 done 컬럼이 있는지 확인해 주세요. (schema.sql 실행)")
    st.stop()

total = len(day_events)
done_count = sum(e["done"] for e in day_events)
important = sum(e["importance"] == "상" for e in day_events)
remaining = total - done_count
percent = round(done_count / total * 100) if total else 0

_, c_prev, c_mid, c_next, _ = st.columns(
    [2, 0.8, 4.8, 0.8, 2], vertical_alignment="center"
)

with c_prev:
    st.button("‹", key="prev_day", on_click=shift_day, args=(-1,), help="전날")

with c_next:
    st.button("›", key="next_day", on_click=shift_day, args=(1,), help="다음날")

with c_mid:
    card_title = "오늘의 할 일" if day == today else f"{day.month}월 {day.day}일의 할 일"

    with st.container(key="planner_card"):
        st.markdown(
            '<div class="rings">' + "<i></i>" * 7 + "</div>",
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="card-head">'
            f'<div class="card-title">{esc(card_title)}</div>'
            f'<div class="card-count">{done_count} / {total} 완료</div>'
            '</div>'
            f'<div class="pbar"><div style="width:{percent}%"></div></div>',
            unsafe_allow_html=True
        )

        if not day_events:
            st.markdown(
                '<div class="planner-empty">이 날은 등록된 할 일이 없어요.<br>'
                '<small>캘린더에서 일정을 추가해 보세요.</small></div>',
                unsafe_allow_html=True
            )

        for e in day_events:
            kind = "done" if e["done"] else "todo"

            with st.container(key=f"item_{kind}_{e['id']}"):
                st.button(
                    f"~~{e['title']}~~" if e["done"] else e["title"],
                    key=f"tgl_{e['id']}",
                    icon=(
                        ":material/check_circle:"
                        if e["done"]
                        else ":material/radio_button_unchecked:"
                    ),
                    on_click=toggle_done,
                    args=(e["id"], not e["done"]),
                    use_container_width=True
                )

                info = []

                if e["importance"] != "없음":
                    info.append(f"중요도 {e['importance']}")

                info += e["categories"]

                lines = []

                if info:
                    lines.append(esc(" · ".join(info)))

                if e["description"]:
                    lines.append(esc(e["description"]))

                if lines:
                    st.markdown(
                        f'<div class="item-meta">{"<br>".join(lines)}</div>',
                        unsafe_allow_html=True
                    )

        pal = theme.palette()

        st.markdown(
            '<div class="tiles">'
            f'<div class="tile" style="background:{pal["tile1"]};color:{pal["tile1_text"]}">'
            '<div class="t">☆ 중요 일정</div>'
            f'<div class="n">{important}</div></div>'
            f'<div class="tile" style="background:{pal["tile2"]};color:{pal["tile2_text"]}">'
            '<div class="t">📅 남은 일정</div>'
            f'<div class="n">{remaining}</div></div>'
            '</div>',
            unsafe_allow_html=True
        )

    if day != today:
        st.write("")
        st.button(
            "오늘로 돌아가기", key="go_today", on_click=go_today,
            icon=":material/today:", use_container_width=True
        )


# ==========================================
# 5. 주간 보기
# ==========================================

if st.session_state.show_week:
    try:
        counts = fetch_week_counts(client, uid, week_start, week_end)
    except Exception as exc:
        counts = {}
        st.warning(f"주간 일정을 불러오지 못했습니다: {exc}")

    st.write("")

    _, w_mid, _ = st.columns([1, 8, 1])

    with w_mid:
        with st.container(key="week_panel"):
            st.markdown(
                '<div class="panel-title"><i></i>'
                f'{week_start.month}월 {week_start.day}일 ~ '
                f'{week_end.month}월 {week_end.day}일</div>',
                unsafe_allow_html=True
            )

            cols = st.columns(7)

            for i, col in enumerate(cols):
                d = week_start + timedelta(days=i)
                t, dn = counts.get(d.isoformat(), (0, 0))

                with col:
                    st.button(
                        f"{theme.WEEKDAYS_KR[i]} {d.day}",
                        key=f"week_{d.isoformat()}",
                        type="primary" if d == day else "secondary",
                        on_click=pick_day, args=(d,),
                        use_container_width=True
                    )
                    st.markdown(
                        f'<div class="week-note">{f"{dn}/{t} 완료" if t else "일정 없음"}</div>',
                        unsafe_allow_html=True
                    )
