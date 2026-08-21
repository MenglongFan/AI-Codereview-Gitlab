# -*- coding: utf-8 -*-
import math

import altair as alt
import pandas as pd
import streamlit as st

# 设置Streamlit主题 - 必须是第一个st命令
st.set_page_config(layout="wide", page_title="AI代码审查平台", initial_sidebar_state="expanded")

import datetime
import os
import hashlib
import hmac
import base64
import time
import pandas as pd
from dotenv import load_dotenv
import streamlit as st

from biz.service.review_service import ReviewService
from streamlit_cookies_manager import CookieManager

load_dotenv("conf/.env")

# 从环境变量中读取用户名和密码
DASHBOARD_USER = os.getenv("DASHBOARD_USER", "admin")
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "admin")
USER_CREDENTIALS = {
    DASHBOARD_USER: DASHBOARD_PASSWORD
}

# 用于生成和验证token的密钥
SECRET_KEY = os.getenv("DASHBOARD_SECRET_KEY", "fac8cf149bdd616c07c1a675c4571ccacc40d7f7fe16914cfe0f9f9d966bb773")

# 初始化cookie管理器
cookies = CookieManager()


def generate_token(username):
    """生成包含时间戳的认证token"""
    timestamp = str(int(time.time()))
    message = f"{username}:{timestamp}"

    # 使用HMAC-SHA256生成签名
    signature = hmac.new(
        SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).digest()

    # 将消息和签名编码为base64
    token = base64.b64encode(f"{message}:{base64.b64encode(signature).decode()}".encode()).decode()
    return token


