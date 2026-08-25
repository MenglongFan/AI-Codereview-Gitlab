# -*- coding: utf-8 -*-
"""审查内容块（MR / Push 共用渲染逻辑，原 ui.py 1798-1835、1942-1962 行）。"""
import pandas as pd
import streamlit as st

from ui_app.charts import render_charts
from ui_app.data import get_data
from ui_app.views.kpis import render_kpis


# ============ 页面配置常量 ============
# 审查页明细列（不含 token 列；token 相关已移入 Token 统计页）
MR_COLUMNS = ["project_name", "author", "source_branch", "target_branch", "updated_at", "commit_messages", "delta",
              "score", "url", "additions", "deletions"]

PUSH_COLUMNS = ["project_name", "author", "branch", "updated_at", "commit_messages", "delta", "score", "url",
                "additions", "deletions"]


def _mr_column_config():
    """MR 明细列配置（运行时构建，避免模块顶层执行 st.column_config）。"""
    return {
        "project_name": "项目名称",
        "author": "开发者",
        "source_branch": "源分支",
        "target_branch": "目标分支",
        "updated_at": "更新时间",
        "commit_messages": "提交信息",
        "delta": "代码变更",
        "score": st.column_config.ProgressColumn(
            "得分", min_value=0, max_value=100, format="%d",
        ),
        "url": st.column_config.LinkColumn("操作", max_chars=100, display_text="查看详情"),
        "additions": None,
        "deletions": None,
    }


def _push_column_config():
    """Push 明细列配置（运行时构建，避免模块顶层执行 st.column_config）。"""
    return {
        "project_name": "项目名称",
        "author": "开发者",
        "branch": "分支",
        "updated_at": "更新时间",
        "commit_messages": "提交信息",
        "delta": "代码变更",
        "score": st.column_config.ProgressColumn(
            "得分", min_value=0, max_value=100, format="%d",
        ),
        "url": st.column_config.LinkColumn("操作", max_chars=100, display_text="查看详情"),
        "additions": None,
        "deletions": None,
    }


# ============ 审查内容块（MR / Push 共用渲染逻辑） ============
def render_review_block(service_func, columns, column_config, filters):
    data = get_data(service_func, authors=filters["authors"], project_names=filters["project_names"],
                    updated_at_gte=filters["start_datetime"], updated_at_lte=filters["end_datetime"],
                    columns=columns)
    df = pd.DataFrame(data)

    # KPI 指标
    render_kpis(df)

    # 统计图表
    st.markdown('<div class="chart-title">统计图表</div>', unsafe_allow_html=True)
    render_charts(df)

    # 数据明细（token 相关列已移入 Token 统计选项卡）
    st.markdown('<div class="chart-title">数据明细</div>', unsafe_allow_html=True)
    st.data_editor(
        df,
        use_container_width=True,
        column_config=column_config,
        hide_index=True,
    )
