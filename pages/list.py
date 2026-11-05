from datetime import date, timedelta

import streamlit as st

import theme

st.set_page_config(
    page_title="하루결 | My Planner",
    page_icon="📒",
    layout="wide",
    initial_sidebar_state="expanded"
)

client, uid = theme.page_setup("planner")

esc = theme.esc
ORDER = theme.IMPORTANCE_ORDER
today = theme.today_kst()

MIN_SLOTS = 5  # 일정이 없어도 항상 보이는 최소 칸 수


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
# 1-2. 못 끝낸 일정 이월
# ==========================================

CARRY_DAYS = 30  # 최근 며칠 안의 못 끝낸 일정만 이월 대상으로 본다
CARRY_SHOW = 5   # 패널에 하나씩 보여 줄 최대 개수 (나머지는 '모두 옮기기'로)


def fetch_overdue(client, uid, today):
    """오늘 이전(최근 CARRY_DAYS일)에 있는 완료하지 않은 일정."""
    rows = (
        client.table("events")
        .select("*")
        .eq("user_id", uid)
        .eq("done", False)
        .gte("event_date", (today - timedelta(days=CARRY_DAYS)).isoformat())
        .lt("event_date", today.isoformat())
        .order("event_date")
        .execute()
        .data or []
    )

    result = []

    for r in rows:
        importance = r.get("importance")

        result.append({
            "id": str(r["id"]),
            "date": str(r["event_date"])[:10],
            "title": r.get("title") or "(제목 없음)",
            "importance": importance if importance in ORDER else "없음",
        })

    # 어제처럼 가까운 날짜의 일정이 먼저 보이도록 최근 날짜순, 같은 날은 중요한 순
    result.sort(key=lambda e: (
        -date.fromisoformat(e["date"]).toordinal(),
        ORDER[e["importance"]],
        e["title"]
    ))
    return result


def carry_events(items, target_iso, target_text):
    """items의 일정 날짜를 target_iso로 옮긴다. 되돌릴 수 있게 원래 날짜를 기억해 둔다."""
    ids = [i["id"] for i in items]

    if not ids:
        return

    try:
        st.session_state.supabase_client.table("events").update(
            {"event_date": target_iso}
        ).in_("id", ids).eq(
            "user_id", st.session_state.user_id
        ).execute()
    except Exception as exc:
        st.toast(f"일정을 옮기지 못했습니다: {exc}")
        return

    st.session_state.carry_undo = [(i["id"], i["date"]) for i in items]
    st.session_state.carry_undo_text = f"{len(ids)}개 일정을 {target_text}로 옮겼어요."


def undo_carry():
    undo = st.session_state.get("carry_undo") or []

    try:
        for event_id, old_date in undo:
            st.session_state.supabase_client.table("events").update(
                {"event_date": old_date}
            ).eq("id", event_id).eq(
                "user_id", st.session_state.user_id
            ).execute()
    except Exception as exc:
        st.toast(f"되돌리지 못했습니다: {exc}")
        return

    st.session_state.pop("carry_undo", None)
    st.session_state.pop("carry_undo_text", None)
    st.toast("원래 날짜로 되돌렸어요.")


def overdue_label(date_str):
    d = date.fromisoformat(date_str)
    diff = (today - d).days
    return f"{d.month}월 {d.day}일 ({theme.WEEKDAYS_KR[d.weekday()]}) · {diff}일 지남"


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

# ----- 못 끝낸 일정 이월 안내 (카드 폭에 맞춰 가운데에 표시) -----
# 보고 있는 날이 오늘 이후면 그 날짜로, 지난 날이면 오늘로 옮긴다
target_day = max(day, today)
target_text = "오늘" if target_day == today else f"{target_day.month}월 {target_day.day}일"

try:
    overdue = fetch_overdue(client, uid, today)
except Exception:
    overdue = []

carry_undo = st.session_state.get("carry_undo")

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

# 왼쪽: 전날 ‹ / 플래너 수첩 / 다음날 ›   오른쪽: 이월 배너 (수첩 위쪽과 높이를 맞춤)
c_left, c_side = st.columns([6.6, 4], vertical_alignment="top")

with c_left:
    c_prev, c_mid, c_next = st.columns([0.8, 4.8, 0.8], vertical_alignment="center")

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

        # 일정이 MIN_SLOTS개보다 적어도 빈 칸으로 채워서 항상 5줄 높이를 유지한다.
        # 일정이 그 이상이면 칸이 늘어난다.
        for i in range(total, max(MIN_SLOTS, total)):
            with st.container(key=f"item_empty_{i}"):
                hint = (
                    "이 날은 등록된 일정이 없어요. 캘린더에서 추가해 보세요."
                    if total == 0 and i == 0
                    else "&nbsp;"
                )
                st.markdown(
                    f'<div class="item-empty">{hint}</div>',
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


with c_side:
    with st.container(key="carry_side"):
        # ----- 못 끝낸 일정 이월 (플래너 카드 오른쪽 옆) -----
        if carry_undo:
            with st.container(key="carry_undo"):
                st.markdown(
                    f'<div class="carry-note">{esc(st.session_state.get("carry_undo_text", ""))}</div>',
                    unsafe_allow_html=True
                )
                st.button(
                    "되돌리기", key="carry_undo_btn", icon=":material/undo:",
                    on_click=undo_carry, use_container_width=True
                )

        if overdue:
            with st.container(key="carry_panel"):
                st.markdown(
                    f'<div class="panel-title"><i></i>못 끝낸 일정 {len(overdue)}개</div>'
                    f'<div class="carry-sub">최근 {CARRY_DAYS}일 · {esc(target_text)}로 옮길 수 있어요</div>',
                    unsafe_allow_html=True
                )

                st.button(
                    "모두 옮기기", key="carry_all",
                    icon=":material/arrow_forward:", type="primary",
                    on_click=carry_events,
                    args=(overdue, target_day.isoformat(), target_text),
                    use_container_width=True
                )

                for item in overdue[:CARRY_SHOW]:
                    # 한 일정당 두 줄: 제목(전체 폭, 길면 줄바꿈) / 날짜 + 옮기기 버튼
                    with st.container(key=f"carry_item_{item['id']}"):
                        st.markdown(
                            '<div class="carry-title">'
                            f'<span class="up-dot" style="background:{theme.IMPORTANCE_COLOR[item["importance"]]}"></span>'
                            f'<span>{esc(item["title"])}</span></div>',
                            unsafe_allow_html=True
                        )

                        c_meta, c_one = st.columns([3, 2], vertical_alignment="center")

                        with c_meta:
                            st.markdown(
                                f'<div class="carry-meta">{esc(overdue_label(item["date"]))}</div>',
                                unsafe_allow_html=True
                            )

                        with c_one:
                            st.button(
                                "옮기기", key=f"carry_one_{item['id']}",
                                on_click=carry_events,
                                args=([item], target_day.isoformat(), target_text),
                                use_container_width=True
                            )

                if len(overdue) > CARRY_SHOW:
                    st.caption(f"외 {len(overdue) - CARRY_SHOW}개는 '모두 옮기기'로 함께 옮겨져요.")


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
