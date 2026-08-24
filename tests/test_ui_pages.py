# -*- coding: utf-8 -*-
"""UI 冒烟测试：验证单页仪表盘（选项卡切换 MR/Push/Token）可正常渲染。

- test_default_page_is_dashboard：以真实入口（from_file）运行 ui.py，
  验证登录 → 仪表盘 → 选项卡结构（MR / Push / Token）的完整链路。
- test_token_section_renders：仪表盘内 Token 选项卡含审查 Token（MR + Push）
  与日报 Token 区块；「来源」过滤控件已移除，标题始终显示 MR + Push。

通过 stub CookieManager 构造已登录状态，使用 streamlit.testing.v1.AppTest
（进程内执行，patch 可见）。
"""
import base64
import hashlib
import hmac
import os
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from dotenv import load_dotenv
from streamlit.testing.v1 import AppTest

UI_PATH = str(Path(__file__).resolve().parent.parent / "ui.py")

# 与 ui.py 行为保持一致：优先读取 conf/.env 中的配置
load_dotenv("conf/.env")
DEFAULT_SECRET_KEY = "fac8cf149bdd616c07c1a675c4571ccacc40d7f7fe16914cfe0f9f9d966bb773"
SECRET_KEY = os.environ.get("DASHBOARD_SECRET_KEY", DEFAULT_SECRET_KEY)
DASHBOARD_USER = os.environ.get("DASHBOARD_USER", "admin")


def _auth_token(username=DASHBOARD_USER):
    """按 ui.generate_token 的逻辑构造一个有效 token。"""
    ts = str(int(time.time()))
    message = f"{username}:{ts}"
    signature = hmac.new(SECRET_KEY.encode(), message.encode(), hashlib.sha256).digest()
    return base64.b64encode(
        f"{message}:{base64.b64encode(signature).decode()}".encode()
    ).decode()


@pytest.fixture
def ui_import_ctx():
    """以已登录状态 stub CookieManager，保证 ui 模块级代码走导航分支。"""
    with patch("streamlit_cookies_manager.CookieManager") as mock_cls:
        inst = mock_cls.return_value
        inst.ready.return_value = True
        inst.get.return_value = _auth_token()
        yield


@pytest.fixture
def push_enabled():
    os.environ["PUSH_REVIEW_ENABLED"] = "1"
    yield
    os.environ.pop("PUSH_REVIEW_ENABLED", None)


def _markdown_values(at: AppTest):
    return [m.value for m in at.markdown]


def test_default_page_is_dashboard(ui_import_ctx, push_enabled):
    """真实入口：默认渲染仪表盘，选项卡为 MR / Push / Token。"""
    at = AppTest.from_file(UI_PATH, default_timeout=30)
    at.run(timeout=30)
    assert not at.exception, list(at.exception)

    values = _markdown_values(at)
    assert any("审查仪表盘" in v for v in values), values
    assert any("AI REVIEW" in v for v in values), values

    tab_labels = [t.label for t in at.tabs]
    assert tab_labels == ["MR 审查", "Push 审查", "Token 统计"], tab_labels


def test_token_section_renders(ui_import_ctx, push_enabled):
    """仪表盘内 Token 选项卡：含审查 Token（MR + Push 合并）与日报 Token 区块。"""
    at = AppTest.from_file(UI_PATH, default_timeout=30)
    at.run(timeout=30)
    assert not at.exception, list(at.exception)

    values = _markdown_values(at)
    assert any("审查 Token · MR + Push" in v for v in values), values
    assert any("审查 Token 明细" in v for v in values), values
    assert any("日报 Token 消耗" in v for v in values), values
