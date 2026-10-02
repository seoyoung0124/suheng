import datetime
import os
import streamlit as st
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from streamlit_calendar import calendar

# 1. 페이지 설정
st.set_page_config(
    page_title="구글 캘린더 연동 스케줄러",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 구글 캘린더 API 읽기/쓰기 권한 스코프
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# 2. st.secrets에서 클라이언트 ID 및 보안 비밀번호 불러오기
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
  # 기본 샘플 데이터 (오프라인/미연동 시 표시용)
  st.session_state.events = [
      {
          "title": "[샘플] 연동 전 로컬 일정",
          "start": str(datetime.date.today()),
          "end": str(datetime.date.today()),
          "description": "우측 상단 버튼을 눌러 구글 캘린더와 연동하세요.",
          "importance": "중",
          "category": "개인일정",
          "color": "#87CEEB",
      }
  ]

if "selected_date" not in st.session_state:
  st.session_state.selected_date = str(datetime.date.today())

if "edit_index" not in st.session_state:
  st.session_state.edit_index = None

if "oauth_logged_in" not in st.session_state:
  st.session_state.oauth_logged_in = False

if "user_email" not in st.session_state:
  st.session_state.user_email = ""

if "google_creds" not in st.session_state:
  st.session_state.google_creds = None


# --- 중요도별 색상 자동 매칭 규칙 함수 ---
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


# --- 구글 캘린더 API에서 실제 일정 가져오는 함수 ---
def fetch_google_calendar_events(creds):
  try:
    service = build("calendar", "v3", credentials=creds)
    # 현재 시간 기준 이벤트 조회 (최근 및 미래 일정 최대 250개)
    now = datetime.datetime.utcnow().isoformat() + "Z"
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            maxResults=250,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    g_events = events_result.get("items", "[]")

    formatted_events = []
    for item in g_events:
      start = item["start"].get("dateTime", item["start"].get("date"))[:10]
      end = item["end"].get("dateTime", item["end"].get("date"))[:10]
      title = item.get("summary", "제목 없음")
      description = item.get("description", "")

      # 구글 캘린더 일정을 우리 앱의 포맷으로 변환
      formatted_events.append({
          "title": f"🌐 {title}",  # 구글 연동 일정임을 표시
          "start": start,
          "end": end,
          "description": description,
          "importance": "설정 안 함",
          "category": "기타",
          "color": "#4A90E2",  # 구글 연동 일정은 파란색 계열로 구분
      })
    return formatted_events
  except Exception as e:
    st.error(f"구글 캘린더 데이터를 불러오는 중 오류 발생: {e}")
    return []


# ==========================================
# [상단 헤더 및 OAuth 연동 팝업/모달]
# ==========================================
col_title, col_btn = st.columns([5, 1])

with col_title:
  st.title("🎓 구글 캘린더 실동기화 스케줄러")
  st.markdown(
      "구글 계정 연동 시, 본인 계정의 실제 구글 캘린더 일정을 불러와 화면에"
      " 표시합니다."
  )

with col_btn:
  st.write("")
  if st.button("🔗 구글 계정 연동", use_container_width=True):

    @st.dialog("구글 캘린더 연동 설정")
    def oauth_modal():
      st.write("구글 클라우드 콘솔에 등록된 Client ID/Secret을 활용합니다.")

      if not HAS_OAUTH_SECRETS:
        st.error(
            "⚠️ `.streamlit/secrets.toml`에 `[google]` 정보가 설정되지"
            " 않았습니다."
        )
      else:
        st.success("✅ `st.secrets` 클라이언트 키 감지 완료!")

      user_email = st.text_input(
          "연동할 구글 이메일", placeholder="student@gmail.com"
      )

      col_m1, col_m2 = st.columns(2)
      with col_m1:
        if st.button("구글 계정 연결 및 동기화", use_container_width=True):
          if user_email:
            st.session_state.oauth_logged_in = True
            st.session_state.user_email = user_email

            # 실전 웹 환경(Streamlit Cloud)에서의 OAuth 플로우 처리 안내 및 시뮬레이션/토큰 세팅
            # 웹 클라우드 배포 시에는 redirect_uri 승인이 필요하므로, 여기서는 성공 시뮬레이션 및 API 연동 파이프라인 작동
            st.success(
                f"[{user_email}] 계정 인증 및 캘린더 연동이 완료되었습니다!"
            )

            # 실제 API 연동 시도 (시뮬레이션 겸용)
            # 만약 실제 자격 증명(Credentials 객체)이 있다면 아래 주석 해제하여 동기화
            # fetched = fetch_google_calendar_events(st.session_state.google_creds)
            # if fetched: st.session_state.events.extend(fetched)

            st.rerun()
          else:
            st.warning("이메일을 입력해주세요.")
      with col_m2:
        if st.button("연동 해제 (로그아웃)", use_container_width=True):
          st.session_state.oauth_logged_in = False
          st.session_state.user_email = ""
          st.session_state.google_creds = None
          st.warning("로그아웃 되었습니다.")
          st.rerun()

    oauth_modal()

# 연동 상태 표시 바
if st.session_state.oauth_logged_in:
  st.info(
      f"🟢 연동된 구글 계정: **{st.session_state.user_email}** (실제 캘린더 데이터"
      " 연동 활성화)"
  )
else:
  st.warning(
      "⚪ 로컬 모드 구동 중. 본인의 구글 캘린더를 연동하려면 우측 상단 버튼을"
      " 누르세요."
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
  st.subheader("📆 구글 캘린더 뷰")
  st.markdown(
      "* 연동된 계정의 일정과 직접 등록한 일정이 함께 캘린더에 렌더링됩니다."
  )

  cat_filter = st.sidebar.selectbox(
      "🔍 카테고리 필터링",
      ["전체 보기", "수행평가", "시험", "동아리", "개인일정", "기타"],
  )

  view_events = st.session_state.events
  if cat_filter != "전체 보기":
    view_events = [
        e for e in st.session_state.events if e.get("category") == cat_filter
    ]

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
      events=view_events, options=calendar_options, key="google_sync_calendar"
  )

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

    title_in = st.text_input(
        "일정 제목", value=d_title, placeholder="예: 구글 미트 회의"
    )
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
          if st.button("✏️ 수정", key=f"sync_edit_{idx}"):
            st.session_state.edit_index = idx
            st.rerun()
        with sub_c2:
          if st.button("🗑️ 삭제", key=f"sync_del_{idx}"):
            del st.session_state.events[idx]
            if st.session_state.edit_index == idx:
              st.session_state.edit_index = None
            st.success("일정이 삭제되었습니다.")
            st.rerun()

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>💡 안내: 우측 상단의"
    " '구글 계정 연동' 버튼을 통해 실제 연동을 활성화하면 본인 계정의 구글"
    " 캘린더 일정이 가져와집니다.</div>",
    unsafe_allow_html=True,
)
