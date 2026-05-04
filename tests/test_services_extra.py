"""Script tests for remaining service handlers.

Run: python tests/test_services_extra.py
"""

import asyncio
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
    print("TEST SERVICES EXTRA")
    print("=" * 64)

    clear_modules(PKG)
    install_package_root()
    stub_voluptuous()
    stub_homeassistant_minimal()
    stub_component_modules_for_services()
    services = load_module("services", "services.py")

    class FakeCode:
        def __init__(self, code_id, name, expired):
            self.id = code_id
            self.name = name
            self.expired = expired

    class FakeApi:
        def __init__(self):
            self.deleted = []
            self.refresh_called = 0

        async def list_passcodes(self, lock_id, is_parse=True):
            if is_parse:
                return [
                    FakeCode(1, "expired-code", True),
                    FakeCode(2, "active-code", False),
                ]
            return {"list": [{"id": 1}]}

        async def delete_passcode(self, lock_id, code_id):
            self.deleted.append((lock_id, code_id))
            return {"ok": True}

        async def list_unlock_records(self, lock_id, page_no, page_size):
            return {"lock_id": lock_id, "page": page_no, "size": page_size}

    class FakeCoordinator:
        def __init__(self):
            self.lock_id = 1001
            self.api = FakeApi()
            self.refresh_count = 0

        async def async_request_refresh(self):
            self.refresh_count += 1

    coordinator = FakeCoordinator()
    services.coordinator_for = lambda hass, entity_id: coordinator

    class FakeServiceRegistry:
        def __init__(self):
            self.register_calls = []
            self.async_register_calls = []

        def register(self, *args, **kwargs):
            self.register_calls.append((args, kwargs))

        def async_register(self, *args, **kwargs):
            self.async_register_calls.append((args, kwargs))

    hass = SimpleNamespace(services=FakeServiceRegistry())
    svc = services.Services(hass=hass)

    svc.register_new()
    check_true(
        "register_new registers services", len(hass.services.register_calls) >= 6
    )
    svc.register_old()
    check_true(
        "register_old async-registers services",
        len(hass.services.async_register_calls) >= 6,
    )

    res_list = await svc.handle_list_passcodes(
        SimpleNamespace(data={"entity_id": ["lock.ttlock_abc"]})
    )
    check("list passcodes returns api payload", res_list, {"list": [{"id": 1}]})

    res_cleanup = await svc.handle_cleanup_passcodes(
        SimpleNamespace(data={"entity_id": ["lock.ttlock_abc"]})
    )
    check(
        "cleanup removes only expired names", res_cleanup, {"removed": ["expired-code"]}
    )
    check("cleanup delete calls", coordinator.api.deleted, [(1001, 1)])

    res_unlock_records = await svc.handle_list_unlock_records(
        SimpleNamespace(
            data={"entity_id": ["lock.ttlock_abc"], "page_no": "2", "page_size": "10"}
        )
    )
    check(
        "list unlock records parses paging",
        res_unlock_records,
        {"lock_id": 1001, "page": 2, "size": 10},
    )

    res_delete = await svc.handle_delete_passcode(
        SimpleNamespace(data={"entity_id": ["lock.ttlock_abc"], "keyboardPwdId": "55"})
    )
    check("delete passcode response passthrough", res_delete, {"ok": True})
    check_true("delete includes id 55", (1001, 55) in coordinator.api.deleted)

    await svc.update_lock_state(
        SimpleNamespace(data={"entity_id": ["lock.ttlock_abc"]})
    )
    check("update lock requests refresh", coordinator.refresh_count, 1)

    services.coordinator_for = lambda hass, entity_id: None
    err_res = await svc.handle_list_unlock_records(
        SimpleNamespace(
            data={
                "entity_id": ["lock.ttlock_missing"],
                "page_no": "1",
                "page_size": "1",
            }
        )
    )
    check(
        "missing coordinator returns error",
        err_res,
        {"error": "No coordinator found for the given entity."},
    )

    # _get_coordinator takes first entity_id from list
    picked = {"entity": None}

    def pick_coordinator(hass_obj, entity_id):
        picked["entity"] = entity_id
        return coordinator

    services.coordinator_for = pick_coordinator
    svc._get_coordinator(
        SimpleNamespace(data={"entity_id": ["lock.ttlock_first", "lock.ttlock_second"]})
    )
    check("_get_coordinator picks first entity", picked["entity"], "lock.ttlock_first")

    print("\n" + "=" * 64)
    if tests_failed == 0:
        print(f"ALL {tests_run} TESTS PASSED")
    else:
        print(f"FAILED: {tests_failed}/{tests_run}")
    print("=" * 64 + "\n")
    raise SystemExit(0 if tests_failed == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
