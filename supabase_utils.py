import streamlit as st
from supabase import create_client

# Supabase 연결을 재사용하거나 새로 생성하고 로그인 세션을 복원한다.
def get_supabase():
    # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
    if "supabase_client" in st.session_state:
        # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
        return st.session_state.supabase_client
    # 오류가 발생할 수 있는 작업을 실행하고 예외 상황에 대비한다.
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    # 앞선 작업에서 오류가 발생했을 때 예외 처리를 수행한다.
    except Exception:
        st.error("Streamlit Cloud Settings → Secrets에 SUPABASE_URL과 SUPABASE_KEY를 설정하세요.")
        # 현재 실행을 중단해 이후 화면 처리가 진행되지 않도록 한다.
        st.stop()
    client = create_client(url, key)
    access = st.session_state.get("supabase_access_token")
    refresh = st.session_state.get("supabase_refresh_token")
    # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
    if access and refresh:
        # 오류가 발생할 수 있는 작업을 실행하고 예외 상황에 대비한다.
        try:
            client.auth.set_session(access, refresh)
        # 앞선 작업에서 오류가 발생했을 때 예외 처리를 수행한다.
        except Exception:
            # 목록의 항목을 하나씩 확인하며 필요한 처리를 반복한다.
            for k in ("supabase_access_token", "supabase_refresh_token", "user_id", "user_email"):
                # 페이지가 다시 실행되어도 필요한 값을 유지하도록 세션 상태를 갱신한다.
                st.session_state.pop(k, None)
    st.session_state.supabase_client = client
    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return client

# 인증 응답에서 사용자와 토큰을 꺼내 세션에 저장한다.
def store_auth_session(client, response):
    session = getattr(response, "session", None)
    user = getattr(response, "user", None)
    # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
    if not session or not user:
        # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
        return False
    st.session_state.supabase_access_token = session.access_token
    st.session_state.supabase_refresh_token = session.refresh_token
    st.session_state.user_id = str(user.id)
    st.session_state.user_email = user.email or ""
    st.session_state.supabase_client = client
    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return True

# 현재 로그인한 사용자의 ID를 반환한다.
def current_user_id():
    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return st.session_state.get("user_id")

# 현재 사용자의 인증 정보를 정리하고 로그아웃한다.
def sign_out():
    client = st.session_state.get("supabase_client")
    # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
    if client:
        # 오류가 발생할 수 있는 작업을 실행하고 예외 상황에 대비한다.
        try:
            client.auth.sign_out()
        # 앞선 작업에서 오류가 발생했을 때 예외 처리를 수행한다.
        except Exception:
            pass
    # 목록의 항목을 하나씩 확인하며 필요한 처리를 반복한다.
    for k in ("supabase_client", "supabase_access_token", "supabase_refresh_token", "user_id", "user_email"):
        # 페이지가 다시 실행되어도 필요한 값을 유지하도록 세션 상태를 갱신한다.
        st.session_state.pop(k, None)
