"""하루결 공통 모듈: 테마(화이트 / 블랙 / 파스텔), 사이드바, 로그인 확인."""

import html
from datetime import datetime, timedelta, timezone

import streamlit as st

KST = timezone(timedelta(hours=9))

CATEGORIES = [
    "수행평가", "시험", "동아리",
    "개인일정", "과제", "학교행사", "기타"
]

IMPORTANCE_COLOR = {
    "상": "#F58AB0",
    "중": "#F7C65B",
    "하": "#7DD3A8",
    "없음": "#A7A9F5",
}
IMPORTANCE_ORDER = {"상": 0, "중": 1, "하": 2, "없음": 3}
PERSONAL_COLOR = "#7CC3F3"
DONE_COLOR = "#C9CCD6"

WEEKDAYS_KR = ["월", "화", "수", "목", "금", "토", "일"]
WEEKDAYS_EN = [
    "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY",
    "FRIDAY", "SATURDAY", "SUNDAY"
]
MONTHS_EN = [
    "JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY",
    "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"
]


def today_kst():
    """서버가 UTC여도 한국 시간 기준의 오늘 날짜를 돌려준다."""
    return datetime.now(KST).date()


def esc(text):
    return html.escape(str(text or ""))


# ==========================================
# 1. 테마 팔레트
# ==========================================

DEFAULT_THEME = "pastel"

THEMES = {
    "white": {
        "label": "화이트",
        "desc": "깔끔한 흰 배경",
        "scheme": "light",
        "page_bg": "#FFFFFF",
        "sidebar": "#F6F7F9",
        "bg": "#FFFFFF",
        "card": "#FFFFFF",
        "text": "#1C1E23",
        "sub": "#6B7280",
        "accent": "#8D91F2",
        "accent_text": "#4F54D6",
        "soft": "#EFF0FD",
        "border": "#E7E9EE",
        "hdr": "#F7F8FA",
        "input": "#FFFFFF",
        "shadow": "0 10px 34px rgba(17,24,39,.08)",
        "tile1": "#F0F1FD",
        "tile1_text": "#4F54D6",
        "tile2": "#F3F4F6",
        "tile2_text": "#374151",
        "sun": "#E5484D",
        "sat": "#3B6FE0",
        "rail": "#E9EBF0",
        "grad": "linear-gradient(90deg,#B4B7F8,#8D91F2)",
        "today": "#E6E8FC",
        "on_accent": "#FFFFFF",
        "ring_a": "#E4E6EE",
        "ring_b": "#C3C7D6",
        "line": "#E3E6EC",
    },
    "black": {
        "label": "블랙",
        "desc": "눈이 편한 어두운 화면",
        "scheme": "dark",
        "page_bg": "#0E1014",
        "sidebar": "#13161C",
        "bg": "#0E1014",
        "card": "#1A1D25",
        "text": "#ECEEF3",
        "sub": "#9BA1B3",
        "accent": "#8D91F2",
        "accent_text": "#B4B7FA",
        "soft": "#262A3A",
        "border": "#2A2E3A",
        "hdr": "#1F232D",
        "input": "#12151B",
        "shadow": "0 14px 44px rgba(0,0,0,.55)",
        "tile1": "#23274A",
        "tile1_text": "#C9CBFB",
        "tile2": "#3A2233",
        "tile2_text": "#F5B5D3",
        "sun": "#F27BA9",
        "sat": "#7B9CF5",
        "rail": "#2A2E3A",
        "grad": "linear-gradient(90deg,#6B6FE0,#9A9EF8)",
        "today": "#2F3560",
        "on_accent": "#FFFFFF",
        "ring_a": "#3A3F55",
        "ring_b": "#262A3A",
        "line": "#2A2E3A",
    },
    "pastel": {
        "label": "파스텔",
        "desc": "부드러운 라벤더 · 핑크",
        "scheme": "light",
        "page_bg": (
            "radial-gradient(900px 520px at 100% 0%, rgba(196,206,254,.38), transparent 60%),"
            "radial-gradient(800px 560px at 100% 100%, rgba(251,207,232,.38), transparent 60%),"
            "#F8F7FF"
        ),
        "sidebar": "linear-gradient(180deg,#EFEEFD 0%,#F6F1FC 62%,#FCE9F4 100%)",
        "bg": "#F8F7FF",
        "card": "#FFFFFF",
        "text": "#25264D",
        "sub": "#8587B8",
        "accent": "#8D91F2",
        "accent_text": "#5D61D8",
        "soft": "#E8E9FD",
        "border": "#ECEBFA",
        "hdr": "#F6F5FE",
        "input": "#FFFFFF",
        "shadow": "0 14px 44px rgba(141,145,242,.20)",
        "tile1": "#EFEAFE",
        "tile1_text": "#4B4F9E",
        "tile2": "#FDE8F3",
        "tile2_text": "#8A3A68",
        "sun": "#EC6FA3",
        "sat": "#5C86EE",
        "rail": "#ECEDFB",
        "grad": "linear-gradient(90deg,#C3C6FB,#8D91F2)",
        "today": "#DDE3FF",
        "on_accent": "#FFFFFF",
        "ring_a": "#D9DBFD",
        "ring_b": "#A9ADF6",
        "line": "#D8D9F2",
    },
}


