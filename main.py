# 메인 캘린더 화면: 로그인, 일정 등록·수정·삭제와 월간 캘린더 표시를 담당한다.
import uuid
from datetime import date, datetime

import streamlit as st
from streamlit_calendar import calendar
from supabase import create_client

import theme

st.set_page_config(
    page_title="Daily Planner | Calendar",
    page_icon="🗓️",
    layout="wide"
)

CATEGORIES = theme.CATEGORIES
COLORS = theme.IMPORTANCE_COLOR
ORDER = theme.IMPORTANCE_ORDER
PERSONAL_COLOR = theme.PERSONAL_COLOR
DONE_COLOR = theme.DONE_COLOR
esc = theme.esc


# ==========================================
# 1. Supabase 연결 및 로그인 관리
# ==========================================

def get_supabase():
    if "supabase_client" in st.session_state:
        client = st.session_state.supabase_client
        access = st.session_state.get("supabase_access_token")
        refresh = st.session_state.get("supabase_refresh_token")

        if access and refresh and not st.session_state.get("supabase_session_restored"):
            try:
                client.auth.set_session(access, refresh)
                st.session_state.supabase_session_restored = True
            except Exception:
                for key in (
                    "supabase_access_token", "supabase_refresh_token",
                    "user_id", "user_email", "supabase_client",
                    "supabase_session_restored"
                ):
                    st.session_state.pop(key, None)
                st.rerun()
        return client

    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except Exception:
        st.error("Streamlit Cloud의 Settings → Secrets에 SUPABASE_URL과 SUPABASE_KEY를 설정해 주세요.")
        st.stop()

    client = create_client(url, key)
    access = st.session_state.get("supabase_access_token")
    refresh = st.session_state.get("supabase_refresh_token")

    if access and refresh:
        try:
            client.auth.set_session(access, refresh)
            st.session_state.supabase_session_restored = True
        except Exception:
            for key in (
                "supabase_access_token", "supabase_refresh_token",
                "user_id", "user_email", "supabase_session_restored"
            ):
                st.session_state.pop(key, None)

    st.session_state.supabase_client = client
    return client


def store_auth_session(client, response):
    session = getattr(response, "session", None)
    user = getattr(response, "user", None)

    if not session or not user:
        return False

    st.session_state.supabase_access_token = session.access_token
    st.session_state.supabase_refresh_token = session.refresh_token
    st.session_state.user_id = str(user.id)
    st.session_state.user_email = user.email or ""
    st.session_state.supabase_client = client
    st.session_state.supabase_session_restored = True

    # 계정에 저장해 둔 테마가 있으면 불러온다
    theme.load_from_user(user)

    return True


def current_user_id():
    return st.session_state.get("user_id")


# ==========================================
# 2. 로그인 및 회원가입
# ==========================================

def auth_page():
    theme.apply_theme(sidebar=False)

    client = get_supabase()

    _, mid, _ = st.columns([1, 1.5, 1])

    with mid:
        st.markdown(theme.brand_html(), unsafe_allow_html=True)
        st.caption("회원가입 또는 로그인하면 나만의 캘린더를 사용할 수 있어요.")

        login, signup = st.tabs(["로그인", "회원가입"])

        with login:
            with st.form("login_form"):
                email = st.text_input("이메일", key="login_email")
                password = st.text_input(
                    "비밀번호", type="password", key="login_password"
                )
                submit = st.form_submit_button(
                    "로그인", type="primary", use_container_width=True
                )

            if submit:
                try:
                    response = client.auth.sign_in_with_password({
                        "email": email.strip(),
                        "password": password
                    })

                    if store_auth_session(client, response):
                        st.rerun()

                    st.error("로그인 세션을 만들지 못했습니다. 이메일 인증 여부를 확인해 주세요.")

                except Exception:
                    st.error("로그인에 실패했습니다. 이메일·비밀번호 또는 이메일 인증 상태를 확인해 주세요.")

        with signup:
            with st.form("signup_form"):
                email = st.text_input("이메일 주소", key="signup_email")
                password = st.text_input(
                    "비밀번호", type="password", key="signup_password"
                )
                confirm = st.text_input(
                    "비밀번호 확인", type="password", key="signup_confirm"
                )
                submit = st.form_submit_button(
                    "회원가입", type="primary", use_container_width=True
                )

            if submit:
                if not email.strip() or not password:
                    st.warning("이메일과 비밀번호를 입력해 주세요.")
                elif password != confirm:
                    st.warning("비밀번호가 일치하지 않습니다.")
                elif len(password) < 6:
                    st.warning("비밀번호를 6자 이상 입력해 주세요.")
                else:
                    try:
                        response = client.auth.sign_up({
                            "email": email.strip(),
                            "password": password
                        })

                        if store_auth_session(client, response):
                            st.success("회원가입이 완료되었습니다.")
                            st.rerun()
                        else:
                            st.success("가입 요청이 완료되었습니다. 이메일 인증 후 로그인해 주세요.")

                    except Exception:
                        st.error("회원가입에 실패했습니다. 이메일 형식과 Supabase 설정을 확인해 주세요.")


