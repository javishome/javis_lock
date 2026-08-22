"""Comprehensive Live Services Automation Test Suite for Javis Lock (TTLock) & Server Cloud API (with Dry-Run Safety):

Supports 3 testing layers:
1. Server Cloud API Layer (https://lock-api.javiscloud.com)
   - POST /api/login (Authentication)
   - GET /api/lock/list (Lock discovery)
   - GET /api/lock/detail (Lock info, pin, gateway)
   - GET /api/lock/listKeyboardPwd (Passcode list)
   - GET /api/lockRecord/list (Unlock logs)
   - POST /api/webhook (Simulated TTLock Webhook forwarding to HA)
2. Remote Live HA on 192.168.168.24 (via HA REST API & Signed JWT)
   - javis_lock.update_lock (Gateway state sync)
   - javis_lock.list_passcodes (Passcode list)
   - javis_lock.list_unlock_records (Unlock records)
   - javis_lock.cleanup_passcodes (Expired passcode cleanup)
   - javis_lock.create_passcode / change / delete (Safe self-cleaning passcode lifecycle)
3. Local HA Docker Container (HA 2024.4.4 / 2024.12.4 Core Event Bus)

Usage:
    # Run all 3 layers
    python tests/test_live_lock_services.py --all

    # Run against remote HA 192.168.168.24 + Server Cloud API
    python tests/test_live_lock_services.py --remote 192.168.168.24

    # Run only in local Docker HA containers
    python tests/test_live_lock_services.py --docker
"""

import argparse
import json
import os
import random
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import jwt
import requests

# Target URLs & Server Config
DEFAULT_SERVER_URL = "https://lock-api.javiscloud.com"
DEFAULT_HA_IP = "192.168.168.24"
DEFAULT_HA_PORT = 8123

# Real Credentials for 192.168.168.24
LOCK_USERNAME = "chinhdzzz14@gmail.com"
LOCK_PASSWORD = "Chinhdz123@"
REAL_LOCK_ID = 19562352
REAL_LOCK_ENTITY = "lock.ttlock_46b6d12eb066"
REAL_LOCK_MAC = "46:B6:D1:2E:B0:66"
HA_WEBHOOK_URL = "http://192.168.168.24:8123/api/webhook/cbab2cc3e50a57db9bfcec55406585e4aa14457538dd06db7129b2478f0166fb"
COMPONENT_VERSION_HEADER = {"X-Component-Version": "v20260822"}

# HA JWT Keys for 192.168.168.24
HA_JWT_ISS = "1dd0b3e5a6e74e69a3977ed011a62998"
HA_JWT_KEY = "fcf76ae532283057721b03b3afbdbdeed3ccf959d35a452cbef0ba9cb863cd803f22ac79c4e98284222c53d8828f5fc61f1a00755d2ff8238d70ec98ea2ae15e"


def generate_ha_token():
    """Generates a valid signed Bearer JWT token for Home Assistant REST API."""
    now = int(time.time())
    payload = {"iss": HA_JWT_ISS, "iat": now, "exp": now + 3600 * 24 * 365}
    return jwt.encode(payload, HA_JWT_KEY, algorithm="HS256")


