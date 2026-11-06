# 새 일정을 만들 때 고유한 ID를 생성하기 위해 uuid를 가져온다.
import uuid
# 날짜 계산과 날짜 문자열 변환에 필요한 클래스를 가져온다.
from datetime import date, datetime

# 웹 화면 구성과 사용자 입력 처리를 위한 Streamlit을 가져온다.
import streamlit as st
# 월간 캘린더를 화면에 표시하는 컴포넌트를 가져온다.
from streamlit_calendar import calendar
# Supabase 데이터베이스 연결을 생성하는 함수를 가져온다.
from supabase import create_client

# 색상, 테마, 날짜 처리 등 공통 설정을 가져온다.
import theme

# 브라우저 탭 제목과 아이콘, 화면 너비를 설정한다.
st.set_page_config(
    page_title="Daily Planner | Calendar",
    page_icon="🗓️",
    layout="wide"
)

# 여러 화면에서 공통으로 사용하는 카테고리와 색상 설정을 가져온다.
CATEGORIES = theme.CATEGORIES
COLORS = theme.IMPORTANCE_COLOR
ORDER = theme.IMPORTANCE_ORDER
PERSONAL_COLOR = theme.PERSONAL_COLOR
DONE_COLOR = theme.DONE_COLOR
esc = theme.esc


# ==========================================
# 1. Supabase 연결 및 로그인 관리
# ==========================================

# Supabase 연결을 가져오고 저장된 로그인 세션을 복원한다.
def get_supabase():
# 이미 연결 객체가 세션에 있으면 새로 만들지 않고 재사용한다.
    if "supabase_client" in st.session_state:
# 세션에 저장된 Supabase 연결 객체를 가져온다.
        client = st.session_state.supabase_client
# 저장된 인증 토큰을 가져와 로그인 상태를 복원할 준비를 한다.
        access = st.session_state.get("supabase_access_token")
# 만료된 인증 토큰을 갱신할 때 사용할 토큰을 가져온다.
        refresh = st.session_state.get("supabase_refresh_token")

# 토큰이 있고 아직 세션 복원이 안 된 경우 인증 정보를 다시 설정한다.
        if access and refresh and not st.session_state.get("supabase_session_restored"):
            try:
# 저장된 토큰으로 Supabase 로그인 세션을 복원한다.
                client.auth.set_session(access, refresh)
                st.session_state.supabase_session_restored = True
# 세션 복원에 실패하면 잘못된 로그인 정보를 정리한다.
            except Exception:
# 인증이 만료되거나 잘못된 경우 세션에 남은 로그인 정보를 삭제한다.
                for key in (
                    "supabase_access_token", "supabase_refresh_token",
                    "user_id", "user_email", "supabase_client",
                    "supabase_session_restored"
                ):
                    st.session_state.pop(key, None)
# 정리된 로그인 상태로 화면을 다시 실행한다.
                st.rerun()
        return client

# Streamlit Secrets에서 데이터베이스 접속 정보를 읽는다.
    try:
# Supabase 프로젝트 주소를 비밀 설정에서 가져온다.
        url = st.secrets["SUPABASE_URL"]
# Supabase 접속용 API 키를 비밀 설정에서 가져온다.
        key = st.secrets["SUPABASE_KEY"]
# 접속 정보가 없으면 오류를 안내하고 실행을 중단한다.
    except Exception:
        st.error("Streamlit Cloud의 Settings → Secrets에 SUPABASE_URL과 SUPABASE_KEY를 설정해 주세요.")
        st.stop()

# 프로젝트 주소와 API 키로 Supabase 연결 객체를 생성한다.
    client = create_client(url, key)
    access = st.session_state.get("supabase_access_token")
    refresh = st.session_state.get("supabase_refresh_token")

# 기존 토큰이 있으면 새 연결에도 로그인 세션을 적용한다.
    if access and refresh:
# 일정 저장 과정에서 발생할 수 있는 오류를 처리한다.
        try:
            client.auth.set_session(access, refresh)
            st.session_state.supabase_session_restored = True
        except Exception:
            for key in (
                "supabase_access_token", "supabase_refresh_token",
                "user_id", "user_email", "supabase_session_restored"
            ):
                st.session_state.pop(key, None)

# 생성한 연결 객체를 세션에 저장해 이후에도 재사용한다.
    st.session_state.supabase_client = client
    return client


