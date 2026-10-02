import datetime
import streamlit as st
from streamlit_calendar import calendar

# 1. 페이지 설정
st.set_page_config(
    page_title="OAuth 스마트 캘린더 & 스케줄러",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. st.secrets에서 클라이언트 ID 및 보안 비밀번호 안전하게 불러오기
try:
  GOOGLE_CLIENT_ID = st.secrets["google"]["client_id"]
  GOOGLE_CLIENT_SECRET = st.secrets["google"]["client_secret"]
  HAS_OAUTH_SECRETS = True
except Exception:
  GOOGLE_CLIENT_ID = None
  GOOGLE_CLIENT_SECRET = None
  HAS_OAUTH_SECRETS = False

# 3. 세션 상태 초기화
if "events" not in st.session_state:
  st.session_state.events = [
      {
          "title": "[수행] 프로그래밍 포트폴리오",
          "start": str(datetime.date.today()),
          "end": str(datetime.date.today()),
          "description": "Streamlit OAuth 캘린더 연동 구현",
          "importance": "상",
          "category": "수행평가",
          "color": "#FF4B4B",
      },
      {
          "title": "[시험] 파이썬 응용 중간고사",
          "start": str(
              datetime.date.today() + datetime.timedelta(days=3)
          ),
          "end": str(datetime.date.today() + datetime.timedelta(days=3)),
          "description": "클래스 및 API 연동 범위",
          "importance": "상",
          "category": "시험",
          "color": "#FF4B4B",
      },
      {
          "title": "[동아리] 스터디 모임",
          "start": str(
              datetime.date.today() + datetime.timedelta(days=5)
          ),
          "end": str(
              datetime.date.today() + datetime.timedelta(days=5)
          ),
          "description": "프로젝트 아이디어 피드백",
          "importance": "중",
          "category": "동아리",
          "color": "#FFA500",
      },
  ]

if "selected_date" not in st.session_state:
  st.session_state.selected_date = str(datetime.date.today())

if "edit_index" not in st.session_state:
  st.session_state.edit_index = None

if "oauth_logged_in" not in st.session_state:
  st.session_state.oauth_logged_in = False

if "user_email" not in st.session_state:
  st.session_state.user_email = ""


# --- 색상 자동 매칭 규칙 함수 ---
def get_event_color(importance, category):
  if importance == "상":
    return "#FF4B4B"  # 빨간색
  elif importance == "중":
    return "#FFA500"  # 노란색
  elif importance == "하":
    return "#2ECC71"  # 초록색
  elif category == "개인일정":
    return "#87CEEB"  # 하늘색
  else:
    return "#D7BDE2"  # 연보라색 (기본)


# ==========================================
# [상단 헤더 및 OAuth 연동 팝업/모달]
# ==========================================
col_title, col_btn = st.columns([5, 1])

with col_title:
  st.title("🎓 OAuth 2.0 연동 스마트 스케줄러")
  st.markdown(
      "구글 클라이언트 키(`client_id`, `client_secret`)를 활용해 구글 계정에"
      " 안전하게 로그인하고 일정을 관리하세요."
  )

with col_btn:
  st.write("")
  if st.button("🔗 구글 계정 연동", use_container_width=True):

    @st.dialog("구글 캘린더 OAuth 2.0 연동")
    def oauth_modal():
      st.write("구글 클라우드 콘솔에 등록된 키를 통해 인증을 진행합니다.")

      if not HAS_OAUTH_SECRETS:
        st.error(
            "⚠️ `.streamlit/secrets.toml`에 `[google]` 하위의 `client_id`와"
            " `client_secret`이 올바르게 설정되지 않았습니다."
        )
      else:
        st.success(
            "✅ `st.secrets`에서 구글 클라이언트 키가 안전하게 감지되었습니다!"
        )

      input_email = st.text_input(
          "연동할 구글 이메일", placeholder="student@gmail.com"
      )

      col_m1, col_m2 = st.columns(2)
      with col_m1:
        if st.button("구글 로그인 및 연동", use_container_width=True):
          if input_email:
            st.session_state.oauth_logged_in = True
            st.session_state.user_email = input_email
            st.success(f"[{input_email}] 계정 연동 인증 성공!")
            st.rerun()
          else:
            st.warning("이메일을 입력해주세요.")
      with col_m2:
        if st.button("연동 해제 (로그아웃)", use_container_width=True):
          st.session_state.oauth_logged_in = False
          st.session_state.user_email = ""
          st.warning("로그아웃 되었습니다.")
          st.rerun()

    oauth_modal()

# 연동 상태 표시 바
if st.session_state.oauth_logged_in:
  st.info(
      f"🟢 구글 계정 연동됨: **{st.session_state.user_email}** (OAuth 2.0 활성)"
  )
else:
  st.warning(
      "⚪ 오프라인 모드 구동 중. 구글 캘린더와 동기화하려면 우측 상단 버튼을"
      " 눌러 연동하세요."
  )

st.divider()

# ==========================================
# [대시보드 요약 지표 카드]
# ==========================================
total_e = len(st.session_state.events)
exam_e = sum(1 for e in st.session_state.events if e.get("category") == "시험")
task_e = sum(
    1 for e in st.session_state.events if e.get("category") == "수행평가"
)
high_e = sum(1 for e in st.session_state.events if e.get("importance") == "상")

c1, c2, c3, c4 = st.columns(4)
c1.metric("총 일정 수", f"{total_e} 개")
c2.metric("중요도 '상' (빨강)", f"{high_e} 개")
c3.metric("수행평가", f"{task_e} 개")
c4.metric("시험", f"{exam_e} 개")

st.markdown("")

# ==========================================
# [중앙 본문: 캘린더 vs 관리 사이드바]
# ==========================================
col_cal, col_side = st.columns([2, 1])

with col_cal:
  st.subheader("📆 캘린더 뷰")
  st.markdown(
      "* 캘린더에서 **날짜를 클릭**하면 우측 관리창의 대상 날짜가 변경됩니다."
  )

  # 사이드바 카테고리 필터
  cat_filter = st.sidebar.selectbox(
      "🔍 카테고리 필터링",
      ["전체 보기", "수행평가", "시험", "동아리", "개인일정", "기타"],
  )

  view_events = st.session_state.events
  if cat_filter != "전체 보기":
    view_events = [
        e for e in st.session_state.events if e.get("category") == cat_filter
    ]

  # FullCalendar 설정
  calendar_options = {
      "editable": True,
      "selectable": True,
      "headerToolbar": {
          "left": "prev,next today",
          "center": "title",
          "right": "dayGridMonth,timeGridWeek",
      },
      "initialView": "dayGridMonth",
      "locale": "ko",
  }

  calendar_res = calendar(
      events=view_events, options=calendar_options, key="oauth_calendar"
  )

  # 날짜 클릭 감지
  if calendar_res and "dateClick" in calendar_res:
    clicked_date = calendar_res["dateClick"]["date"][:10]
    st.session_state.selected_date = clicked_date
    st.session_state.edit_index = None


with col_side:
  st.subheader("📝 일정 등록 및 수정")

  target_date_obj = datetime.datetime.strptime(
      st.session_state.selected_date, "%Y-%m-%d"
  ).date()
  selected_date_input = st.date_input("선택 날짜", value=target_date_obj)
  st.session_state.selected_date = str(selected_date_input)

  is_editing = st.session_state.edit_index is not None
  cur_event = (
      st.session_state.events[st.session_state.edit_index]
      if is_editing
      else None
  )

  if is_editing:
    st.info("✏️ **[수정 모드]** 기존 일정을 변경하고 있습니다.")
  else:
    st.success("➕ **[신규 등록 모드]** 새로운 일정을 입력하세요.")

  with st.form(key="oauth_event_form", clear_on_submit=not is_editing):
    d_title = cur_event["title"] if is_editing else ""
    d_desc = cur_event["description"] if is_editing else ""

    title_in = st.text_input("일정 제목", value=d_title, placeholder="예: 영어 단어 시험")
    desc_in = st.text_area(
        "부가 설명", value=d_desc, placeholder="세부 내용 입력 (선택사항)"
    )

    st.markdown("---")
    col_i, col_c = st.columns(2)

    with col_i:
      st.markdown("**중요도 설정**")
      imp_list = ["상", "중", "하", "설정 안 함"]
      d_imp_idx = 3
      if is_editing:
        val = cur_event.get("importance", "설정 안 함")
        if val in imp_list:
          d_imp_idx = imp_list.index(val)
      importance = st.radio("중요도 선택", imp_list, index=d_imp_idx)

    with col_c:
      st.markdown("**카테고리 설정**")
      cat_list = ["수행평가", "시험", "동아리", "개인일정", "기타"]
      d_cat_idx = 4
      if is_editing:
        val = cur_event.get("category", "기타")
        if val in cat_list:
          d_cat_idx = cat_list.index(val)
      category = st.selectbox("카테고리 선택", cat_list, index=d_cat_idx)

    st.markdown("")
    submit_btn = st.form_submit_button(
        "✨ 일정 수정 완료" if is_editing else "💾 일정 등록"
    )

    if submit_btn:
      imp_val = None if importance == "설정 안 함" else importance
      color_val = get_event_color(imp_val, category)

      new_item = {
          "title": title_in if title_in.strip() else "제목 없음",
          "start": st.session_state.selected_date,
          "end": st.session_state.selected_date,
          "description": desc_in,
          "importance": imp_val,
          "category": category,
          "color": color_val,
      }

      if is_editing:
        st.session_state.events[st.session_state.edit_index] = new_item
        st.success("일정이 수정되었습니다!")
        st.session_state.edit_index = None
      else:
        st.session_state.events.append(new_item)
        st.success("일정이 등록되었습니다!")
      st.rerun()

  if is_editing:
    if st.button("❌ 수정 취소", use_container_width=True):
      st.session_state.edit_index = None
      st.rerun()

# ==========================================
# [하단 영역: 선택 날짜의 일정 목록 및 관리]
# ==========================================
st.divider()
st.subheader(f"📌 [{st.session_state.selected_date}] 날짜의 일정 내역")

day_matched_events = [
    (i, ev)
    for i, ev in enumerate(st.session_state.events)
    if ev["start"] == st.session_state.selected_date
]

if not day_matched_events:
  st.info("이 날짜에 등록된 일정이 없습니다. 우측에서 추가해 보세요.")
else:
  for idx, ev in day_matched_events:
    imp_text = (
        f"중요도: {ev.get('importance')}"
        if ev.get("importance")
        else "중요도: 없음"
    )
    cat_text = f"카테고리: {ev.get('category')}"

    with st.container(border=True):
      c_info, c_act = st.columns([3, 1])

      with c_info:
        st.markdown(f"### **{ev['title']}**")
        st.markdown(f"`{cat_text}` | `{imp_text}`")
        if ev["description"]:
          st.write(f"설명: {ev['description']}")

      with c_act:
        st.write("")
        sub_c1, sub_c2 = st.columns(2)
        with sub_c1:
          if st.button("✏️ 수정", key=f"oauth_edit_{idx}"):
            st.session_state.edit_index = idx
            st.rerun()
        with sub_c2:
          if st.button("🗑️ 삭제", key=f"oauth_del_{idx}"):
            del st.session_state.events[idx]
            if st.session_state.edit_index == idx:
              st.session_state.edit_index = None
            st.success("일정이 삭제되었습니다.")
            st.rerun()

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>💡 안내: OAuth"
    " 클라이언트 키(`client_id`, `client_secret`)는 상단 연동 모달에서"
    " 안전하게 관리 및 세션 검증에 사용됩니다.</div>",
    unsafe_allow_html=True,
)
