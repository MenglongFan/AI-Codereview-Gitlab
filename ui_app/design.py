# -*- coding: utf-8 -*-
"""设计系统（原 ui.py 168-1201、1588-1606 行）：CSS 样式串、组件 HTML 模板、GSAP 加载。

说明：GLOBAL_CSS / LOGIN_CSS 由一次性迁移脚本按 AST 逐字提取，请勿手工改写字符串内容；
如需调整样式，请直接修改本文件并同步 CSS 测试。
"""
from pathlib import Path


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
[data-testid="stSegmentedControl"] {width: 100%;}
[data-testid="stSegmentedControl"] > div {width: 100%;}
[data-testid="stDateInput"] {width: 100%;}
[data-testid="stDateInput"] [data-baseweb="input"] {width: 100%;}
[data-testid="stMultiselect"] {width: 100%;}
[data-testid="stMultiselect"] [data-baseweb="select"] {width: 100%;}

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
    border-bottom: 1px solid rgba(255, 255, 255, 0.02) !important;
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
[data-testid="stDateInput"] [data-baseweb="input"]:hover,
[data-testid="stMultiselect"] [data-baseweb="select"] > div:hover,
[data-testid="stTextInput"] input:hover {
    background: var(--surface-3);
    border-color: rgba(76, 141, 255, 0.45);
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
        return (Path(__file__).resolve().parent.parent / "static" / "gsap.min.js").read_text(encoding="utf-8")
    except OSError:
        return ""


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
