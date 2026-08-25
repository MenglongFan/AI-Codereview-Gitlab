# -*- coding: utf-8 -*-
"""AI 代码审查平台 · Streamlit 入口（薄入口）。

业务逻辑已拆分至 ui_app/ 包；本文件仅保留 set_page_config 与入口调用，
保证 `streamlit run ui.py`、Dockerfile COPY ui.py 与 AppTest.from_file(ui.py) 兼容。
"""
import streamlit as st

st.set_page_config(layout="wide", page_title="AI代码审查平台", initial_sidebar_state="collapsed")

from ui_app.main import main

main()
