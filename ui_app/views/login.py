# -*- coding: utf-8 -*-
"""登录页（原 ui.py 1205-1244 行）。"""
import streamlit as st

from ui_app.auth import authenticate, get_saved_credentials
from ui_app.design import GIT_ANIM_HTML, GLOBAL_CSS, LOGIN_CSS, _LOGIN_BRAND_HTML


def login_page(cookies):
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    st.markdown(LOGIN_CSS, unsafe_allow_html=True)

    # 获取保存的用户名和密码
    saved_username, saved_password = get_saved_credentials(cookies)

    # 左右分栏：品牌面板 | 认证卡片
    brand_col, auth_col = st.columns([1.12, 1], gap="large")

    with brand_col:
        st.markdown(_LOGIN_BRAND_HTML, unsafe_allow_html=True)
        st.html(GIT_ANIM_HTML)

    with auth_col:
        # 创建一个form，支持回车提交
        with st.form("login_form", clear_on_submit=False):
            st.markdown(
                '<div class="auth-head">'
                '<h1>登录控制台</h1>'
                '<p>使用管理员账号访问审查仪表盘</p>'
                '</div>',
                unsafe_allow_html=True,
            )
            username = st.text_input(
                "用户名", value=saved_username, placeholder="用户名", label_visibility="collapsed"
            )
            password = st.text_input(
                "密码", type="password", value=saved_password, placeholder="密码", label_visibility="collapsed"
            )
            remember_password = st.checkbox("记住密码", value=bool(saved_username))
            submit = st.form_submit_button("登 录", use_container_width=True)

            if submit:
                if authenticate(cookies, username, password, remember_password):
                    st.rerun()  # 重新运行应用以显示主要内容
                else:
                    st.error("用户名或密码错误")

        st.markdown('<div class="login-version">AI-Codereview-Gitlab · v1</div>', unsafe_allow_html=True)
