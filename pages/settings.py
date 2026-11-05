import streamlit as st

import theme

st.set_page_config(
    page_title="Daily Planner",
    layout="wide"
)

client, uid = theme.page_setup("settings")

esc = theme.esc

st.markdown('<div class="page-title">Settings</div>', unsafe_allow_html=True)
st.caption("화면 테마와 계정을 관리할 수 있어요.")


# ==========================================
# 1. 테마 선택
# ==========================================

st.markdown('<div class="section-title">테마</div>', unsafe_allow_html=True)

current = theme.current_name()


def preview_html(p):
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

for col, (name, p) in zip(cols, theme.THEMES.items()):
    with col:
        st.markdown(
            preview_html(p)
            + f'<div class="tp-name">{esc(p["label"])}</div>'
            + f'<div class="tp-desc">{esc(p["desc"])}</div>',
            unsafe_allow_html=True
        )

        selected = name == current

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

st.markdown('<div class="section-title">계정</div>', unsafe_allow_html=True)

with st.container(key="account_card"):
    st.markdown(
        '<div class="muted">로그인한 계정</div>'
        f'<div style="font-weight:600;margin:2px 0 12px">'
        f'{esc(st.session_state.get("user_email", ""))}</div>',
        unsafe_allow_html=True
    )

    if st.button("로그아웃", key="account_logout", icon=":material/logout:"):
        theme.sign_out()
        st.switch_page("main.py")
