import streamlit as st
from supabase import create_client

def get_supabase():
    if "supabase_client" in st.session_state:
        return st.session_state.supabase_client
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except Exception:
        st.error("Streamlit Cloud Settings → Secrets에 SUPABASE_URL과 SUPABASE_KEY를 설정하세요.")
        st.stop()
    client = create_client(url, key)
    access = st.session_state.get("supabase_access_token")
    refresh = st.session_state.get("supabase_refresh_token")
    if access and refresh:
        try:
            client.auth.set_session(access, refresh)
        except Exception:
            for k in ("supabase_access_token", "supabase_refresh_token", "user_id", "user_email"):
                st.session_state.pop(k, None)
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
    return True

def current_user_id():
    return st.session_state.get("user_id")

def sign_out():
    client = st.session_state.get("supabase_client")
    if client:
        try:
            client.auth.sign_out()
        except Exception:
            pass
    for k in ("supabase_client", "supabase_access_token", "supabase_refresh_token", "user_id", "user_email"):
        st.session_state.pop(k, None)
