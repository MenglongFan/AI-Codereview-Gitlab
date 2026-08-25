# -*- coding: utf-8 -*-
"""顶部标题栏（原 ui.py 1846-1884 行）。"""
import streamlit as st

from ui_app.auth import logout
from ui_app.design import GLOBAL_CSS


# ============ 顶部标题栏（各页面共用） ============
def render_header(title, subtitle, cookies, logout_key="logout_button"):
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    username = st.session_state.get('username', '')

    # 顶栏：左侧标题 | 右侧 LIVE + 圆形退出按钮
    header_left, header_right = st.columns([6, 1.6])

    with header_left:
        left_html = (
            f'<div class="dash-nav-left">'
            f'  <span class="nav-mark" aria-hidden="true">'
            f'    <svg viewBox="0 0 24 24"><path d="M8 7l-5 5 5 5"/><path d="M16 7l5 5-5 5"/></svg>'
            f'  </span>'
            f'  <div class="nav-titles">'
            f'    <h4>{title}</h4>'
            f'    <span class="dash-nav-sub">{subtitle}</span>'
            f'  </div>'
            f'</div>'
        )
        st.markdown(left_html, unsafe_allow_html=True)

    with header_right:
        st.markdown('<div class="dash-nav-right">', unsafe_allow_html=True)
        live_col, btn_col = st.columns([2.2, 1])
        with live_col:
            live_html = (
                f'<div class="live-wrap">'
                f'  <span class="live-dot"></span>'
                f'  <span class="live-label">LIVE</span>'
                f'  <span class="live-user">{username}</span>'
                f'</div>'
            )
            st.markdown(live_html, unsafe_allow_html=True)
        with btn_col:
            st.markdown('<div class="nav-logout">', unsafe_allow_html=True)
            if st.button("⏻", key=logout_key, help="退出登录"):
                logout(cookies)
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