# 로그인 응답에서 사용자와 인증 토큰을 꺼내 세션에 저장한다.
def store_auth_session(client, response):
# 응답에 포함된 로그인 세션 정보를 가져온다.
    session = getattr(response, "session", None)
# 응답에 포함된 사용자 정보를 가져온다.
    user = getattr(response, "user", None)

# 세션이나 사용자 정보가 없으면 저장하지 못한 것으로 처리한다.
    if not session or not user:
        return False

# 다음 접속에서도 로그인 상태를 복원할 수 있도록 접근 토큰을 저장한다.
    st.session_state.supabase_access_token = session.access_token
# 접근 토큰 갱신에 사용할 토큰을 저장한다.
    st.session_state.supabase_refresh_token = session.refresh_token
# 사용자 ID를 문자열로 저장해 개인별 데이터를 구분한다.
    st.session_state.user_id = str(user.id)
    st.session_state.user_email = user.email or ""
# 생성한 연결 객체를 세션에 저장해 이후에도 재사용한다.
    st.session_state.supabase_client = client
    st.session_state.supabase_session_restored = True

    # 계정에 저장해 둔 테마가 있으면 불러온다
# 해당 계정에 저장된 테마 설정을 불러온다.
    theme.load_from_user(user)

    return True


# 현재 로그인한 사용자의 ID를 반환한다.
def current_user_id():
    return st.session_state.get("user_id")


# ==========================================
# 2. 로그인 및 회원가입
# ==========================================

# 로그인과 회원가입 입력 화면을 구성하고 인증 요청을 처리한다.
def auth_page():
# 로그인 화면에는 사이드바 없이 테마를 적용한다.
    theme.apply_theme(sidebar=False)

# 로그인 요청에 사용할 Supabase 연결을 가져온다.
    client = get_supabase()

# 좌우 여백을 두어 로그인 폼을 화면 가운데 배치한다.
    _, mid, _ = st.columns([1, 1.5, 1])

    with mid:
        st.markdown(theme.brand_html(), unsafe_allow_html=True)
        st.caption("회원가입 또는 로그인하면 나만의 캘린더를 사용할 수 있어요.")

# 로그인과 회원가입 화면을 탭으로 나눈다.
        login, signup = st.tabs(["로그인", "회원가입"])

        with login:
# 로그인 입력값을 하나의 폼으로 묶는다.
            with st.form("login_form"):
# 사용자가 입력한 이메일 주소를 받는다.
                email = st.text_input("이메일", key="login_email")
# 비밀번호를 입력받고 화면에는 문자가 노출되지 않도록 한다.
                password = st.text_input(
                    "비밀번호", type="password", key="login_password"
                )
                submit = st.form_submit_button(
                    "로그인", type="primary", use_container_width=True
                )

# 회원가입 버튼을 눌렀을 때 입력값을 검사한다.
            if submit:
                try:
# 입력한 이메일과 비밀번호로 Supabase 로그인을 시도한다.
                    response = client.auth.sign_in_with_password({
                        "email": email.strip(),
                        "password": password
                    })

# 로그인 세션 저장에 성공하면 인증된 화면으로 이동한다.
                    if store_auth_session(client, response):
# 로그인 상태를 반영해 앱을 다시 실행한다.
                        st.rerun()

                    st.error("로그인 세션을 만들지 못했습니다. 이메일 인증 여부를 확인해 주세요.")

# 인증에 실패하면 사용자에게 오류 안내를 표시한다.
                except Exception:
                    st.error("로그인에 실패했습니다. 이메일·비밀번호 또는 이메일 인증 상태를 확인해 주세요.")

        with signup:
# 회원가입에 필요한 정보를 입력받는 폼을 만든다.
            with st.form("signup_form"):
                email = st.text_input("이메일 주소", key="signup_email")
# 비밀번호를 입력받고 화면에는 문자가 노출되지 않도록 한다.
                password = st.text_input(
                    "비밀번호", type="password", key="signup_password"
                )
                confirm = st.text_input(
                    "비밀번호 확인", type="password", key="signup_confirm"
                )
                submit = st.form_submit_button(
                    "회원가입", type="primary", use_container_width=True
                )

# 회원가입 버튼을 눌렀을 때 입력값을 검사한다.
            if submit:
