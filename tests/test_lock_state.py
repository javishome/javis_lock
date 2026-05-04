"""Script tests for lock state helper logic.

Run: python tests/test_lock_state.py
"""

from datetime import datetime
from types import SimpleNamespace

from _component_test_stubs import (
    PKG,
    clear_modules,
    install_package_root,
    load_module,
    stub_component_modules_for_coordinator,
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


def main():
    print("\n" + "=" * 64)
    print("TEST LOCK STATE HELPERS")
    print("=" * 64)

    clear_modules(PKG)
    install_package_root()
    stub_homeassistant_minimal()
    stub_component_modules_for_coordinator()

    coord = load_module("coordinator", "coordinator.py")

    lock_state = coord.LockState(name="Front Door", mac="AA:BB:CC")
    lock_state.auto_lock_seconds = 15
    lock_state.passage_mode_config = SimpleNamespace(
        enabled=True,
        week_days=[1, 2, 3, 4, 5, 6, 7],
        all_day=False,
        start_minute=9 * 60,
        end_minute=17 * 60,
    )

    active_time = datetime(2026, 4, 6, 10, 0, 0)
    inactive_time = datetime(2026, 4, 6, 20, 0, 0)

    check(
        "passage_mode_active in schedule",
        lock_state.passage_mode_active(active_time),
        True,
    )
    check(
        "passage_mode_active out of schedule",
        lock_state.passage_mode_active(inactive_time),
        False,
    )
    check(
        "auto_lock_delay disabled during passage",
        lock_state.auto_lock_delay(active_time),
        None,
    )
    check(
        "auto_lock_delay available outside passage",
        lock_state.auto_lock_delay(inactive_time),
        15,
    )

    print("\n" + "=" * 64)
    if tests_failed == 0:
        print(f"ALL {tests_run} TESTS PASSED")
    else:
        print(f"FAILED: {tests_failed}/{tests_run}")
    print("=" * 64 + "\n")

    raise SystemExit(0 if tests_failed == 0 else 1)


if __name__ == "__main__":
    main()
