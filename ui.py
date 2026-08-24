# -*- coding: utf-8 -*-
import math
from pathlib import Path

import datetime
import os
import hashlib
import hmac
import base64
import time

import altair as alt
import pandas as pd
import streamlit as st
st.set_page_config(layout="wide", page_title="AI代码审查平台", initial_sidebar_state="expanded")
from dotenv import load_dotenv

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


# ============================================================
# 深色开发者工具风 · 设计系统（Linear / Vercel / GitHub 灵感）
# 令牌：深石墨底 + 克制蓝 + 语义色 + 等宽字体点缀 + 工具化圆角
# ============================================================
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

/* ---- Design Tokens ---- */
:root {
    /* 色板：深石墨底 */
    --bg: #0A0B0E;
    --bg-soft: #0E1014;
    --surface: #14161B;
    --surface-2: #191C22;
    --surface-3: #20242C;
    --border: rgba(255, 255, 255, 0.07);
    --border-strong: rgba(255, 255, 255, 0.14);
    --text: #E8EAEE;
    --text-dim: #9BA2AF;
    --text-faint: #6E7686;
    /* 品牌与语义色 */
    --accent: #4C8DFF;
    --accent-hover: #6FA3FF;
    --accent-weak: rgba(76, 141, 255, 0.13);
    --green: #3FB950;
    --green-weak: rgba(63, 185, 80, 0.14);
    --amber: #D29922;
    --amber-weak: rgba(210, 153, 34, 0.16);
    --red: #F85149;
    --red-weak: rgba(248, 81, 73, 0.14);
    --purple: #A371F7;
    --purple-weak: rgba(163, 113, 247, 0.14);
    /* 字体 */
    --mono: "SF Mono", "JetBrains Mono", "Cascadia Code", "Fira Code", "IBM Plex Mono",
            Consolas, "SourceHanSansSC", "PingFang SC", "Microsoft YaHei", monospace;
    --sans: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto,
            "Helvetica Neue", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei",
            "SourceHanSansSC", Arial, sans-serif;
    /* 圆角与阴影（工具化：小圆角、轻阴影） */
    --radius-sm: 6px;
    --radius: 10px;
    --radius-lg: 14px;
    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.35);
    --shadow-md: 0 8px 24px rgba(0, 0, 0, 0.35);
    --ring: 0 0 0 3px rgba(76, 141, 255, 0.22);
    --ease: cubic-bezier(0.25, 0.1, 0.25, 1);
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
[data-testid="stDataEditor"] td,
.kpi-value {
    font-variant-numeric: tabular-nums;
    font-feature-settings: "tnum";
}

/* ---- 页面背景：纯深石墨 + 顶部一束克制蓝光 ---- */
[data-testid="stAppViewContainer"] {
    background-color: var(--bg);
    background-image:
        radial-gradient(1100px 340px at 50% -160px, rgba(76, 141, 255, 0.07), transparent 70%);
    background-attachment: fixed;
}

/* ---- 侧边栏：平坦深灰面板 + 发丝线 ---- */
[data-testid="stSidebar"] {
    background: var(--bg-soft);
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] .block-container {padding-top: 1.2rem !important;}
.side-label {
    font-family: var(--mono);
    font-size: 0.64rem;
    font-weight: 600;
    color: var(--text-faint);
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin: 0.8rem 0 0.4rem 0;
}
.side-version {
    font-family: var(--mono);
    font-size: 0.62rem;
    color: var(--text-faint);
    margin-top: 1.4rem;
    letter-spacing: 0.04em;
}

/* ---- 顶部导航栏：去框线 + 渐变光丝 ---- */
.dash-nav {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: transparent;
    border: none;
    border-radius: 0;
    padding: 0.55rem 0;
    margin-bottom: 0.9rem;
    box-shadow: none;
    gap: 1rem;
    overflow: hidden;
}
.dash-nav::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(76, 141, 255, 0.45), transparent);
    opacity: 0.5;
}
.dash-nav-left {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    min-width: 0;
}
.nav-mark {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 30px;
    height: 30px;
    border-radius: 8px;
    background: linear-gradient(135deg, #4C8DFF 0%, #7C5CFF 100%);
    box-shadow: 0 4px 14px rgba(76, 141, 255, 0.35);
    flex: none;
}
.nav-mark svg {
    width: 16px;
    height: 16px;
    fill: none;
    stroke: #FFFFFF;
    stroke-width: 2.2;
    stroke-linecap: round;
    stroke-linejoin: round;
}
.nav-titles {
    display: flex;
    flex-direction: column;
    min-width: 0;
    line-height: 1.2;
}
.dash-nav-left h4 {
    font-family: var(--sans);
    font-size: 1.02rem;
    font-weight: 650;
    color: var(--text);
    margin: 0;
    letter-spacing: -0.015em;
    white-space: nowrap;
}
.dash-nav-sub {
    font-family: var(--mono);
    font-size: 0.62rem;
    color: var(--text-faint);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-weight: 500;
    white-space: nowrap;
    margin-top: 1px;
}
.dash-nav-right {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 12px;
    flex: none;
    min-height: 34px;
}

/* ---- LIVE 状态灯 ---- */
.live-wrap {
    display: flex;
    align-items: center;
    gap: 7px;
    flex: none;
    min-height: 34px;
}
.live-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 0 3px rgba(63, 185, 80, 0.16), 0 0 8px rgba(63, 185, 80, 0.4);
    animation: pulse 2.4s cubic-bezier(0.22, 1, 0.36, 1) infinite;
}
@keyframes pulse {0%, 100% {opacity: 1; transform: scale(1);} 50% {opacity: 0.4; transform: scale(0.82);}}
.live-label {
    font-family: var(--mono);
    font-size: 0.64rem;
    font-weight: 600;
    color: var(--green);
    letter-spacing: 0.12em;
}
.live-user {
    font-family: var(--sans);
    font-size: 0.72rem;
    color: var(--text-dim);
    font-weight: 500;
}