# 이메일이나 비밀번호가 비어 있는지 확인한다.
                if not email.strip() or not password:
                    st.warning("이메일과 비밀번호를 입력해 주세요.")
# 비밀번호와 비밀번호 확인 값이 같은지 검사한다.
                elif password != confirm:
                    st.warning("비밀번호가 일치하지 않습니다.")
# 비밀번호가 최소 6자인지 검사한다.
                elif len(password) < 6:
                    st.warning("비밀번호를 6자 이상 입력해 주세요.")
                else:
                    try:
# 입력한 이메일과 비밀번호로 새 계정을 생성한다.
                        response = client.auth.sign_up({
                            "email": email.strip(),
                            "password": password
                        })

# 가입 직후 세션까지 만들어졌다면 로그인 상태로 전환한다.
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

# 특정 사용자의 일정을 데이터베이스에서 불러와 화면용 형태로 정리한다.
def fetch_events(client, uid):
# events 테이블에서 현재 사용자에게 속한 일정을 날짜순으로 조회한다.
    rows = (
        client.table("events")
        .select("*")
        .eq("user_id", uid)
        .order("event_date")
        .execute()
        .data or []
    )

# 데이터베이스 결과를 화면에서 사용하기 쉬운 목록으로 변환할 공간이다.
    result = []

# 조회된 일정 데이터를 하나씩 확인한다.
    for r in rows:
# 날짜가 없는 잘못된 일정 데이터는 목록에서 제외한다.
        if not r.get("event_date"):
            continue

# 카테고리 값이 없으면 빈 목록으로 처리한다.
        cats = r.get("categories") or []

# 카테고리가 문자열 하나로 저장된 경우 목록 형태로 바꾼다.
        if isinstance(cats, str):
            cats = [cats]

# 각 일정의 필드를 화면에서 사용하는 이름과 형식으로 정리한다.
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


# 일정 정보를 Supabase에 저장하거나 기존 일정을 갱신한다.
def write_event(client, uid, event):
    # done(완료 여부)은 보내지 않는다 → 수정해도 기존 완료 상태가 유지됨
# 일정 ID가 이미 있으면 수정하고 없으면 새 일정으로 저장한다.
    client.table("events").upsert({
        "id": event["id"],
        "user_id": uid,
        "event_date": event["date"],
        "title": event["title"],
        "description": event["description"],
        "importance": event["importance"],
        "categories": event["categories"]
    }).execute()


# 캘린더에서 전달된 날짜 값을 YYYY-MM-DD 형식으로 정리한다.
def date_from(value):
# 날짜 값이 비어 있으면 변환할 수 없으므로 None을 반환한다.
    if not value:
        return None

# Streamlit Secrets에서 데이터베이스 접속 정보를 읽는다.
    try:
# ISO 형식 날짜 문자열을 날짜 객체로 변환한다.
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))

        # 시간대(UTC 등)가 붙은 값은 한국 시간(UTC+9)으로 바꿔서 날짜를 뽑는다
# 날짜에 시간대 정보가 포함되어 있는지 확인한다.
        if dt.tzinfo is not None:
# 시간대가 있다면 한국 시간으로 변환해 날짜가 달라지는 문제를 막는다.
            dt = dt.astimezone(theme.KST)

        return dt.date().isoformat()
# 전체 날짜·시간 형식으로 변환할 수 없을 때 날짜 부분만 다시 읽는다.
    except ValueError:
# 일정 저장 과정에서 발생할 수 있는 오류를 처리한다.
        try:
            return date.fromisoformat(str(value)[:10]).isoformat()
        except ValueError:
            return None


# 완료 여부와 카테고리, 중요도에 따라 일정 표시 색상을 결정한다.
def event_color(e):
# 완료된 일정은 완료 상태 전용 색상을 사용한다.
    if e["done"]:
        return DONE_COLOR
# 개인 일정은 중요도와 관계없이 개인 일정 색상을 사용한다.
    if "개인일정" in e["categories"]:
        return PERSONAL_COLOR
    return COLORS[e["importance"]]


# 일정 날짜가 오늘로부터 얼마나 떨어져 있는지 D-day 문구로 만든다.
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

# 로그인하지 않은 사용자는 인증 화면을 보여 주고 캘린더 접근을 막는다.
if not current_user_id():
    auth_page()
    st.stop()

