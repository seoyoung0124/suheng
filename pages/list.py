from datetime import date, timedelta

import streamlit as st

import theme

st.set_page_config(
    page_title="Daily Planner | My Planner",
    page_icon="📓",
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

# 지정한 날짜에 해당하는 사용자의 일정을 조회한다.
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

    # 목록의 항목을 하나씩 확인하며 필요한 처리를 반복한다.
    for r in rows:
        cats = r.get("categories") or []

        # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
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
    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return result


# 지정한 주의 날짜별 일정 개수를 계산한다.
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

    # 목록의 항목을 하나씩 확인하며 필요한 처리를 반복한다.
    for r in rows:
        key = str(r["event_date"])[:10]
        total, done = counts.get(key, (0, 0))
        counts[key] = (total + 1, done + (1 if r.get("done") else 0))

    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return counts


# 선택한 일정의 완료 여부를 데이터베이스에 갱신한다.
def toggle_done(event_id, new_value):
    # 오류가 발생할 수 있는 작업을 실행하고 예외 상황에 대비한다.
    try:
        # Supabase 데이터베이스에서 해당 일정 정보를 조회하거나 변경한다.
        st.session_state.supabase_client.table("events").update(
            {"done": new_value}
        ).eq("id", event_id).eq(
            "user_id", st.session_state.user_id
        ).execute()
    # 앞선 작업에서 오류가 발생했을 때 예외 처리를 수행한다.
    except Exception as exc:
        st.toast(f"완료 상태를 저장하지 못했습니다: {exc}")


# ==========================================
# 1-2. 못 끝낸 일정 이월
# ==========================================

CARRY_DAYS = 30  # 최근 며칠 안의 못 끝낸 일정만 이월 대상으로 본다
CARRY_SHOW = 5   # 패널에 하나씩 보여 줄 최대 개수 (나머지는 '모두 옮기기'로)


# 오늘보다 이전 날짜에 남아 있는 미완료 일정을 조회한다.
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

    # 목록의 항목을 하나씩 확인하며 필요한 처리를 반복한다.
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
    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return result


# 미완료 일정을 지정한 날짜로 이월해 저장한다.
def carry_events(items, target_iso, target_text):
    """items의 일정 날짜를 target_iso로 옮긴다. 되돌릴 수 있게 원래 날짜를 기억해 둔다."""
    ids = [i["id"] for i in items]

    # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
    if not ids:
        # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
        return

    # 오류가 발생할 수 있는 작업을 실행하고 예외 상황에 대비한다.
    try:
        # Supabase 데이터베이스에서 해당 일정 정보를 조회하거나 변경한다.
        st.session_state.supabase_client.table("events").update(
            {"event_date": target_iso}
        ).in_("id", ids).eq(
            "user_id", st.session_state.user_id
        ).execute()
    # 앞선 작업에서 오류가 발생했을 때 예외 처리를 수행한다.
    except Exception as exc:
        st.toast(f"일정을 옮기지 못했습니다: {exc}")
        # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
        return

    st.session_state.carry_undo = [(i["id"], i["date"]) for i in items]
    st.session_state.carry_undo_text = f"{len(ids)}개 일정을 {target_text}로 옮겼어요."


# 마지막 일정 이월 작업을 취소한다.
def undo_carry():
    undo = st.session_state.get("carry_undo") or []

    # 오류가 발생할 수 있는 작업을 실행하고 예외 상황에 대비한다.
    try:
        # 목록의 항목을 하나씩 확인하며 필요한 처리를 반복한다.
        for event_id, old_date in undo:
            # Supabase 데이터베이스에서 해당 일정 정보를 조회하거나 변경한다.
            st.session_state.supabase_client.table("events").update(
                {"event_date": old_date}
            ).eq("id", event_id).eq(
                "user_id", st.session_state.user_id
            ).execute()
    # 앞선 작업에서 오류가 발생했을 때 예외 처리를 수행한다.
    except Exception as exc:
        st.toast(f"되돌리지 못했습니다: {exc}")
        # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
        return

    # 페이지가 다시 실행되어도 필요한 값을 유지하도록 세션 상태를 갱신한다.
    st.session_state.pop("carry_undo", None)
    # 페이지가 다시 실행되어도 필요한 값을 유지하도록 세션 상태를 갱신한다.
    st.session_state.pop("carry_undo_text", None)
    st.toast("원래 날짜로 되돌렸어요.")


# 미완료 일정이 얼마나 지났는지 표시할 문구를 만든다.
def overdue_label(date_str):
    d = date.fromisoformat(date_str)
    diff = (today - d).days
    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return f"{d.month}월 {d.day}일 ({theme.WEEKDAYS_KR[d.weekday()]}) · {diff}일 지남"


# ==========================================
# 2. 날짜 이동 (화살표 / 날짜 선택 / 주간 보기)
# ==========================================

# 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
if "planner_picker" not in st.session_state:
    st.session_state.planner_picker = today

# 페이지가 다시 실행되어도 필요한 값을 유지하도록 세션 상태를 갱신한다.
st.session_state.setdefault("show_week", False)


# 플래너에서 표시할 날짜를 이전 또는 다음 날로 이동한다.
def shift_day(delta):
    st.session_state.planner_picker += timedelta(days=delta)


# 플래너의 표시 날짜를 오늘로 변경한다.
def go_today():
    st.session_state.planner_picker = theme.today_kst()


# 사용자가 선택한 날짜를 플래너 표시 날짜로 설정한다.
def pick_day(day):
    st.session_state.planner_picker = day


# 주간 일정 요약의 표시 상태를 전환한다.
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
    # 화면에 입력 요소 또는 안내 내용을 표시한다.
    st.markdown(
        '<div class="date-head"><span class="line"></span>'
        f'<span class="date-chip">🗓 {theme.WEEKDAYS_EN[day.weekday()]}, '
        f'{theme.MONTHS_EN[day.month - 1]} {day.day}</span>'
        '<span class="line"></span></div>',
        unsafe_allow_html=True
    )

with h_week:
    # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
    if st.session_state.show_week:
        week_label = "주간 보기 닫기"
    # 앞의 조건에 해당하지 않을 때 실행할 작업을 처리한다.
    else:
        week_label = "이번 주 보기" if same_week else "이 주 보기"

    # 화면에 입력 요소 또는 안내 내용을 표시한다.
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

# 오류가 발생할 수 있는 작업을 실행하고 예외 상황에 대비한다.
try:
    overdue = fetch_overdue(client, uid, today)
# 앞선 작업에서 오류가 발생했을 때 예외 처리를 수행한다.
except Exception:
    overdue = []

carry_undo = st.session_state.get("carry_undo")

# 오류가 발생할 수 있는 작업을 실행하고 예외 상황에 대비한다.
try:
    day_events = fetch_day_events(client, uid, day)
# 앞선 작업에서 오류가 발생했을 때 예외 처리를 수행한다.
except Exception as exc:
    st.error(f"일정을 불러오지 못했습니다: {exc}")
    st.info("Supabase events 테이블에 done 컬럼이 있는지 확인해 주세요. (schema.sql 실행)")
    # 현재 실행을 중단해 이후 화면 처리가 진행되지 않도록 한다.
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
    # 화면에 입력 요소 또는 안내 내용을 표시한다.
    st.button("‹", key="prev_day", on_click=shift_day, args=(-1,), help="전날")

with c_next:
    # 화면에 입력 요소 또는 안내 내용을 표시한다.
    st.button("›", key="next_day", on_click=shift_day, args=(1,), help="다음날")

with c_mid:
    card_title = "오늘의 할 일" if day == today else f"{day.month}월 {day.day}일의 할 일"

    # 관련 화면 요소를 하나의 영역으로 묶는다.
    with st.container(key="planner_card"):
        # 화면에 입력 요소 또는 안내 내용을 표시한다.
        st.markdown(
            '<div class="rings">' + "<i></i>" * 7 + "</div>",
            unsafe_allow_html=True
        )

        # 화면에 입력 요소 또는 안내 내용을 표시한다.
        st.markdown(
            '<div class="card-head">'
            f'<div class="card-title">{esc(card_title)}</div>'
            f'<div class="card-count">{done_count} / {total} 완료</div>'
            '</div>'
            f'<div class="pbar"><div style="width:{percent}%"></div></div>',
            unsafe_allow_html=True
        )

        # 목록의 항목을 하나씩 확인하며 필요한 처리를 반복한다.
        for e in day_events:
            kind = "done" if e["done"] else "todo"

            # 관련 화면 요소를 하나의 영역으로 묶는다.
            with st.container(key=f"item_{kind}_{e['id']}"):
                # 화면에 입력 요소 또는 안내 내용을 표시한다.
                st.button(
                    f"~~{e['title']}~~" if e["done"] else e["title"],
                    key=f"tgl_{e['id']}",
                    icon=(
                        ":material/check_circle:"
                        # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
                        if e["done"]
                        else ":material/radio_button_unchecked:"
                    ),
                    on_click=toggle_done,
                    args=(e["id"], not e["done"]),
                    use_container_width=True
                )

                info = []

                # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
                if e["importance"] != "없음":
                    info.append(f"중요도 {e['importance']}")

                info += e["categories"]

                lines = []

                # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
                if info:
                    lines.append(esc(" · ".join(info)))

                # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
                if e["description"]:
                    lines.append(esc(e["description"]))

                # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
                if lines:
                    # 화면에 입력 요소 또는 안내 내용을 표시한다.
                    st.markdown(
                        f'<div class="item-meta">{"<br>".join(lines)}</div>',
                        unsafe_allow_html=True
                    )

        # 일정이 MIN_SLOTS개보다 적어도 빈 칸으로 채워서 항상 5줄 높이를 유지한다.
        # 일정이 그 이상이면 칸이 늘어난다.
        for i in range(total, max(MIN_SLOTS, total)):
            # 관련 화면 요소를 하나의 영역으로 묶는다.
            with st.container(key=f"item_empty_{i}"):
                hint = (
                    "이 날은 등록된 일정이 없어요. 캘린더에서 추가해 보세요."
                    # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
                    if total == 0 and i == 0
                    else "&nbsp;"
                )
                # 화면에 입력 요소 또는 안내 내용을 표시한다.
                st.markdown(
                    f'<div class="item-empty">{hint}</div>',
                    unsafe_allow_html=True
                )

        pal = theme.palette()

        # 화면에 입력 요소 또는 안내 내용을 표시한다.
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


    # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
    if day != today:
        # 화면에 입력 요소 또는 안내 내용을 표시한다.
        st.write("")
        # 화면에 입력 요소 또는 안내 내용을 표시한다.
        st.button(
            "오늘로 돌아가기", key="go_today", on_click=go_today,
            icon=":material/today:", use_container_width=True
        )


with c_side:
    # 관련 화면 요소를 하나의 영역으로 묶는다.
    with st.container(key="carry_side"):
        # ----- 못 끝낸 일정 이월 (플래너 카드 오른쪽 옆) -----
        if carry_undo:
            # 관련 화면 요소를 하나의 영역으로 묶는다.
            with st.container(key="carry_undo"):
                # 화면에 입력 요소 또는 안내 내용을 표시한다.
                st.markdown(
                    f'<div class="carry-note">{esc(st.session_state.get("carry_undo_text", ""))}</div>',
                    unsafe_allow_html=True
                )
                # 화면에 입력 요소 또는 안내 내용을 표시한다.
                st.button(
                    "되돌리기", key="carry_undo_btn", icon=":material/undo:",
                    on_click=undo_carry, use_container_width=True
                )

        # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
        if overdue:
            # 관련 화면 요소를 하나의 영역으로 묶는다.
            with st.container(key="carry_panel"):
                # 화면에 입력 요소 또는 안내 내용을 표시한다.
                st.markdown(
                    f'<div class="panel-title"><i></i>못 끝낸 일정 {len(overdue)}개</div>'
                    f'<div class="carry-sub">최근 {CARRY_DAYS}일 · {esc(target_text)}로 옮길 수 있어요</div>',
                    unsafe_allow_html=True
                )

                # 화면에 입력 요소 또는 안내 내용을 표시한다.
                st.button(
                    "모두 옮기기", key="carry_all",
                    icon=":material/arrow_forward:", type="primary",
                    on_click=carry_events,
                    args=(overdue, target_day.isoformat(), target_text),
                    use_container_width=True
                )

                # 목록의 항목을 하나씩 확인하며 필요한 처리를 반복한다.
                for item in overdue[:CARRY_SHOW]:
                    # 한 일정당 두 줄: 제목(전체 폭, 길면 줄바꿈) / 날짜 + 옮기기 버튼
                    with st.container(key=f"carry_item_{item['id']}"):
                        # 화면에 입력 요소 또는 안내 내용을 표시한다.
                        st.markdown(
                            '<div class="carry-title">'
                            f'<span class="up-dot" style="background:{theme.IMPORTANCE_COLOR[item["importance"]]}"></span>'
                            f'<span>{esc(item["title"])}</span></div>',
                            unsafe_allow_html=True
                        )

                        c_meta, c_one = st.columns([3, 2], vertical_alignment="center")

                        with c_meta:
                            # 화면에 입력 요소 또는 안내 내용을 표시한다.
                            st.markdown(
                                f'<div class="carry-meta">{esc(overdue_label(item["date"]))}</div>',
                                unsafe_allow_html=True
                            )

                        with c_one:
                            # 화면에 입력 요소 또는 안내 내용을 표시한다.
                            st.button(
                                "옮기기", key=f"carry_one_{item['id']}",
                                on_click=carry_events,
                                args=([item], target_day.isoformat(), target_text),
                                use_container_width=True
                            )

                # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
                if len(overdue) > CARRY_SHOW:
                    # 화면에 입력 요소 또는 안내 내용을 표시한다.
                    st.caption(f"외 {len(overdue) - CARRY_SHOW}개는 '모두 옮기기'로 함께 옮겨져요.")


# ==========================================
# 5. 주간 보기
# ==========================================

# 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
if st.session_state.show_week:
    # 오류가 발생할 수 있는 작업을 실행하고 예외 상황에 대비한다.
    try:
        counts = fetch_week_counts(client, uid, week_start, week_end)
    # 앞선 작업에서 오류가 발생했을 때 예외 처리를 수행한다.
    except Exception as exc:
        counts = {}
        st.warning(f"주간 일정을 불러오지 못했습니다: {exc}")

    # 화면에 입력 요소 또는 안내 내용을 표시한다.
    st.write("")

    _, w_mid, _ = st.columns([1, 8, 1])

    with w_mid:
        # 관련 화면 요소를 하나의 영역으로 묶는다.
        with st.container(key="week_panel"):
            # 화면에 입력 요소 또는 안내 내용을 표시한다.
            st.markdown(
                '<div class="panel-title"><i></i>'
                f'{week_start.month}월 {week_start.day}일 ~ '
                f'{week_end.month}월 {week_end.day}일</div>',
                unsafe_allow_html=True
            )

            cols = st.columns(7)

            # 목록의 항목을 하나씩 확인하며 필요한 처리를 반복한다.
            for i, col in enumerate(cols):
                d = week_start + timedelta(days=i)
                t, dn = counts.get(d.isoformat(), (0, 0))

                with col:
                    # 화면에 입력 요소 또는 안내 내용을 표시한다.
                    st.button(
                        f"{theme.WEEKDAYS_KR[i]} {d.day}",
                        key=f"week_{d.isoformat()}",
                        type="primary" if d == day else "secondary",
                        on_click=pick_day, args=(d,),
                        use_container_width=True
                    )
                    # 화면에 입력 요소 또는 안내 내용을 표시한다.
                    st.markdown(
                        f'<div class="week-note">{f"{dn}/{t} 완료" if t else "일정 없음"}</div>',
                        unsafe_allow_html=True
                    )
