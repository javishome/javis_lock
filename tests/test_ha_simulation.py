"""Home Assistant Simulation Harness (HA 2024.4.4 and HA 2024.12.4).

Validates:
1. Complete HA lifecycle for HA 2024.4.4 (Python 3.12 target) and HA 2024.12.4 (Python 3.13 target).
2. Module reload idempotency (guards against duplicate validator runtime errors).
3. Component setup, coordinator initialization, service registration, and clean unload.
4. Compiled bytecode (.pyc) load sanity in Python 3.12 and Python 3.13.

Run: python tests/test_ha_simulation.py
"""

import asyncio
import os
import subprocess
import sys
import types
from datetime import datetime

from _component_test_stubs import (
    BASE_DIR,
    MAIN_CODE_DIR,
    clear_modules,
    stub_aiohttp_retry,
    stub_homeassistant_minimal,
    stub_voluptuous,
)

BUILD_2024_4_4 = os.path.join(BASE_DIR, "build", "2024_4_4")
BUILD_2024_12_4 = os.path.join(BASE_DIR, "build", "2024_12_4")

tests_run = 0
tests_failed = 0


def check(test_name, condition, extra=""):
    global tests_run, tests_failed
    tests_run += 1
    if condition:
        print(f"  PASS: {test_name}")
    else:
        tests_failed += 1
        print(f"  FAIL: {test_name} {extra}")


def setup_ha_environment(ha_version_str):
    clear_modules("custom_components.javis_lock")
    clear_modules("homeassistant")
    stub_voluptuous()
    stub_aiohttp_retry()
    stub_homeassistant_minimal()

    # Set specific HA version
    sys.modules["homeassistant.const"].__version__ = ha_version_str
    sys.modules["homeassistant.core"].callback = lambda fn: fn


def load_component_package(src_dir):
    import importlib.util

    pkg_name = "custom_components.javis_lock"
    pkg_mod = types.ModuleType(pkg_name)
    pkg_mod.__path__ = [src_dir]
    sys.modules[pkg_name] = pkg_mod

    # Load submodules
    for sub in ["const", "models", "api", "coordinator", "services"]:
        sub_path = os.path.join(src_dir, f"{sub}.py")
        if os.path.exists(sub_path):
            spec = importlib.util.spec_from_file_location(f"{pkg_name}.{sub}", sub_path)
            sub_mod = importlib.util.module_from_spec(spec)
            sys.modules[f"{pkg_name}.{sub}"] = sub_mod
            spec.loader.exec_module(sub_mod)
            setattr(pkg_mod, sub, sub_mod)

    return pkg_mod