# 로그인한 사용자의 일정 조회와 저장에 사용할 연결을 가져온다.
client = get_supabase()
# 데이터 조회 시 사용할 현재 사용자 ID를 가져온다.
uid = current_user_id()

# 캘린더 페이지에 공통 테마와 현재 메뉴 표시를 적용한다.
theme.apply_theme(sidebar=True, active="calendar")

# 오늘 날짜를 한국 시간 기준으로 가져온다.
today = theme.today_kst()


# ==========================================
# 5. 일정 불러오기
# ==========================================

# 데이터베이스에서 일정 목록을 불러오며 오류 발생 여부를 확인한다.
try:
# 현재 로그인한 사용자의 전체 일정을 가져온다.
    events = fetch_events(client, uid)

# 일정 조회에 실패하면 오류와 확인할 설정을 안내한다.
except Exception as exc:
    st.error(f"일정을 불러오지 못했습니다: {exc}")
    st.info("Supabase의 events 테이블과 RLS 정책을 확인해 주세요. (done 컬럼이 없다면 schema.sql을 실행해 주세요.)")
    st.stop()


# ==========================================
# 6. 상단: 월 이동 + 일정 추가 버튼
# ==========================================

# cal_ver: 바뀌면 캘린더가 새로 만들어져 이전 클릭 값이 초기화됩니다.
# cal_start_date: 지금 보고 있는 달
# 캘린더를 새로 그릴 때 사용할 버전 값을 초기화한다.
st.session_state.setdefault("cal_ver", 0)
# 처음 열었을 때 이번 달 1일을 캘린더 기준 날짜로 설정한다.
st.session_state.setdefault("cal_start_date", today.replace(day=1).isoformat())


# 캘린더 버전을 올려 컴포넌트를 새로 표시하게 한다.
def refresh_calendar():
    st.session_state.cal_ver += 1


# 이전 달 또는 다음 달로 캘린더 표시 기간을 이동한다.
def shift_month(delta):
# 현재 캘린더 기준 날짜를 날짜 객체로 변환한다.
    cur = date.fromisoformat(st.session_state.cal_start_date)
# 연도와 월을 하나의 월 번호로 계산해 연도 경계 이동도 처리한다.
    index = cur.year * 12 + (cur.month - 1) + delta
    st.session_state.cal_start_date = date(
        index // 12, index % 12 + 1, 1
    ).isoformat()
    st.session_state.cal_ver += 1


# 오늘 날짜를 선택하고 새 일정 입력 창을 열도록 상태를 설정한다.
def open_new_event():
    st.session_state.selected_date = theme.today_kst().isoformat()
    st.session_state.edit_event_id = None
    st.session_state.show_event_form = True


# 화면에 표시할 연도와 월을 날짜 객체에서 가져온다.
shown = date.fromisoformat(st.session_state.cal_start_date)

# 월 이동 버튼, 월 제목, 일정 추가 버튼을 가로로 배치한다.
c_prev, c_title, c_next, _, c_add = st.columns(
    [0.4, 1.9, 0.4, 5.6, 1.8], vertical_alignment="center"
)

# 이전 달로 이동하는 버튼을 표시한다.
with c_prev:
    st.button("‹", key="cal_prev", on_click=shift_month, args=(-1,))

# 현재 보고 있는 연도와 월을 제목으로 표시한다.
with c_title:
    st.markdown(
        f'<div class="month-title">{shown.year}년 {shown.month}월</div>',
        unsafe_allow_html=True
    )

# 다음 달로 이동하는 버튼을 표시한다.
with c_next:
    st.button("›", key="cal_next", on_click=shift_month, args=(1,))

# 새 일정을 입력하는 버튼을 표시한다.
with c_add:
    st.button(
        "일정 추가", key="cal_add", icon=":material/add:",
        on_click=open_new_event, use_container_width=True
    )


# ==========================================
# 7. 캘린더 표시
# ==========================================

# 캘린더 컴포넌트에 전달할 일정 이벤트 목록을 만든다.
cal_events = []
# 날짜별 배경색을 저장해 일정이 있는 날짜를 구분한다.
day_color = {}

# 미완료 일정과 중요도 순으로 정렬해 날짜별 대표 색상을 정한다.
for e in sorted(events, key=lambda x: (x["done"], ORDER[x["importance"]])):
# 현재 일정에 적용할 색상을 계산한다.
    color = event_color(e)

    # 그날 가장 중요한(완료 안 한) 일정의 색을 날짜 배경색으로 쓴다
    day_color.setdefault(e["date"], color)

