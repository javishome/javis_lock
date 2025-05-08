import os
import shutil
import json
import subprocess
import sys


map_python_version = {
    "2024_4_4": "3.12",
    "2024_12_4": "3.13",
}



def remove_old_build(build_dir):
    if os.path.exists(build_dir):
        print(f"🧹 Removing old build folder: {build_dir}")
        shutil.rmtree(build_dir)
    else:
        print("✅ No previous build to remove.")

def update_manifest_version(main_code_dir):
    manifest_path = os.path.join(main_code_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        print(f"❌ manifest.json not found in {main_code_dir}")
        return
    with open(manifest_path, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data["version"] = str(int(data["version"]) + 1)
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
    print(f"📝 Updated manifest.json version to {data['version']}")

def copy_main_code_to_build(build_dir,main_code_dir):
    print(f"📁 Copying from {main_code_dir} to {build_dir}")
    shutil.copytree(main_code_dir, build_dir)

def encode_py_files(build_dir):
    print("🚀 Encoding .py files to .pyc")
    os.chdir(build_dir)
    result = subprocess.run(["python", "encode.py"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Encode failed: {result.stderr}")
    else:
        print(f"✅ Encode successful: {result.stdout}")

def check_encoded_files():
    expected_files = ["__init__.pyc", "const.pyc", "api.pyc"]
    for file in expected_files:
        if os.path.exists(file):
            print(f"✅ Found encoded file: {file}")
        else:
            print(f"❌ Missing encoded file: {file}")

def main():
    current_version = sys.version_info[:2]
    current_version_str = f"{current_version[0]}.{current_version[1]}"

    versions_supported = list(map_python_version.keys())
    version = input(f"Nhập version cần release (phải trong {versions_supported}): ")
    print(f"🔁 Starting release process for version {version}")
    ROOT_DIR = os.getcwd()
    build_dir = os.path.join(ROOT_DIR, "build", version)
    main_code_dir = os.path.join(ROOT_DIR, "main_code", "2024")
    if version not in map_python_version:
        print("❌ Version không hợp lệ. Chỉ hỗ trợ 2024_4_4 hoặc 2024_12_4.")
        return
    python_version = map_python_version[version]
    print(f"🔄 Using Python version: {python_version}")
    # kiểm tra xem có đang chạy đúng python version không
    if current_version_str != python_version:
        print(f"❌ Python version mismatch. Expected {python_version}, but got {current_version_str}.")
        return
    print(f"🔄 Current Python version: {current_version_str}")
    remove_old_build(build_dir)
    update_manifest_version(main_code_dir)
    copy_main_code_to_build(build_dir,main_code_dir)

    encode_py_files(build_dir)
    check_encoded_files()
    print("🎉 Release process completed!")

if __name__ == "__main__":
    main()
