"""Run all local test scripts for 103_smartlock_component.

Usage:
    python tests/run_all.py
"""

import os
import subprocess
import sys


TEST_FILES = [
    "test_versioning.py",
    "test_services.py",
    "test_services_extra.py",
    "test_config_flow.py",
    "test_lock_state.py",
    "test_coordinator_runtime.py",
    "test_api_client.py",
    "test_init_setup.py",
    "test_entities_and_diagnostics.py",
    "test_models.py",
]


def main() -> int:
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    python_exe = sys.executable

    print("\n" + "=" * 64)
    print("RUN ALL TEST SCRIPTS")
    print("=" * 64)

    failed = []
    for test_file in TEST_FILES:
        test_path = os.path.join(tests_dir, test_file)
        print(f"\n>>> Running {test_file}")
        result = subprocess.run([python_exe, test_path], cwd=tests_dir)
        if result.returncode != 0:
            failed.append((test_file, result.returncode))

    print("\n" + "=" * 64)
    if not failed:
        print(f"ALL {len(TEST_FILES)} TEST SCRIPTS PASSED")
        print("=" * 64 + "\n")
        return 0

    print(f"FAILED: {len(failed)}/{len(TEST_FILES)}")
    for name, code in failed:
        print(f"- {name} (exit={code})")
    print("=" * 64 + "\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
