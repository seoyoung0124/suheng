import streamlit as st

import theme

st.set_page_config(
    page_title="Daily Planner",
    layout="wide"
)

client, uid = theme.page_setup("settings")

esc = theme.esc

# 화면에 입력 요소 또는 안내 내용을 표시한다.
st.markdown('<div class="page-title">Settings</div>', unsafe_allow_html=True)
# 화면에 입력 요소 또는 안내 내용을 표시한다.
st.caption("화면 테마와 계정을 관리할 수 있어요.")


# ==========================================
# 1. 테마 선택
# ==========================================

# 화면에 입력 요소 또는 안내 내용을 표시한다.
st.markdown('<div class="section-title">테마</div>', unsafe_allow_html=True)

current = theme.current_name()


# 선택한 테마의 배경과 카드 색상을 미리 보는 HTML을 만든다.
def preview_html(p):
    # 계산하거나 처리한 결과를 호출한 위치로 반환한다.
    return (
        f'<div class="tp" style="background:{p["bg"]};border:1px solid {p["border"]}">'
        f'<div class="tp-side" style="background:{p["sidebar"]}"></div>'
        '<div class="tp-main">'
        f'<div class="tp-card" style="background:{p["card"]};border:1px solid {p["border"]}">'
        f'<i style="width:60%;background:{p["accent"]}"></i>'
        f'<i style="width:85%;background:{p["rail"]}"></i>'
        f'<i style="width:70%;background:{p["rail"]}"></i>'
        f'<i style="width:40%;background:{p["tile2"]}"></i>'
        '</div></div></div>'
    )


cols = st.columns(3, gap="large")

# 목록의 항목을 하나씩 확인하며 필요한 처리를 반복한다.
for col, (name, p) in zip(cols, theme.THEMES.items()):
    with col:
        # 화면에 입력 요소 또는 안내 내용을 표시한다.
        st.markdown(
            preview_html(p)
            + f'<div class="tp-name">{esc(p["label"])}</div>'
            + f'<div class="tp-desc">{esc(p["desc"])}</div>',
            unsafe_allow_html=True
        )

        selected = name == current

        # 화면에 입력 요소 또는 안내 내용을 표시한다.
        st.button(
            "사용 중" if selected else "선택",
            key=f"theme_{name}",
            icon=":material/check:" if selected else None,
            type="primary" if selected else "secondary",
            disabled=selected,
            on_click=theme.set_theme,
            args=(name,),
            use_container_width=True
        )


# ==========================================
# 2. 계정
# ==========================================

# 화면에 입력 요소 또는 안내 내용을 표시한다.
st.markdown('<div class="section-title">계정</div>', unsafe_allow_html=True)

# 관련 화면 요소를 하나의 영역으로 묶는다.
with st.container(key="account_card"):
    # 화면에 입력 요소 또는 안내 내용을 표시한다.
    st.markdown(
        '<div class="muted">로그인한 계정</div>'
        f'<div style="font-weight:600;margin:2px 0 12px">'
        f'{esc(st.session_state.get("user_email", ""))}</div>',
        unsafe_allow_html=True
    )

    # 조건을 확인해 해당 상황에서만 다음 작업을 실행한다.
    if st.button("로그아웃", key="account_logout", icon=":material/logout:"):
        theme.sign_out()
        st.switch_page("main.py")