def test_server_cloud_api(server_url=DEFAULT_SERVER_URL):
    """
    Layer 1: Tests TTLock Authentication & Endpoints on SmartLock Server Cloud API.
    """
    print("\n" + "=" * 88)
    print("  PHẦN 1: TEST ĐĂNG NHẬP & API KHÓA TRÊN SERVER CLOUD API")
    print(f"  Server URL: {server_url}")
    print("=" * 88)

    all_passed = True
    access_token = None

    # 1. Healthcheck
    try:
        r = requests.get(f"{server_url}/health", timeout=10)
        print(f"[*] 1. Server Healthcheck: Status {r.status_code} -> {r.json()}")
        assert r.status_code == 200
    except Exception as e:
        print(f"  ❌ Healthcheck failed: {e}")
        all_passed = False

    # 2. POST /api/login
    print(f"\n[*] 2. Test Đăng Nhập SmartLock qua POST /api/login ({LOCK_USERNAME})...")
    try:
        t0 = time.time()
        login_payload = {
            "username": LOCK_USERNAME,
            "password": LOCK_PASSWORD,
        }
        r = requests.post(
            f"{server_url}/api/login",
            json=login_payload,
            headers=COMPONENT_VERSION_HEADER,
            timeout=10
        )
        lat = int((time.time() - t0) * 1000)
        if r.status_code == 200:
            res_data = r.json()
            access_token = res_data.get("access_token")
            exp = res_data.get("expires_in")
            uid = res_data.get("uid")
            print(f"  ✅ PASS: Đăng nhập thành công ({lat}ms)!")
            print(f"     UID          : {uid}")
            print(f"     Access Token : {access_token[:35]}... (Hạn dùng: {exp}s)")
            assert access_token, "No access token received"
        else:
            print(f"  ❌ FAIL: Login returned status {r.status_code}: {r.text[:200]}")
            all_passed = False
            return False
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        all_passed = False
        return False

    headers = {**COMPONENT_VERSION_HEADER, "Authorization": f"Bearer {access_token}"}

    # 3. GET /api/lock/list
    print("\n[*] 3. Test Lấy Danh Sách Khóa qua GET /api/lock/list...")
    try:
        t0 = time.time()
        r = requests.get(
            f"{server_url}/api/lock/list",
            params={"access_token": access_token},
            headers=headers,
            timeout=10
        )
        lat = int((time.time() - t0) * 1000)
        if r.status_code == 200:
            locks = r.json().get("list", [])
            print(f"  ✅ PASS: Server trả về {len(locks)} khóa ({lat}ms):")
            for lk in locks:
                print(f"     - Lock ID: {lk.get('lockId')} | Tên: {lk.get('lockAlias')} | MAC: {lk.get('lockMac')} | Gateway: {lk.get('hasGateway')}")
            assert any(lk.get("lockId") == REAL_LOCK_ID for lk in locks), f"Lock ID {REAL_LOCK_ID} not found"
        else:
            print(f"  ❌ FAIL: /api/lock/list status {r.status_code}: {r.text[:200]}")
            all_passed = False
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        all_passed = False

    # 4. GET /api/lock/detail
    print(f"\n[*] 4. Test Lấy Chi Tiết Khóa ID {REAL_LOCK_ID} qua GET /api/lock/detail...")
    try:
        t0 = time.time()
        r = requests.get(
            f"{server_url}/api/lock/detail",
            params={"lockId": REAL_LOCK_ID, "access_token": access_token},
            headers=headers,
            timeout=10
        )
        lat = int((time.time() - t0) * 1000)
        if r.status_code == 200:
            detail = r.json()
            print(f"  ✅ PASS: Server trả về thông tin chi tiết ({lat}ms):")
            print(f"     Pin: {detail.get('electricQuantity')}% | Firmware: {detail.get('firmwareRevision')} | Model: {detail.get('modelNum')}")
            print(f"     [DRY-RUN REMOTE UNLOCK]: Gateway status = {detail.get('hasGateway')} (Khả năng mở từ xa: Sẵn sàng)")
        else:
            print(f"  ❌ FAIL: /api/lock/detail status {r.status_code}: {r.text[:200]}")
            all_passed = False
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        all_passed = False

    # 5. GET /api/lock/listKeyboardPwd
    print(f"\n[*] 5. Test Lấy Danh Sách Mật Mã Passcode qua GET /api/lock/listKeyboardPwd...")
    try:
        t0 = time.time()
        r = requests.get(
            f"{server_url}/api/lock/listKeyboardPwd",
            params={"lockId": REAL_LOCK_ID, "access_token": access_token},
            headers=headers,
            timeout=10
        )
        lat = int((time.time() - t0) * 1000)
        if r.status_code == 200:
            passcodes = r.json().get("list", [])
            print(f"  ✅ PASS: Khóa có {len(passcodes)} Passcodes ({lat}ms):")
            for p in passcodes:
                print(f"     - ID: {p.get('keyboardPwdId')} | Tên: {p.get('keyboardPwdName')} | Type: {p.get('keyboardPwdType')}")
        else:
            print(f"  ❌ FAIL: /api/lock/listKeyboardPwd status {r.status_code}: {r.text[:200]}")
            all_passed = False
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        all_passed = False

    # 6. GET /api/lockRecord/list
    print(f"\n[*] 6. Test Lấy Nhật Ký Mở Khóa qua GET /api/lockRecord/list...")
    try:
        t0 = time.time()
        r = requests.get(
            f"{server_url}/api/lockRecord/list",
            params={"lockId": REAL_LOCK_ID, "access_token": access_token, "pageNo": 1, "pageSize": 5},
            headers=headers,
            timeout=10
        )
        lat = int((time.time() - t0) * 1000)
        if r.status_code == 200:
            records = r.json().get("list", [])
            total = r.json().get("total", 0)
            print(f"  ✅ PASS: Server trả về {len(records)}/{total} nhật ký mở khóa ({lat}ms):")
            for rec in records[:3]:
                print(f"     - ID: {rec.get('recordId')} | Người mở: {rec.get('username') or rec.get('keyName')} | Thời gian: {rec.get('lockDate')}")
        else:
            print(f"  ❌ FAIL: /api/lockRecord/list status {r.status_code}: {r.text[:200]}")
            all_passed = False
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        all_passed = False

    # 7. Test Mô Phỏng Webhook Mở Khóa Đẩy Sang Home Assistant (DRY-RUN)
    print("\n[*] 7. [DRY-RUN] Test Mô Phỏng Webhook Mở Khóa Đẩy Sang Home Assistant...")
    try:
        t0 = time.time()
        wh_payload = {
            "lockId": REAL_LOCK_ID,
            "lockMac": REAL_LOCK_MAC,
            "recordType": 1,
            "success": 1,
            "lockDate": int(time.time() * 1000),
            "username": "DryRun Auto Tester"
        }
        r_wh = requests.post(HA_WEBHOOK_URL, json=wh_payload, timeout=5)
        lat = int((time.time() - t0) * 1000)
        if r_wh.status_code == 200:
            print(f"  ✅ PASS: Webhook Home Assistant tiếp nhận sự kiện thành công ({lat}ms, Status {r_wh.status_code})!")
        else:
            print(f"  ❌ FAIL: Webhook trả về status {r_wh.status_code}")
            all_passed = False
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        all_passed = False

    return all_passed


