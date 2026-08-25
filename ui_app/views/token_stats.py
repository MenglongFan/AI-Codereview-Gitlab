# -*- coding: utf-8 -*-
"""Token 统计块（原 ui.py 1643-1780、1985-2014 行）。"""
import datetime

import altair as alt
import pandas as pd
import streamlit as st

from biz.service.review_service import ReviewService
from ui_app.charts import _bar_hover, _dev_chart, _v_grad
from ui_app.config import push_review_enabled
from ui_app.data import load_review_tokens
from ui_app.views.kpis import _kpi_cards


# 渲染 Token 消耗统计（KPI + 聚合图，随侧边栏筛选联动）
def render_token_stats(df):
    if df.empty or "total_tokens" not in df.columns:
        st.info("当前筛选条件下暂无数据")
        return

    total = int(df["total_tokens"].sum())
    prompt = int(df["prompt_tokens"].sum())
    completion = int(df["completion_tokens"].sum())
    avg = int(df["total_tokens"].mean())
    pct_prompt = int(round(prompt / total * 100)) if total else 0
    pct_completion = int(round(completion / total * 100)) if total else 0

    _kpi_cards([
        ("Token Total", f"{total:,}", f"平均 {avg:,} / 次审查", "kpi-accent", "circle"),
        ("Prompt Tokens", f"{prompt:,}", f"占比 {pct_prompt}%", "kpi-green", "arrow-in"),
        ("Completion Tokens", f"{completion:,}", f"占比 {pct_completion}%", "kpi-amber", "arrow-out"),
        ("Avg / Review", f"{avg:,}", f"共 {len(df)} 次审查", "kpi-purple", "avg"),
    ])

    # 按项目 / 按作者 token 排行
    pt = df.groupby("project_name")["total_tokens"].sum().reset_index(name="tokens").sort_values("tokens", ascending=False)
    at = df.groupby("author")["total_tokens"].sum().reset_index(name="tokens").sort_values("tokens", ascending=False)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="chart-title">Token by Project</div>', unsafe_allow_html=True)
        pmax = max(pt["tokens"].max() if not pt.empty else 0, 1)
        hover, opacity = _bar_hover()
        chart = _dev_chart(
            alt.Chart(pt)
            .mark_bar(color=_v_grad("#6FA3FF", "#2B5CD6"), cornerRadiusEnd=4)
            .encode(
                x=alt.X(
                    "tokens:Q",
                    scale=alt.Scale(domain=[0, pmax * 1.1]),
                    title=None,
                    axis=alt.Axis(tickMinStep=1, format="d", labelExpr="datum.value % 1 === 0 ? datum.label : ''"),
                ),
                y=alt.Y("project_name:N", sort=alt.EncodingSortField(field="tokens", op="sum", order="descending"), title=None),
                opacity=opacity,
            )
            .add_params(hover),
            height=300,
        )
        st.altair_chart(chart, use_container_width=True)
    with c2:
        st.markdown('<div class="chart-title">Token by Author</div>', unsafe_allow_html=True)
        amax = max(at["tokens"].max() if not at.empty else 0, 1)
        hover, opacity = _bar_hover()
        chart = _dev_chart(
            alt.Chart(at)
            .mark_bar(color=_v_grad("#A78BFA", "#6E3FD1"), cornerRadiusEnd=4)
            .encode(
                x=alt.X(
                    "tokens:Q",
                    scale=alt.Scale(domain=[0, amax * 1.1]),
                    title=None,
                    axis=alt.Axis(tickMinStep=1, format="d", labelExpr="datum.value % 1 === 0 ? datum.label : ''"),
                ),
                y=alt.Y("author:N", sort=alt.EncodingSortField(field="tokens", op="sum", order="descending"), title=None),
                opacity=opacity,
            )
            .add_params(hover),
            height=300,
        )
        st.altair_chart(chart, use_container_width=True)

    # Token 时间趋势（按天聚合，渐变面积图）
    daily = df.copy()
    daily["day"] = pd.to_datetime(daily["updated_at"]).dt.date
    daily_tokens = daily.groupby("day")["total_tokens"].sum().reset_index(name="tokens")
    st.markdown('<div class="chart-title">Token Trend</div>', unsafe_allow_html=True)
    if len(daily_tokens) > 0:
        area_grad = alt.LinearGradient(
            gradient="linear",
            x1=0, y1=0, x2=0, y2=1,
            stops=[
                alt.GradientStop(color="rgba(76, 141, 255, 0.30)", offset=0),
                alt.GradientStop(color="rgba(76, 141, 255, 0.02)", offset=1),
            ],
        )
        chart = _dev_chart(
            alt.Chart(daily_tokens)
            .mark_area(
                color=area_grad,
                line={"color": "#6FA3FF", "strokeWidth": 2.5},
                interpolate="monotone",
            )
            .encode(
                x=alt.X("day:T", title=None),
                y=alt.Y(
                    "tokens:Q",
                    scale=alt.Scale(domain=[0, max(daily_tokens["tokens"].max(), 1) * 1.1]),
                    title=None,
                    axis=alt.Axis(tickMinStep=1, format="d", labelExpr="datum.value % 1 === 0 ? datum.label : ''"),
                ),
            ),
            height=300,
        )
        st.altair_chart(chart, use_container_width=True)