/* ---- 退出按钮：右上角圆形图标按钮，hover 泛红 ---- */
.nav-logout {
    display: flex;
    align-items: center;
    flex: none;
}
.nav-logout .stButton {
    margin: 0 !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
.nav-logout .stButton > button {
    background: transparent !important;
    border: none !important;
    border-radius: 50% !important;
    color: var(--text-faint) !important;
    width: 32px !important;
    height: 32px !important;
    padding: 0 !important;
    font-size: 1.1rem !important;
    line-height: 1 !important;
    min-height: auto !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: background 0.2s var(--ease), color 0.2s, transform 0.12s !important;
}
.nav-logout .stButton > button:hover {
    background: rgba(248, 81, 73, 0.12) !important;
    color: #FF9188 !important;
}
.nav-logout .stButton > button:active {
    transform: scale(0.92) !important;
}

/* ---- KPI 指标卡：平坦表面 + 语义色图标 + 等宽副文案 ---- */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin: 0.4rem 0 1.1rem 0;
}
.kpi {
    position: relative;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem 1.1rem 0.95rem 1.1rem;
    overflow: hidden;
    box-shadow: var(--shadow-sm);
    transition: border-color 0.2s var(--ease), background 0.2s var(--ease), transform 0.2s var(--ease);
}
.kpi:hover {
    border-color: var(--border-strong);
    background: var(--surface-2);
    transform: translateY(-2px);
}
.kpi-top {
    display: flex;
    align-items: center;
    gap: 9px;
    margin-bottom: 0.6rem;
}
.kpi-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border-radius: 7px;
    background: var(--kpi-bg);
    border: 1px solid var(--kpi-border);
    color: var(--kpi-color);
    flex: none;
}
.kpi-icon svg {
    width: 15px;
    height: 15px;
    fill: none;
    stroke: currentColor;
    stroke-width: 2;
    stroke-linecap: round;
    stroke-linejoin: round;
}
.kpi-label {
    font-family: var(--mono);
    font-size: 0.62rem;
    font-weight: 600;
    color: var(--text-faint);
    letter-spacing: 0.1em;
    text-transform: uppercase;
}
.kpi-value {
    font-family: var(--sans);
    font-size: 1.7rem;
    font-weight: 680;
    color: var(--text);
    line-height: 1.05;
    font-variant-numeric: tabular-nums;
    letter-spacing: -0.02em;
}
.kpi-sub {
    font-family: var(--mono);
    font-size: 0.68rem;
    color: var(--text-faint);
    margin-top: 0.35rem;
    letter-spacing: 0.02em;
}
.kpi-accent {--kpi-color: var(--accent); --kpi-bg: var(--accent-weak); --kpi-border: rgba(76, 141, 255, 0.28);}
.kpi-green  {--kpi-color: var(--green);  --kpi-bg: var(--green-weak);  --kpi-border: rgba(63, 185, 80, 0.28);}
.kpi-amber  {--kpi-color: var(--amber);  --kpi-bg: var(--amber-weak);  --kpi-border: rgba(210, 153, 34, 0.30);}
.kpi-purple {--kpi-color: var(--purple); --kpi-bg: var(--purple-weak); --kpi-border: rgba(163, 113, 247, 0.28);}
@media (max-width: 900px) {
    .kpi-grid {grid-template-columns: repeat(2, 1fr);}
}
@media (max-width: 520px) {
    .kpi-grid {grid-template-columns: 1fr;}
}

/* ---- 卡片化容器（图表 / 明细面板） ---- */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--surface);
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    box-shadow: var(--shadow-sm);
    transition: border-color 0.2s ease;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: var(--border-strong);
}
[data-testid="stVerticalBlockBorderWrapper"] > div {background: transparent;}

/* ---- 面板标题：等宽小字 ---- */
.chart-title {
    font-family: var(--mono);
    font-size: 0.7rem;
    font-weight: 600;
    color: var(--text-faint);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin: 0.4rem 0 0.5rem 0;
}

/* ---- 按钮：扁平工具化 ---- */
.stButton > button {
    background: var(--surface-2);
    border: 1px solid var(--border-strong);
    border-radius: var(--radius-sm);
    color: var(--text-dim);
    font-family: var(--sans);
    font-size: 0.8rem;
    font-weight: 500;
    letter-spacing: 0.02em;
    transition: background 0.2s var(--ease), color 0.2s, box-shadow 0.2s, transform 0.12s, border-color 0.2s;
}
.stButton > button:hover {
    background: rgba(76, 141, 255, 0.12);
    border-color: rgba(76, 141, 255, 0.4);
    color: var(--accent-hover);
}
.stButton > button:active {
    transform: scale(0.97);
}

/* ---- 分段控件（时间预设）：扁平分段 ---- */
[data-testid="stSegmentedControl"] {
    background: var(--bg-soft);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 3px;
}
[data-testid="stSegmentedControl"] label span {
    font-family: var(--sans);
    font-size: 0.76rem;
    font-weight: 500;
    letter-spacing: 0.02em;
}
[data-testid="stSegmentedControl"] label {
    border-radius: 4px;
    transition: background 0.2s var(--ease), box-shadow 0.2s;
}
[data-testid="stSegmentedControl"] label:hover {background: rgba(255, 255, 255, 0.05);}
[data-testid="stSegmentedControl"] label[aria-checked="true"] {
    background: var(--surface-3);
    box-shadow: inset 0 1px 1px rgba(0, 0, 0, 0.3);
}

