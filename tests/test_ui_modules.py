# -*- coding: utf-8 -*-
"""ui_app 模块冒烟测试：鉴权 token 函数、push_review_enabled 行为、薄入口可执行。"""
import os

from ui_app.auth import generate_token, verify_token
from ui_app.config import push_review_enabled


def test_generate_and_verify_token():
    token = generate_token("admin")
    assert verify_token(token) == "admin"


def test_verify_token_rejects_tampered():
    token = generate_token("admin")
    tampered = token[:-4] + ("AAAA" if not token.endswith("AAAA") else "BBBB")
    assert verify_token(tampered) is None


def test_verify_token_rejects_garbage():
    assert verify_token("not-a-valid-token") is None
    assert verify_token("") is None


def test_push_review_enabled_default_off():
    os.environ.pop("PUSH_REVIEW_ENABLED", None)
    assert push_review_enabled() is False


def test_push_review_enabled_on():
    os.environ["PUSH_REVIEW_ENABLED"] = "1"
    try:
        assert push_review_enabled() is True
    finally:
        os.environ.pop("PUSH_REVIEW_ENABLED", None)


def test_thin_entry_importable():
    from ui_app.main import main

    assert callable(main)


def test_design_system_present():
    """设计系统核心字符串已代码化集中管理。"""
    from ui_app.design import GIT_ANIM_HTML, GLOBAL_CSS, LOGIN_CSS, _LOGIN_BRAND_HTML

    assert "<style>" in GLOBAL_CSS
    assert ".login-brand" in LOGIN_CSS
    assert "git-anim" in GIT_ANIM_HTML
    assert "login-brand" in _LOGIN_BRAND_HTML
