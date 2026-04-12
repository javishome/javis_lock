"""Script tests for coordinator runtime behaviors.

Run: python tests/test_coordinator_runtime.py
"""

import asyncio
from datetime import datetime, timedelta
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
    print("TEST COORDINATOR RUNTIME")
    print("=" * 64)

    clear_modules(PKG)
    install_package_root()
    stub_homeassistant_minimal()
    stub_component_modules_for_coordinator()
    coord_mod = load_module("coordinator", "coordinator.py")

    class FakeApi:
        def __init__(self):
            self.lock_calls = 0
            self.unlock_calls = 0

        async def lock(self, lock_id):
            self.lock_calls += 1
            return True

        async def unlock(self, lock_id):
            self.unlock_calls += 1
            return True

    hass = SimpleNamespace(create_task=lambda coro: asyncio.create_task(coro))
    coordinator = coord_mod.LockUpdateCoordinator(hass, FakeApi(), 101)
    coordinator.data = coord_mod.LockState(name="Door", mac="AA:BB", locked=False)

    # lock_action should always clear pending even when body raises
    try:
        with coord_mod.lock_action(coordinator):
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    check(
        "lock_action resets pending after exception",
        coordinator.data.action_pending,
        False,
    )

    await coordinator.lock()
    check("lock() sets locked True", coordinator.data.locked, True)
    await coordinator.unlock()
    check("unlock() sets locked False", coordinator.data.locked, False)

    # _process_webhook_data should ignore unrelated event id
    before_locked = coordinator.data.locked
    unrelated_event = SimpleNamespace(id=999, success=True)
    coordinator._process_webhook_data(unrelated_event)
    check(
        "unrelated webhook does not change state",
        coordinator.data.locked,
        before_locked,
    )

    # _process_webhook_data should ignore failed event
    failed_event = SimpleNamespace(id=101, success=False)
    coordinator._process_webhook_data(failed_event)
    check(
        "failed webhook does not change state", coordinator.data.locked, before_locked
    )

    # _process_webhook_data should call _handle_auto_lock when unlocked event received
    called = {"count": 0}

    original_handle_auto_lock = coordinator._handle_auto_lock

    def fake_handle_auto_lock(lock_ts, server_ts):
        called["count"] += 1

    coordinator._handle_auto_lock = fake_handle_auto_lock
    coordinator.data.auto_lock_seconds = 10
    coordinator.data.passage_mode_config = None

    unlock_event = SimpleNamespace(
        id=101,
        success=True,
        battery_level=77,
        state=SimpleNamespace(locked=coord_mod.State.unlocked),
        lock_ts=datetime.now(),
        server_ts=datetime.now(),
        user="user1",
        event=SimpleNamespace(description="unlock by app"),
    )
    coordinator._process_webhook_data(unlock_event)
    check_true("unlock event triggers auto-lock handler", called["count"] == 1)
    check("unlock event sets battery level", coordinator.data.battery_level, 77)
    check("unlock event sets last user", coordinator.data.last_user is not None, True)
    coordinator._handle_auto_lock = original_handle_auto_lock

    # _handle_auto_lock with disabled auto-lock does nothing
    coordinator.data.auto_lock_seconds = -1
    coordinator.data.locked = False
    coordinator._handle_auto_lock(datetime.now(), datetime.now())
    await asyncio.sleep(0.01)
    check("disabled auto-lock keeps unlocked", coordinator.data.locked, False)

    # _handle_auto_lock should lock after delay path
    coordinator.data.auto_lock_seconds = 1
    coordinator.data.locked = False
    now = datetime.now()
    coordinator._handle_auto_lock(now, now + timedelta(seconds=2))
    await asyncio.sleep(0.05)
    check("auto-lock eventually sets locked True", coordinator.data.locked, True)

    print("\n" + "=" * 64)
    if tests_failed == 0:
        print(f"ALL {tests_run} TESTS PASSED")
    else:
        print(f"FAILED: {tests_failed}/{tests_run}")
    print("=" * 64 + "\n")
    raise SystemExit(0 if tests_failed == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