# ==========================================
# 3. 일정 불러오기 및 저장
# ==========================================

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

    for r in rows:
        if not r.get("event_date"):
            continue

        cats = r.get("categories") or []

        if isinstance(cats, str):
            cats = [cats]

        result.append({
            "id": str(r["id"]),
            "date": str(r["event_date"])[:10],
            "title": r.get("title") or "",
            "description": r.get("description") or "",
            "importance": (
                r.get("importance")
                if r.get("importance") in COLORS
                else "없음"
            ),
            "categories": [x for x in cats if x in CATEGORIES],
            "done": bool(r.get("done"))
        })

    return result


def write_event(client, uid, event):
    # done(완료 여부)은 보내지 않는다 → 수정해도 기존 완료 상태가 유지됨
    client.table("events").upsert({
        "id": event["id"],
        "user_id": uid,
        "event_date": event["date"],
        "title": event["title"],
        "description": event["description"],
        "importance": event["importance"],
        "categories": event["categories"]
    }).execute()


def date_from(value):
    if not value:
        return None

    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))

        # 시간대(UTC 등)가 붙은 값은 한국 시간(UTC+9)으로 바꿔서 날짜를 뽑는다
        if dt.tzinfo is not None:
            dt = dt.astimezone(theme.KST)

        return dt.date().isoformat()
    except ValueError:
        try:
            return date.fromisoformat(str(value)[:10]).isoformat()
        except ValueError:
            return None


def event_color(e):
    if e["done"]:
        return DONE_COLOR
    if "개인일정" in e["categories"]:
        return PERSONAL_COLOR
    return COLORS[e["importance"]]


def d_label(day, today):
    diff = (day - today).days

    if diff == 0:
        return "오늘"
    if diff > 0:
        return f"D-{diff}"
    return f"D+{-diff}"


# ==========================================
# 4. 로그인 확인
# ==========================================

if not current_user_id():
    auth_page()
    st.stop()

client = get_supabase()
uid = current_user_id()

theme.apply_theme(sidebar=True, active="calendar")

today = theme.today_kst()


# ==========================================
# 5. 일정 불러오기
# ==========================================

try:
    events = fetch_events(client, uid)

except Exception as exc:
    st.error(f"일정을 불러오지 못했습니다: {exc}")
    st.info("Supabase의 events 테이블과 RLS 정책을 확인해 주세요. (done 컬럼이 없다면 schema.sql을 실행해 주세요.)")
    st.stop()


# ==========================================
# 6. 상단: 월 이동 + 일정 추가 버튼
# ==========================================

# cal_ver: 바뀌면 캘린더가 새로 만들어져 이전 클릭 값이 초기화됩니다.
# cal_start_date: 지금 보고 있는 달
st.session_state.setdefault("cal_ver", 0)
st.session_state.setdefault("cal_start_date", today.replace(day=1).isoformat())


def refresh_calendar():
    st.session_state.cal_ver += 1


def shift_month(delta):
    cur = date.fromisoformat(st.session_state.cal_start_date)
    index = cur.year * 12 + (cur.month - 1) + delta
    st.session_state.cal_start_date = date(
        index // 12, index % 12 + 1, 1
    ).isoformat()
    st.session_state.cal_ver += 1


def open_new_event():
    st.session_state.selected_date = theme.today_kst().isoformat()
    st.session_state.edit_event_id = None
    st.session_state.show_event_form = True


shown = date.fromisoformat(st.session_state.cal_start_date)

c_prev, c_title, c_next, _, c_add = st.columns(
    [0.4, 1.9, 0.4, 5.6, 1.8], vertical_alignment="center"
)

with c_prev:
    st.button("‹", key="cal_prev", on_click=shift_month, args=(-1,))

with c_title:
    st.markdown(
        f'<div class="month-title">{shown.year}년 {shown.month}월</div>',
        unsafe_allow_html=True
    )

with c_next:
    st.button("›", key="cal_next", on_click=shift_month, args=(1,))

with c_add:
    st.button(
        "일정 추가", key="cal_add", icon=":material/add:",
        on_click=open_new_event, use_container_width=True
    )


# ==========================================
# 7. 캘린더 표시
# ==========================================

cal_events = []
day_color = {}

