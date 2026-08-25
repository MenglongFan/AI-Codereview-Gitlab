# -*- coding: utf-8 -*-
"""共享筛选（原 ui.py 1248-1276、1904-1938 行）。"""
import datetime

import streamlit as st

from ui_app.data import _load_combined_base


# 渲染时间范围筛选（预设按钮 + 日期选择联动，主页面紧凑版）
def render_date_filter(tab_key, columns=None):
    presets = {"近7天": 7, "近30天": 30, "近90天": 90, "全部": None}
    preset = st.segmented_control(
        "时间范围", list(presets.keys()), default="近7天", key=f"{tab_key}_preset"
    )

    # 预设变化时重置日期选择，让默认日期跟随预设
    last_preset = st.session_state.get(f"{tab_key}_last_preset")
    if last_preset is not None and last_preset != preset:
        for k in (f"{tab_key}_start", f"{tab_key}_end"):
            st.session_state.pop(k, None)
        st.session_state[f"{tab_key}_last_preset"] = preset
        st.rerun()
    st.session_state[f"{tab_key}_last_preset"] = preset

    current_date = datetime.date.today()
    days = presets[preset]
    if days is None:
        if columns is not None:
            for col in columns:
                col.caption("不限时间范围")
        return None, None

    default_start = current_date - datetime.timedelta(days=days)
    if columns is None:
        columns = st.columns(2)
    start_date = columns[0].date_input("开始", value=default_start, key=f"{tab_key}_start")
    end_date = columns[1].date_input("结束", value=current_date, key=f"{tab_key}_end")
    return start_date, end_date


# ============ 共享筛选（侧边栏，作用于仪表盘全部选项卡） ============
def render_shared_filter():
    """主页面顶部共享筛选条：时间预设 + 日期 + 开发者 + 项目。

    选项列表来自 MR + Push 合并记录，保证各选项卡都能选中自己源的数据。
    返回 dict，供各内容块渲染函数使用。
    """
    # 第一行：时间范围预设 + 起止日期
    c1, c2, c3 = st.columns([1.35, 1, 1], gap="small")
    with c1:
        start_date, end_date = render_date_filter("dash", columns=[c2, c3])

    start_datetime = (int(datetime.datetime.combine(start_date, datetime.time.min).timestamp())
                      if start_date else None)
    end_datetime = (int(datetime.datetime.combine(end_date, datetime.time.max).timestamp())
                    if end_date else None)

    base = _load_combined_base(start_datetime, end_datetime)
    unique_authors = (sorted(base["author"].dropna().unique().tolist()) if not base.empty else [])
    unique_projects = (sorted(base["project_name"].dropna().unique().tolist()) if not base.empty else [])

    # 第二行：开发者 + 项目多选
    c4, c5 = st.columns([1, 1], gap="small")
    with c4:
        authors = st.multiselect("开发者", unique_authors, default=[], key="dash_authors",
                                 placeholder="全部开发者")
    with c5:
        project_names = st.multiselect("项目名称", unique_projects, default=[], key="dash_projects",
                                       placeholder="全部项目")

    return {
        "authors": authors,
        "project_names": project_names,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
    }