# 渲染工作日报的 Token 消耗（独立归类，与 review 统计分开）
def render_daily_report_stats(updated_at_gte=None, updated_at_lte=None):
    try:
        rdf = ReviewService().get_daily_report_logs(
            updated_at_gte=updated_at_gte, updated_at_lte=updated_at_lte
        )
    except Exception:
        return
    if rdf.empty or "total_tokens" not in rdf.columns:
        st.caption("日报 Token 消耗：暂无记录")
        return

    total = int(rdf["total_tokens"].sum())
    prompt = int(rdf["prompt_tokens"].sum())
    completion = int(rdf["completion_tokens"].sum())
    pct_prompt = int(round(prompt / total * 100)) if total else 0
    pct_completion = int(round(completion / total * 100)) if total else 0

    _kpi_cards([
        ("Daily Report Tokens", f"{total:,}", f"{len(rdf)} 次生成", "kpi-accent", "doc"),
        ("Prompt Tokens", f"{prompt:,}", f"占比 {pct_prompt}%", "kpi-green", "arrow-in"),
        ("Completion Tokens", f"{completion:,}", f"占比 {pct_completion}%", "kpi-amber", "arrow-out"),
        ("生成次数", f"{len(rdf)}", "工作日报", "kpi-purple", "pulse"),
    ])

    rview = rdf.copy()
    rview["report_time"] = rview["report_time"].apply(
        lambda ts: datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
        if isinstance(ts, (int, float)) else ts
    )
    rview = rview.rename(columns={
        "report_time": "生成时间",
        "prompt_tokens": "Prompt",
        "completion_tokens": "Completion",
        "total_tokens": "Tokens",
    })
    st.dataframe(rview, use_container_width=True, hide_index=True)


# ============ Token 统计块 ============
def render_token_block(filters):
    rdf = load_review_tokens(authors=filters["authors"], project_names=filters["project_names"],
                             updated_at_gte=filters["start_datetime"],
                             updated_at_lte=filters["end_datetime"])

    # 审查 Token（MR + Push 合并展示）
    source_label = "MR + Push" if push_review_enabled() else "MR"
    st.markdown(f'<div class="chart-title">审查 Token · {source_label}</div>', unsafe_allow_html=True)
    render_token_stats(rdf)

    # 审查 Token 明细（含 token 列）
    st.markdown('<div class="chart-title">审查 Token 明细</div>', unsafe_allow_html=True)
    if rdf.empty:
        st.info("当前筛选条件下暂无数据")
    else:
        detail = rdf[["project_name", "author", "updated_at",
                      "prompt_tokens", "completion_tokens", "total_tokens"]].rename(columns={
            "project_name": "项目",
            "author": "开发者",
            "updated_at": "更新时间",
            "prompt_tokens": "Prompt",
            "completion_tokens": "Completion",
            "total_tokens": "Tokens",
        })
        st.dataframe(detail, use_container_width=True, hide_index=True)

    # 日报 Token（共用本页时间筛选）
    st.markdown('<div class="chart-title">日报 Token 消耗</div>', unsafe_allow_html=True)
    render_daily_report_stats(updated_at_gte=filters["start_datetime"],
                              updated_at_lte=filters["end_datetime"])
