# -*- coding: utf-8 -*-
"""UI 冒烟测试：验证 st.navigation 多页拆分结构（MR/Push/Token）可正常渲染。

- test_default_page_is_mr_review：以真实入口（from_file）运行 ui.py，
  验证登录 → st.navigation → 默认页（MR 审查）的完整链路。
- 其余用例直接调用页面渲染函数，验证各页面独立渲染不抛异常。

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


def test_default_page_is_mr_review(ui_import_ctx, push_enabled):
    """真实入口：默认页为 MR 审查，且审查页不再展示 token 消耗区块。"""
    at = AppTest.from_file(UI_PATH, default_timeout=30)
    at.run(timeout=30)
    assert not at.exception, list(at.exception)

    values = _markdown_values(at)
    assert any("MR 审查" in v for v in values), values
    assert any("AI REVIEW" in v for v in values), values
    # 审查页不应再出现 token 消耗区块（已移入 Token 统计页）
    assert not any("Token 消耗统计" in v for v in values), values


def _token_page_app():
    import ui

    ui.render_token_page()


def _push_page_app():
    import ui

    ui.render_push_review_page()


def test_token_page_renders(ui_import_ctx, push_enabled):
    """Token 统计页：含审查 Token（合并 MR+Push）与日报 Token 区块。"""
    at = AppTest.from_function(_token_page_app, default_timeout=30)
    at.run(timeout=30)
    assert not at.exception, list(at.exception)

    values = _markdown_values(at)
    assert any("Token 统计" in v for v in values), values
    assert any("审查 Token" in v for v in values), values
    assert any("日报 Token 消耗" in v for v in values), values


def test_push_page_renders(ui_import_ctx, push_enabled):
    """Push 审查页可正常渲染（PUSH_REVIEW_ENABLED=1）。"""
    at = AppTest.from_function(_push_page_app, default_timeout=30)
    at.run(timeout=30)
    assert not at.exception, list(at.exception)

    values = _markdown_values(at)
    assert any("Push 审查" in v for v in values), values
