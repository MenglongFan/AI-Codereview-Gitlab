"""侧边栏结构测试。

单页仪表盘后，导航树已移除，侧边栏只保留共享筛选。回归测试断言：
- 侧边栏不再包含 .nav-tree / .nav-item / .nav-grp 元素
- 仪表盘选项卡随 PUSH_REVIEW_ENABLED 切换数量
- 默认入口仍渲染「审查仪表盘」
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

load_dotenv("conf/.env")
DEFAULT_SECRET_KEY = "fac8cf149bdd616c07c1a675c4571ccacc40d7f7fe16914cfe0f9f9d966bb773"
SECRET_KEY = os.environ.get("DASHBOARD_SECRET_KEY", DEFAULT_SECRET_KEY)
DASHBOARD_USER = os.environ.get("DASHBOARD_USER", "admin")


def _auth_token(username=DASHBOARD_USER):
    ts = str(int(time.time()))
    message = f"{username}:{ts}"
    signature = hmac.new(SECRET_KEY.encode(), message.encode(), hashlib.sha256).digest()
    return base64.b64encode(
        f"{message}:{base64.b64encode(signature).decode()}".encode()
    ).decode()


@pytest.fixture
def ui_import_ctx():
    """已登录 CookieManager stub。"""
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


def _all_html(at: AppTest) -> str:
    """拼接所有 markdown 输出，便于断言 HTML 结构。"""
    return "\n".join(m.value for m in at.markdown)


def test_sidebar_has_no_nav_tree(ui_import_ctx, push_enabled):
    """侧边栏不再包含自定义导航树（.nav-tree / .nav-item / .nav-grp）。"""
    at = AppTest.from_file(UI_PATH, default_timeout=30)
    at.run()
    assert not at.exception, list(at.exception)

    html = _all_html(at)
    assert "nav-tree" not in html
    assert "nav-item" not in html
    assert "nav-grp" not in html
    assert "?page=" not in html


def test_dashboard_tabs_rendered(ui_import_ctx, push_enabled):
    """仪表盘以选项卡形式包含 MR / Push / Token 三块内容。"""
    at = AppTest.from_file(UI_PATH, default_timeout=30)
    at.run()
    assert not at.exception, list(at.exception)

    tab_labels = [t.label for t in at.tabs]
    assert tab_labels == ["MR 审查", "Push 审查", "Token 统计"], tab_labels


def test_dashboard_tabs_without_push(ui_import_ctx):
    """PUSH_REVIEW_ENABLED 关闭时只有 MR / Token 两个选项卡。"""
    at = AppTest.from_file(UI_PATH, default_timeout=30)
    at.run()
    assert not at.exception, list(at.exception)

    tab_labels = [t.label for t in at.tabs]
    assert tab_labels == ["MR 审查", "Token 统计"], tab_labels


def test_default_route_loads_dashboard(ui_import_ctx, push_enabled):
    """默认入口直接渲染仪表盘，无 ?page 路由分发。"""
    at = AppTest.from_file(UI_PATH, default_timeout=30)
    at.run()
    assert not at.exception, list(at.exception)

    values = [m.value for m in at.markdown]
    assert any("审查仪表盘" in v for v in values), values
    assert any("AI REVIEW" in v for v in values), values


def test_legacy_page_query_param_ignored(ui_import_ctx, push_enabled):
    """旧的 ?page= 参数被静默忽略，仍然渲染仪表盘。"""
    at = AppTest.from_file(UI_PATH, default_timeout=30)
    at.query_params["page"] = "mr-review"
    at.run()
    assert not at.exception, list(at.exception)

    values = [m.value for m in at.markdown]
    assert any("审查仪表盘" in v for v in values), values


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-x", "-q", "-s"])
