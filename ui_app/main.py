# -*- coding: utf-8 -*-
"""入口编排（原 ui.py 2018-2048 行 + CookieManager 初始化）。"""
import streamlit as st


def main():
    # 关键契约：CookieManager 的 import 与实例化必须在函数内按运行执行，
    # 保证 AppTest 每次 run() 都能取到当前 patch 的 mock（测试隔离），
    # 且模块顶层不产生任何 Streamlit 命令副作用。
    from streamlit_cookies_manager import CookieManager

    cookies = CookieManager()

    from ui_app.auth import check_login_status
    from ui_app.views.login import login_page

    if not check_login_status(cookies):
        login_page(cookies)
        st.stop()

    render_dashboard_page(cookies)


# ============ 仪表盘（单页，选项卡切换 MR / Push / Token） ============
def render_dashboard_page(cookies):
    from biz.service.review_service import ReviewService
    from ui_app.config import push_review_enabled
    from ui_app.views.filters import render_shared_filter
    from ui_app.views.header import render_header
    from ui_app.views.review_table import (
        MR_COLUMNS,
        PUSH_COLUMNS,
        _mr_column_config,
        _push_column_config,
        render_review_block,
    )
    from ui_app.views.token_stats import render_token_block

    render_header("审查仪表盘", "AI REVIEW · DASHBOARD", cookies, logout_key="logout_dashboard")

    # 共享筛选（主页面顶部，作用于全部选项卡）
    filters = render_shared_filter()

    tab_labels = ["MR 审查"]
    if push_review_enabled():
        tab_labels.append("Push 审查")
    tab_labels.append("Token 统计")
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        render_review_block(ReviewService().get_mr_review_logs, MR_COLUMNS, _mr_column_config(), filters)

    if push_review_enabled():
        with tabs[1]:
            render_review_block(ReviewService().get_push_review_logs, PUSH_COLUMNS, _push_column_config(), filters)

    with tabs[-1]:
        render_token_block(filters)
