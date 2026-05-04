"""Script tests for models and validators.

Run: python tests/test_models.py
"""

import sys
import types
import importlib.util
from datetime import datetime, timedelta

from _component_test_stubs import PKG, clear_modules, install_package_root, load_module


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


def main():
    print("\n" + "=" * 64)
    print("TEST MODELS")
    print("=" * 64)

    clear_modules(PKG)
    install_package_root()

    if importlib.util.find_spec("pydantic") is None:
        print("  SKIP: pydantic is not installed in this environment")
        print("\n" + "=" * 64)
        print("ALL 0 TESTS PASSED (1 SKIPPED)")
        print("=" * 64 + "\n")
        raise SystemExit(0)

    ha = types.ModuleType("homeassistant")
    sys.modules["homeassistant"] = ha
    ha_util = types.ModuleType("homeassistant.util")
    sys.modules["homeassistant.util"] = ha_util
    ha_dt = types.ModuleType("homeassistant.util.dt")
    ha_dt.as_local = lambda dt_value: dt_value
    ha_dt.utc_from_timestamp = lambda ts: datetime.fromtimestamp(ts)
    ha_dt.now = lambda: datetime.now()
    sys.modules["homeassistant.util.dt"] = ha_dt

    models = load_module("models", "models.py")

    passcode_raw = {
        "keyboardPwdId": 1,
        "keyboardPwd": "123456",
        "keyboardPwdName": "temp",
        "keyboardPwdType": 3,
        "startDate": int((datetime.now() - timedelta(hours=2)).timestamp() * 1000),
        "endDate": int((datetime.now() - timedelta(hours=1)).timestamp() * 1000),
    }
    passcode = models.Passcode.parse_obj(passcode_raw)
    check("period passcode expired", passcode.expired, True)

    weekend_raw = {
        "keyboardPwdId": 2,
        "keyboardPwd": "654321",
        "keyboardPwdName": "weekend",
        "keyboardPwdType": 5,
        "startDate": int(datetime.now().timestamp() * 1000),
        "endDate": int(datetime.now().timestamp() * 1000),
    }
    weekend = models.Passcode.parse_obj(weekend_raw)
    check("cyclic passcode not forced expired", weekend.expired, False)

    ev = models.Event.validate(1)
    check("event action mapping", ev.action, models.Action.unlock)
    check("event description mapping", ev.description, "unlock by app")

    try:
        models.Event.validate(9999)
        check_true("invalid event should fail", False)
    except ValueError:
        check_true("invalid event rejected", True)

    pmc = models.PassageModeConfig.parse_obj(
        {
            "passageMode": 1,
            "startDate": None,
            "endDate": None,
            "isAllDay": 2,
            "weekDays": [1, 2],
            "autoUnlock": 2,
        }
    )
    check("passage config default start minute", pmc.start_minute, 0)
    check("passage config default end minute", pmc.end_minute, 0)

    features = models.Features.from_feature_value("3")
    check_true("features parsing returns flag", bool(features))

    print("\n" + "=" * 64)
    if tests_failed == 0:
        print(f"ALL {tests_run} TESTS PASSED")
    else:
        print(f"FAILED: {tests_failed}/{tests_run}")
    print("=" * 64 + "\n")
    raise SystemExit(0 if tests_failed == 0 else 1)


if __name__ == "__main__":
    main()
