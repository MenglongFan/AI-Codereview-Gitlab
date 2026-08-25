# -*- coding: utf-8 -*-
"""KPI 指标卡（原 ui.py 1609-1639 行）。"""
import streamlit as st

from ui_app.design import _KPI_CARD, _KPI_ICONS


def _kpi_cards(cards):
    """cards: list of (label, value, sub, cls, icon_key)"""
    html = "".join(
        _KPI_CARD.format(
            cls=cls,
            icon=_KPI_ICONS[icon],
            label=label,
            value=value,
            sub_html=f'<div class="kpi-sub">{sub}</div>' if sub else "",
        )
        for label, value, sub, cls, icon in cards
    )
    st.markdown(f'<div class="kpi-grid">{html}</div>', unsafe_allow_html=True)


# 渲染 KPI 指标卡（自定义 HTML，开发者工具卡片风格）
def render_kpis(df):
    if df.empty:
        return
    total_records = len(df)
    average_score = df["score"].mean()
    project_cnt = df["project_name"].nunique()
    add_sum = int(df["additions"].sum())
    del_sum = int(df["deletions"].sum())

    _kpi_cards([
        ("审查记录数", f"{total_records}", f"{project_cnt} 个项目", "kpi-accent", "doc"),
        ("平均得分", f"{average_score:.1f}", f"基于 {total_records} 次审查", "kpi-green", "star"),
        ("涉及项目", f"{project_cnt}", f"{total_records} 条记录", "kpi-amber", "folder"),
        ("代码变更", f"+{add_sum} / -{del_sum}", f"{add_sum + del_sum} 行总变更", "kpi-purple", "code"),
    ])
