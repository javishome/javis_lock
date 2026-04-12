"""Script tests for entity mapping and diagnostics redaction.

Run: python tests/test_entities_and_diagnostics.py
"""

import asyncio
import sys
import types
from types import SimpleNamespace

from _component_test_stubs import (
    PKG,
    clear_modules,
    install_package_root,
    load_module,
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


def _install_extra_homeassistant_stubs():
    sensor = types.ModuleType("homeassistant.components.sensor")

    class SensorDeviceClass:
        BATTERY = "battery"

    class SensorEntity:
        pass

    sensor.SensorDeviceClass = SensorDeviceClass
    sensor.SensorEntity = SensorEntity
    sys.modules["homeassistant.components.sensor"] = sensor

    binary_sensor = types.ModuleType("homeassistant.components.binary_sensor")

    class BinarySensorEntity:
        pass

    binary_sensor.BinarySensorEntity = BinarySensorEntity
    sys.modules["homeassistant.components.binary_sensor"] = binary_sensor

    lock = types.ModuleType("homeassistant.components.lock")

    class LockEntity:
        pass

    lock.LockEntity = LockEntity
    sys.modules["homeassistant.components.lock"] = lock

    diagnostics = types.ModuleType("homeassistant.components.diagnostics")

    def _redact(value, redact):
        if isinstance(value, dict):
            return {
                k: ("REDACTED" if k in redact else _redact(v, redact))
                for k, v in value.items()
            }
        if isinstance(value, list):
            return [_redact(x, redact) for x in value]
        return value

    diagnostics.async_redact_data = lambda data, redact: _redact(data, redact)
    sys.modules["homeassistant.components.diagnostics"] = diagnostics

    restore_state = types.ModuleType("homeassistant.helpers.restore_state")

    class RestoreEntity:
        async def async_added_to_hass(self):
            return None

        async def async_get_last_state(self):
            return None

    restore_state.RestoreEntity = RestoreEntity
    sys.modules["homeassistant.helpers.restore_state"] = restore_state

    entity_platform = types.ModuleType("homeassistant.helpers.entity_platform")
    entity_platform.AddEntitiesCallback = object
    sys.modules["homeassistant.helpers.entity_platform"] = entity_platform

    config_entries = types.ModuleType("homeassistant.config_entries")

    class ConfigEntry:
        pass

    config_entries.ConfigEntry = ConfigEntry
    sys.modules["homeassistant.config_entries"] = config_entries

    ha_const = sys.modules["homeassistant.const"]
    ha_const.PERCENTAGE = "%"
    ha_const.STATE_UNAVAILABLE = "unavailable"


def _install_component_stubs():
    coord = types.ModuleType(f"{PKG}.coordinator")
    coord.lock_coordinators = lambda hass, entry: []

    class LockUpdateCoordinator:
        pass

    coord.LockUpdateCoordinator = LockUpdateCoordinator
    sys.modules[f"{PKG}.coordinator"] = coord

    const = types.ModuleType(f"{PKG}.const")
    const.DOMAIN = "javis_lock"
    const.TT_LOCKS = "locks"
    sys.modules[f"{PKG}.const"] = const


async def _run_tests():
    entity_mod = load_module("entity", "entity.py")
    lock_mod = load_module("lock", "lock.py")
    sensor_mod = load_module("sensor", "sensor.py")
    bin_mod = load_module("binary_sensor", "binary_sensor.py")
    diagnostics_mod = load_module("diagnostics", "diagnostics.py")

    lock_data = SimpleNamespace(
        mac="AA:BB:CC:DD",
        name="Front Door",
        locked=True,
        action_pending=False,
        battery_level=88,
        last_user="admin",
        last_reason="unlock by app",
        passage_mode_active=lambda *args, **kwargs: True,
    )
    fake_coordinator = SimpleNamespace(
        data=lock_data,
        device_info={"id": 1},
        unique_id="javis_lock-1",
    )

    lock_entity = lock_mod.Lock(fake_coordinator)
    check("lock entity_id mapping", lock_entity.entity_id, "lock.ttlock_aabbccdd")
    check("lock name mapping", lock_entity._attr_name, "Front Door")
    check("lock state mapping", lock_entity._attr_is_locked, True)

    battery_entity = sensor_mod.LockBattery(fake_coordinator)
    check(
        "battery entity id", battery_entity.entity_id, "sensor.ttlock_aabbccdd_battery"
    )
    check("battery value", battery_entity._attr_native_value, 88)

    trigger_entity = sensor_mod.LockTrigger(fake_coordinator)
    check("trigger sensor value", trigger_entity._attr_native_value, "unlock by app")

    # RestoreEntity path for operator/trigger
    operator_entity = sensor_mod.LockOperator(fake_coordinator)

    async def fake_last_state_operator():
        return SimpleNamespace(state="restored_user")

    operator_entity.async_get_last_state = fake_last_state_operator
    operator_entity._attr_native_value = None
    fake_coordinator.data.last_user = None
    await operator_entity.async_added_to_hass()
    check(
        "operator restores last state",
        operator_entity._attr_native_value,
        "restored_user",
    )

    trigger_restore_entity = sensor_mod.LockTrigger(fake_coordinator)

    async def fake_last_state_trigger():
        return SimpleNamespace(state="restored_trigger")

    trigger_restore_entity.async_get_last_state = fake_last_state_trigger
    trigger_restore_entity._attr_native_value = None
    fake_coordinator.data.last_reason = None
    await trigger_restore_entity.async_added_to_hass()
    check(
        "trigger restores last state",
        trigger_restore_entity._attr_native_value,
        "restored_trigger",
    )

    passage_entity = bin_mod.PassageMode(fake_coordinator)
    check("passage mode binary sensor on", passage_entity._attr_is_on, True)

    class DemoEntity(entity_mod.BaseLockEntity):
        def _update_from_coordinator(self):
            self._attr_name = "demo"

    demo = DemoEntity(fake_coordinator)
    demo._handle_coordinator_update()
    check("base entity writes HA state", demo._write_called, True)

    config_entry = SimpleNamespace(
        entry_id="entry-1",
        as_dict=lambda: {"token": "secret", "name": "demo"},
    )
    hass = SimpleNamespace(
        data={
            "javis_lock": {
                "entry-1": {
                    "locks": [
                        SimpleNamespace(
                            as_dict=lambda: {
                                "device": {"adminPwd": "1234", "name": "Front Door"},
                                "entities": [],
                            }
                        )
                    ]
                }
            }
        }
    )

    diag = await diagnostics_mod.async_get_config_entry_diagnostics(hass, config_entry)
    check("diagnostics redacts token", diag["config_entry"]["token"], "REDACTED")
    check(
        "diagnostics redacts adminPwd",
        diag["locks"][0]["device"]["adminPwd"],
        "REDACTED",
    )


def main():
    print("\n" + "=" * 64)
    print("TEST ENTITIES AND DIAGNOSTICS")
    print("=" * 64)

    clear_modules(PKG)
    install_package_root()
    stub_homeassistant_minimal()
    _install_extra_homeassistant_stubs()
    _install_component_stubs()
    asyncio.run(_run_tests())

    print("\n" + "=" * 64)
    if tests_failed == 0:
        print(f"ALL {tests_run} TESTS PASSED")
    else:
        print(f"FAILED: {tests_failed}/{tests_run}")
    print("=" * 64 + "\n")
    raise SystemExit(0 if tests_failed == 0 else 1)


if __name__ == "__main__":
    main()
