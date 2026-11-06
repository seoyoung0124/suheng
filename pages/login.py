import streamlit as st

from supabase_utils import get_supabase, store_auth_session, current_user_id

st.set_page_config(page_title="Daily Planner | 로그인", page_icon="🔐", layout="centered")

# 화면에 입력 요소 또는 안내 내용을 표시한다.
st.title("🔐 Daily Planner 로그인")
# 화면에 입력 요소 또는 안내 내용을 표시한다.
st.write("로그인하거나 회원가입한 뒤 나만의 캘린더를 이용할 수 있어요.")

# 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
if current_user_id():
    st.success(f"이미 로그인되어 있습니다: {st.session_state.get('user_email', '')}")
    # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
    if st.button("캘린더로 이동", type="primary", use_container_width=True):
        st.switch_page("main.py")
    # 현재 실행을 중단해 이후 화면 처리가 진행되지 않도록 한다.
    st.stop()

client = get_supabase()
login_tab, signup_tab = st.tabs(["로그인", "회원가입"])

with login_tab:
    # 관련 입력 항목을 하나의 폼으로 묶어 제출 시 함께 처리한다.
    with st.form("login_form"):
        login_email = st.text_input("이메일", key="login_email")
        login_password = st.text_input("비밀번호", type="password", key="login_password")
        login_submit = st.form_submit_button(
            "로그인", type="primary", use_container_width=True
        )

    # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
    if login_submit:
        # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
        if not login_email.strip() or not login_password:
            st.warning("이메일과 비밀번호를 모두 입력해 주세요.")
        # 앞의 조건에 해당하지 않을 때 실행할 작업을 처리한다.
        else:
            # 오류가 발생할 수 있는 작업을 실행하고 예외 상황에 대비한다.
            try:
                response = client.auth.sign_in_with_password({
                    "email": login_email.strip(),
                    "password": login_password,
                })
                # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
                if store_auth_session(client, response):
                    st.success("로그인되었습니다.")
                    st.switch_page("main.py")
                # 앞의 조건에 해당하지 않을 때 실행할 작업을 처리한다.
                else:
                    st.error(
                        "로그인 세션을 만들지 못했습니다. "
                        "이메일 인증이 필요한지 확인해 주세요."
                    )
            # 앞선 작업에서 오류가 발생했을 때 예외 처리를 수행한다.
            except Exception as exc:
                st.error("로그인에 실패했습니다. 계정 정보와 이메일 인증 상태를 확인해 주세요.")
                # 화면에 입력 요소 또는 안내 내용을 표시한다.
                st.caption(f"오류 유형: {type(exc).__name__}")
                # 화면에 입력 요소 또는 안내 내용을 표시한다.
                st.caption(f"오류 내용: {exc}")

with signup_tab:
    # 관련 입력 항목을 하나의 폼으로 묶어 제출 시 함께 처리한다.
    with st.form("signup_form"):
        signup_email = st.text_input("이메일 주소", key="signup_email")
        signup_password = st.text_input("비밀번호", type="password", key="signup_password")
        signup_confirm = st.text_input("비밀번호 확인", type="password", key="signup_confirm")
        signup_submit = st.form_submit_button(
            "회원가입", type="primary", use_container_width=True
        )

    # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
    if signup_submit:
        # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
        if not signup_email.strip() or not signup_password:
            st.warning("이메일과 비밀번호를 입력해 주세요.")
        # 앞선 조건이 아닌 경우 추가 조건을 확인한다.
        elif signup_password != signup_confirm:
            st.warning("비밀번호가 일치하지 않습니다.")
        # 앞선 조건이 아닌 경우 추가 조건을 확인한다.
        elif len(signup_password) < 6:
            st.warning("비밀번호를 6자 이상 입력해 주세요.")
        # 앞의 조건에 해당하지 않을 때 실행할 작업을 처리한다.
        else:
            # 오류가 발생할 수 있는 작업을 실행하고 예외 상황에 대비한다.
            try:
                response = client.auth.sign_up({
                    "email": signup_email.strip(),
                    "password": signup_password,
                })

                # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
                if store_auth_session(client, response):
                    st.success("회원가입과 로그인이 완료되었습니다.")
                    st.switch_page("main.py")
                # 앞의 조건에 해당하지 않을 때 실행할 작업을 처리한다.
                else:
                    st.success(
                        "가입 요청이 완료되었습니다. 이메일 인증이 설정되어 있다면 "
                        "메일을 확인한 뒤 로그인해 주세요."
                    )
            # 앞선 작업에서 오류가 발생했을 때 예외 처리를 수행한다.
            except Exception as exc:
                st.error("회원가입에 실패했습니다.")
                # 화면에 입력 요소 또는 안내 내용을 표시한다.
                st.caption(f"오류 유형: {type(exc).__name__}")
                # 화면에 입력 요소 또는 안내 내용을 표시한다.
                st.caption(f"오류 코드: {getattr(exc, 'code', '확인 불가')}")
                # 화면에 입력 요소 또는 안내 내용을 표시한다.
                st.caption(f"HTTP 상태: {getattr(exc, 'status', '확인 불가')}")
                # 화면에 입력 요소 또는 안내 내용을 표시한다.
                st.caption(f"오류 설명: {exc}")

st.divider()
# 화면에 입력 요소 또는 안내 내용을 표시한다.
st.page_link("main.py", label="캘린더 페이지로 이동", icon="🗓️")
