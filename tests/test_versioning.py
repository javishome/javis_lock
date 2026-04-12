"""Script tests for manifest version bump behavior.

Run: python tests/test_versioning.py
"""

import json
import os
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import auto_encode as release_tool


tests_run = 0
tests_failed = 0


def show_case(case_id, goal, test_input, expected_output, note):
    print("\n" + "-" * 60)
    print(f"CASE {case_id}: {goal}")
    print(f"Input: {test_input}")
    print(f"Expected output: {expected_output}")
    print(f"Note: {note}")


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


def expect_raises_value_error(test_name, func, value):
    global tests_run, tests_failed
    tests_run += 1
    try:
        func(value)
        tests_failed += 1
        print(f"  FAIL: {test_name}")
        print("        Expected ValueError but no exception was raised")
    except ValueError:
        print(f"  PASS: {test_name}")


print("\n" + "=" * 60)
print("TEST VERSION BUMP LOGIC (auto_encode.py)")
print("=" * 60)


show_case(
    "V-001",
    "Bump prefixed version",
    "v1",
    "v2",
    "Normal path for the new format.",
)
check("_bump_version_tag('v1')", release_tool._bump_version_tag("v1"), "v2")


show_case(
    "V-002",
    "Reject numeric-only version",
    "1",
    "ValueError",
    "Server requires versions to start with lowercase 'v'.",
)
expect_raises_value_error(
    "_bump_version_tag('1') raises ValueError",
    release_tool._bump_version_tag,
    "1",
)


show_case(
    "V-003",
    "Reject uppercase prefix",
    "V9",
    "ValueError",
    "Version format is strict lowercase: vN.",
)
expect_raises_value_error(
    "_bump_version_tag('V9') raises ValueError",
    release_tool._bump_version_tag,
    "V9",
)


show_case(
    "V-004",
    "Reject invalid formats",
    "['vx', '1.2', '', 'v', 'v1.0.0']",
    "ValueError for each item",
    "Only lowercase v followed by digits is valid.",
)
for invalid_value in ("vx", "1.2", "", "v", "v1.0.0"):
    expect_raises_value_error(
        f"_bump_version_tag('{invalid_value}') raises ValueError",
        release_tool._bump_version_tag,
        invalid_value,
    )


show_case(
    "V-005",
    "Update manifest file from v-format",
    '{"version": "v1"}',
    'old="v1", new="v2", file version="v2"',
    "Avoid unicode print issues by mocking print in this test.",
)
with tempfile.TemporaryDirectory() as tmp:
    manifest_path = os.path.join(tmp, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({"version": "v1"}, f)

    with patch("builtins.print"):
        old_version, new_version = release_tool.update_manifest_version(tmp)

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    check("update_manifest_version old", old_version, "v1")
    check("update_manifest_version new", new_version, "v2")
    check("manifest file updated to v2", data["version"], "v2")


show_case(
    "V-006",
    "Reject manifest file using numeric-only format",
    '{"version": "1"}',
    "returns (None, None) and file stays unchanged",
    "Server requires v-prefixed versions; numeric format is invalid.",
)
with tempfile.TemporaryDirectory() as tmp:
    manifest_path = os.path.join(tmp, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({"version": "1"}, f)

    with patch("builtins.print"):
        old_version, new_version = release_tool.update_manifest_version(tmp)

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    check("numeric-only old version", old_version, None)
    check("numeric-only new version", new_version, None)
    check("numeric-only manifest unchanged", data["version"], "1")


show_case(
    "V-007",
    "Invalid manifest version should not be overwritten",
    '{"version": "alpha"}',
    "returns (None, None) and file stays unchanged",
    "A safe failure path for malformed data.",
)
with tempfile.TemporaryDirectory() as tmp:
    manifest_path = os.path.join(tmp, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({"version": "alpha"}, f)

    with patch("builtins.print"):
        old_version, new_version = release_tool.update_manifest_version(tmp)

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    check("invalid format old version", old_version, None)
    check("invalid format new version", new_version, None)
    check_true("file version remains unchanged", data["version"] == "alpha")


show_case(
    "V-008",
    "Interactive prompt accepts keep-version=yes",
    "stdin is TTY, user input='y'",
    "returns True",
    "Main flow should keep version when user confirms.",
)
with (
    patch.object(
        release_tool, "sys", SimpleNamespace(stdin=SimpleNamespace(isatty=lambda: True))
    ),
    patch("builtins.input", return_value="y"),
):
    keep_true = release_tool.should_keep_current_version()
check("should_keep_current_version('y')", keep_true, True)


show_case(
    "V-009",
    "Interactive prompt default path",
    "stdin is TTY, user presses Enter",
    "returns False",
    "Enter should map to default No (auto bump).",
)
with (
    patch.object(
        release_tool, "sys", SimpleNamespace(stdin=SimpleNamespace(isatty=lambda: True))
    ),
    patch("builtins.input", return_value=""),
):
    keep_false = release_tool.should_keep_current_version()
check("should_keep_current_version('')", keep_false, False)


show_case(
    "V-010",
    "Non-interactive mode fallback",
    "stdin is not TTY",
    "returns False",
    "CI/non-interactive runs should auto-bump without waiting for input.",
)
with (
    patch.object(
        release_tool,
        "sys",
        SimpleNamespace(stdin=SimpleNamespace(isatty=lambda: False)),
    ),
    patch("builtins.print"),
):
    keep_non_tty = release_tool.should_keep_current_version()
check("should_keep_current_version(non-tty)", keep_non_tty, False)


print("\n" + "=" * 60)
if tests_failed == 0:
    print(f"ALL {tests_run} TESTS PASSED")
else:
    print(f"FAILED: {tests_failed}/{tests_run}")
print("=" * 60 + "\n")

sys.exit(0 if tests_failed == 0 else 1)
