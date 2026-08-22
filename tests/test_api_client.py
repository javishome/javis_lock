"""Script tests for API client behavior.

Run: python tests/test_api_client.py
"""

import asyncio
import json
import sys
import types
from unittest.mock import AsyncMock
from types import SimpleNamespace

from _component_test_stubs import (
    PKG,
    clear_modules,
    install_package_root,
    load_module,
    stub_aiohttp_retry,
    stub_homeassistant_minimal,
    stub_voluptuous,
)


tests_run = 0
tests_failed = 0


def check(test_name, actual, expected):
    global tests_run, tests_failed
    tests_run += 1
    if actual == expected:
        print(f"  PASS: {test_name}")
    else:
        tests_failed += 1
        print(f"  FAIL: {test_name}")
        print(f"        Expected: {expected!r}")
        print(f"        Actual  : {actual!r}")


def check_true(test_name, condition):
    global tests_run, tests_failed
    tests_run += 1
    if condition:
        print(f"  PASS: {test_name}")
    else:
        tests_failed += 1
        print(f"  FAIL: {test_name}")


async def expect_raises(test_name, exc_type, coro_func):
    global tests_run, tests_failed
    tests_run += 1
    try:
        await coro_func()
        tests_failed += 1
        print(f"  FAIL: {test_name}")
        print(f"        Expected exception: {exc_type.__name__}")
    except exc_type:
        print(f"  PASS: {test_name}")


class FakeResp:
    def __init__(self, status, payload=None, text_body=""):
        self.status = status
        self._payload = payload if payload is not None else {}
        self._text = text_body

    async def json(self):
        return self._payload

    async def text(self):
        if self._text:
            return self._text
        return json.dumps(self._payload)

    def raise_for_status(self):
        if self.status >= 400:
            raise RuntimeError(f"HTTP {self.status}")


class _AsyncCM:
    def __init__(self, value):
        self.value = value

    async def __aenter__(self):
        return self.value

    async def __aexit__(self, exc_type, exc, tb):
        return False


def _install_component_stubs_for_api():
    const = types.ModuleType(f"{PKG}.const")
    const.SERVER_URL = "https://example.test"
    const.HOST1 = "h1"
    const.HOST2 = "h2"
    const.HOST3 = "h3"
    const.COMPONENT_VERSION = "v1"
    sys.modules[f"{PKG}.const"] = const

    models = types.ModuleType(f"{PKG}.models")

    class Features:
        wifi = "wifi"

        @classmethod
        def from_feature_value(cls, value):
            if value:
                return {cls.wifi}
            return set()

    class Dummy:
        @classmethod
        def parse_obj(cls, obj):
            return obj

    models.Features = Features
    models.AddPasscodeConfig = Dummy
    models.Lock = Dummy
    models.LockState = Dummy
    models.PassageModeConfig = Dummy
    models.Passcode = Dummy
    sys.modules[f"{PKG}.models"] = models