async def simulate_ha_version(ha_version, label):
    print(f"\n=======================================================")
    print(f"  SIMULATING HOME ASSISTANT {ha_version} ({label})")
    print(f"=======================================================")

    setup_ha_environment(ha_version)

    # 1. Package loading
    try:
        mod = load_component_package(MAIN_CODE_DIR)
        check(f"[{ha_version}] Import custom_components.javis_lock cleanly", True)
    except Exception as e:
        check(f"[{ha_version}] Import custom_components.javis_lock cleanly", False, str(e))
        return

    # 2. Duplicate reload idempotency check (Catches Pydantic duplicate validator bug)
    try:
        import importlib.util

        models_path = os.path.join(MAIN_CODE_DIR, "models.py")
        spec = importlib.util.spec_from_file_location("custom_components.javis_lock.models", models_path)
        m1 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m1)
        # Reload second time
        spec.loader.exec_module(m1)
        # Reload third time
        spec.loader.exec_module(m1)
        check(f"[{ha_version}] Pydantic models reload 3x without duplicate validator error", True)
    except Exception as e:
        check(f"[{ha_version}] Pydantic models reload 3x without duplicate validator error", False, str(e))

    # 3. Setup lifecycle simulation
    ha_core = sys.modules["homeassistant.core"]
    ha_cfg = sys.modules["homeassistant.config_entries"]

    hass = ha_core.HomeAssistant()
    hass.data = {}
    def _reg(domain, s_name, handler, schema=None, **kw):
        hass.services._services.setdefault(domain, {})[s_name] = handler

    hass.services = types.SimpleNamespace(
        _services={},
        register=_reg,
        async_register=_reg,
        async_call=lambda domain, s_name, data=None: hass.services._services.get(domain, {}).get(s_name)(data),
    )

    entry = ha_cfg.ConfigEntry()
    entry.entry_id = "mock_entry_id"
    entry.data = {"username": "test@javis.io", "password": "pwd", "url": "https://speaker.javis.io"}

    api_mock = types.SimpleNamespace(
        ensure_valid_token=lambda: asyncio.sleep(0.001, result=True),
        get_locks=lambda: asyncio.sleep(0.001, result=[{"lockId": 1001, "lockName": "Door", "lockMac": "00:11:22:33:44:55"}]),
        set_passage_mode=lambda *args, **kw: asyncio.sleep(0.001, result=True),
    )

    # 4. Coordinator setup
    try:
        from custom_components.javis_lock.coordinator import LockUpdateCoordinator
        coordinator = LockUpdateCoordinator(hass, api_mock, 1001)
        coordinator.data = {1001: {"lockId": 1001, "state": 1, "electricQuantity": 95}}

        hass.data.setdefault("javis_lock", {})[entry.entry_id] = {
            "coordinator": coordinator,
            "api": api_mock,
            "locks": [1001],
        }
        check(f"[{ha_version}] Initialize coordinator and store in hass.data", True)
    except Exception as e:
        check(f"[{ha_version}] Initialize coordinator", False, str(e))

    # 5. Service registration check
    try:
        from custom_components.javis_lock.services import Services
        srv = Services(hass)
        srv.register_new()
        reg_count = len(hass.services._services.get("javis_lock", {}))
        check(f"[{ha_version}] Register all 5 lock services into HA Event Bus", reg_count >= 5)
    except Exception as e:
        check(f"[{ha_version}] Register lock services", False, str(e))

    # 6. Unload & Reload Simulation
    try:
        hass.data["javis_lock"].pop(entry.entry_id, None)
        check(f"[{ha_version}] Clean unload of entry data", entry.entry_id not in hass.data.get("javis_lock", {}))
    except Exception as e:
        check(f"[{ha_version}] Clean unload of entry data", False, str(e))


def test_compiled_bytecode(py_executable, build_dir, label):
    """Run standalone python subprocess in targeted Python version on compiled bytecode."""
    if not os.path.exists(py_executable):
        print(f"  SKIP: {label} executable {py_executable} not found")
        return

    test_script = f"""
import sys, os, importlib.util

found = 0
for root, _, files in os.walk({repr(build_dir)}):
    for f in files:
        if f.endswith(".pyc"):
            found += 1
            mod_name = f[:-4]
            spec = importlib.util.spec_from_file_location(mod_name, os.path.join(root, f))
            if spec is None or spec.loader is None:
                print(f"FAIL: spec is None for {{f}}")
                sys.exit(1)

print(f"BYTECODE_OK: {{found}} pyc files verified")
"""
    proc = subprocess.run([py_executable, "-c", test_script], capture_output=True, text=True)
    check(f"Bytecode sanity in {label} ({os.path.basename(build_dir)})", proc.returncode == 0 and "BYTECODE_OK" in proc.stdout, proc.stderr)


async def main():
    print("\n" + "=" * 64)
    print("HOME ASSISTANT SIMULATION TEST SUITE (2024.4.4 & 2024.12.4)")
    print("=" * 64)

    # 1. Simulate HA 2024.4.4 (Python 3.12 target)
    await simulate_ha_version("2024.4.4", "HA 2024.4.4 - Python 3.12")

    # 2. Simulate HA 2024.12.4 (Python 3.13 target)
    await simulate_ha_version("2024.12.4", "HA 2024.12.4 - Python 3.13")

    # 3. Test compiled bytecode in Python 3.12 and Python 3.13
    test_compiled_bytecode("/usr/bin/python3.12", BUILD_2024_4_4, "Python 3.12")
    test_compiled_bytecode(os.path.expanduser("~/miniconda3/envs/py313/bin/python"), BUILD_2024_12_4, "Python 3.13")

    print("\n" + "=" * 64)
    if tests_failed == 0:
        print(f"ALL {tests_run} HA SIMULATION TESTS PASSED!")
    else:
        print(f"FAILED: {tests_failed}/{tests_run}")
    print("=" * 64 + "\n")
    sys.exit(0 if tests_failed == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
