import streamlit as st

from supabase_utils import get_supabase, store_auth_session, current_user_id

st.set_page_config(page_title="하루결 | 로그인", page_icon="🔐", layout="centered")

st.title("🔐 하루결 로그인")
st.write("로그인하거나 회원가입한 뒤 나만의 캘린더를 이용할 수 있어요.")

if current_user_id():
    st.success(f"이미 로그인되어 있습니다: {st.session_state.get('user_email', '')}")
    if st.button("캘린더로 이동", type="primary", use_container_width=True):
        st.switch_page("main.py")
    st.stop()

client = get_supabase()
login_tab, signup_tab = st.tabs(["로그인", "회원가입"])

with login_tab:
    with st.form("login_form"):
        login_email = st.text_input("이메일", key="login_email")
        login_password = st.text_input("비밀번호", type="password", key="login_password")
        login_submit = st.form_submit_button("로그인", type="primary", use_container_width=True)

    if login_submit:
        if not login_email.strip() or not login_password:
            st.warning("이메일과 비밀번호를 모두 입력해 주세요.")
        else:
            try:
                response = client.auth.sign_in_with_password({
                    "email": login_email.strip(),
                    "password": login_password,
                })
                if store_auth_session(client, response):
                    st.success("로그인되었습니다.")
                    st.switch_page("main.py")
                else:
                    st.error("로그인 세션을 만들지 못했습니다. 이메일 인증이 필요한지 확인해 주세요.")
            except Exception as exc:
                st.error("로그인에 실패했습니다. 이메일·비밀번호와 이메일 인증 상태를 확인해 주세요.")
                st.caption(f"오류 내용: {exc}")

with signup_tab:
    with st.form("signup_form"):
        signup_email = st.text_input("이메일 주소", key="signup_email")
        signup_password = st.text_input("비밀번호", type="password", key="signup_password")
        signup_confirm = st.text_input("비밀번호 확인", type="password", key="signup_confirm")
        signup_submit = st.form_submit_button("회원가입", type="primary", use_container_width=True)

    if signup_submit:
        if not signup_email.strip() or not signup_password:
            st.warning("이메일과 비밀번호를 입력해 주세요.")
        elif signup_password != signup_confirm:
            st.warning("비밀번호가 일치하지 않습니다.")
        elif len(signup_password) < 6:
            st.warning("비밀번호를 6자 이상 입력해 주세요.")
        else:
            try:
                response = client.auth.sign_up({
                    "email": signup_email.strip(),
                    "password": signup_password,
                })
                if store_auth_session(client, response):
                    st.success("회원가입과 로그인이 완료되었습니다.")
                    st.switch_page("main.py")
                else:
                    st.success("가입 요청이 완료되었습니다. 이메일 인증이 설정되어 있다면 받은 편지함에서 인증한 뒤 로그인해 주세요.")
            except Exception as exc:
    st.error("회원가입에 실패했습니다.")

    # 비밀번호나 인증 토큰은 출력하지 않고 오류 정보만 확인
    st.write("오류 유형:", type(exc).__name__)
    st.write("오류 코드:", getattr(exc, "code", "확인 불가"))
    st.write("HTTP 상태:", getattr(exc, "status", "확인 불가"))
    st.write("오류 설명:", str(exc))

st.divider()
st.page_link("main.py", label="캘린더 페이지로 이동", icon="🗓️")
