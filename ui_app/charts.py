# -*- coding: utf-8 -*-
"""Altair 图表层（原 ui.py 1279-1584 行）。"""
import altair as alt
import pandas as pd
import streamlit as st


_ALT_FONT = "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'PingFang SC', 'Microsoft YaHei', sans-serif"


def _dev_chart(chart, height=None):
    """统一应用深色开发者工具风图表配置：透明容器、深色 view、柔和网格、无边框。"""
    cfg = (
        chart.configure(background="transparent")
        .configure_axis(
            labelFont=_ALT_FONT,
            labelFontSize=11,
            labelColor="#9BA2AF",
            titleFont=_ALT_FONT,
            titleFontSize=11,
            titleColor="#6E7686",
            gridColor="rgba(255, 255, 255, 0.05)",
            gridWidth=1,
            tickColor="rgba(255, 255, 255, 0.10)",
            domainColor="rgba(255, 255, 255, 0.06)",
        )
        .configure_view(
            fill="#14161B",
            strokeWidth=0,
        )
        .configure_legend(
            labelFont=_ALT_FONT,
            labelFontSize=11,
            labelColor="#9BA2AF",
            titleFont=_ALT_FONT,
            titleFontSize=11,
            titleColor="#6E7686",
        )
    )
    if height is not None:
        cfg = cfg.properties(height=height)
    return cfg


def _v_grad(top, bottom):
    """垂直渐变（上亮下深），为柱状图增加光泽感。坐标按 normalized [0,1] 解析。"""
    return alt.LinearGradient(
        gradient="linear",
        x1=0, y1=0, x2=0, y2=1,
        stops=[
            alt.GradientStop(color=top, offset=0),
            alt.GradientStop(color=bottom, offset=1),
        ],
    )


def _bar_hover():
    """柱状图悬停高亮：返回 (selection, opacity encoding)。"""
    hover = alt.selection_point(on="pointerover", empty=False)
    opacity = alt.condition(hover, alt.value(1.0), alt.value(0.5))
    return hover, opacity


# GitLab 提交统计风格：53 周 × 7 天热力图配色与阈值
_HEATMAP_LEVEL_COLORS = ["#161B22", "#0E4429", "#006D32", "#26A641", "#39D353"]
_WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_HEATMAP_WEEKS = 53


def _review_count_to_level(count: int) -> int:
    """将日审查数映射为 0-4 颜色等级（GitHub 阈值：0, 1-3, 4-6, 7-9, 10+）。"""
    if count <= 0:
        return 0
    if count <= 3:
        return 1
    if count <= 6:
        return 2
    if count <= 9:
        return 3
    return 4


