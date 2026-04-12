"""Script tests for config flow.

Run: python tests/test_config_flow.py
"""

import asyncio

from _component_test_stubs import (
    PKG,
    clear_modules,
    install_package_root,
    load_module,
    stub_component_modules_for_config_flow,
    stub_homeassistant_minimal,
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


async def main():
    print("\n" + "=" * 64)
    print("TEST CONFIG FLOW")
    print("=" * 64)

    clear_modules(PKG)
    install_package_root()
    stub_homeassistant_minimal()
    stub_component_modules_for_config_flow()

    cfg = load_module("config_flow", "config_flow.py")
    flow = cfg.GithubCustomConfigFlow()

    async def login_ok(username, password, url):
        return {"is_success": True, "error": ""}

    cfg.login = login_ok
    result_ok = await flow.async_step_user(
        {"username": "user@demo", "password": "pass", "url": "cloud-a"}
    )
    check("success creates entry", result_ok["type"], "create_entry")
    check("success title", result_ok["title"], "user@demo")

    async def login_invalid(username, password, url):
        return {"is_success": False, "error": "auth"}

    cfg.login = login_invalid
    result_auth_fail = await flow.async_step_user(
        {"username": "user@demo", "password": "wrong", "url": "cloud-a"}
    )
    check("auth fail shows form", result_auth_fail["type"], "form")
    check("auth fail sets base error", result_auth_fail["errors"].get("base"), "auth")

    async def login_raises(username, password, url):
        raise ValueError("bad input")

    cfg.login = login_raises
    result_value_error = await flow.async_step_user(
        {"username": "user@demo", "password": "wrong", "url": "cloud-a"}
    )
    check("valueerror maps to auth", result_value_error["errors"].get("base"), "auth")

    print("\n" + "=" * 64)
    if tests_failed == 0:
        print(f"ALL {tests_run} TESTS PASSED")
    else:
        print(f"FAILED: {tests_failed}/{tests_run}")
    print("=" * 64 + "\n")

    raise SystemExit(0 if tests_failed == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