/* ---- 侧边栏控件文字与聚焦态 ---- */
[data-testid="stSidebar"] label p,
[data-testid="stSidebar"] [data-baseweb="select"] div {
    font-size: 0.8rem;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-baseweb="input"] input {
    background: var(--surface-2);
    border-color: var(--border);
    border-radius: var(--radius-sm);
    color: var(--text);
    transition: border-color 0.2s, box-shadow 0.2s, background 0.2s;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div:hover,
[data-testid="stSidebar"] [data-baseweb="input"] input:hover {
    background: var(--surface-3);
    border-color: rgba(76, 141, 255, 0.45);
}
[data-testid="stSidebar"] [data-baseweb="select"] > div:focus-within,
[data-testid="stSidebar"] [data-baseweb="input"] input:focus {
    border-color: var(--accent) !important;
    box-shadow: var(--ring);
}

/* ---- 数据表：平坦 + 发丝行线 + hover 行 ---- */
[data-testid="stDataFrame"],
[data-testid="stDataEditor"] {
    border-radius: var(--radius);
    overflow: hidden;
    border: 1px solid var(--border);
    background: var(--surface);
}
[data-testid="stDataFrame"] thead th,
[data-testid="stDataEditor"] thead th {
    background: var(--surface-2);
    font-family: var(--mono);
    font-size: 0.64rem;
    font-weight: 600;
    color: var(--text-faint);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    border-bottom: 1px solid var(--border) !important;
}
[data-testid="stDataFrame"] td,
[data-testid="stDataEditor"] td {
    background: transparent;
    color: var(--text-dim);
    border-bottom: 1px solid rgba(255, 255, 255, 0.04) !important;
    font-size: 0.8rem;
}
[data-testid="stDataFrame"] tbody tr:hover td,
[data-testid="stDataEditor"] tbody tr:hover td {
    background: var(--surface-2);
}

/* ---- Tabs：下划线式（GitHub / Linear 风格） ---- */
.stTabs [data-baseweb="tab-list"] {
    gap: 2px;
    border-bottom: 1px solid var(--border);
    background: transparent;
    border-radius: 0;
    padding: 0;
    box-shadow: none;
    margin-bottom: 0.5rem;
}
.stTabs [data-baseweb="tab"] {
    font-family: var(--sans);
    font-size: 0.86rem;
    font-weight: 500;
    letter-spacing: 0.02em;
    color: var(--text-dim);
    border-radius: var(--radius-sm) var(--radius-sm) 0 0;
    padding: 0.5rem 1rem !important;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
    transition: color 0.2s, background 0.2s, border-color 0.2s;
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--text);
    background: rgba(255, 255, 255, 0.04);
}
.stTabs [aria-selected="true"] {
    color: var(--text);
    font-weight: 600;
    border-bottom: 2px solid var(--accent);
    background: transparent;
}
.stTabs [data-baseweb="tab-highlight"] {display: none;}

/* ---- 滚动条：纤细深色 ---- */
::-webkit-scrollbar {width: 9px; height: 9px;}
::-webkit-scrollbar-track {background: transparent;}
::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.14);
    border-radius: 6px;
    border: 2px solid transparent;
    background-clip: content-box;
}
::-webkit-scrollbar-thumb:hover {background: rgba(255, 255, 255, 0.24);}

/* ---- 原生控件深色覆盖 ---- */
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label p {color: var(--text-dim);}
[data-testid="stDateInput"] [data-baseweb="input"],
[data-testid="stDateInput"] [data-baseweb="input"] input,
[data-testid="stMultiselect"] [data-baseweb="select"] > div,
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {
    background: var(--surface-2);
    border-color: var(--border);
    color: var(--text);
}
[data-testid="stDateInput"] [data-baseweb="input"]:focus-within,
[data-testid="stMultiselect"] [data-baseweb="select"] > div:focus-within,
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus {
    border-color: var(--accent) !important;
    box-shadow: var(--ring);
}

/* ---- Chrome / Edge 自动填充修复 ---- */
input:-webkit-autofill,
input:-webkit-autofill:hover,
input:-webkit-autofill:focus {
    -webkit-text-fill-color: #E8EAEE !important;
    -webkit-box-shadow: 0 0 0 1000px #16191F inset !important;
    caret-color: var(--accent);
    transition: background-color 9999s ease-in-out 0s;
}
[data-baseweb="popover"] [data-baseweb="menu"],
[data-baseweb="popover"] [data-baseweb="menu"] li,
[data-baseweb="calendar"] {
    background: var(--surface-2);
    color: var(--text);
}
[data-baseweb="popover"] [data-baseweb="menu"] li:hover {
    background: rgba(76, 141, 255, 0.12);
}
[data-baseweb="tag"] {
    background: var(--accent-weak);
    color: var(--accent-hover);
    border-radius: 4px;
}
[data-testid="stCheckbox"] label p {color: var(--text-dim);}
[data-testid="stCheckbox"] label:hover p {color: var(--text);}
[data-testid="stCheckbox"] [role="checkbox"][aria-checked="true"] {
    background: var(--accent);
    border-color: var(--accent);
}
[data-testid="stExpander"] {
    background: var(--surface);
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
}
[data-testid="stAlert"] {
    background: rgba(76, 141, 255, 0.06);
    border: 1px solid rgba(76, 141, 255, 0.18);
    border-radius: var(--radius);
    color: var(--text-dim);
}
[data-testid="stAlert"] [data-testid="stAlertContent"] p {color: var(--text-dim);}
[data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
    color: var(--text);
}

/* ---- 得分进度条：语义色 ---- */
[data-testid="stDataFrame"] [data-testid="stProgress"] div div,
[data-testid="stDataEditor"] [data-testid="stProgress"] div div {
    background: var(--accent) !important;
}