def _build_review_heatmap_df(df):
    """构建过去 53 周（365 天）的审查活跃度数据，返回 (heatmap_df, total_reviews)。"""
    today = pd.Timestamp.today().normalize()
    if not df.empty and "updated_at" in df.columns:
        max_dt = pd.to_datetime(df["updated_at"]).max()
        if pd.notna(max_dt):
            today = pd.Timestamp(max_dt).normalize()
    # 锚定到最近一个周日（GitHub 风格：列首=周日）
    end_week_start = today - pd.Timedelta(days=(today.weekday() + 1) % 7)
    start_week_start = end_week_start - pd.Timedelta(weeks=_HEATMAP_WEEKS - 1)
    full_dates = pd.date_range(start=start_week_start, periods=_HEATMAP_WEEKS * 7, freq="D")

    if df.empty or "updated_at" not in df.columns:
        counts = pd.Series(0, index=full_dates)
    else:
        day_series = pd.to_datetime(df["updated_at"]).dt.normalize()
        counts = day_series.value_counts().reindex(full_dates, fill_value=0).sort_index()

    heatmap_df = pd.DataFrame({"date": full_dates, "count": counts.values.astype(int)})
    heatmap_df["week"] = ((heatmap_df["date"] - start_week_start).dt.days // 7).astype(int)
    heatmap_df["weekday"] = heatmap_df["date"].dt.weekday
    heatmap_df["weekday_label"] = heatmap_df["weekday"].map(dict(enumerate(_WEEKDAY_LABELS)))
    heatmap_df["level"] = heatmap_df["count"].map(_review_count_to_level).astype(int)
    return heatmap_df, int(heatmap_df["count"].sum())


def _render_review_heatmap(heatmap_df):
    """渲染 GitLab 提交统计样式的 53 周 × 7 天审查活跃度热力图。"""
    cell = (
        alt.Chart(heatmap_df)
        .mark_rect(stroke="#0D1117", strokeWidth=2)
        .encode(
            x=alt.X(
                "week:O",
                title=None,
                axis=alt.Axis(labels=False, ticks=False, domain=False, grid=False),
            ),
            y=alt.Y(
                "weekday_label:N",
                sort=_WEEKDAY_LABELS,
                title=None,
                axis=alt.Axis(
                    ticks=False,
                    domain=False,
                    grid=False,
                    labelFontSize=10,
                    labelColor="#6E7686",
                    labelExpr="datum.value === 'Mon' || datum.value === 'Wed' || datum.value === 'Fri' ? datum.value : ''",
                ),
            ),
            color=alt.Color(
                "level:O",
                scale=alt.Scale(domain=[0, 1, 2, 3, 4], range=_HEATMAP_LEVEL_COLORS),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("date:T", title="日期", format="%Y-%m-%d"),
                alt.Tooltip("count:Q", title="审查数"),
            ],
        )
        .properties(height=140)
    )

    # 顶部月份标签：每月 1 号所在周标注月份缩写
    month_starts = heatmap_df[heatmap_df["date"].dt.day == 1][["week", "date"]].copy()
    month_starts["label"] = month_starts["date"].dt.strftime("%b")
    month_starts = month_starts.drop_duplicates(subset=["label"], keep="first")

    month_text = (
        alt.Chart(month_starts)
        .mark_text(align="left", baseline="top", fontSize=10, color="#9BA2AF", dy=-2)
        .encode(
            x=alt.X("week:O", axis=None),
            y=alt.value(0),
            text="label:N",
        )
    )

    chart = (cell + month_text).resolve_scale(y="shared")
    st.altair_chart(_dev_chart(chart, height=170), use_container_width=True)

    # Less [■■■■■] More 图例
    swatches = "".join(
        f'<span style="display:inline-block;width:11px;height:11px;'
        f'background:{c};border-radius:2px;"></span>'
        for c in _HEATMAP_LEVEL_COLORS
    )
    st.markdown(
        f'<div style="display:flex;align-items:center;justify-content:flex-end;'
        f'gap:6px;margin:-8px 0 16px;font-size:11px;color:#6E7686;">'
        f'<span>Less</span>{swatches}<span>More</span></div>',
        unsafe_allow_html=True,
    )


def _grouped_change_chart(df, key):
    """生成人员/项目代码变更行数分组柱状图，X 轴从 0 开始。"""
    df = df.melt(id_vars=[key], value_vars=["additions", "deletions"], var_name="type", value_name="lines")
    df["type"] = df["type"].map({"additions": "新增", "deletions": "删除"})
    xmax = max(df["lines"].max() if not df.empty else 0, 1)
    color_scale = alt.Scale(domain=["新增", "删除"], range=["#3FB950", "#F85149"])
    hover, opacity = _bar_hover()
    return _dev_chart(
        alt.Chart(df)
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            x=alt.X(
                "lines:Q",
                scale=alt.Scale(domain=[0, xmax * 1.1]),
                title=None,
                axis=alt.Axis(tickMinStep=1, format="d", labelExpr="datum.value % 1 === 0 ? datum.label : ''"),
            ),
            y=alt.Y(f"{key}:N", sort="-x", title=None),
            color=alt.Color("type:N", scale=color_scale, title=None),
            opacity=opacity,
        )
        .add_params(hover),
        height=300,
    )