for e in sorted(events, key=lambda x: (x["done"], ORDER[x["importance"]])):
    color = event_color(e)

    # 그날 가장 중요한(완료 안 한) 일정의 색을 날짜 배경색으로 쓴다
    day_color.setdefault(e["date"], color)

    cal_events.append({
        "id": e["id"],
        "title": e["title"] or "(제목 없음)",
        "start": e["date"],
        "allDay": True,
        "display": "list-item",
        "color": color,
        "classNames": ["ev-done"] if e["done"] else []
    })

for day_str, color in day_color.items():
    cal_events.append({
        "id": f"bg-{day_str}",
        "start": day_str,
        "allDay": True,
        "display": "background",
        "backgroundColor": color + "55"
    })

state = calendar(
    events=cal_events,
    options={
        "initialView": "dayGridMonth",
        "initialDate": st.session_state.cal_start_date,
        # 한글 로케일은 날짜 숫자 뒤에 '일'이 붙어서 영어로 두고 요일만 CSS로 한글 표시
        "locale": "en",
        "timeZone": "local",
        "height": 640,
        "expandRows": True,
        "dayMaxEvents": 2,
        "moreLinkText": "개 더보기",
        "selectable": False,
        "editable": False,
        "headerToolbar": False,
        "displayEventTime": False,
        "fixedWeekCount": False
    },
    custom_css=theme.calendar_css(),
    callbacks=["dateClick", "eventClick"],
    key=f"main_calendar_{st.session_state.cal_ver}"
)


# ==========================================
# 8. 날짜 및 일정 클릭 처리
# ==========================================

if isinstance(state, dict):
    callback = state.get("callback")

    dc = state.get("dateClick")
    ec = state.get("eventClick")

    if callback == "dateClick" or (callback is None and isinstance(dc, dict)):
        dc = dc or {}
        # dateStr(로컬 날짜)을 우선 사용 — date는 UTC라 하루 밀릴 수 있음
        picked = date_from(dc.get("dateStr") or dc.get("date"))

        if picked:
            st.session_state.selected_date = picked
            st.session_state.edit_event_id = None
            st.session_state.show_event_form = True
            refresh_calendar()
            st.rerun()

    elif callback == "eventClick" or (callback is None and isinstance(ec, dict)):
        event_data = (ec or {}).get("event") or {}
        clicked_id = str(event_data.get("id") or "")

        # 날짜 배경용 이벤트(bg-)는 클릭 대상이 아니다
        if clicked_id and not clicked_id.startswith("bg-"):
            st.session_state.view_event_id = clicked_id
            refresh_calendar()
            st.rerun()


# ==========================================
# 9. 일정 상세 정보 및 수정·삭제
# ==========================================

view_id = st.session_state.get("view_event_id")
view_event = next(
    (e for e in events if e["id"] == view_id),
    None
)

if view_event:
    with st.container(key="detail_panel"):
        st.markdown(
            f'<div class="panel-title"><i></i>{esc(view_event["title"] or "(제목 없음)")}</div>',
            unsafe_allow_html=True
        )

        chips = [f"📅 {view_event['date']}"]

        if view_event["importance"] != "없음":
            chips.append(f"중요도 {view_event['importance']}")

        chips += view_event["categories"]
        chips.append("✅ 완료" if view_event["done"] else "진행 전")

        st.markdown(
            "".join(f'<span class="chip">{esc(c)}</span>' for c in chips),
            unsafe_allow_html=True
        )

        if view_event["description"]:
            st.write(view_event["description"])

        c1, c2, c3, c4 = st.columns(4)

        if c1.button("수정", key="view_edit", use_container_width=True):
            st.session_state.edit_event_id = view_id
            st.session_state.selected_date = view_event["date"]
            st.session_state.show_event_form = True
            st.session_state.view_event_id = None
            st.rerun()

        done_label = "완료 취소" if view_event["done"] else "완료"

        if c2.button(done_label, key="view_done", use_container_width=True):
            try:
                client.table("events").update(
                    {"done": not view_event["done"]}
                ).eq("id", view_id).eq("user_id", uid).execute()
                st.rerun()
            except Exception as exc:
                st.error(f"상태 변경에 실패했습니다: {exc}")

        if c3.button("삭제", key="view_delete", use_container_width=True):
            st.session_state.pending_delete_id = view_id
            st.rerun()

        if c4.button("닫기", key="view_close", use_container_width=True):
            st.session_state.view_event_id = None
            st.rerun()


# ==========================================
# 10. 다가오는 일정
# ==========================================

today_str = today.isoformat()

upcoming = sorted(
    [e for e in events if e["date"] >= today_str and not e["done"]],
    key=lambda e: (e["date"], ORDER[e["importance"]])
)[:5]

st.write("")