/* ---- 无障碍：尊重减少动效偏好 ---- */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}
</style>
"""


# ============================================================
# 登录页 · 深色开发者工具风（左右分栏：品牌面板 + 认证卡片）
# ============================================================
LOGIN_CSS = """
<style>
/* ---- 登录页背景：深石墨 + 双色克制光晕 ---- */
[data-testid="stAppViewContainer"] {
    background-color: #0A0B0E;
    background-image:
        radial-gradient(900px 480px at 12% -12%, rgba(76, 141, 255, 0.12), transparent 62%),
        radial-gradient(760px 420px at 104% 108%, rgba(163, 113, 247, 0.07), transparent 60%);
    background-attachment: fixed;
}
[data-testid="stHeader"] {display: none;}
[data-testid="stToolbar"] {display: none;}
[data-testid="stMain"] {
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-height: 100vh;
}
div.block-container {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    max-width: 980px !important;
}
[data-testid="stMain"] .block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
}

/* ---- 左：品牌面板 ---- */
.login-brand {
    padding: 0.6rem 1.2rem 0.6rem 0;
}
.lb-logo {
    display: flex;
    align-items: center;
    gap: 11px;
    margin-bottom: 1.7rem;
}
.lb-logo-mark {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border-radius: 9px;
    background: linear-gradient(135deg, #4C8DFF 0%, #7C5CFF 100%);
    box-shadow: 0 8px 24px rgba(76, 141, 255, 0.38);
    flex: none;
}
.lb-logo-mark svg {
    width: 19px;
    height: 19px;
    fill: none;
    stroke: #FFFFFF;
    stroke-width: 2.2;
    stroke-linecap: round;
    stroke-linejoin: round;
}
.lb-logo-name {
    font-size: 1.02rem;
    font-weight: 650;
    letter-spacing: -0.01em;
    color: #E8EAEE !important;
    line-height: 1.2;
}
.lb-logo-sub {
    font-family: var(--mono);
    font-size: 0.62rem;
    color: #6E7686 !important;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-top: 2px;
}
.lb-title {
    font-size: 1.85rem;
    font-weight: 660;
    letter-spacing: -0.025em;
    line-height: 1.22;
    color: #E8EAEE !important;
    margin: 0 0 0.7rem 0;
}
.lb-title em {
    font-style: normal;
    color: #6FA3FF !important;
}
.lb-desc {
    color: #9BA2AF !important;
    font-size: 0.9rem;
    line-height: 1.7;
    margin: 0 0 1.4rem 0;
    max-width: 400px;
}
.lb-feats {
    list-style: none;
    margin: 0 0 1.6rem 0;
    padding: 0;
    display: grid;
    gap: 0.6rem;
    max-width: 420px;
}
.lb-feats li {
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
    color: #9BA2AF !important;
    font-size: 0.84rem;
    line-height: 1.5;
}
.feat-ico {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 18px;
    height: 18px;
    border-radius: 5px;
    background: var(--green-weak);
    border: 1px solid rgba(63, 185, 80, 0.3);
    color: var(--green);
    flex: none;
    margin-top: 1px;
}
.feat-ico svg {
    width: 11px;
    height: 11px;
    fill: none;
    stroke: currentColor;
    stroke-width: 2.6;
    stroke-linecap: round;
    stroke-linejoin: round;
}

/* ---- 右：认证卡片 ---- */
[data-testid="stForm"] {
    position: relative;
    background: var(--surface);
    border: 1px solid var(--border-strong);
    border-radius: 16px;
    padding: 2.1rem 1.9rem 1.8rem 1.9rem;
    box-shadow: 0 24px 70px rgba(0, 0, 0, 0.5);
    animation: fade-in 0.5s var(--ease) both;
}
[data-testid="stForm"]::before {
    content: "";
    position: absolute;
    top: 0;
    left: 14%;
    right: 14%;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(76, 141, 255, 0.6), transparent);
    opacity: 0.8;
}
.auth-head {
    margin-bottom: 1.5rem;
}
.auth-head h1 {
    font-size: 1.22rem;
    font-weight: 660;
    letter-spacing: -0.015em;
    color: var(--text);
    margin: 0 0 0.3rem 0;
}
.auth-head p {
    font-size: 0.8rem;
    color: var(--text-faint);
    margin: 0;
}

/* ---- 输入框：平坦表面 + 蓝色聚焦环 ---- */
[data-testid="stForm"] [data-testid="stTextInput"] {
    margin-bottom: 0.2rem;
}
[data-testid="stForm"] [data-testid="stTextInput"] [data-baseweb="input"] {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    box-shadow: none !important;
    transition: border-color 0.2s var(--ease), box-shadow 0.2s var(--ease);
}
[data-testid="stForm"] [data-testid="stTextInput"] [data-baseweb="input"]:hover {
    border-color: rgba(76, 141, 255, 0.45) !important;
}
[data-testid="stForm"] [data-testid="stTextInput"] [data-baseweb="input"]:focus-within {
    border-color: var(--accent) !important;
    box-shadow: var(--ring) !important;
}
[data-testid="stForm"] [data-testid="stTextInput"] input {
    background: transparent !important;
    color: var(--text) !important;
    caret-color: var(--accent);
    -webkit-text-fill-color: var(--text);
    font-family: var(--sans);
    font-size: 0.92rem;
    font-weight: 500;
    letter-spacing: 0.02em;
}
[data-testid="stForm"] [data-testid="stTextInput"] input::placeholder {
    color: var(--text-faint) !important;
    -webkit-text-fill-color: var(--text-faint);
    font-weight: 400;
}

/* ---- Chrome / Edge 自动填充修复 ---- */
[data-testid="stForm"] [data-testid="stTextInput"] input:-webkit-autofill,
[data-testid="stForm"] [data-testid="stTextInput"] input:-webkit-autofill:hover,
[data-testid="stForm"] [data-testid="stTextInput"] input:-webkit-autofill:focus {
    -webkit-text-fill-color: var(--text) !important;
    -webkit-box-shadow: 0 0 0 1000px var(--surface-2) inset !important;
    caret-color: var(--accent);
    transition: background-color 9999s ease-in-out 0s;
}