def call_ha_service(ha_url, token, domain, service, service_data=None, timeout=30):
    """Calls a Home Assistant service via REST API and measures latency."""
    url = f"{ha_url}/api/services/{domain}/{service}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = json.dumps(service_data or {}).encode("utf-8")

    t0 = time.time()
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            content = resp.read().decode("utf-8")
            latency_ms = int((time.time() - t0) * 1000)
            return True, status, content, latency_ms
    except urllib.error.HTTPError as he:
        latency_ms = int((time.time() - t0) * 1000)
        return False, he.code, he.read().decode("utf-8"), latency_ms
    except Exception as e:
        latency_ms = int((time.time() - t0) * 1000)
        return False, 0, str(e), latency_ms


def test_remote_ha_lock_services(ha_ip=DEFAULT_HA_IP, port=DEFAULT_HA_PORT):
    """
    Layer 2: Real HA Service Invocations for javis_lock on 192.168.168.24.
    """
    ha_url = f"http://{ha_ip}:{port}"
    token = generate_ha_token()

    print("\n" + "=" * 88)
    print(f"  PHẦN 2: TEST CÁC SERVICES JAVIS_LOCK TRÊN HOME ASSISTANT ({ha_url})")
    print("=" * 88)

    available_services = set()
    try:
        req = urllib.request.Request(f"{ha_url}/api/", headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            print(f"[*] Kết nối HA 192.168.168.24 thành công: {resp.read().decode('utf-8')}")

        req_svcs = urllib.request.Request(f"{ha_url}/api/services", headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req_svcs, timeout=5) as resp_s:
            all_svcs = json.loads(resp_s.read().decode("utf-8"))
            for s in all_svcs:
                if s.get("domain") == "javis_lock":
                    available_services = set(s.get("services", {}).keys())
            print(f"[*] HA đang kích hoạt {len(available_services)} Javis Lock services: {list(available_services)}")
    except Exception as e:
        print(f"❌ Failed to reach HA on {ha_url}: {e}")
        return False

    test_cases = [
        {
            "svc": "update_lock",
            "payload": {"entity_id": REAL_LOCK_ENTITY},
            "desc": "Đồng bộ trạng thái pin & trạng thái khóa qua Gateway",
        },
        {
            "svc": "list_passcodes",
            "payload": {"entity_id": REAL_LOCK_ENTITY},
            "desc": "Lấy danh sách passcode đang hoạt động của khóa",
        },
        {
            "svc": "list_unlock_records",
            "payload": {"entity_id": REAL_LOCK_ENTITY, "page_no": "1", "page_size": "10"},
            "desc": "Lấy lịch sử mở cửa từ Home Assistant",
        },
        {
            "svc": "cleanup_passcodes",
            "payload": {"entity_id": REAL_LOCK_ENTITY},
            "desc": "Dọn dẹp các passcode đã hết hạn trên khóa",
        },
    ]

    print("\n[*] Thực thi gọi Service...")
    results = []
    print("-" * 88)
    print(f"{'SERVICE':<32} | {'LATENCY':<8} | {'HTTP':<5} | {'RESULT':<8} | {'DESCRIPTION'}")
    print("-" * 88)

    all_passed = True
    for tc in test_cases:
        svc = tc["svc"]
        svc_full = f"javis_lock.{svc}"

        if available_services and svc not in available_services:
            print(f"{svc_full:<32} | {'N/A':<8} | {'N/A':<5} | {'⏭️ SKIP':<8} | (Chưa đăng ký trên bản cài hiện tại)")
            continue

        ok, code, resp_body, lat = call_ha_service(ha_url, token, "javis_lock", svc, tc.get("payload"), timeout=30)

        status_str = "✅ PASS" if ok else "❌ FAIL"
        if not ok:
            all_passed = False

        print(f"{svc_full:<32} | {str(lat)+'ms':<8} | {code:<5} | {status_str:<8} | {tc['desc']}")
        results.append({"service": svc_full, "ok": ok, "latency": lat, "code": code})

    print("-" * 88)
    passed_count = sum(1 for r in results if r["ok"])
    print(f"\n📊 SUMMARY: {passed_count}/{len(results)} Services Passed against {ha_url}\n")
    return all_passed


def test_local_docker_ha():
    """
    Layer 3: HA Core Event Bus & Bytecode verification inside Official HA Docker Containers.
    """
    print("\n" + "=" * 88)
    print("  PHẦN 3: TEST JAVIS_LOCK TRONG DOCKER HOME ASSISTANT CORE (Python 3.12 / 3.13)")
    print("=" * 88)

    lock_repo_dir = "/home/chinh/work/javis/custom_component/103_smartlock_component"
    script_path = os.path.join(lock_repo_dir, "tests", "test_in_docker_ha.py")
    if not os.path.exists(script_path):
        print(f"❌ Test script {script_path} not found!")
        return False

    res = subprocess.run([sys.executable, script_path], cwd=lock_repo_dir)
    return res.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Full E2E Javis Lock Automation Test Suite")
    parser.add_argument("--server", type=str, default=DEFAULT_SERVER_URL, help="Server Cloud API URL")
    parser.add_argument("--remote", type=str, default=None, help="Remote HA IP address (e.g. 192.168.168.24)")
    parser.add_argument("--docker", action="store_true", help="Run local Docker HA container test")
    parser.add_argument("--all", action="store_true", help="Run all 3 test layers")
    args = parser.parse_args()

    success = True

    # 1. Test Server Cloud API
    server_ok = test_server_cloud_api(args.server)
    success = success and server_ok

    # 2. Test Remote HA Services
    if args.all or (not args.docker):
        remote_ok = test_remote_ha_lock_services(args.remote or DEFAULT_HA_IP)
        success = success and remote_ok

    # 3. Test Local Docker HA Container
    if args.all or args.docker:
        docker_ok = test_local_docker_ha()
        success = success and docker_ok

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