def current_name():
    name = st.session_state.get("theme", DEFAULT_THEME)
    return name if name in THEMES else DEFAULT_THEME


def palette(name=None):
    return THEMES[name if name in THEMES else current_name()]


def _fill(template, p):
    for key, value in p.items():
        template = template.replace(f"__{key}__", value)
    return template


# ==========================================
# 2. 공통 스타일 (Streamlit 화면)
# ==========================================

BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap');

:root { color-scheme: __scheme__; }

html, body, .stApp, button, input, textarea, select {
  font-family: 'Noto Sans KR', -apple-system, 'Segoe UI', 'Apple SD Gothic Neo', sans-serif;
}
.stApp { background: __page_bg__; background-attachment: fixed; color: __text__; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebarNav"] { display: none; }
[data-testid="stSidebar"] { background: __sidebar__; border-right: none; }
[data-testid="stSidebar"] > div:first-child { background: transparent; }
.block-container { padding-top: 2.4rem; padding-bottom: 3rem; max-width: 1180px; }

/* 스타일을 넣기 위한 빈 요소가 공간을 차지하지 않게 */
[data-testid="stElementContainer"]:has(style), .element-container:has(style) { display: none; }

/* ---------- 글자색 ---------- */
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
.stApp [data-testid="stMarkdownContainer"],
.stApp [data-testid="stMarkdownContainer"] p,
.stApp [data-testid="stMarkdownContainer"] li,
.stApp label, .stApp [data-testid="stWidgetLabel"] p { color: __text__; }
.stApp [data-testid="stCaptionContainer"],
.stApp [data-testid="stCaptionContainer"] p { color: __sub__; }
.stApp hr { border-color: __border__; }

/* ---------- 버튼 ---------- */
.stApp button[data-testid^="stBaseButton-secondary"] {
  border-radius: 999px; border: 1px solid __border__; background: __card__; color: __text__;
  font-weight: 600; padding: .5rem 1.2rem; box-shadow: none; transition: all .15s ease;
}
.stApp button[data-testid^="stBaseButton-secondary"]:hover {
  border-color: __accent__; background: __soft__; color: __accent_text__;
}
.stApp button[data-testid^="stBaseButton-primary"] {
  border-radius: 999px; border: 1px solid __accent__; background: __accent__; color: __on_accent__;
  font-weight: 600; padding: .5rem 1.2rem; box-shadow: none;
}
.stApp button[data-testid^="stBaseButton-primary"]:hover { filter: brightness(1.06); color: __on_accent__; }
.stApp button:disabled { opacity: .65; }
.stApp button [data-testid="stMarkdownContainer"] p,
.stApp a [data-testid="stMarkdownContainer"] p { color: inherit; }

/* ---------- 입력창 ---------- */
.stApp [data-baseweb="input"], .stApp [data-baseweb="base-input"],
.stApp [data-baseweb="textarea"], .stApp [data-baseweb="select"] > div {
  background: __input__; border-color: __border__; border-radius: 14px;
}
.stApp input, .stApp textarea { color: __text__; -webkit-text-fill-color: __text__; }
[data-baseweb="popover"] [data-baseweb="menu"], [data-baseweb="popover"] ul { background: __card__; color: __text__; }
[data-baseweb="popover"] li { color: __text__; }
[data-baseweb="calendar"] { background: __card__; color: __text__; }

/* ---------- 팝업 / 탭 ---------- */
div[role="dialog"] { background: __card__; color: __text__; border-radius: 24px; }
button[data-baseweb="tab"] { color: __sub__; }
button[data-baseweb="tab"][aria-selected="true"] { color: __accent_text__; }
[data-baseweb="tab-highlight"] { background: __accent__; }

/* ---------- 사이드바 ---------- */
.brand { font-size: 1.9rem; font-weight: 500; line-height: 1.12; color: __text__; letter-spacing: -.01em; }
.brand b { font-weight: 500; color: __accent_text__; opacity: .85; }
.brand-line { width: 46px; height: 2px; background: __accent__; opacity: .45; margin: 16px 0 22px; border-radius: 2px; }
.stApp [class*="st-key-nav_"] button[data-testid^="stBaseButton"] {
  justify-content: flex-start; border: none; background: transparent; color: __sub__;
  border-radius: 18px; padding: .8rem 1rem; font-weight: 500; gap: .7rem; width: 100%;
}
.stApp [class*="st-key-nav_"] button[data-testid^="stBaseButton"]:hover { background: __soft__; color: __accent_text__; }
.stApp [class*="st-key-nav_active_"] button[data-testid^="stBaseButton"] {
  background: __soft__; color: __accent_text__; font-weight: 600;
}
.side-user { font-size: .8rem; color: __sub__; margin-top: 2.2rem; word-break: break-all; }
.stApp .st-key-side_logout button[data-testid^="stBaseButton"] {
  padding: .35rem .9rem; font-size: .85rem; color: __sub__; background: transparent;
}

/* ---------- 공통 문구 ---------- */
.page-title { font-size: 1.9rem; font-weight: 700; color: __text__; margin-bottom: .2rem; }
.section-title { font-size: 1.1rem; font-weight: 700; color: __text__; margin: 1.6rem 0 .6rem; }
.panel-title { font-size: 1.05rem; font-weight: 700; color: __text__; }
.panel-title i { display: inline-block; width: 5px; height: 18px; border-radius: 3px;
  background: __accent__; margin-right: 10px; vertical-align: -3px; }
.chip { display: inline-block; padding: 3px 12px; border-radius: 999px; background: __soft__;
  color: __accent_text__; font-size: .8rem; font-weight: 600; margin: 0 6px 6px 0; }
.muted { color: __sub__; }

/* ---------- 캘린더 화면 ---------- */
.month-title { font-size: 1.75rem; font-weight: 600; color: __text__; letter-spacing: -.01em; white-space: nowrap; text-align: center; }
.stApp .st-key-cal_prev button[data-testid^="stBaseButton"],
.stApp .st-key-cal_next button[data-testid^="stBaseButton"] {
  border: none; background: transparent; box-shadow: none; font-size: 1.9rem; line-height: 1;
  padding: 0 .6rem; color: __sub__;
}
.stApp .st-key-cal_prev button[data-testid^="stBaseButton"]:hover,
.stApp .st-key-cal_next button[data-testid^="stBaseButton"]:hover { background: __soft__; color: __accent_text__; }
.stApp .st-key-cal_add button[data-testid^="stBaseButton"] {
  background: __soft__; color: __accent_text__; border: 1px solid __border__; padding: .65rem 1.4rem;
}
.stApp .st-key-upcoming, .stApp .st-key-detail_panel, .stApp .st-key-week_panel, .stApp .st-key-account_card {
  background: __card__; border: 1px solid __border__; border-radius: 22px; padding: 1.1rem 1.5rem 1.2rem;
  box-shadow: 0 4px 24px rgba(0,0,0,.03);
}
.stApp .st-key-detail_panel { margin-top: 1rem; }
.up-row { display: flex; align-items: center; gap: 12px; padding: 11px 4px; border-top: 1px solid __border__; }
.up-dot { width: 10px; height: 10px; border-radius: 50%; flex: none; }
.up-title { flex: 1; min-width: 0; font-weight: 500; color: __text__; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.up-meta { color: __sub__; font-size: .85rem; white-space: nowrap; }
.up-empty { text-align: center; color: __sub__; padding: 20px 0 10px; border-top: 1px solid __border__; }
.stApp .st-key-upcoming [data-testid="stPageLink-NavLink"] { justify-content: flex-end; color: __sub__; }

/* ---------- 플래너 화면 ---------- */
.date-head { display: flex; align-items: center; gap: 18px; }
.date-head .line { flex: 1; height: 1px; background: __line__; }
.date-chip { display: flex; align-items: center; gap: 10px; color: __sub__; font-weight: 600;
  letter-spacing: .06em; font-size: .98rem; white-space: nowrap; }
.stApp .st-key-prev_day button[data-testid^="stBaseButton"],
.stApp .st-key-next_day button[data-testid^="stBaseButton"] {
  width: 52px; height: 52px; min-height: 52px; padding: 0; border-radius: 50%; border: none;
  background: __soft__; color: __accent_text__; font-size: 1.9rem; line-height: 1;
  display: flex; align-items: center; justify-content: center; margin: 0 auto;
}
.stApp .st-key-prev_day button[data-testid^="stBaseButton"]:hover,
.stApp .st-key-next_day button[data-testid^="stBaseButton"]:hover { filter: brightness(.96); background: __soft__; }
.stApp .st-key-planner_card {
  background: __card__; border-radius: 30px; padding: 2.6rem 1.8rem 1.6rem; margin-top: 2.4rem;
  box-shadow: __shadow__; position: relative; gap: .2rem;
}
.rings { display: flex; justify-content: space-between; padding: 0 7%; margin: -4.4rem 0 1.2rem; position: relative; z-index: 2; }
.rings i { display: block; width: 13px; height: 40px; border-radius: 9px;
  background: linear-gradient(180deg, __ring_a__, __ring_b__); box-shadow: 0 3px 8px rgba(120,120,200,.22); }
.card-head { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }
.card-title { font-size: 1.3rem; font-weight: 700; color: __text__; }
.card-count { font-size: 1.05rem; font-weight: 600; color: __sub__; white-space: nowrap; }
.pbar { height: 12px; border-radius: 99px; background: __rail__; overflow: hidden; margin: 14px 0 6px; }
.pbar > div { height: 100%; border-radius: 99px; background: __grad__; }
.stApp [class*="st-key-item_"] { border-bottom: 1px solid __border__; gap: 0; }
.stApp [class*="st-key-item_"] button[data-testid^="stBaseButton"] {
  justify-content: flex-start; background: transparent; border: none; box-shadow: none; width: 100%;
  text-align: left; padding: .5rem .2rem; font-size: 1.05rem; font-weight: 500; color: __text__;
  gap: .9rem; border-radius: 12px;
}
.stApp [class*="st-key-item_"] button[data-testid^="stBaseButton"]:hover { background: __hdr__; color: __text__; }
.stApp [class*="st-key-item_"] [data-testid="stIconMaterial"] { font-size: 1.9rem; color: __sub__; }
.stApp [class*="st-key-item_done_"] button[data-testid^="stBaseButton"] { color: __sub__; }
.stApp [class*="st-key-item_done_"] [data-testid="stIconMaterial"] { color: __accent__; }
.item-meta { font-size: .8rem; color: __sub__; padding: 0 0 .55rem 3.1rem; line-height: 1.5; margin-top: -.3rem; }
.planner-empty { text-align: center; color: __sub__; padding: 2rem 0 1.4rem; }
.tiles { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 1.2rem; }
.tile { border-radius: 20px; padding: 14px 10px 12px; text-align: center; }
.tile .t { font-weight: 500; font-size: .95rem; }
.tile .n { font-size: 2rem; font-weight: 700; line-height: 1.2; margin-top: 2px; }
.stApp .st-key-week_panel button[data-testid^="stBaseButton"] { width: 100%; padding: .45rem .2rem; font-size: .9rem; }
.week-note { text-align: center; font-size: .78rem; color: __sub__; margin-top: 4px; }

/* ---------- 설정 화면 ---------- */
.tp { height: 118px; border-radius: 16px; display: flex; overflow: hidden; }
.tp-side { width: 26%; }
.tp-main { flex: 1; padding: 12px; }
.tp-card { height: 100%; border-radius: 10px; padding: 10px; box-sizing: border-box; }
.tp-card i { display: block; height: 8px; border-radius: 6px; margin-bottom: 8px; }
.tp-name { font-weight: 700; margin: 10px 0 0; color: __text__; }
.tp-desc { font-size: .82rem; color: __sub__; margin-bottom: 8px; }
"""


def build_css(name=None):
    return _fill(BASE_CSS, palette(name))


# ==========================================
# 3. 캘린더(FullCalendar iframe) 스타일
# ==========================================

CALENDAR_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap');
html, body { background: transparent; font-family: 'Noto Sans KR', -apple-system, 'Segoe UI', sans-serif; }
.fc { color: __text__; --fc-border-color: __border__; --fc-page-bg-color: transparent;
  --fc-neutral-bg-color: __hdr__; --fc-today-bg-color: transparent; --fc-event-border-color: transparent; }
.fc-view-harness { background: __card__; border-radius: 22px; border: 1px solid __border__; overflow: hidden;
  box-shadow: 0 4px 24px rgba(0,0,0,.03); }
.fc .fc-scrollgrid { border: 0; margin: -1px; width: calc(100% + 2px) !important; }

/* 요일 머리글: 영어 대신 한글 요일로 */
.fc .fc-col-header-cell { background: __hdr__; padding: 12px 0; }
.fc .fc-col-header-cell-cushion { font-size: 0; display: block; padding: 0; text-decoration: none; }
.fc .fc-col-header-cell-cushion::after { font-size: .92rem; font-weight: 600; color: __sub__; }
.fc .fc-day-sun .fc-col-header-cell-cushion::after { content: "일"; color: __sun__; }
.fc .fc-day-mon .fc-col-header-cell-cushion::after { content: "월"; }
.fc .fc-day-tue .fc-col-header-cell-cushion::after { content: "화"; }
.fc .fc-day-wed .fc-col-header-cell-cushion::after { content: "수"; }
.fc .fc-day-thu .fc-col-header-cell-cushion::after { content: "목"; }
.fc .fc-day-fri .fc-col-header-cell-cushion::after { content: "금"; }
.fc .fc-day-sat .fc-col-header-cell-cushion::after { content: "토"; color: __sat__; }

/* 날짜 칸 */
.fc .fc-daygrid-day { cursor: pointer; }
.fc .fc-daygrid-day:hover { background: __hdr__; }
.fc .fc-daygrid-day-top { flex-direction: row; justify-content: center; padding-top: 5px; }
.fc .fc-daygrid-day-number { display: flex; align-items: center; justify-content: center; width: 34px; height: 34px;
  padding: 0; border-radius: 50%; color: __text__; font-weight: 500; font-size: 1.02rem; text-decoration: none; }
.fc .fc-day-sun .fc-daygrid-day-number { color: __sun__; }
.fc .fc-day-sat .fc-daygrid-day-number { color: __sat__; }
.fc .fc-day-other .fc-daygrid-day-top { opacity: .38; }
.fc .fc-day-today { background: transparent !important; }
.fc .fc-day-today .fc-daygrid-day-number { background: __today__; color: __accent_text__; font-weight: 700; }

/* 일정이 있는 날: 숫자 뒤에 둥근 색 배경 */
.fc .fc-daygrid-bg-harness { left: 0 !important; right: 0 !important; display: flex;
  justify-content: center; align-items: flex-start; padding-top: 5px; }
.fc .fc-bg-event { position: static !important; width: 34px; height: 34px; border-radius: 50%;
  opacity: 1 !important; flex: none; }

/* 일정: 점 + 제목 */
.fc .fc-daygrid-event { font-size: .72rem; margin: 1px 6px; border-radius: 6px; }
.fc .fc-daygrid-dot-event { padding: 2px 4px; }
.fc .fc-daygrid-dot-event:hover { background: __soft__; }
.fc .fc-daygrid-event-dot { margin: 0 6px 0 0; border-width: 4px; }
.fc .fc-daygrid-dot-event .fc-event-title { color: __sub__; font-weight: 500; }
.fc .ev-done .fc-event-title { text-decoration: line-through; opacity: .6; }
.fc .fc-more-link { color: __accent_text__; font-size: .72rem; font-weight: 600; }
.fc .fc-popover { background: __card__; border-color: __border__; border-radius: 14px; }
.fc .fc-popover-header { background: __hdr__; color: __text__; }
"""


def calendar_css(name=None):
    return _fill(CALENDAR_CSS, palette(name))


# ==========================================
# 4. 사이드바 / 로그인 확인 / 테마 저장
# ==========================================

NAV = [
    ("calendar", "Calendar", "main.py", ":material/calendar_month:"),
    ("planner", "My Planner", "pages/list.py", ":material/task_alt:"),
    ("settings", "Settings", "pages/settings.py", ":material/settings:"),
]


def brand_html():
    return (
        '<div class="brand">Daily<br><b>Planner</b></div>'
        '<div class="brand-line"></div>'
    )


def sign_out():
    client = st.session_state.get("supabase_client")

    if client:
        try:
            client.auth.sign_out()
        except Exception:
            pass

    for key in (
        "supabase_client", "supabase_access_token",
        "supabase_refresh_token", "user_id",
        "user_email", "supabase_session_restored"
    ):
        st.session_state.pop(key, None)


def render_sidebar(active=None):
    with st.sidebar:
        st.markdown(brand_html(), unsafe_allow_html=True)

        for key, label, path, icon in NAV:
            button_key = f"nav_active_{key}" if key == active else f"nav_{key}"

            if st.button(label, key=button_key, icon=icon, use_container_width=True):
                try:
                    st.switch_page(path)
                except Exception:
                    st.warning(
                        "페이지 파일을 찾을 수 없어요. "
                        "main.py와 pages 폴더(list.py, settings.py) 위치를 확인해 주세요."
                    )

        email = st.session_state.get("user_email")

        if email:
            st.markdown(
                f'<div class="side-user">{esc(email)}</div>',
                unsafe_allow_html=True
            )

            if st.button("로그아웃", key="side_logout"):
                sign_out()
                st.switch_page("main.py")


def apply_theme(sidebar=True, active=None):
    css = build_css()

    if not sidebar:
        css += (
            "[data-testid='stSidebar'], [data-testid='stSidebarCollapsedControl'],"
            "[data-testid='collapsedControl'] { display: none; }"
        )

    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    if sidebar:
        render_sidebar(active)


def page_setup(active):
    """pages/ 안의 화면에서 쓰는 공통 시작 코드. 로그인이 안 되어 있으면 안내 후 멈춘다."""
    client = st.session_state.get("supabase_client")
    uid = st.session_state.get("user_id")

    if not client or not uid:
        apply_theme(sidebar=False)
        st.markdown(brand_html(), unsafe_allow_html=True)
        st.info("먼저 캘린더 화면에서 로그인해 주세요.")

        try:
            st.page_link("main.py", label="로그인하러 가기", icon=":material/login:")
        except Exception:
            pass

        st.stop()

    apply_theme(sidebar=True, active=active)
    return client, uid


def load_from_user(user):
    """로그인할 때 계정에 저장해 둔 테마를 불러온다."""
    meta = getattr(user, "user_metadata", None) or {}
    saved = meta.get("theme") if isinstance(meta, dict) else None

    if saved in THEMES:
        st.session_state.theme = saved


def set_theme(name):
    """테마를 바꾸고 계정(Supabase 사용자 정보)에도 저장한다."""
    if name not in THEMES:
        return

    st.session_state.theme = name
    client = st.session_state.get("supabase_client")

    if client:
        try:
            client.auth.update_user({"data": {"theme": name}})
        except Exception:
            pass