# 캘린더가 인식할 수 있는 형식으로 일정 정보를 추가한다.
    cal_events.append({
        "id": e["id"],
        "title": e["title"] or "(제목 없음)",
        "start": e["date"],
        "allDay": True,
        "display": "list-item",
        "color": color,
        "classNames": ["ev-done"] if e["done"] else []
    })

# 일정이 등록된 날짜마다 배경 표시용 이벤트를 추가한다.
for day_str, color in day_color.items():
# 캘린더가 인식할 수 있는 형식으로 일정 정보를 추가한다.
    cal_events.append({
        "id": f"bg-{day_str}",
        "start": day_str,
        "allDay": True,
        "display": "background",
        "backgroundColor": color + "55"
    })

# 일정 목록과 표시 옵션을 전달해 월간 캘린더를 화면에 생성한다.
state = calendar(
    events=cal_events,
# 캘린더의 초기 화면, 높이, 언어, 이벤트 표시 방식 등을 설정한다.
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
# 공통 CSS를 적용해 캘린더의 색상과 모양을 꾸민다.
    custom_css=theme.calendar_css(),
# 날짜와 일정 항목을 클릭했을 때 발생하는 이벤트를 받는다.
    callbacks=["dateClick", "eventClick"],
    key=f"main_calendar_{st.session_state.cal_ver}"
)


# ==========================================
# 8. 날짜 및 일정 클릭 처리
# ==========================================

# 캘린더 컴포넌트가 반환한 클릭 결과가 딕셔너리인지 확인한다.
if isinstance(state, dict):
# 어떤 종류의 클릭이 발생했는지 구분하는 값을 가져온다.
    callback = state.get("callback")

# 날짜 칸을 클릭했을 때 전달된 정보를 가져온다.
    dc = state.get("dateClick")
# 일정 항목을 클릭했을 때 전달된 정보를 가져온다.
    ec = state.get("eventClick")

# 날짜 클릭 이벤트라면 선택한 날짜를 확인한다.
    if callback == "dateClick" or (callback is None and isinstance(dc, dict)):
        dc = dc or {}
        # dateStr(로컬 날짜)을 우선 사용 — date는 UTC라 하루 밀릴 수 있음
# 클릭한 날짜를 한국 시간 기준 날짜 문자열로 변환한다.
        picked = date_from(dc.get("dateStr") or dc.get("date"))

# 날짜 변환에 성공한 경우 새 일정 입력 상태를 설정한다.
        if picked:
# 사용자가 선택한 날짜를 일정 입력 폼에 전달하도록 저장한다.
            st.session_state.selected_date = picked
# 저장 후 수정 모드 상태를 초기화한다.
            st.session_state.edit_event_id = None
# 다음 화면 실행에서 일정 입력 팝업을 열도록 표시한다.
            st.session_state.show_event_form = True
# 클릭 상태가 남지 않도록 캘린더를 새로 만든다.
            refresh_calendar()
# 변경된 선택 날짜와 팝업 상태를 화면에 반영한다.
            st.rerun()

# 일정 항목 클릭 이벤트라면 클릭한 일정의 정보를 확인한다.
    elif callback == "eventClick" or (callback is None and isinstance(ec, dict)):
# 클릭 결과에서 실제 일정 데이터를 꺼낸다.
        event_data = (ec or {}).get("event") or {}
# 선택한 일정의 고유 ID를 문자열로 가져온다.
        clicked_id = str(event_data.get("id") or "")

        # 날짜 배경용 이벤트(bg-)는 클릭 대상이 아니다
# 날짜 배경 표시용 이벤트가 아닌 실제 일정만 선택 처리한다.
        if clicked_id and not clicked_id.startswith("bg-"):
# 상세 정보를 보여 줄 일정 ID를 저장한다.
            st.session_state.view_event_id = clicked_id
# 클릭 상태가 남지 않도록 캘린더를 새로 만든다.
            refresh_calendar()
# 변경된 선택 날짜와 팝업 상태를 화면에 반영한다.
            st.rerun()


# ==========================================
# 9. 일정 상세 정보 및 수정·삭제
# ==========================================