def verify_token(token):
    """验证token的有效性并提取用户名"""
    try:
        # 解码token
        decoded = base64.b64decode(token.encode()).decode()
        message, signature = decoded.rsplit(":", 1)
        username, timestamp = message.split(":", 1)

        # 验证签名
        expected_signature = hmac.new(
            SECRET_KEY.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()

        actual_signature = base64.b64decode(signature)

        if not hmac.compare_digest(expected_signature, actual_signature):
            return None

        # 检查token是否过期（30天）
        if int(time.time()) - int(timestamp) > 30 * 24 * 60 * 60:
            return None

        return username
    except:
        return None


# 检查登录状态
def check_login_status():
    if not cookies.ready():
        st.stop()

    if 'login_status' not in st.session_state:
        st.session_state['login_status'] = False

    # 尝试从cookie获取token
    auth_token = cookies.get('auth_token')
    if auth_token:
        username = verify_token(auth_token)
        if username and username in USER_CREDENTIALS:
            st.session_state['login_status'] = True
            st.session_state['username'] = username
            st.session_state['saved_username'] = username

    return st.session_state['login_status']


# 设置登录状态
def set_login_status(username, remember):
    st.session_state['login_status'] = True
    st.session_state['username'] = username
    st.session_state['saved_username'] = username if remember else ''

    if remember:
        # 生成并保存token到cookie
        auth_token = generate_token(username)
        cookies['auth_token'] = auth_token
    else:
        # 如果不记住登录状态，清除cookie
        if 'auth_token' in cookies:
            del cookies['auth_token']
    cookies.save()


# 获取保存的用户名
def get_saved_credentials():
    auth_token = cookies.get('auth_token')
    if auth_token:
        username = verify_token(auth_token)
        if username:
            return username, ''
    return st.session_state.get('saved_username', ''), ''


# 登录验证函数
def authenticate(username, password, remember_password=False):
    if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
        set_login_status(username, remember_password)
        return True
    return False


# 获取数据函数
def get_data(service_func, authors=None, project_names=None, updated_at_gte=None, updated_at_lte=None, columns=None):
    df = service_func(authors=authors, project_names=project_names, updated_at_gte=updated_at_gte,
                      updated_at_lte=updated_at_lte)

    if df.empty:
        return pd.DataFrame(columns=columns)

    if "updated_at" in df.columns:
        df["updated_at"] = df["updated_at"].apply(
            lambda ts: datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
            if isinstance(ts, (int, float)) else ts
        )

    def format_delta(row):
        if not math.isnan(row['additions']) and not math.isnan(row['deletions']):
            return f"+{int(row['additions'])}  -{int(row['deletions'])}"
        else:
            return ""

    if "additions" in df.columns and "deletions" in df.columns:
        df["delta"] = df.apply(format_delta, axis=1)
    else:
        df["delta"] = ""

    data = df[columns]
    return data


# ============ 深色终端美学 · 全局样式 ============
GLOBAL_CSS = """
<style>
/* ---- 自托管思源黑体（woff2 子集，避免客户端系统字体差异） ---- */
@font-face {
    font-family: "SourceHanSansSC";
    src: url("/app/static/fonts/SourceHanSansSC-subset.woff2") format("woff2");
    font-weight: 400;
    font-style: normal;
    font-display: swap;
}

:root {
    --bg: #0A0E17;
    --card: rgba(16, 24, 42, 0.82);
    --card-solid: #0E1526;
    --border: rgba(148, 163, 184, 0.14);
    --border-strong: rgba(148, 163, 184, 0.26);
    --text: #E2E8F0;
    --text-dim: #94A3B8;
    --text-faint: #5B6B82;
    --accent: #22D3EE;
    --green: #4ADE80;
    --amber: #FBBF24;
    --red: #FB7185;
    --purple: #C084FC;
    --mono: "JetBrains Mono", "Cascadia Code", "SF Mono", "Fira Code", "IBM Plex Mono",
            Consolas, "SourceHanSansSC", "PingFang SC", "Microsoft YaHei", monospace;
    --sans: "SourceHanSansSC", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei",
            -apple-system, "Helvetica Neue", Arial, sans-serif;
}

/* ---- 全局字体与渲染 ---- */
html, body, [class*="css"], [data-testid="stAppViewContainer"] {
    font-family: var(--sans);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-rendering: optimizeLegibility;
    font-kerning: normal;
}

/* ---- 隐藏默认 chrome ---- */
#MainMenu {visibility: hidden;}
header[data-testid="stHeader"] {display: none !important;}
footer {visibility: hidden;}
div.block-container {padding-top: 1.1rem !important; padding-bottom: 1.5rem !important;}

/* ---- 等宽数字对齐（避免表格/指标数字跳动） ---- */
[data-testid="stMetricValue"],
[data-testid="stDataFrame"] td,
.kpi-value {
    font-variant-numeric: tabular-nums;
    font-feature-settings: "tnum";
}

/* ---- 页面背景：墨蓝黑 + 细网格纹理 + 微弱光晕 ---- */
[data-testid="stAppViewContainer"] {
    background-color: var(--bg);
    background-image:
        linear-gradient(rgba(148, 163, 184, 0.045) 1px, transparent 1px),
        linear-gradient(90deg, rgba(148, 163, 184, 0.045) 1px, transparent 1px),
        radial-gradient(circle at 12% -5%, rgba(34, 211, 238, 0.09), transparent 42%),
        radial-gradient(circle at 92% 6%, rgba(74, 222, 128, 0.05), transparent 38%),
        radial-gradient(circle at 70% 95%, rgba(192, 132, 252, 0.05), transparent 40%);
    background-size: 32px 32px, 32px 32px, auto, auto, auto;
    background-attachment: fixed;
}

/* ---- 侧边栏 ---- */
[data-testid="stSidebar"] {
    background: #0C1220;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] .block-container {padding-top: 1.1rem !important;}
.side-label {
    font-family: var(--mono);
    font-size: 0.66rem;
    color: var(--text-faint);
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin: 0.6rem 0 0.25rem 0;
}
.side-label::before {content: "// "; color: var(--accent);}
.side-version {
    font-family: var(--mono);
    font-size: 0.64rem;
    color: var(--text-faint);
    margin-top: 1.2rem;
}

/* ---- 顶部标题 ---- */
.dash-heading-bar h4 {
    font-family: var(--sans);
    font-size: 1.55rem;
    font-weight: 700;
    color: var(--text);
    margin: 0;
    letter-spacing: -0.01em;
}
.dash-subtitle {
    font-family: var(--mono);
    font-size: 0.7rem;
    color: var(--text-faint);
    text-transform: uppercase;
    letter-spacing: 0.14em;
    margin-top: 0.2rem;
}
.dash-subtitle b {color: var(--accent); font-weight: 600;}

/* ---- LIVE 状态灯 ---- */
.live-wrap {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    height: 100%;
    gap: 8px;
}
.live-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 10px rgba(74, 222, 128, 0.7);
    animation: pulse 2.2s ease-in-out infinite;
}
@keyframes pulse {0%, 100% {opacity: 1;} 50% {opacity: 0.3;}}
.live-label {
    font-family: var(--mono);
    font-size: 0.68rem;
    color: var(--green);
    letter-spacing: 0.14em;
}
.live-user {
    font-family: var(--mono);
    font-size: 0.68rem;
    color: var(--text-faint);
}

/* ---- KPI 卡片（终端面板风） ---- */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin: 0.4rem 0 0.8rem 0;
}
.kpi {
    position: relative;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.05rem 1.2rem 1.2rem 1.2rem;
    overflow: hidden;
}
.kpi::before {
    content: "";
    position: absolute;
    left: 0; top: 0;
    width: 100%; height: 2px;
    background: linear-gradient(90deg, var(--kpi-color), transparent 75%);
}
.kpi::after {
    content: "";
    position: absolute;
    right: 14px; top: 12px;
    width: 7px; height: 7px;
    border: 1px solid var(--kpi-color);
    transform: rotate(45deg);
    opacity: 0.55;
}
.kpi-label {
    font-family: var(--mono);
    font-size: 0.66rem;
    color: var(--text-dim);
    letter-spacing: 0.12em;
    text-transform: uppercase;
}
.kpi-value {
    font-family: var(--mono);
    font-size: 1.9rem;
    font-weight: 700;
    color: var(--text);
    margin-top: 0.35rem;
    line-height: 1.1;
    font-variant-numeric: tabular-nums;
}
.kpi-accent  {--kpi-color: var(--accent);}
.kpi-green   {--kpi-color: var(--green);}
.kpi-amber   {--kpi-color: var(--amber);}
.kpi-purple  {--kpi-color: var(--purple);}

/* ---- 卡片化容器（图表 / 明细面板） ---- */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--card);
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.25);
}
[data-testid="stVerticalBlockBorderWrapper"] > div {background: transparent;}

/* ---- 面板标题 ---- */
.chart-title {
    font-family: var(--mono);
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin: 0.4rem 0 0.3rem 0;
}
.chart-title::before {content: "// "; color: var(--accent);}

/* ---- 按钮 ---- */
.stButton > button {
    background: transparent;
    border: 1px solid var(--border-strong);
    border-radius: 8px;
    color: var(--text-dim);
    font-family: var(--mono);
    font-size: 0.76rem;
    letter-spacing: 0.05em;
    transition: all 0.18s ease;
}
.stButton > button:hover {
    border-color: var(--accent);
    color: var(--accent);
}

/* ---- 分段控件（时间预设） ---- */
[data-testid="stSegmentedControl"] {
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 3px;
}
[data-testid="stSegmentedControl"] label span {
    font-family: var(--mono);
    font-size: 0.72rem;
    letter-spacing: 0.04em;
}

/* ---- 侧边栏控件文字 ---- */
[data-testid="stSidebar"] label p,
[data-testid="stSidebar"] [data-baseweb="select"] div {
    font-size: 0.78rem;
}

/* ---- 数据表 ---- */
[data-testid="stDataFrame"] {border-radius: 8px; overflow: hidden;}

/* ---- Tabs（备用样式） ---- */
.stTabs [data-baseweb="tab-list"] {gap: 2px; border-bottom: 1px solid var(--border);}
.stTabs [data-baseweb="tab"] {
    font-family: var(--mono);
    font-size: 0.76rem;
    letter-spacing: 0.06em;
    color: var(--text-dim);
    text-transform: uppercase;
}
.stTabs [aria-selected="true"] {color: var(--accent);}

/* ---- 登录页文字 ---- */
.login-title {
    font-family: var(--mono);
    font-size: 1.9rem;
    font-weight: 700;
    color: var(--text);
    text-align: center;
    margin: 0.4rem 0 0.2rem 0;
    letter-spacing: 0.02em;
}
.login-title::before {content: "> "; color: var(--accent);}
.login-subtitle {
    font-family: var(--mono);
    font-size: 0.72rem;
    color: var(--text-faint);
    text-align: center;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    margin-bottom: 1.4rem;
}
</style>
"""

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# ============ 深色终端美学 · 登录页 ============
LOGIN_CSS = """
<style>
[data-testid="stAppViewContainer"] {
    background-color: #0A0E17;
    background-image:
        linear-gradient(rgba(148, 163, 184, 0.05) 1px, transparent 1px),
        linear-gradient(90deg, rgba(148, 163, 184, 0.05) 1px, transparent 1px),
        radial-gradient(circle at 50% 12%, rgba(34, 211, 238, 0.12), transparent 45%),
        radial-gradient(circle at 85% 85%, rgba(74, 222, 128, 0.07), transparent 40%),
        radial-gradient(circle at 10% 80%, rgba(192, 132, 252, 0.08), transparent 38%);
    background-size: 32px 32px, 32px 32px, auto, auto, auto;
}
[data-testid="stHeader"] {display: none;}
[data-testid="stToolbar"] {display: none;}
div.block-container {padding-top: 4.5rem !important;}
.stForm {
    background: var(--card, rgba(16, 24, 42, 0.85));
    border: 1px solid var(--border, rgba(148, 163, 184, 0.18));
    border-radius: 12px;
    padding: 2.4rem 2.8rem;
    box-shadow: 0 0 50px rgba(34, 211, 238, 0.07), 0 20px 60px rgba(0, 0, 0, 0.5);
}
.stForm [data-testid="stTextInput"] input {
    background: rgba(10, 14, 23, 0.8);
    border: 1px solid var(--border, rgba(148, 163, 184, 0.2));
    border-radius: 8px;
    color: var(--text, #E2E8F0);
    font-family: var(--mono, monospace);
}
.stForm [data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #0891B2 0%, #06B6D4 60%, #22D3EE 100%);
    border: none;
    border-radius: 8px;
    color: #04121A;
    font-family: var(--mono, monospace);
    font-weight: 700;
    letter-spacing: 0.22em;
    font-size: 0.82rem;
}
.stForm [data-testid="stFormSubmitButton"] button:hover {
    box-shadow: 0 0 22px rgba(34, 211, 238, 0.4);
}
.stForm [data-testid="stCheckbox"] label p {font-size: 0.78rem;}
</style>
"""


# 登录界面
def login_page():
    st.markdown(LOGIN_CSS, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<h1 class="login-title">AI代码审查平台</h1>', unsafe_allow_html=True)
        st.markdown('<p class="login-subtitle">REVIEW DASHBOARD</p>', unsafe_allow_html=True)

        # 获取保存的用户名和密码
        saved_username, saved_password = get_saved_credentials()

        # 创建一个form，支持回车提交
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("用户名", value=saved_username)
            password = st.text_input("密码", type="password", value=saved_password)
            remember_password = st.checkbox("记住密码", value=bool(saved_username))
            submit = st.form_submit_button("登 录", use_container_width=True)

            if submit:
                if authenticate(username, password, remember_password):
                    st.rerun()  # 重新运行应用以显示主要内容
                else:
                    st.error("用户名或密码错误")


# 渲染时间范围筛选（预设按钮 + 日期选择联动，侧边栏紧凑版）
def render_date_filter(tab_key):
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
        return None, None

    default_start = current_date - datetime.timedelta(days=days)
    c1, c2 = st.columns(2)
    start_date = c1.date_input("开始", value=default_start, key=f"{tab_key}_start")
    end_date = c2.date_input("结束", value=current_date, key=f"{tab_key}_end")
    return start_date, end_date


def _grouped_change_chart(df, key):
    """生成人员/项目代码变更行数分组柱状图，X 轴从 0 开始。"""
    df = df.melt(id_vars=[key], value_vars=["additions", "deletions"], var_name="type", value_name="lines")
    df["type"] = df["type"].map({"additions": "新增", "deletions": "删除"})
    xmax = max(df["lines"].max() if not df.empty else 0, 1)
    color_scale = alt.Scale(domain=["新增", "删除"], range=["#4ADE80", "#FB7185"])
    return (
        alt.Chart(df)
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            x=alt.X("lines:Q", scale=alt.Scale(domain=[0, xmax * 1.1]), title="lines"),
            y=alt.Y(f"{key}:N", sort="x", title=None),
            color=alt.Color("type:N", scale=color_scale, title=None),
        )
    )


# 渲染统计图表（统一使用 Altair，固定坐标轴从 0 开始）
def render_charts(df):
    if df.empty:
        st.info("当前筛选条件下暂无数据")
        return

    # 每日审查量趋势
    daily = df.copy()
    daily["day"] = pd.to_datetime(daily["updated_at"]).dt.date
    daily_counts = daily.groupby("day").size().reset_index(name="count")
    st.markdown('<div class="chart-title">每日审查量趋势</div>', unsafe_allow_html=True)
    chart = alt.Chart(daily_counts).mark_line(color="#22D3EE", strokeWidth=3).encode(
        x=alt.X("day:T", title=None),
        y=alt.Y("count:Q", scale=alt.Scale(domain=[0, max(daily_counts["count"].max(), 1) * 1.1]), title="count"),
    )
    st.altair_chart(chart, use_container_width=True)

    # 项目提交统计 & 项目平均得分
    pc = df.groupby("project_name").size().reset_index(name="count").sort_values("count", ascending=True)
    ps = df.groupby("project_name")["score"].mean().reset_index(name="score").sort_values("score", ascending=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="chart-title">项目提交统计</div>', unsafe_allow_html=True)
        pmax = max(pc["count"].max() if not pc.empty else 0, 1)
        chart = alt.Chart(pc).mark_bar(color="#22D3EE", cornerRadiusEnd=4).encode(
            x=alt.X("count:Q", scale=alt.Scale(domain=[0, pmax * 1.1]), title="count"),
            y=alt.Y("project_name:N", sort="x", title=None),
        )
        st.altair_chart(chart, use_container_width=True)
    with c2:
        st.markdown('<div class="chart-title">项目平均得分</div>', unsafe_allow_html=True)
        chart = alt.Chart(ps).mark_bar(color="#4ADE80", cornerRadiusEnd=4).encode(
            x=alt.X("score:Q", scale=alt.Scale(domain=[0, 100]), title="score"),
            y=alt.Y("project_name:N", sort="x", title=None),
        )
        st.altair_chart(chart, use_container_width=True)

    # 开发者提交统计 & 开发者平均得分
    ac = df.groupby("author").size().reset_index(name="count").sort_values("count", ascending=True)
    as_ = df.groupby("author")["score"].mean().reset_index(name="score").sort_values("score", ascending=True)
    c3, c4 = st.columns(2)
    with c3:
        st.markdown('<div class="chart-title">开发者提交统计</div>', unsafe_allow_html=True)
        amax = max(ac["count"].max() if not ac.empty else 0, 1)
        chart = alt.Chart(ac).mark_bar(color="#FBBF24", cornerRadiusEnd=4).encode(
            x=alt.X("count:Q", scale=alt.Scale(domain=[0, amax * 1.1]), title="count"),
            y=alt.Y("author:N", sort="x", title=None),
        )
        st.altair_chart(chart, use_container_width=True)
    with c4:
        st.markdown('<div class="chart-title">开发者平均得分</div>', unsafe_allow_html=True)
        chart = alt.Chart(as_).mark_bar(color="#C084FC", cornerRadiusEnd=4).encode(
            x=alt.X("score:Q", scale=alt.Scale(domain=[0, 100]), title="score"),
            y=alt.Y("author:N", sort="x", title=None),
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


# 渲染 KPI 指标卡（自定义 HTML，终端面板风）
def render_kpis(df):
    if df.empty:
        return
    total_records = len(df)
    average_score = df["score"].mean()
    project_cnt = df["project_name"].nunique()
    add_sum = int(df["additions"].sum())
    del_sum = int(df["deletions"].sum())

    cards = [
        ("审查记录数", f"{total_records}", "kpi-accent"),
        ("平均得分", f"{average_score:.1f}", "kpi-green"),
        ("涉及项目", f"{project_cnt}", "kpi-amber"),
        ("代码变更", f"+{add_sum} / -{del_sum}", "kpi-purple"),
    ]
    html = "".join(
        f'<div class="kpi {cls}"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div></div>'
        for label, value, cls in cards
    )
    st.markdown(f'<div class="kpi-grid">{html}</div>', unsafe_allow_html=True)


# 渲染 Token 消耗统计（KPI + 聚合图，随侧边栏筛选联动）
def render_token_stats(df):
    if df.empty or "total_tokens" not in df.columns:
        return

    total = int(df["total_tokens"].sum())
    prompt = int(df["prompt_tokens"].sum())
    completion = int(df["completion_tokens"].sum())
    avg = int(df["total_tokens"].mean())

    cards = [
        ("Token Total", f"{total:,}", "kpi-accent"),
        ("Prompt Tokens", f"{prompt:,}", "kpi-green"),
        ("Completion Tokens", f"{completion:,}", "kpi-amber"),
        ("Avg / Review", f"{avg:,}", "kpi-purple"),
    ]
    html = "".join(
        f'<div class="kpi {cls}"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div></div>'
        for label, value, cls in cards
    )
    st.markdown(f'<div class="kpi-grid">{html}</div>', unsafe_allow_html=True)

    # 按项目 / 按作者 token 排行
    pt = df.groupby("project_name")["total_tokens"].sum().reset_index(name="tokens").sort_values("tokens")
    at = df.groupby("author")["total_tokens"].sum().reset_index(name="tokens").sort_values("tokens")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="chart-title">Token by Project</div>', unsafe_allow_html=True)
        pmax = max(pt["tokens"].max() if not pt.empty else 0, 1)
        chart = alt.Chart(pt).mark_bar(color="#22D3EE", cornerRadiusEnd=4).encode(
            x=alt.X("tokens:Q", scale=alt.Scale(domain=[0, pmax * 1.1]), title="tokens"),
            y=alt.Y("project_name:N", sort="x", title=None),
        )
        st.altair_chart(chart, use_container_width=True)
    with c2:
        st.markdown('<div class="chart-title">Token by Author</div>', unsafe_allow_html=True)
        amax = max(at["tokens"].max() if not at.empty else 0, 1)
        chart = alt.Chart(at).mark_bar(color="#C084FC", cornerRadiusEnd=4).encode(
            x=alt.X("tokens:Q", scale=alt.Scale(domain=[0, amax * 1.1]), title="tokens"),
            y=alt.Y("author:N", sort="x", title=None),
        )
        st.altair_chart(chart, use_container_width=True)

    # Token 时间趋势（按天聚合）
    daily = df.copy()
    daily["day"] = pd.to_datetime(daily["updated_at"]).dt.date
    daily_tokens = daily.groupby("day")["total_tokens"].sum().reset_index(name="tokens")
    st.markdown('<div class="chart-title">Token Trend</div>', unsafe_allow_html=True)
    if len(daily_tokens) > 0:
        chart = alt.Chart(daily_tokens).mark_area(color="#22D3EE", opacity=0.6).encode(
            x=alt.X("day:T", title=None),
            y=alt.Y("tokens:Q", scale=alt.Scale(domain=[0, max(daily_tokens["tokens"].max(), 1) * 1.1]), title="tokens"),
        )
        st.altair_chart(chart, use_container_width=True)


# 渲染工作日报的 Token 消耗（独立归类，与 review 统计分开）
def render_daily_report_stats():
    try:
        rdf = ReviewService().get_daily_report_logs()
    except Exception:
        return
    if rdf.empty or "total_tokens" not in rdf.columns:
        st.caption("日报 Token 消耗：暂无记录")
        return

    total = int(rdf["total_tokens"].sum())
    prompt = int(rdf["prompt_tokens"].sum())
    completion = int(rdf["completion_tokens"].sum())

    cards = [
        ("Daily Report Tokens", f"{total:,}", "kpi-accent"),
        ("Prompt Tokens", f"{prompt:,}", "kpi-green"),
        ("Completion Tokens", f"{completion:,}", "kpi-amber"),
        ("生成次数", f"{len(rdf)}", "kpi-purple"),
    ]
    html = "".join(
        f'<div class="kpi {cls}"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div></div>'
        for label, value, cls in cards
    )
    st.markdown(f'<div class="kpi-grid">{html}</div>', unsafe_allow_html=True)

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


# 退出登录函数
def logout():
    # 清除session状态
    st.session_state['login_status'] = False
    st.session_state.pop('username', None)
    st.session_state.pop('saved_username', None)

    # 清除cookie
    if 'auth_token' in cookies:
        del cookies['auth_token']
    cookies.save()

    st.rerun()


def main_page():
    # ---- 顶部：标题 + LIVE 状态 + 退出登录 ----
    head_left, head_right = st.columns([7, 3])
    with head_left:
        st.markdown(
            '<div class="dash-heading-bar"><h4>代码审查统计</h4></div>'
            '<div class="dash-subtitle"><b>AI REVIEW</b> &nbsp;·&nbsp; MR / PUSH DASHBOARD</div>',
            unsafe_allow_html=True,
        )
    with head_right:
        top_status, top_btn = st.columns([1.6, 1.4])
        with top_status:
            username = st.session_state.get('username', '')
            st.markdown(
                f'<div class="live-wrap"><span class="live-dot"></span>'
                f'<span class="live-label">LIVE</span>'
                f'<span class="live-user">{username}</span></div>',
                unsafe_allow_html=True,
            )
        with top_btn:
            if st.button("退出登录", key="logout_button", use_container_width=True):
                logout()

    # ---- 数据源定义 ----
    mr_columns = ["project_name", "author", "source_branch", "target_branch", "updated_at", "commit_messages", "delta",
                  "score", "url", 'additions', 'deletions',
                  "prompt_tokens", "completion_tokens", "total_tokens"]

    mr_column_config = {
        "project_name": "项目名称",
        "author": "开发者",
        "source_branch": "源分支",
        "target_branch": "目标分支",
        "updated_at": "更新时间",
        "commit_messages": "提交信息",
        "delta": "代码变更",
        "score": st.column_config.NumberColumn(
            "得分", format="%d", min_value=0, max_value=100,
        ),
        "url": st.column_config.LinkColumn("操作", max_chars=100, display_text="查看详情"),
        "additions": None,
        "deletions": None,
        "prompt_tokens": st.column_config.NumberColumn("Prompt", format="%d"),
        "completion_tokens": st.column_config.NumberColumn("Completion", format="%d"),
        "total_tokens": st.column_config.NumberColumn("Tokens", format="%d"),
    }

    push_columns = ["project_name", "author", "branch", "updated_at", "commit_messages", "delta", "score",
                    'additions', 'deletions',
                    "prompt_tokens", "completion_tokens", "total_tokens"]

    push_column_config = {
        "project_name": "项目名称",
        "author": "开发者",
        "branch": "分支",
        "updated_at": "更新时间",
        "commit_messages": "提交信息",
        "delta": "代码变更",
        "score": st.column_config.NumberColumn(
            "得分", format="%d", min_value=0, max_value=100,
        ),
        "additions": None,
        "deletions": None,
        "prompt_tokens": st.column_config.NumberColumn("Prompt", format="%d"),
        "completion_tokens": st.column_config.NumberColumn("Completion", format="%d"),
        "total_tokens": st.column_config.NumberColumn("Tokens", format="%d"),
    }

    show_push_tab = os.environ.get('PUSH_REVIEW_ENABLED', '0') == '1'

    # ---- 侧边栏：视图切换 + 筛选 ----
    with st.sidebar:
        st.markdown('<div class="side-label">View</div>', unsafe_allow_html=True)
        if show_push_tab:
            view = st.radio("数据源", ["合并请求", "代码推送"], label_visibility="collapsed")
        else:
            view = "合并请求"

        tab_key = "push" if view == "代码推送" else "mr"
        service_func = (ReviewService().get_push_review_logs if view == "代码推送"
                        else ReviewService().get_mr_review_logs)
        columns = push_columns if view == "代码推送" else mr_columns
        column_config = push_column_config if view == "代码推送" else mr_column_config

        st.markdown('<div class="side-label">Filter</div>', unsafe_allow_html=True)
        start_date, end_date = render_date_filter(tab_key)

        start_datetime = (int(datetime.datetime.combine(start_date, datetime.time.min).timestamp())
                          if start_date else None)
        end_datetime = (int(datetime.datetime.combine(end_date, datetime.time.max).timestamp())
                        if end_date else None)

        # 先按时间范围查一次，用于构建作者/项目选项
        base = get_data(service_func, updated_at_gte=start_datetime,
                        updated_at_lte=end_datetime, columns=columns)
        df_base = pd.DataFrame(base)
        unique_authors = (sorted(df_base["author"].dropna().unique().tolist()) if not df_base.empty else [])
        unique_projects = (sorted(df_base["project_name"].dropna().unique().tolist()) if not df_base.empty else [])

        authors = st.multiselect("开发者", unique_authors, default=[], key=f"{tab_key}_authors")
        project_names = st.multiselect("项目名称", unique_projects, default=[], key=f"{tab_key}_projects")

        st.markdown('<div class="side-version">AI-Codereview-Gitlab · v1</div>', unsafe_allow_html=True)

    # ---- 主区内容 ----
    data = get_data(service_func, authors=authors, project_names=project_names,
                    updated_at_gte=start_datetime, updated_at_lte=end_datetime, columns=columns)
    df = pd.DataFrame(data)

    # KPI 指标
    render_kpis(df)

    # Token 消耗统计（明细聚合，随筛选联动）
    if not df.empty:
        st.divider()
        with st.container(border=True):
            st.markdown('<div class="chart-title">Token 消耗统计</div>', unsafe_allow_html=True)
            render_token_stats(df)

    # 统计图表
    with st.container(border=True):
        st.markdown('<div class="chart-title">统计图表</div>', unsafe_allow_html=True)
        render_charts(df)

    # 工作日报 Token 消耗（独立归类）
    st.divider()
    with st.container(border=True):
        st.markdown('<div class="chart-title">日报 Token 消耗</div>', unsafe_allow_html=True)
        render_daily_report_stats()

    # 数据明细
    with st.container(border=True):
        st.markdown('<div class="chart-title">数据明细</div>', unsafe_allow_html=True)
        st.data_editor(
            df,
            use_container_width=True,
            column_config=column_config,
            hide_index=True,
        )


# 应用入口
if check_login_status():
    main_page()
else:
    login_page()