# 渲染统计图表（统一使用 Altair，固定坐标轴从 0 开始）
def render_charts(df):
    # 审查活跃度热力图（GitLab 提交统计风格，过去 53 周）
    st.markdown('<div class="chart-title">审查活跃度 · 过去一年</div>', unsafe_allow_html=True)
    heatmap_df, total_reviews = _build_review_heatmap_df(df)
    st.caption(f"过去一年共 **{total_reviews}** 次审查")
    _render_review_heatmap(heatmap_df)

    if df.empty:
        st.info("当前筛选条件下暂无更多数据")
        return

    # 项目提交统计 & 项目平均得分
    pc = df.groupby("project_name").size().reset_index(name="count").sort_values("count", ascending=False)
    ps = df.groupby("project_name")["score"].mean().reset_index(name="score").sort_values("score", ascending=False)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="chart-title">项目提交统计</div>', unsafe_allow_html=True)
        pmax = max(pc["count"].max() if not pc.empty else 0, 1)
        hover, opacity = _bar_hover()
        chart = _dev_chart(
            alt.Chart(pc)
            .mark_bar(color=_v_grad("#6FA3FF", "#2B5CD6"), cornerRadiusEnd=4)
            .encode(
                x=alt.X(
                    "count:Q",
                    scale=alt.Scale(domain=[0, pmax * 1.1]),
                    title=None,
                    axis=alt.Axis(tickMinStep=1, format="d", labelExpr="datum.value % 1 === 0 ? datum.label : ''"),
                ),
                y=alt.Y("project_name:N", sort="-x", title=None),
                opacity=opacity,
            )
            .add_params(hover),
            height=300,
        )
        st.altair_chart(chart, use_container_width=True)
    with c2:
        st.markdown('<div class="chart-title">项目平均得分</div>', unsafe_allow_html=True)
        hover, opacity = _bar_hover()
        chart = _dev_chart(
            alt.Chart(ps)
            .mark_bar(color=_v_grad("#56D364", "#2F9E44"), cornerRadiusEnd=4)
            .encode(
                x=alt.X("score:Q", scale=alt.Scale(domain=[0, 100]), title=None),
                y=alt.Y("project_name:N", sort="-x", title=None),
                opacity=opacity,
            )
            .add_params(hover),
            height=300,
        )
        st.altair_chart(chart, use_container_width=True)

    # 开发者提交统计 & 开发者平均得分
    ac = df.groupby("author").size().reset_index(name="count").sort_values("count", ascending=False)
    as_ = df.groupby("author")["score"].mean().reset_index(name="score").sort_values("score", ascending=False)
    c3, c4 = st.columns(2)
    with c3:
        st.markdown('<div class="chart-title">开发者提交统计</div>', unsafe_allow_html=True)
        amax = max(ac["count"].max() if not ac.empty else 0, 1)
        hover, opacity = _bar_hover()
        chart = _dev_chart(
            alt.Chart(ac)
            .mark_bar(color=_v_grad("#E3B341", "#9A6E14"), cornerRadiusEnd=4)
            .encode(
                x=alt.X(
                    "count:Q",
                    scale=alt.Scale(domain=[0, amax * 1.1]),
                    title=None,
                    axis=alt.Axis(tickMinStep=1, format="d", labelExpr="datum.value % 1 === 0 ? datum.label : ''"),
                ),
                y=alt.Y("author:N", sort="-x", title=None),
                opacity=opacity,
            )
            .add_params(hover),
            height=300,
        )
        st.altair_chart(chart, use_container_width=True)
    with c4:
        st.markdown('<div class="chart-title">开发者平均得分</div>', unsafe_allow_html=True)
        hover, opacity = _bar_hover()
        chart = _dev_chart(
            alt.Chart(as_)
            .mark_bar(color=_v_grad("#A78BFA", "#6E3FD1"), cornerRadiusEnd=4)
            .encode(
                x=alt.X("score:Q", scale=alt.Scale(domain=[0, 100]), title=None),
                y=alt.Y("author:N", sort="-x", title=None),
                opacity=opacity,
            )
            .add_params(hover),
            height=300,
        )
        st.altair_chart(chart, use_container_width=True)

    # 人员/项目代码变更行数
    acode = df.groupby("author")[["additions", "deletions"]].sum().reset_index()
    pcode = df.groupby("project_name")[["additions", "deletions"]].sum().reset_index()
    c5, c6 = st.columns(2)
    with c5:
        st.markdown('<div class="chart-title">人员代码变更行数</div>', unsafe_allow_html=True)
        st.altair_chart(
            _grouped_change_chart(acode, "author"),
            use_container_width=True,
        )
    with c6:
        st.markdown('<div class="chart-title">项目代码变更行数</div>', unsafe_allow_html=True)
        st.altair_chart(
            _grouped_change_chart(pcode, "project_name"),
            use_container_width=True,
        )