# 현재 상세 화면에서 보여 줄 일정 ID를 가져온다.
view_id = st.session_state.get("view_event_id")
# 전체 일정 중 선택한 ID와 일치하는 일정 하나를 찾는다.
view_event = next(
    (e for e in events if e["id"] == view_id),
    None
)

# 선택된 일정이 존재할 때만 상세 정보와 버튼을 표시한다.
if view_event:
    with st.container(key="detail_panel"):
        st.markdown(
            f'<div class="panel-title"><i></i>{esc(view_event["title"] or "(제목 없음)")}</div>',
            unsafe_allow_html=True
        )

# 상세 정보 상단에 일정 날짜를 표시할 항목을 만든다.
        chips = [f"📅 {view_event['date']}"]

# 중요도가 설정된 경우 중요도 표시를 추가한다.
        if view_event["importance"] != "없음":
            chips.append(f"중요도 {view_event['importance']}")

# 일정에 등록된 카테고리를 표시 목록에 추가한다.
        chips += view_event["categories"]
# 완료 여부를 상세 정보에 표시한다.
        chips.append("✅ 완료" if view_event["done"] else "진행 전")

        st.markdown(
            "".join(f'<span class="chip">{esc(c)}</span>' for c in chips),
            unsafe_allow_html=True
        )

# 부가 설명이 입력된 일정에만 설명 내용을 보여 준다.
        if view_event["description"]:
            st.write(view_event["description"])

# 수정, 완료, 삭제, 닫기 버튼을 가로로 배치한다.
        c1, c2, c3, c4 = st.columns(4)

# 수정 버튼을 누르면 선택한 일정의 정보를 편집하도록 설정한다.
        if c1.button("수정", key="view_edit", use_container_width=True):
            st.session_state.edit_event_id = view_id
            st.session_state.selected_date = view_event["date"]
# 다음 화면 실행에서 일정 입력 팝업을 열도록 표시한다.
            st.session_state.show_event_form = True
# 저장 후 기존 상세 정보 패널 선택 상태를 초기화한다.
            st.session_state.view_event_id = None
# 변경된 선택 날짜와 팝업 상태를 화면에 반영한다.
            st.rerun()

# 현재 상태에 따라 완료 버튼 문구를 바꾼다.
        done_label = "완료 취소" if view_event["done"] else "완료"

# 완료 상태 변경 버튼을 누르면 데이터베이스 값을 반대로 바꾼다.
        if c2.button(done_label, key="view_done", use_container_width=True):
            try:
# 선택한 일정의 완료 여부를 데이터베이스에서 수정한다.
                client.table("events").update(
                    {"done": not view_event["done"]}
                ).eq("id", view_id).eq("user_id", uid).execute()
# 정리된 로그인 상태로 화면을 다시 실행한다.
                st.rerun()
# 삭제 중 오류가 발생하면 실패 메시지를 표시한다.
            except Exception as exc:
                st.error(f"상태 변경에 실패했습니다: {exc}")

# 삭제 버튼을 누르면 삭제 확인 창을 열기 위한 ID를 저장한다.
        if c3.button("삭제", key="view_delete", use_container_width=True):
            st.session_state.pending_delete_id = view_id
# 변경된 선택 날짜와 팝업 상태를 화면에 반영한다.
            st.rerun()

# 상세 정보 패널을 닫도록 선택된 일정 ID를 비운다.
        if c4.button("닫기", key="view_close", use_container_width=True):
# 저장 후 기존 상세 정보 패널 선택 상태를 초기화한다.
            st.session_state.view_event_id = None
# 변경된 선택 날짜와 팝업 상태를 화면에 반영한다.
            st.rerun()


# ==========================================
# 10. 다가오는 일정
# ==========================================

# 오늘 날짜를 문자열로 바꿔 일정 날짜와 비교할 수 있게 한다.
today_str = today.isoformat()

# 오늘 이후의 미완료 일정 중 날짜와 중요도 순으로 정렬해 최대 5개를 고른다.
upcoming = sorted(
    [e for e in events if e["date"] >= today_str and not e["done"]],
    key=lambda e: (e["date"], ORDER[e["importance"]])
)[:5]

st.write("")

# 다가오는 일정 제목과 목록을 하나의 영역에 표시한다.
with st.container(key="upcoming"):
    h_title, h_more = st.columns([5, 1], vertical_alignment="center")

    with h_title:
        st.markdown(
            '<div class="panel-title"><i></i>다가오는 일정</div>',
            unsafe_allow_html=True
        )

    with h_more:
