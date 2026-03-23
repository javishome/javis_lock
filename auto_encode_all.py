import os
import shutil
import json
import subprocess
import sys

# Map: HA version → python version (Linux: python3.12, python3.13)
map_python_version = {
    "2024_4_4":  {"py_ver": "3.12"},
    "2024_12_4": {"py_ver": "3.13"},
}


def remove_old_build(build_dir):
    if os.path.exists(build_dir):
        print(f"🧹 Removing old build folder: {build_dir}")
        shutil.rmtree(build_dir)


def update_manifest_version(main_code_dir):
    manifest_path = os.path.join(main_code_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        print(f"❌ manifest.json not found in {main_code_dir}")
        return None
    with open(manifest_path, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data["version"] = str(int(data["version"]) + 1)
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
    print(f"📝 Updated manifest.json version to {data['version']}")
    return data["version"]


def copy_main_code_to_build(build_dir, main_code_dir):
    print(f"📁 Copying from {main_code_dir} to {build_dir}")
    shutil.copytree(main_code_dir, build_dir)


def is_python_available(py_ver: str) -> bool:
    """Kiểm tra python3.x có trong PATH không."""
    result = subprocess.run(
        f"python{py_ver} --version",
        shell=True, capture_output=True, text=True
    )
    return result.returncode == 0


def _sudo() -> str:
    """Return empty string when already root (avoids hostname resolution issues with sudo)."""
    return "" if os.getuid() == 0 else "sudo "


def check_or_install_python(py_ver: str) -> bool:
    """
    Nếu python{py_ver} chưa có:
      1. Thử cài tự động qua deadsnakes PPA (Ubuntu/Debian).
      2. Nếu không được, log hướng dẫn cài thủ công rồi trả về False.
    """
    if is_python_available(py_ver):
        print(f"✅ python{py_ver} found.")
        return True

    print(f"⚠️  python{py_ver} not found. Attempting auto-install via deadsnakes PPA...")
    s = _sudo()
    cmds = [
        f"{s}apt-get update -qq",
        f"{s}apt-get install -y software-properties-common",
        f"{s}add-apt-repository -y ppa:deadsnakes/ppa",
        f"{s}apt-get update -qq",
        f"{s}apt-get install -y python{py_ver} python{py_ver}-distutils",
    ]
    for cmd in cmds:
        print(f"  ▶ {cmd}")
        r = subprocess.run(cmd, shell=True)
        if r.returncode != 0:
            print(f"❌ Auto-install failed at: {cmd}")
            _print_manual_guide(py_ver)
            return False

    if is_python_available(py_ver):
        print(f"✅ python{py_ver} installed successfully.")
        return True

    print(f"❌ python{py_ver} still not found after install.")
    _print_manual_guide(py_ver)
    return False


def _print_manual_guide(py_ver: str):
    print(f"""
📖 Hướng dẫn cài thủ công python{py_ver} trên Ubuntu/Debian:
   sudo apt-get update
   sudo apt-get install -y software-properties-common
   sudo add-apt-repository -y ppa:deadsnakes/ppa
   sudo apt-get update
   sudo apt-get install -y python{py_ver} python{py_ver}-distutils

📖 Trên Fedora/RHEL:
   sudo dnf install python{py_ver}

📖 Build từ source (mọi distro):
   https://www.python.org/downloads/release/python-{py_ver.replace('.', '')}0/
""")


def encode_with_python(py_ver: str, build_dir: str):
    """Gọi python3.x để encode .py -> .pyc"""
    py_exe = f"python{py_ver}"
    encode_script = os.path.join(build_dir, "encode.py")
    cmd = f"{py_exe} \"{encode_script}\""
    print(f"🚀 Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=build_dir)
    if result.returncode != 0:
        print(f"❌ Encode failed:\n{result.stderr}")
        return False
    else:
        print(f"✅ Encode successful:\n{result.stdout}")
        return True



def check_encoded_files(build_dir):
    expected_files = ["__init__.pyc", "const.pyc", "api.pyc"]
    all_ok = True
    for file in expected_files:
        path = os.path.join(build_dir, file)
        if os.path.exists(path):
            print(f"✅ Found: {file}")
        else:
            print(f"❌ Missing: {file}")
            all_ok = False
    return all_ok


def build_version(ha_version: str, root_dir: str, main_code_dir: str):
    cfg = map_python_version[ha_version]
    py_ver = cfg["py_ver"]

    build_dir = os.path.join(root_dir, "build", ha_version)
    print(f"\n{'='*55}")
    print(f"📦 Building {ha_version}  (Python {py_ver}) [Linux]")
    print(f"{'='*55}")

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

    print("🔁 Starting release for ALL versions")
    update_manifest_version(main_code_dir)

    results = {}
    for ha_version in map_python_version:
        ok = build_version(ha_version, root_dir, main_code_dir)
        results[ha_version] = "✅ OK" if ok else "❌ FAILED"

    print(f"\n{'='*55}")
    print("📊 Summary:")
    for ver, status in results.items():
        py = map_python_version[ver]["py_ver"]
        print(f"  {ver} (Python {py}): {status}")
    print("🎉 Done!")


if __name__ == "__main__":
    main()
