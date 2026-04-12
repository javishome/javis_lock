"""Script tests for service handlers.

Run: python tests/test_services.py
"""

import asyncio
from datetime import datetime
from types import SimpleNamespace

from _component_test_stubs import (
    PKG,
    clear_modules,
    install_package_root,
    load_module,
    stub_component_modules_for_services,
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


async def main():
    print("\n" + "=" * 64)
    print("TEST SERVICES LOGIC")
    print("=" * 64)

    clear_modules(PKG)
    install_package_root()
    stub_voluptuous()
    stub_homeassistant_minimal()
    stub_component_modules_for_services()

    services = load_module("services", "services.py")

    class FakeApi:
        def __init__(self):
            self.add_calls = []
            self.change_calls = []

        async def add_passcode(self, lock_id, config):
            self.add_calls.append(
                {
                    "lock_id": lock_id,
                    "name": config.passcode_name,
                    "start": config.start_minute,
                    "end": config.end_minute,
                    "type": config.type,
                }
            )
            return {"ok": True, "lock_id": lock_id}

        async def change_passcode(self, lock_id, pwd_id, new_pwd, pwd_name):
            self.change_calls.append(
                {
                    "lock_id": lock_id,
                    "pwd_id": pwd_id,
                    "new_pwd": new_pwd,
                    "pwd_name": pwd_name,
                }
            )
            return {"ok": True}

    fake_coordinator = SimpleNamespace(lock_id=123456, api=FakeApi())
    services.coordinator_for = lambda hass, entity_id: fake_coordinator

    svc = services.Services(hass=SimpleNamespace())

    result_missing_period_time = await svc.handle_create_passcode(
        SimpleNamespace(
            data={
                "entity_id": ["lock.ttlock_abc"],
                "passcode_name": "period-code",
                "type": "3",
            }
        )
    )
    check(
        "type=3 requires start/end",
        result_missing_period_time,
        {"error": "Need start time and end time with period passcode."},
    )

    result_invalid_range = await svc.handle_create_passcode(
        SimpleNamespace(
            data={
                "entity_id": ["lock.ttlock_abc"],
                "passcode_name": "period-code",
                "type": "3",
                "start_time": datetime(2026, 1, 1, 10, 0, 0),
                "end_time": datetime(2026, 1, 1, 9, 0, 0),
            }
        )
    )
    check(
        "reject start >= end",
        result_invalid_range,
        {"error": "Start time must be less than end time."},
    )

    result_ok = await svc.handle_create_passcode(
        SimpleNamespace(
            data={
                "entity_id": ["lock.ttlock_abc"],
                "passcode_name": "one-time",
                "type": "1",
            }
        )
    )
    check("type<=2 returns api response", result_ok, {"ok": True, "lock_id": 123456})
    check_true("add_passcode called once", len(fake_coordinator.api.add_calls) == 1)
    if fake_coordinator.api.add_calls:
        first_call = fake_coordinator.api.add_calls[0]
        check("startDate type<=2", first_call["start"], 0)
        check("endDate type<=2", first_call["end"], 0)

    result_change_invalid = await svc.handle_change_passcode(
        SimpleNamespace(
            data={
                "entity_id": ["lock.ttlock_abc"],
                "keyboardPwdId": "99",
            }
        )
    )
    check(
        "change_passcode requires new value",
        result_change_invalid,
        {"error": "New passcode or passcode name is required."},
    )

    result_change_ok = await svc.handle_change_passcode(
        SimpleNamespace(
            data={
                "entity_id": ["lock.ttlock_abc"],
                "keyboardPwdId": "99",
                "newKeyboardPwd": "246810",
            }
        )
    )
    check("change_passcode successful", result_change_ok, {"ok": True})
    check_true(
        "change_passcode called once", len(fake_coordinator.api.change_calls) == 1
    )

    print("\n" + "=" * 64)
    if tests_failed == 0:
        print(f"ALL {tests_run} TESTS PASSED")
    else:
        print(f"FAILED: {tests_failed}/{tests_run}")
    print("=" * 64 + "\n")

    raise SystemExit(0 if tests_failed == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