# 일정 저장 과정에서 발생할 수 있는 오류를 처리한다.
        try:
            st.page_link("pages/list.py", label="더보기 ›")
        except Exception:
            pass

# 다가오는 일정이 있을 때 목록을 만든다.
    if upcoming:
        rows = []

# 선택된 다가오는 일정을 하나씩 화면 표시용 문구로 변환한다.
        for e in upcoming:
# 일정 날짜를 날짜 객체로 바꿔 월·일·요일을 계산한다.
            d = date.fromisoformat(e["date"])
            meta = (
                f"{d.month}월 {d.day}일 ({theme.WEEKDAYS_KR[d.weekday()]})"
                f" · {d_label(d, today)}"
            )
# 일정 색상, 제목, D-day 정보를 한 줄의 HTML로 구성한다.
            rows.append(
                '<div class="up-row">'
                f'<span class="up-dot" style="background:{event_color(e)}"></span>'
                f'<span class="up-title">{esc(e["title"] or "(제목 없음)")}</span>'
                f'<span class="up-meta">{meta}</span>'
                '</div>'
            )

# 만든 일정 행들을 이어 붙여 화면에 표시한다.
        st.markdown("".join(rows), unsafe_allow_html=True)
# 표시할 일정이 없으면 안내 문구를 보여 준다.
    else:
        st.markdown(
            '<div class="up-empty">다가오는 일정이 없습니다.</div>',
            unsafe_allow_html=True
        )


# ==========================================
# 11. 일정 삭제 확인 창
# ==========================================

# 삭제 여부를 확인하는 팝업 창으로 함수를 표시한다.
@st.dialog("일정 삭제 확인")
# 삭제할 일정을 확인하고 관련 데이터를 데이터베이스에서 제거한다.
def confirm_delete_dialog(event_id):
# 전달받은 ID에 해당하는 일정 정보를 찾는다.
    target = next(
        (item for item in events if item["id"] == event_id),
        None
    )

# 삭제 대상이 존재하지 않으면 안내 후 함수를 종료한다.
    if target is None:
        st.warning("삭제할 일정을 찾을 수 없습니다.")
        return

    st.warning("이 일정을 삭제할까요? 삭제하면 복구할 수 없습니다.")
    st.markdown(f"**{target['title'] or '(제목 없음)'}**")
    st.caption(f"날짜: {target['date']}")

# 삭제 확인과 취소 버튼을 나란히 배치한다.
    yes, no = st.columns(2)

    with yes:
# 취소 버튼을 누르면 삭제하지 않고 팝업을 닫는다.
        if st.button(
            "삭제하기",
            type="primary",
            use_container_width=True,
            key="confirm_delete_yes"
        ):
            try:
# 해당 일정에 연결된 할 일 상태 데이터를 먼저 삭제한다.
                client.table("todo_status").delete().eq(
                    "event_id", event_id
                ).eq(
                    "user_id", uid
                ).execute()

# 현재 사용자 소유의 일정 데이터를 삭제한다.
                client.table("events").delete().eq(
                    "id", event_id
                ).eq(
                    "user_id", uid
                ).execute()

                st.session_state.view_event_id = None
                st.success("일정을 삭제했습니다.")
# 정리된 로그인 상태로 화면을 다시 실행한다.
                st.rerun()

# 삭제 중 오류가 발생하면 실패 메시지를 표시한다.
            except Exception as exc:
                st.error(f"일정 삭제에 실패했습니다: {exc}")

    with no:
# 취소 버튼을 누르면 삭제하지 않고 팝업을 닫는다.
        if st.button(
            "취소",
            use_container_width=True,
            key="confirm_delete_no"
        ):
# 변경된 선택 날짜와 팝업 상태를 화면에 반영한다.
            st.rerun()


# pop으로 꺼내 한 번만 열리게 함 (X/바깥 클릭으로 닫아도 다시 안 뜸)
# 삭제 대기 ID를 꺼내면서 세션에서 제거해 팝업이 반복해서 열리지 않게 한다.
pending_delete_id = st.session_state.pop("pending_delete_id", None)

# 삭제 대기 ID가 있을 때만 삭제 확인 팝업을 실행한다.
if pending_delete_id:
    confirm_delete_dialog(pending_delete_id)