async def _run_async_tests(api_mod):
    api = api_mod.TTLockApi(
        hass=SimpleNamespace(),
        websession=SimpleNamespace(),
        username="u",
        password="p",
        url="https://server",
    )

    parsed_ok = await api._parse_resp(FakeResp(200, {"errcode": 0, "x": 1}), "ok")
    check("_parse_resp returns payload on errcode 0", parsed_ok, {"errcode": 0, "x": 1})

    async def _raise_outdated():
        await api._parse_resp(FakeResp(426, {"errcode": 426}, "old"), "o")

    await expect_raises(
        "_parse_resp raises ComponentOutdatedError on 426",
        api_mod.ComponentOutdatedError,
        _raise_outdated,
    )

    async def _raise_request_failed():
        await api._parse_resp(FakeResp(200, {"errcode": 2, "errmsg": "x"}), "r")

    await expect_raises(
        "_parse_resp raises RequestFailed on errcode != 0",
        api_mod.RequestFailed,
        _raise_request_failed,
    )

    async def _raise_http_error():
        await api._parse_resp(FakeResp(500, {"errcode": 0}), "h")

    await expect_raises(
        "_parse_resp raises HTTP error for status>=400", RuntimeError, _raise_http_error
    )

    get_calls = []

    class FakeRetryClient:
        def __init__(self, websession, retry_options=None, raise_for_status=False):
            self.websession = websession

        def get(self, url, **kwargs):
            get_calls.append((url, kwargs))
            return _AsyncCM(FakeResp(200, {"errcode": 0, "ok": True}))

    api_mod.RetryClient = FakeRetryClient

    api.ensure_valid_token = types.MethodType(lambda self: _noop_async(), api)
    api.token = "token-1"
    get_result = await api.get("lock/list", lockId=7)
    check("get returns parsed response", get_result, {"errcode": 0, "ok": True})
    check_true("get called once", len(get_calls) == 1)
    if get_calls:
        _, call_kwargs = get_calls[0]
        headers = call_kwargs["headers"]
        params = call_kwargs["params"]
        check(
            "get adds component version header",
            headers.get("X-Component-Version"),
            "v1",
        )
        check("get adds access_token", params.get("access_token"), "token-1")

    class FakeWebSession:
        def __init__(self):
            self.post_calls = []

        async def post(self, url, json=None, headers=None):
            self.post_calls.append({"url": url, "json": json, "headers": headers})
            return FakeResp(200, {"errcode": 0, "posted": True})

    post_session = FakeWebSession()
    api_post = api_mod.TTLockApi(
        hass=SimpleNamespace(),
        websession=post_session,
        username="u",
        password="p",
        url="https://server",
    )
    api_post.ensure_valid_token = types.MethodType(lambda self: _noop_async(), api_post)
    api_post.token = "token-2"
    post_result = await api_post.post("lock/unlock", lockId=99)
    check("post returns parsed response", post_result, {"errcode": 0, "posted": True})
    check_true("post called once", len(post_session.post_calls) == 1)
    if post_session.post_calls:
        post_call = post_session.post_calls[0]
        check(
            "post includes version header",
            post_call["headers"].get("X-Component-Version"),
            "v1",
        )
        check(
            "post injects access token",
            post_call["json"].get("access_token"),
            "token-2",
        )

    # ensure_valid_token triggers login when token missing / expired
    api_token = api_mod.TTLockApi(
        hass=SimpleNamespace(),
        websession=SimpleNamespace(),
        username="u",
        password="p",
        url="https://server",
    )
    login_calls = {"count": 0}

    async def fake_login():
        login_calls["count"] += 1
        api_token.token = "new-token"
        api_token.start_time = 0
        api_token.expires_in = 1

    api_token.login = fake_login
    await api_token.ensure_valid_token()
    check("ensure_valid_token calls login when missing token", login_calls["count"], 1)

    api_token.token = "expired"
    api_token.start_time = 0
    api_token.expires_in = 0
    await api_token.ensure_valid_token()
    check("ensure_valid_token calls login when expired", login_calls["count"], 2)

    # get_locks keeps only gateway/wifi-capable locks
    async def fake_get(path, **kwargs):
        return {
            "list": [
                {"lockId": 1, "hasGateway": 1, "featureValue": ""},
                {"lockId": 2, "hasGateway": 0, "featureValue": "wifi"},
                {"lockId": 3, "hasGateway": 0, "featureValue": ""},
            ]
        }

    api_token.get = fake_get
    locks = await api_token.get_locks()
    check("get_locks filters non-connectable locks", locks, [1, 2])

    # post retries after transient failure
    class FlakyPostSession:
        def __init__(self):
            self.calls = 0

        async def post(self, url, json=None, headers=None):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("temporary")
            return FakeResp(200, {"errcode": 0, "ok": True})

    flaky_session = FlakyPostSession()
    flaky_api = api_mod.TTLockApi(
        hass=SimpleNamespace(),
        websession=flaky_session,
        username="u",
        password="p",
        url="https://server",
    )
    flaky_api.ensure_valid_token = types.MethodType(
        lambda self: _noop_async(), flaky_api
    )
    flaky_api.token = "retry-token"
    original_sleep = api_mod.asyncio.sleep
    api_mod.asyncio.sleep = lambda _seconds: _noop_async()
    try:
        retry_post_result = await flaky_api.post("lock/unlock", lockId=7)
    finally:
        api_mod.asyncio.sleep = original_sleep
    check("post retries then succeeds", retry_post_result, {"errcode": 0, "ok": True})
    check("post retried exactly once", flaky_session.calls, 2)



    # Direct high-level API methods tests
    api_methods = api_mod.TTLockApi(
        hass=SimpleNamespace(),
        websession=post_session,
        username="u",
        password="p",
        url="https://server",
    )
    api_methods.ensure_valid_token = types.MethodType(lambda self: _noop_async(), api_methods)

    # 1. lock() success, error, none
    api_methods.get = AsyncMock(return_value={"errcode": 0})
    res_lock_ok = await api_methods.lock(1001)
    check("api.lock() success returns True", res_lock_ok, True)

    api_methods.get = AsyncMock(return_value={"errcode": 1, "errmsg": "Fail"})
    res_lock_err = await api_methods.lock(1001)
    check("api.lock() errcode!=0 returns False", res_lock_err, False)

    api_methods.get = AsyncMock(return_value=None)
    res_lock_none = await api_methods.lock(1001)
    check("api.lock() None response returns False", res_lock_none, False)

    # 2. unlock() success, error, none
    api_methods.get = AsyncMock(return_value={"errcode": 0})
    res_unlock_ok = await api_methods.unlock(1001)
    check("api.unlock() success returns True", res_unlock_ok, True)

    api_methods.get = AsyncMock(return_value={"errcode": 1, "errmsg": "Fail"})
    res_unlock_err = await api_methods.unlock(1001)
    check("api.unlock() errcode!=0 returns False", res_unlock_err, False)

    api_methods.get = AsyncMock(return_value=None)
    res_unlock_none = await api_methods.unlock(1001)
    check("api.unlock() None response returns False", res_unlock_none, False)

    # 3. set_passage_mode success, error, none
    fake_pmc = SimpleNamespace(enabled=True, auto_unlock=True, all_day=False, start_minute=480, end_minute=1080, week_days=[1, 2, 3])
    api_methods.post = AsyncMock(return_value={"errcode": 0})
    res_pm_ok = await api_methods.set_passage_mode(1001, fake_pmc)
    check("api.set_passage_mode() success returns True", res_pm_ok, True)

    api_methods.post = AsyncMock(return_value={"errcode": 1, "errmsg": "Error"})
    res_pm_err = await api_methods.set_passage_mode(1001, fake_pmc)
    check("api.set_passage_mode() error returns False", res_pm_err, False)

    api_methods.post = AsyncMock(return_value=None)
    res_pm_none = await api_methods.set_passage_mode(1001, fake_pmc)
    check("api.set_passage_mode() None returns False", res_pm_none, False)

    # 4. add_passcode success and error
    fake_code_cfg = SimpleNamespace(passcode_name="p1", type="1", start_minute=0, end_minute=0)
    api_methods.post = AsyncMock(return_value={"errcode": 0, "keyboardPwdId": 77})
    res_add_ok = await api_methods.add_passcode(1001, fake_code_cfg)
    check("api.add_passcode() success returns dict", res_add_ok.get("keyboardPwdId"), 77)

    api_methods.post = AsyncMock(return_value={"errcode": 1, "errmsg": "Fail"})
    res_add_err = await api_methods.add_passcode(1001, fake_code_cfg)
    check("api.add_passcode() error returns False", res_add_err, False)

    # 5. list_passcodes parse & raw
    api_methods.get = AsyncMock(return_value={"list": [{"keyboardPwdId": 1}]})
    res_list_raw = await api_methods.list_passcodes(1001, is_parse=False)
    check("api.list_passcodes(raw) returns dict", len(res_list_raw.get("list")), 1)
    res_list_parse = await api_methods.list_passcodes(1001, is_parse=True)
    check("api.list_passcodes(parse) returns list", len(res_list_parse), 1)

    # 6. list_unlock_records parse & raw
    api_methods.get = AsyncMock(return_value={"list": [{"recordId": 99}]})
    res_records_raw = await api_methods.list_unlock_records(1001, 1, 10, is_parse=False)
    check("api.list_unlock_records(raw) returns dict", len(res_records_raw.get("list")), 1)
    res_records_parse = await api_methods.list_unlock_records(1001, 1, 10, is_parse=True)
    check("api.list_unlock_records(parse) returns list", len(res_records_parse), 1)

    # 7. delete_passcode & change_passcode
    api_methods.post = AsyncMock(return_value={"errcode": 0})
    res_del_pwd = await api_methods.delete_passcode(1001, 55)
    check("api.delete_passcode() calls post", res_del_pwd, {"errcode": 0})

    res_chg_pwd = await api_methods.change_passcode(1001, 55, "123456", "NewName")
    check("api.change_passcode() calls post", res_chg_pwd, {"errcode": 0})


async def _noop_async():
    return None


def main():
    print("\n" + "=" * 64)
    print("TEST API CLIENT")
    print("=" * 64)

    clear_modules(PKG)
    install_package_root()
    stub_homeassistant_minimal()
    stub_voluptuous()
    stub_aiohttp_retry()
    _install_component_stubs_for_api()

    api_mod = load_module("api", "api.py")
    asyncio.run(_run_async_tests(api_mod))

    print("\n" + "=" * 64)
    if tests_failed == 0:
        print(f"ALL {tests_run} TESTS PASSED")
    else:
        print(f"FAILED: {tests_failed}/{tests_run}")
    print("=" * 64 + "\n")
    raise SystemExit(0 if tests_failed == 0 else 1)


if __name__ == "__main__":
    main()
