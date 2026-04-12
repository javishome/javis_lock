import json
import os
import re
import shutil
import subprocess
import sys

# Map: HA version -> python version (Linux: python3.12, python3.13)
map_python_version = {
    "2024_4_4": {"py_ver": "3.12"},
    "2024_12_4": {"py_ver": "3.13"},
}


def remove_old_build(build_dir):
    if os.path.exists(build_dir):
        print(f"Removing old build folder: {build_dir}")
        shutil.rmtree(build_dir)


def _read_manifest_version(main_code_dir) -> str | None:
    manifest_path = os.path.join(main_code_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        return None
    with open(manifest_path, "r", encoding="utf-8") as f:
        return str(json.load(f).get("version", "")).strip()


def _bump_version_tag(version: str) -> str:
    """Accept only `vN`, always returns `v{N+1}`."""
    match = re.fullmatch(r"v(\d+)", version.strip())
    if not match:
        raise ValueError(f"Invalid manifest version format: {version!r}")
    current = int(match.group(1))
    return f"v{current + 1}"


def should_keep_current_version() -> bool:
    """Ask user whether to keep the current manifest version."""
    if not hasattr(sys.stdin, "isatty") or not sys.stdin.isatty():
        print("Non-interactive mode detected, default to auto bump version.")
        return False

    while True:
        answer = input("Giữ version hiện tại? (y/N): ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("", "n", "no"):
            return False
        print("Vui lòng nhập 'y' hoặc 'n'.")


def _write_manifest_version(main_code_dir, version: str):
    manifest_path = os.path.join(main_code_dir, "manifest.json")
    with open(manifest_path, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data["version"] = version
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()


def update_manifest_version(main_code_dir):
    """Bump version +1, return (old_version, new_version)."""
    manifest_path = os.path.join(main_code_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        print(f"manifest.json not found in {main_code_dir}")
        return None, None
    old = _read_manifest_version(main_code_dir)
    try:
        new = _bump_version_tag(old)
    except ValueError as err:
        print(err)
        return None, None
    _write_manifest_version(main_code_dir, new)
    print(f"Updated manifest.json version: {old} -> {new}")
    return old, new


def revert_manifest_version(main_code_dir, old_version: str):
    """Revert to previous version when build fails."""
    _write_manifest_version(main_code_dir, old_version)
    print(f"Reverted manifest.json version back to {old_version}")


def copy_main_code_to_build(build_dir, main_code_dir):
    print(f"Copying from {main_code_dir} to {build_dir}")
    shutil.copytree(main_code_dir, build_dir)


def is_python_available(py_ver: str) -> bool:
    """Check whether python3.x is available in PATH."""
    result = subprocess.run(
        f"python{py_ver} --version", shell=True, capture_output=True, text=True
    )
    return result.returncode == 0


def _sudo() -> str:
    """Return empty string when already root."""
    if hasattr(os, "getuid"):
        return "" if os.getuid() == 0 else "sudo "
    return ""


def check_or_install_python(py_ver: str) -> bool:
    """
    If python{py_ver} is missing:
      1. Try auto-install via deadsnakes PPA on Ubuntu/Debian.
      2. If failed, print manual guide and return False.
    """
    if is_python_available(py_ver):
        print(f"python{py_ver} found.")
        return True

    print(f"python{py_ver} not found. Attempting auto-install via deadsnakes PPA...")
    s = _sudo()

    major, minor = (int(x) for x in py_ver.split(".")[:2])
    py_pkgs = f"python{py_ver}"
    if (major, minor) < (3, 12):
        py_pkgs += f" python{py_ver}-distutils"

    cmds = [
        f"{s}apt-get update -qq",
        f"{s}apt-get install -y software-properties-common",
        f"{s}add-apt-repository -y ppa:deadsnakes/ppa",
        f"{s}apt-get update -qq",
        f"{s}apt-get install -y {py_pkgs}",
    ]
    for cmd in cmds:
        print(f"  -> {cmd}")
        r = subprocess.run(cmd, shell=True)
        if r.returncode != 0:
            print(f"Auto-install failed at: {cmd}")
            _print_manual_guide(py_ver)
            return False

    if is_python_available(py_ver):
        print(f"python{py_ver} installed successfully.")
        return True

    print(f"python{py_ver} still not found after install.")
    _print_manual_guide(py_ver)
    return False


def _print_manual_guide(py_ver: str):
    print(
        f"""
Manual install guide for python{py_ver} on Ubuntu/Debian:
   sudo apt-get update
   sudo apt-get install -y software-properties-common
   sudo add-apt-repository -y ppa:deadsnakes/ppa
   sudo apt-get update
   sudo apt-get install -y python{py_ver} python{py_ver}-distutils

On Fedora/RHEL:
   sudo dnf install python{py_ver}

Build from source:
   https://www.python.org/downloads/release/python-{py_ver.replace(".", "")}0/
"""
    )


def encode_with_python(py_ver: str, build_dir: str):
    """Use python3.x to encode .py -> .pyc."""
    py_exe = f"python{py_ver}"
    encode_script = os.path.join(build_dir, "encode.py")
    cmd = f'{py_exe} "{encode_script}"'
    print(f"Running: {cmd}")
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, cwd=build_dir
    )
    if result.returncode != 0:
        print(f"Encode failed:\n{result.stderr}")
        return False
    print(f"Encode successful:\n{result.stdout}")
    return True


def check_encoded_files(build_dir):
    expected_files = ["__init__.pyc", "const.pyc", "api.pyc"]
    all_ok = True
    for file in expected_files:
        path = os.path.join(build_dir, file)
        if os.path.exists(path):
            print(f"Found: {file}")
        else:
            print(f"Missing: {file}")
            all_ok = False
    return all_ok


def build_version(ha_version: str, root_dir: str, main_code_dir: str):
    cfg = map_python_version[ha_version]
    py_ver = cfg["py_ver"]

    build_dir = os.path.join(root_dir, "build", ha_version)
    print(f"\n{'=' * 55}")
    print(f"Building {ha_version} (Python {py_ver}) [Linux]")
    print(f"{'=' * 55}")

    if not check_or_install_python(py_ver):
        return False

    remove_old_build(build_dir)
    copy_main_code_to_build(build_dir, main_code_dir)

    ok = encode_with_python(py_ver, build_dir)
    if ok:
        check_encoded_files(build_dir)
    return ok


def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    main_code_dir = os.path.join(root_dir, "main_code", "2024")

    print("Starting release for all versions")

    current_version = _read_manifest_version(main_code_dir)
    if current_version is None:
        print(f"manifest.json not found in {main_code_dir}")
        sys.exit(1)

    keep_version = should_keep_current_version()
    version_was_bumped = False

    if keep_version:
        old_version = current_version
        new_version = current_version
        print(f"Keep current manifest version: {new_version}")
    else:
        old_version, new_version = update_manifest_version(main_code_dir)
        if new_version is None:
            sys.exit(1)
        version_was_bumped = True

    results = {}
    for ha_version in map_python_version:
        ok = build_version(ha_version, root_dir, main_code_dir)
        results[ha_version] = "OK" if ok else "FAILED"

    print(f"\n{'=' * 55}")
    print("Summary:")
    for ver, status in results.items():
        py = map_python_version[ver]["py_ver"]
        print(f"  {ver} (Python {py}): {status}")

    if all(v == "OK" for v in results.values()):
        print(f"Done! Version {new_version} released.")

        custom_manifest = os.path.join(
            root_dir, "custom_components", "javis_lock", "manifest.json"
        )
        if os.path.exists(custom_manifest):
            try:
                with open(custom_manifest, "r+", encoding="utf-8") as f:
                    data = json.load(f)
                    data["version"] = new_version
                    f.seek(0)
                    json.dump(data, f, indent=4)
                    f.truncate()
                print(
                    "Synced version "
                    f"{new_version} to custom_components/javis_lock/manifest.json"
                )
            except Exception as e:
                print(f"Could not sync version to custom_components: {e}")
    else:
        if version_was_bumped:
            revert_manifest_version(main_code_dir, old_version)
            print("Some builds failed - version reverted to", old_version)
        else:
            print("Some builds failed - version was kept at", new_version)
        sys.exit(1)


if __name__ == "__main__":
    main()