# ==========================================
# 12. 일정 추가 및 수정 팝업창
# ==========================================

# 새 일정 입력과 기존 일정 수정을 위한 팝업 폼을 구성한다.
def event_editor_dialog():
# 수정 모드라면 편집할 일정의 ID를 가져온다.
    edit_id = st.session_state.get("edit_event_id")

# 수정할 일정이 있으면 기존 정보를 찾아 입력칸의 기본값으로 사용한다.
    existing = (
        next((e for e in events if e["id"] == edit_id), None)
        if edit_id else None
    )

# 새 일정이 저장될 날짜를 가져오고 값이 없으면 오늘로 설정한다.
    picked_date = st.session_state.get(
        "selected_date",
        theme.today_kst().isoformat()
    )

    st.caption(f"선택한 날짜: {picked_date}")

# 제목, 설명, 중요도, 카테고리를 하나의 입력 폼으로 묶는다.
    with st.form("event_editor"):
# 일정 제목을 입력받고 수정 시 기존 제목을 미리 표시한다.
        title = st.text_input(
            "일정 제목",
            value=existing["title"] if existing else ""
        )

# 일정에 대한 추가 설명을 입력받는다.
        description = st.text_area(
            "부가 설명",
            value=existing["description"] if existing else ""
        )

# 선택 가능한 중요도 항목을 정의한다.
        imp_options = ["없음", "상", "중", "하"]

# 일정의 중요도를 라디오 버튼으로 하나 선택하게 한다.
        importance = st.radio(
            "중요도",
            imp_options,
            index=imp_options.index(
                existing["importance"] if existing else "없음"
            ),
            horizontal=True
        )

# 일정에 해당하는 카테고리를 여러 개 선택하게 한다.
        categories = st.multiselect(
            "카테고리",
            CATEGORIES,
            default=existing["categories"] if existing else []
        )

# 저장 버튼을 눌렀는지 확인한다.
        save = st.form_submit_button(
            "저장",
            type="primary",
            use_container_width=True
        )

# 저장 버튼을 눌렀을 때 입력값을 일정 데이터로 구성한다.
    if save:
# 데이터베이스 저장 함수에 전달할 일정 정보를 만든다.
        event = {
# 수정이면 기존 ID를 유지하고 새 일정이면 고유 ID를 생성한다.
            "id": edit_id or str(uuid.uuid4()),
            "date": picked_date,
# 제목 앞뒤의 불필요한 공백을 제거한다.
            "title": title.strip(),
# 설명 앞뒤의 불필요한 공백을 제거한다.
            "description": description.strip(),
            "importance": importance,
            "categories": categories
        }

# 일정 저장 과정에서 발생할 수 있는 오류를 처리한다.
        try:
# 정리한 일정 정보를 Supabase에 저장하거나 갱신한다.
            write_event(client, uid, event)

# 저장 후 수정 모드 상태를 초기화한다.
            st.session_state.edit_event_id = None
# 저장 후 기존 상세 정보 패널 선택 상태를 초기화한다.
            st.session_state.view_event_id = None

# 저장이 완료되었음을 사용자에게 알린다.
            st.success("일정을 저장했습니다.")
# 변경된 선택 날짜와 팝업 상태를 화면에 반영한다.
            st.rerun()

# 저장에 실패하면 오류 메시지를 표시한다.
        except Exception as exc:
            st.error(f"저장 실패: {exc}")

# 취소 버튼을 누르면 수정 모드를 해제하고 화면을 다시 실행한다.
    if st.button(
        "취소",
        key="cancel_event_dialog",
        use_container_width=True
    ):
        st.session_state.edit_event_id = None
        st.rerun()


# pop으로 꺼내 한 번만 열리게 하고, 수정 모드면 제목도 바꿈
# 일정 입력 창 열기 요청을 한 번만 꺼내 팝업을 실행한다.
if st.session_state.pop("show_event_form", False):
# 일정 ID가 있으면 수정 모드, 없으면 새 일정 추가 모드로 판단한다.
    is_edit = bool(st.session_state.get("edit_event_id"))
# 모드에 따라 팝업 제목을 정하고 일정 편집 함수를 팝업으로 표시한다.
    st.dialog(
        "일정 수정" if is_edit else "일정 추가",
        width="large"
    )(event_editor_dialog)()