/* ---- 记住密码：蓝色勾选 ---- */
[data-testid="stForm"] [data-testid="stCheckbox"] label p {
    font-size: 0.8rem;
    color: var(--text-faint);
}
[data-testid="stForm"] [data-testid="stCheckbox"] [role="checkbox"] {
    width: 17px;
    height: 17px;
    border-radius: 5px;
    background: var(--surface-2);
    border: 1px solid var(--border-strong);
    transition: background 0.2s var(--ease), border-color 0.2s var(--ease), box-shadow 0.2s var(--ease);
}
[data-testid="stForm"] [data-testid="stCheckbox"] [role="checkbox"][aria-checked="true"] {
    background: var(--accent);
    border-color: var(--accent);
    box-shadow: 0 0 10px rgba(76, 141, 255, 0.4);
}

/* ---- 登录按钮：品牌蓝实底 ---- */
[data-testid="stForm"] [data-testid="stFormSubmitButton"] {
    margin-top: 0.6rem;
}
[data-testid="stForm"] [data-testid="stFormSubmitButton"] button {
    background: linear-gradient(180deg, #5B96FF 0%, #3E7DF2 100%);
    border: 1px solid rgba(76, 141, 255, 0.6);
    border-radius: 8px;
    color: #FFFFFF;
    font-family: var(--sans);
    font-weight: 600;
    letter-spacing: 0.08em;
    font-size: 0.9rem;
    padding: 0.62rem 0;
    box-shadow: 0 8px 24px rgba(76, 141, 255, 0.32), inset 0 1px 0 rgba(255, 255, 255, 0.18);
    transition: filter 0.2s var(--ease), box-shadow 0.25s var(--ease), transform 0.12s var(--ease);
}
[data-testid="stForm"] [data-testid="stFormSubmitButton"] button:hover {
    filter: brightness(1.08);
    box-shadow: 0 12px 32px rgba(76, 141, 255, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.25);
    transform: translateY(-1px);
}
[data-testid="stForm"] [data-testid="stFormSubmitButton"] button:active {transform: scale(0.98);}
[data-testid="stForm"] [data-testid="stFormSubmitButton"] button:focus-visible {
    outline: none;
    box-shadow: 0 0 0 3px rgba(76, 141, 255, 0.4);
}

/* ---- 错误提示 ---- */
[data-testid="stForm"] [data-testid="stAlert"] {
    background: var(--red-weak);
    border: 1px solid rgba(248, 81, 73, 0.32);
    border-radius: 8px;
    color: #FF9188;
    font-size: 0.84rem;
    padding: 0.5rem 0.85rem;
}
[data-testid="stForm"] [data-testid="stAlert"] [data-testid="stAlertContent"] p {color: #FF9188;}

/* ---- 底部版本 ---- */
.login-version {
    text-align: center;
    font-family: var(--mono);
    font-size: 0.62rem;
    color: var(--text-faint);
    letter-spacing: 0.08em;
    margin-top: 1rem;
}

@keyframes fade-in {
    from {opacity: 0; transform: translateY(10px);}
    to {opacity: 1; transform: translateY(0);}
}

/* ---- 窄屏：品牌面板收窄 ---- */
@media (max-width: 760px) {
    .lb-title {font-size: 1.45rem;}
    .lb-feats {display: none;}
}

/* ---- 无障碍：尊重减少动效偏好 ---- */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}
</style>
"""


def _load_gsap() -> str:
    """读取 GSAP 源码用于内联注入。

    Streamlit 静态文件服务会把 .js 以 text/plain 返回，浏览器会因严格 MIME
    检查拒绝执行外部 <script src="app/static/...">，因此这里把 GSAP 内联
    进 st.html 的 <script> 标签中，保证动画在任何部署环境下可用。
    """
    try:
        return (Path(__file__).resolve().parent / "static" / "gsap.min.js").read_text(encoding="utf-8")
    except OSError:
        return ""


# 登录页 Git 提交流程动画（st.html 自包含：样式 + 内联 GSAP 脚本）
_GIT_ANIM_HTML = """<div class="git-anim" aria-label="Git 提交流程演示：add 与 commit 命令逐字打出，提交成功回执弹出">
<style>
.git-anim {
    position: relative; width: 100%; max-width: 440px;
    margin: -0.2rem 0 0; user-select: none; -webkit-user-select: none;
}
.git-anim * { box-sizing: border-box; }
.ga-term {
    background: #101216; border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px; box-shadow: 0 14px 36px rgba(0, 0, 0, 0.45); overflow: hidden;
}
.ga-bar {
    display: flex; align-items: center; gap: 7px; padding: 9px 13px;
    background: rgba(255, 255, 255, 0.03); border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
.ga-bdot { width: 10px; height: 10px; border-radius: 50%; }
.ga-br { background: #FF5F57; }
.ga-by { background: #FEBC2E; }
.ga-bg { background: #28C840; }
.ga-title {
    margin-left: 8px; font: 500 11px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif;
    color: #6E7686; letter-spacing: .04em;
}
.ga-body { padding: 14px 15px 16px; font: 500 12.5px/1.8 ui-monospace, "SF Mono", Menlo, monospace; }
.ga-line { display: flex; gap: 10px; color: #C9CDD6; white-space: nowrap; }
.ga-prompt { color: #3FB950; }
.ga-ch { display: inline-block; will-change: opacity, transform; }
.ga-ok {
    display: flex; gap: 8px; color: #3FB950; margin-top: 4px; white-space: nowrap;
    will-change: opacity, transform;
}
.ga-ok .ga-hash { color: #4C8DFF; }
.ga-muted { color: #6E7686; }
.ga-cursor {
    display: inline-block; margin-left: 4px; color: #3FB950;
    animation: ga-blink 1.1s steps(2, start) infinite;
}
@keyframes ga-blink { 0%, 45% { opacity: 1; } 50%, 100% { opacity: 0; } }
@media (max-width: 620px) {
    .ga-term { transform: scale(0.9); transform-origin: top left; }
}
</style>
<div class="ga-term">
  <div class="ga-bar">
    <span class="ga-bdot ga-br"></span>
    <span class="ga-bdot ga-by"></span>
    <span class="ga-bdot ga-bg"></span>
    <span class="ga-title">AI-CodeReview · git</span>
  </div>
  <div class="ga-body">
    <div class="ga-line"><span class="ga-prompt">&#10095;</span><span class="ga-cmd ga-cmd1"></span></div>
    <div class="ga-line"><span class="ga-prompt">&#10095;</span><span class="ga-cmd ga-cmd2"></span></div>
    <div class="ga-ok ga-ok1"><span>&#10003;</span><span class="ga-hash">a1b2c3d</span><span>(HEAD -&gt; main)</span></div>
    <div class="ga-ok ga-ok2"><span class="ga-muted">2 files changed, 128 insertions(+), 12 deletions(-)</span></div>
    <span class="ga-cursor">&#9644;</span>
  </div>
</div>
<script>
(function () {
  function boot() {
    var g = window.gsap;
    var root = document.querySelector('.git-anim');
    if (!g || !root) return;

    var cmd1 = root.querySelector('.ga-cmd1');
    var cmd2 = root.querySelector('.ga-cmd2');
    var ok1 = root.querySelector('.ga-ok1');
    var ok2 = root.querySelector('.ga-ok2');
    var term = root.querySelector('.ga-term');

    var T1 = 'git add .';
    var T2 = "git commit -m 'feat: 登录页动画'";

    function fill(el, text) {
      el.innerHTML = '';
      text.split('').forEach(function (ch) {
        var s = document.createElement('span');
        s.className = 'ga-ch';
        s.textContent = ch;
        el.appendChild(s);
      });
      return g.utils.toArray(el.querySelectorAll('.ga-ch'));
    }

    var ch1 = fill(cmd1, T1);
    var ch2 = fill(cmd2, T2);

    function play() {
      g.set(term, { autoAlpha: 1, y: 0, clearProps: 'all' });
      g.set(ch1, { autoAlpha: 0 });
      g.set(ch2, { autoAlpha: 0 });
      g.set([ok1, ok2], { autoAlpha: 0, y: 6 });

      var tl = g.timeline({ defaults: { ease: 'power2.out' } });
      tl.fromTo(term, { y: 16, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: 0.5 })
        .to(ch1, { autoAlpha: 1, duration: 0.08, stagger: 0.055 }, '+=0.15')
        .to(ch2, { autoAlpha: 1, duration: 0.08, stagger: 0.05 }, '+=0.4')
        .to(ok1, { autoAlpha: 1, y: 0, duration: 0.4, ease: 'back.out(1.7)' }, '+=0.35')
        .to(ok2, { autoAlpha: 1, y: 0, duration: 0.3 }, '-=0.15')
        .to(term, { autoAlpha: 0, y: -8, duration: 0.45, ease: 'power2.in' }, '+=2.6')
        .add(play);
      return tl;
    }
    play();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
</script>
</div>
"""

GIT_ANIM_HTML = _GIT_ANIM_HTML.replace(
    "<script>\n(function () {",
    "<script>" + _load_gsap() + "</script>\n<script>\n(function () {",
    1,
)


# 登录页左侧品牌面板
_LOGIN_BRAND_HTML = """
<div class="login-brand">
  <div class="lb-logo">
    <span class="lb-logo-mark" aria-hidden="true">
      <svg viewBox="0 0 24 24"><path d="M8 7l-5 5 5 5"/><path d="M16 7l5 5-5 5"/></svg>
    </span>
    <div>
      <div class="lb-logo-name">AI Code Review</div>
      <div class="lb-logo-sub">GitLab · Review Dashboard</div>
    </div>
  </div>
  <h1 class="lb-title">让每一次 <em>提交</em><br>都被认真审查</h1>
  <p class="lb-desc">基于大模型的自动化代码审查，结果直达 Merge Request 与 Commit，质量数据一目了然。</p>
  <ul class="lb-feats">
    <li>
      <span class="feat-ico" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M20 6L9 17l-5-5"/></svg></span>
      <span>多模型支持：DeepSeek / OpenAI / Anthropic / 通义千问</span>
    </li>
    <li>
      <span class="feat-ico" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M20 6L9 17l-5-5"/></svg></span>
      <span>审查结果一键推送：钉钉 / 企业微信 / 飞书</span>
    </li>
    <li>
      <span class="feat-ico" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M20 6L9 17l-5-5"/></svg></span>
      <span>自动化日报：基于 Commit 记录整理每日开发进展</span>
    </li>
  </ul>
</div>
"""


# 登录界面
def login_page():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    st.markdown(LOGIN_CSS, unsafe_allow_html=True)

    # 获取保存的用户名和密码
    saved_username, saved_password = get_saved_credentials()

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
                if authenticate(username, password, remember_password):
                    st.rerun()  # 重新运行应用以显示主要内容
                else:
                    st.error("用户名或密码错误")

        st.markdown('<div class="login-version">AI-Codereview-Gitlab · v1</div>', unsafe_allow_html=True)


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
        ),
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
        chart = _dev_chart(
            alt.Chart(pc).mark_bar(color="#4C8DFF", cornerRadiusEnd=4).encode(
                x=alt.X(
                    "count:Q",
                    scale=alt.Scale(domain=[0, pmax * 1.1]),
                    title=None,
                    axis=alt.Axis(tickMinStep=1, format="d", labelExpr="datum.value % 1 === 0 ? datum.label : ''"),
                ),
                y=alt.Y("project_name:N", sort="-x", title=None),
            ),
            height=300,
        )
        st.altair_chart(chart, use_container_width=True)
    with c2:
        st.markdown('<div class="chart-title">项目平均得分</div>', unsafe_allow_html=True)
        chart = _dev_chart(
            alt.Chart(ps).mark_bar(color="#3FB950", cornerRadiusEnd=4).encode(
                x=alt.X("score:Q", scale=alt.Scale(domain=[0, 100]), title=None),
                y=alt.Y("project_name:N", sort="-x", title=None),
            ),
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
        chart = _dev_chart(
            alt.Chart(ac).mark_bar(color="#D29922", cornerRadiusEnd=4).encode(
                x=alt.X(
                    "count:Q",
                    scale=alt.Scale(domain=[0, amax * 1.1]),
                    title=None,
                    axis=alt.Axis(tickMinStep=1, format="d", labelExpr="datum.value % 1 === 0 ? datum.label : ''"),
                ),
                y=alt.Y("author:N", sort="-x", title=None),
            ),
            height=300,
        )
        st.altair_chart(chart, use_container_width=True)
    with c4:
        st.markdown('<div class="chart-title">开发者平均得分</div>', unsafe_allow_html=True)
        chart = _dev_chart(
            alt.Chart(as_).mark_bar(color="#A371F7", cornerRadiusEnd=4).encode(
                x=alt.X("score:Q", scale=alt.Scale(domain=[0, 100]), title=None),
                y=alt.Y("author:N", sort="-x", title=None),
            ),
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


# SF Symbols 风格线条图标（KPI 卡片用）
_KPI_ICONS = {
    "doc": '<svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/></svg>',
    "star": '<svg viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01z"/></svg>',
    "folder": '<svg viewBox="0 0 24 24"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>',
    "code": '<svg viewBox="0 0 24 24"><path d="M16 18l6-6-6-6"/><path d="M8 6l-6 6 6 6"/></svg>',
    "circle": '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 6v12"/><path d="M9 9.5h3.5a2 2 0 0 1 0 4H10a2 2 0 0 0 0 4h4.5"/></svg>',
    "arrow-in": '<svg viewBox="0 0 24 24"><path d="M21 12H9"/><path d="M15 6l-6 6 6 6"/></svg>',
    "arrow-out": '<svg viewBox="0 0 24 24"><path d="M3 12h12"/><path d="M9 6l6 6-6 6"/></svg>',
    "avg": '<svg viewBox="0 0 24 24"><path d="M4 20h16"/><path d="M7 16v-7"/><path d="M12 16v-10"/><path d="M17 16v-4"/></svg>',
    "pulse": '<svg viewBox="0 0 24 24"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>',
}

_KPI_CARD = (
    '<div class="kpi {cls}"><div class="kpi-top">'
    '<span class="kpi-icon">{icon}</span>'
    '<span class="kpi-label">{label}</span></div>'
    '<div class="kpi-value">{value}</div>'
    '{sub_html}</div>'
)


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
        chart = _dev_chart(
            alt.Chart(pt).mark_bar(color="#4C8DFF", cornerRadiusEnd=4).encode(
                x=alt.X(
                    "tokens:Q",
                    scale=alt.Scale(domain=[0, pmax * 1.1]),
                    title=None,
                    axis=alt.Axis(tickMinStep=1, format="d", labelExpr="datum.value % 1 === 0 ? datum.label : ''"),
                ),
                y=alt.Y("project_name:N", sort=alt.EncodingSortField(field="tokens", op="sum", order="descending"), title=None),
            ),
            height=300,
        )
        st.altair_chart(chart, use_container_width=True)
    with c2:
        st.markdown('<div class="chart-title">Token by Author</div>', unsafe_allow_html=True)
        amax = max(at["tokens"].max() if not at.empty else 0, 1)
        chart = _dev_chart(
            alt.Chart(at).mark_bar(color="#A371F7", cornerRadiusEnd=4).encode(
                x=alt.X(
                    "tokens:Q",
                    scale=alt.Scale(domain=[0, amax * 1.1]),
                    title=None,
                    axis=alt.Axis(tickMinStep=1, format="d", labelExpr="datum.value % 1 === 0 ? datum.label : ''"),
                ),
                y=alt.Y("author:N", sort=alt.EncodingSortField(field="tokens", op="sum", order="descending"), title=None),
            ),
            height=300,
        )
        st.altair_chart(chart, use_container_width=True)

    # Token 时间趋势（按天聚合，渐变面积图）
    daily = df.copy()
    daily["day"] = pd.to_datetime(daily["updated_at"]).dt.date
    daily_tokens = daily.groupby("day")["total_tokens"].sum().reset_index(name="tokens")
    st.markdown('<div class="chart-title">Token Trend</div>', unsafe_allow_html=True)
    if len(daily_tokens) > 0:
        chart = _dev_chart(
            alt.Chart(daily_tokens)
            .mark_area(
                color="#4C8DFF",
                opacity=0.12,
                line={"color": "#4C8DFF", "strokeWidth": 2.5},
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


# ============ 页面配置常量 ============
# 审查页明细列（不含 token 列；token 相关已移入 Token 统计页）
MR_COLUMNS = ["project_name", "author", "source_branch", "target_branch", "updated_at", "commit_messages", "delta",
              "score", "url", "additions", "deletions"]

MR_COLUMN_CONFIG = {
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

PUSH_COLUMNS = ["project_name", "author", "branch", "updated_at", "commit_messages", "delta", "score",
                "additions", "deletions"]

PUSH_COLUMN_CONFIG = {
    "project_name": "项目名称",
    "author": "开发者",
    "branch": "分支",
    "updated_at": "更新时间",
    "commit_messages": "提交信息",
    "delta": "代码变更",
    "score": st.column_config.ProgressColumn(
        "得分", min_value=0, max_value=100, format="%d",
    ),
    "additions": None,
    "deletions": None,
}

# Token 统计页所需的审查记录列
TOKEN_COLUMNS = ["project_name", "author", "updated_at", "prompt_tokens", "completion_tokens", "total_tokens"]


def push_review_enabled():
    return os.environ.get('PUSH_REVIEW_ENABLED', '0') == '1'


# ============ 顶部标题栏（各页面共用） ============
def render_header(title, subtitle, logout_key="logout_button"):
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
                logout()
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ============ 共享筛选（侧边栏，作用于仪表盘全部选项卡） ============
def _load_combined_base(start_datetime, end_datetime):
    """合并 MR（+ Push）基础记录，用于构建共享筛选的作者/项目选项。"""
    frames = []
    funcs = [ReviewService().get_mr_review_logs]
    if push_review_enabled():
        funcs.append(ReviewService().get_push_review_logs)
    for func in funcs:
        df = get_data(func, updated_at_gte=start_datetime, updated_at_lte=end_datetime,
                      columns=["author", "project_name"])
        if not df.empty:
            frames.append(df)
    if not frames:
        return pd.DataFrame(columns=["author", "project_name"])
    return pd.concat(frames, ignore_index=True)


def render_shared_filter():
    """侧边栏共享筛选：时间预设 + 日期 + 开发者 + 项目。

    选项列表来自 MR + Push 合并记录，保证各选项卡都能选中自己源的数据。
    返回 dict，供各内容块渲染函数使用。
    """
    start_date, end_date = render_date_filter("dash")

    start_datetime = (int(datetime.datetime.combine(start_date, datetime.time.min).timestamp())
                      if start_date else None)
    end_datetime = (int(datetime.datetime.combine(end_date, datetime.time.max).timestamp())
                    if end_date else None)

    base = _load_combined_base(start_datetime, end_datetime)
    unique_authors = (sorted(base["author"].dropna().unique().tolist()) if not base.empty else [])
    unique_projects = (sorted(base["project_name"].dropna().unique().tolist()) if not base.empty else [])

    authors = st.multiselect("开发者", unique_authors, default=[], key="dash_authors")
    project_names = st.multiselect("项目名称", unique_projects, default=[], key="dash_projects")

    return {
        "authors": authors,
        "project_names": project_names,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
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
    with st.container(border=True):
        st.markdown('<div class="chart-title">统计图表</div>', unsafe_allow_html=True)
        render_charts(df)

    # 数据明细（token 相关列已移入 Token 统计选项卡）
    with st.container(border=True):
        st.markdown('<div class="chart-title">数据明细</div>', unsafe_allow_html=True)
        st.data_editor(
            df,
            use_container_width=True,
            column_config=column_config,
            hide_index=True,
        )


# ============ Token 统计块 ============
def load_review_tokens(authors=None, project_names=None, updated_at_gte=None, updated_at_lte=None):
    """合并 MR + Push 的审查 token 数据（纯合并，不做来源区分）。"""
    funcs = [ReviewService().get_mr_review_logs]
    if push_review_enabled():
        funcs.append(ReviewService().get_push_review_logs)

    frames = []
    for func in funcs:
        df = get_data(func, authors=authors, project_names=project_names,
                      updated_at_gte=updated_at_gte, updated_at_lte=updated_at_lte,
                      columns=TOKEN_COLUMNS)
        if not df.empty:
            frames.append(df)

    if not frames:
        return pd.DataFrame(columns=TOKEN_COLUMNS)
    return pd.concat(frames, ignore_index=True)


def render_token_block(filters):
    rdf = load_review_tokens(authors=filters["authors"], project_names=filters["project_names"],
                             updated_at_gte=filters["start_datetime"],
                             updated_at_lte=filters["end_datetime"])

    # 审查 Token（MR + Push 合并展示）
    with st.container(border=True):
        source_label = "MR + Push" if push_review_enabled() else "MR"
        st.markdown(f'<div class="chart-title">审查 Token · {source_label}</div>', unsafe_allow_html=True)
        render_token_stats(rdf)

    # 审查 Token 明细（含 token 列）
    with st.container(border=True):
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
    st.divider()
    with st.container(border=True):
        st.markdown('<div class="chart-title">日报 Token 消耗</div>', unsafe_allow_html=True)
        render_daily_report_stats(updated_at_gte=filters["start_datetime"],
                                  updated_at_lte=filters["end_datetime"])


# ============ 仪表盘（单页，选项卡切换 MR / Push / Token） ============
def render_dashboard_page():
    render_header("审查仪表盘", "AI REVIEW · DASHBOARD", logout_key="logout_dashboard")

    with st.sidebar:
        st.markdown('<div class="side-label">Filter</div>', unsafe_allow_html=True)
        filters = render_shared_filter()
        st.markdown('<div class="side-version">AI-Codereview-Gitlab · v1</div>', unsafe_allow_html=True)

    tab_labels = ["MR 审查"]
    if push_review_enabled():
        tab_labels.append("Push 审查")
    tab_labels.append("Token 统计")
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        render_review_block(ReviewService().get_mr_review_logs, MR_COLUMNS, MR_COLUMN_CONFIG, filters)

    if push_review_enabled():
        with tabs[1]:
            render_review_block(ReviewService().get_push_review_logs, PUSH_COLUMNS, PUSH_COLUMN_CONFIG, filters)

    with tabs[-1]:
        render_token_block(filters)


# ============ 主入口 ============
# 单一仪表盘页（MR / Push / Token 三块用选项卡切换），侧边栏只放共享筛选。
if not check_login_status():
    login_page()
    st.stop()

render_dashboard_page()