with st.container(key="upcoming"):
    h_title, h_more = st.columns([5, 1], vertical_alignment="center")

    with h_title:
        st.markdown(
            '<div class="panel-title"><i></i>다가오는 일정</div>',
            unsafe_allow_html=True
        )

    with h_more:
        try:
            st.page_link("pages/list.py", label="더보기 ›")
        except Exception:
            pass

    if upcoming:
        rows = []

        for e in upcoming:
            d = date.fromisoformat(e["date"])
            meta = (
                f"{d.month}월 {d.day}일 ({theme.WEEKDAYS_KR[d.weekday()]})"
                f" · {d_label(d, today)}"
            )
            rows.append(
                '<div class="up-row">'
                f'<span class="up-dot" style="background:{event_color(e)}"></span>'
                f'<span class="up-title">{esc(e["title"] or "(제목 없음)")}</span>'
                f'<span class="up-meta">{meta}</span>'
                '</div>'
            )

        st.markdown("".join(rows), unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="up-empty">다가오는 일정이 없습니다.</div>',
            unsafe_allow_html=True
        )


# ==========================================
# 11. 일정 삭제 확인 창
# ==========================================

@st.dialog("일정 삭제 확인")
def confirm_delete_dialog(event_id):
    target = next(
        (item for item in events if item["id"] == event_id),
        None
    )

    if target is None:
        st.warning("삭제할 일정을 찾을 수 없습니다.")
        return

    st.warning("이 일정을 삭제할까요? 삭제하면 복구할 수 없습니다.")
    st.markdown(f"**{target['title'] or '(제목 없음)'}**")
    st.caption(f"날짜: {target['date']}")

    yes, no = st.columns(2)

    with yes:
        if st.button(
            "삭제하기",
            type="primary",
            use_container_width=True,
            key="confirm_delete_yes"
        ):
            try:
                client.table("todo_status").delete().eq(
                    "event_id", event_id
                ).eq(
                    "user_id", uid
                ).execute()

                client.table("events").delete().eq(
                    "id", event_id
                ).eq(
                    "user_id", uid
                ).execute()

                st.session_state.view_event_id = None
                st.success("일정을 삭제했습니다.")
                st.rerun()

            except Exception as exc:
                st.error(f"일정 삭제에 실패했습니다: {exc}")

    with no:
        if st.button(
            "취소",
            use_container_width=True,
            key="confirm_delete_no"
        ):
            st.rerun()


# pop으로 꺼내 한 번만 열리게 함 (X/바깥 클릭으로 닫아도 다시 안 뜸)
pending_delete_id = st.session_state.pop("pending_delete_id", None)

if pending_delete_id:
    confirm_delete_dialog(pending_delete_id)


# ==========================================
# 12. 일정 추가 및 수정 팝업창
# ==========================================

def event_editor_dialog():
    edit_id = st.session_state.get("edit_event_id")

    existing = (
        next((e for e in events if e["id"] == edit_id), None)
        if edit_id else None
    )

    picked_date = st.session_state.get(
        "selected_date",
        theme.today_kst().isoformat()
    )

    st.caption(f"선택한 날짜: {picked_date}")

    with st.form("event_editor"):
        title = st.text_input(
            "일정 제목",
            value=existing["title"] if existing else ""
        )

        description = st.text_area(
            "부가 설명",
            value=existing["description"] if existing else ""
        )

        imp_options = ["없음", "상", "중", "하"]

        importance = st.radio(
            "중요도",
            imp_options,
            index=imp_options.index(
                existing["importance"] if existing else "없음"
            ),
            horizontal=True
        )

        categories = st.multiselect(
            "카테고리",
            CATEGORIES,
            default=existing["categories"] if existing else []
        )

        save = st.form_submit_button(
            "저장",
            type="primary",
            use_container_width=True
        )

    if save:
        event = {
            "id": edit_id or str(uuid.uuid4()),
            "date": picked_date,
            "title": title.strip(),
            "description": description.strip(),
            "importance": importance,
            "categories": categories
        }

        try:
            write_event(client, uid, event)

            st.session_state.edit_event_id = None
            st.session_state.view_event_id = None

            st.success("일정을 저장했습니다.")
            st.rerun()

        except Exception as exc:
            st.error(f"저장 실패: {exc}")

    if st.button(
        "취소",
        key="cancel_event_dialog",
        use_container_width=True
    ):
        st.session_state.edit_event_id = None
        st.rerun()


# pop으로 꺼내 한 번만 열리게 하고, 수정 모드면 제목도 바꿈
if st.session_state.pop("show_event_form", False):
    is_edit = bool(st.session_state.get("edit_event_id"))
    st.dialog(
        "일정 수정" if is_edit else "일정 추가",
        width="large"
    )(event_editor_dialog)()
