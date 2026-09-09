#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Javis Lock - Universal Dynamic Encrypted Builder & 5-Milestone Architecture Validator
======================================================================================
Compiles javis_lock into a universal, bytecode-free distribution using:
- AST String Encryption
- Zlib Compression (Level 9)
- Rolling-XOR Byte Cipher
- Dynamic In-Memory Module Loader (compile -> exec on target host)
- Automated 5-Milestone Architecture Docker Matrix Validation (2024.4, 2024.6, 2024.12, 2025.6, 2025.12)
"""

import os
import sys
import json
import shutil
import base64
import zlib
import ast
import time
import tempfile
import subprocess
from datetime import date

DOMAIN = "javis_lock"
MASTER_KEY = b"javis_universal_dynamic_loader_2026_"

TEST_IMAGES = [
    ("HA 2024.4.4 (Python 3.12 - Pre-Thread-Safety)", "ghcr.io/home-assistant/home-assistant:2024.4.4"),
    ("HA 2024.6.4 (Python 3.12 - Thread-Safety Fatal Enforcement)", "ghcr.io/home-assistant/home-assistant:2024.6.4"),
    ("HA 2024.12.4 (Python 3.13 - Modern Async & Blocking I/O)", "ghcr.io/home-assistant/home-assistant:2024.12.4"),
    ("HA 2025.6.3 (Python 3.13 - Strict Services Schema & Webhook)", "ghcr.io/home-assistant/home-assistant:2025.6.3"),
    ("HA 2025.12.3 (Python 3.13 - Modern Clean Baseline)", "ghcr.io/home-assistant/home-assistant:2025.12.3"),
]

DEEP_TEST_SCRIPT = r"""
import asyncio
import sys
import importlib
from types import SimpleNamespace
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_setup as async_setup_loader, async_get_integration
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.setup import async_setup_component

async def init_env(hass):
    for comp in ['network', 'http', 'zeroconf']:
        try:
            await async_setup_component(hass, comp, {})
        except Exception:
            pass

async def test():
    domain = 'javis_lock'
    hass = HomeAssistant('/config')
    async_setup_loader(hass)
    await init_env(hass)
    
    # 1. Integration Loader
    integration = await async_get_integration(hass, domain)
    manifest = integration.manifest
    print(f'  [1] PASS: Integration loaded: {domain}, version={manifest.get("version")}')
    
    # 2. Dynamic Memory Component
    comp = await integration.async_get_component()
    print(f'  [2] PASS: Component loaded in RAM: {comp}')
    
    # 3. Async Setup & Services Registration
    res = await comp.async_setup(hass, {})
    assert res is True, 'async_setup returned False'
    services = list(hass.services.async_services().get(domain, {}).keys())
    print(f'  [3] PASS: async_setup registered {len(services)} services: {services}')
    assert len(services) >= 7, f'Expected at least 7 services, got {services}'
    
    # 4. Mock ConfigEntry Setup & Network Resilience
    entry = SimpleNamespace(
        entry_id='mock_test_entry',
        domain=domain,
        data={
            'username': 'test_user',
            'password': 'test_password',
            'url': 'unreachable-dns-test-12345.local',
            'webhook_id': 'test_webhook_id'
        },
        options={}
    )
    try:
        await comp.async_setup_entry(hass, entry)
        print('  [4] FAIL: async_setup_entry did not raise on network failure')
        sys.exit(1)
    except ConfigEntryNotReady as e:
        print(f'  [4] PASS: async_setup_entry raised ConfigEntryNotReady: {e}')
    except Exception as e:
        print(f'  [4] FAIL: unexpected exception: {type(e)} {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    # 5. Reload idempotency
    mod = importlib.import_module(f'custom_components.{domain}')
    importlib.reload(mod)
    print(f'  [5] PASS: Module reload idempotency verified')
    
    import os
    os._exit(0)

if __name__ == '__main__':
    asyncio.run(test())
"""


class StringEncryptor(ast.NodeTransformer):
    """Encrypts string constants in the AST into runtime XOR decryptions."""
    def __init__(self, key: int = 0x5A):
        super().__init__()
        self.key = key
        self.in_joined_str = False

    def visit_JoinedStr(self, node: ast.JoinedStr) -> ast.AST:
        old_val = self.in_joined_str
        self.in_joined_str = True
        self.generic_visit(node)
        self.in_joined_str = old_val
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        if self.in_joined_str:
            return node
        if isinstance(node.value, str) and len(node.value) > 2 and not node.value.startswith("__"):
            encoded_bytes = bytes(b ^ self.key for b in node.value.encode("utf-8"))
            return ast.Call(
                func=ast.Name(id="_D", ctx=ast.Load()),
                args=[ast.Constant(value=encoded_bytes), ast.Constant(value=self.key)],
                keywords=[],
            )
        return node


def obfuscate_python_source(source_code: str, xor_key: int = 0x5A) -> str:
    """Preserves __future__ imports and encrypts strings via AST."""
    lines = source_code.splitlines()
    future_imports = []
    other_lines = []
    for line in lines:
        if line.strip().startswith("from __future__ import"):
            future_imports.append(line)
        else:
            other_lines.append(line)
            
    clean_src = "\n".join(other_lines)
    tree = ast.parse(clean_src)
    transformer = StringEncryptor(xor_key)
    transformed_tree = transformer.visit(tree)
    ast.fix_missing_locations(transformed_tree)
    
    obfuscated_src = ast.unparse(transformed_tree)
    decoder_header = "def _D(b, k):\n    return bytes(x ^ k for x in b).decode('utf-8', 'ignore')\n\n"
    prefix = "\n".join(future_imports) + ("\n" if future_imports else "")
    return prefix + decoder_header + obfuscated_src


def build_hardened_payload(source_code: str, master_key: bytes = MASTER_KEY) -> str:
    """Applies AST obfuscation + Zlib compression + Rolling XOR encryption."""
    obf_source = obfuscate_python_source(source_code)
    compressed = zlib.compress(obf_source.encode("utf-8"), level=9)
    
    key_len = len(master_key)
    encrypted = bytearray()
    prev = 0xAA
    for i, b in enumerate(compressed):
        k = master_key[i % key_len] ^ prev
        enc_b = b ^ k
        encrypted.append(enc_b)
        prev = enc_b
        
    encoded_str = base64.b85encode(bytes(encrypted)).decode("ascii")
    
    loader_code = f"""# -*- coding: utf-8 -*-
# Protected by Javis Universal Dynamic Encrypted Loader
import base64 as _b85, zlib as _zl
def _xload(_s, _k):
    _e = _b85.b85decode(_s)
    _o = bytearray()
    _p = 0xAA
    _kl = len(_k)
    for _i, _b in enumerate(_e):
        _o.append(_b ^ (_k[_i % _kl] ^ _p))
        _p = _b
    return _zl.decompress(bytes(_o))

_KEY = {master_key!r}
_PAYLOAD = "{encoded_str}"
exec(compile(_xload(_PAYLOAD, _KEY), __file__, "exec"), globals())
"""
    return loader_code


def build_universal_package(src_dir: str, dst_dir: str):
    """Packages main_code directory directly into build directory."""
    if os.path.exists(dst_dir):
        for item in os.listdir(dst_dir):
            item_path = os.path.join(dst_dir, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
    os.makedirs(dst_dir, exist_ok=True)
    
    for root, dirs, files in os.walk(src_dir):
        rel = os.path.relpath(root, src_dir)
        target_root = os.path.join(dst_dir, rel) if rel != "." else dst_dir
        os.makedirs(target_root, exist_ok=True)
        
        for file in files:
            src_file = os.path.join(root, file)
            dst_file = os.path.join(target_root, file)
            
            if file.endswith(".py") and file != "encode.py":
                with open(src_file, "r", encoding="utf-8") as f:
                    content = f.read()
                hardened_code = build_hardened_payload(content)
                with open(dst_file, "w", encoding="utf-8") as f:
                    f.write(hardened_code)
            elif not file.endswith(".pyc") and "__pycache__" not in root:
                shutil.copy2(src_file, dst_file)


def run_docker_validation(label: str, image: str, comp_dir: str) -> bool:
    """Runs automated 2-tier verification: Deep In-Memory Functional Lifecycle + Full Headless Boot."""
    temp_dir = tempfile.mkdtemp(prefix="test_docker_boot_")
    try:
        custom_dir = os.path.join(temp_dir, "custom_components", DOMAIN)
        shutil.copytree(comp_dir, custom_dir)
        with open(os.path.join(temp_dir, "test_runner.py"), "w", encoding="utf-8") as f:
            f.write(DEEP_TEST_SCRIPT.strip())
        with open(os.path.join(temp_dir, "configuration.yaml"), "w") as f:
            f.write(f"default_config:\n\n{DOMAIN}:\n")
            
        # Tier 1: Deep Functional In-Memory Lifecycle Test
        cmd_deep = ["docker", "run", "--rm", "--entrypoint", "python3", "-v", f"{temp_dir}:/config", image, "/config/test_runner.py"]
        res_deep = subprocess.run(cmd_deep, capture_output=True, text=True)
        if res_deep.returncode != 0:
            print(f"  ❌ Deep Functional Failure on {label}:")
            print(res_deep.stderr[:500] if res_deep.stderr else res_deep.stdout[:500])
            return False

        # Tier 2: Headless HA Boot Test (8s)
        cmd_boot = ["docker", "run", "-d", "--rm", "-v", f"{temp_dir}:/config", image, "hass", "--config", "/config"]
        cid = subprocess.check_output(cmd_boot, text=True).strip()
        time.sleep(8)
        logs = subprocess.run(["docker", "logs", cid], capture_output=True, text=True).stdout
        subprocess.run(["docker", "rm", "-f", cid], capture_output=True)
        
        errors = [l for l in logs.splitlines() if any(k in l for k in ("ERROR", "RuntimeError", "Traceback", "calls hass.services")) and DOMAIN in l]
        if errors:
            print(f"  ❌ Boot Errors on {label}:")
            for e in errors[:5]:
                print(f"     {e}")
            return False
            
        print(f"  ✅ PASS on {label}: 2/2 Tiers (Deep Lifecycle + Boot) OK!")
        return True
    except Exception as err:
        print(f"  ❌ Exception during Docker test on {label}: {err}")
        return False
    finally:
        subprocess.run(["docker", "run", "--rm", "-v", f"{temp_dir}:/clean", "alpine", "sh", "-c", "rm -rf /clean/* /clean/.* 2>/dev/null || true"], capture_output=True)
        shutil.rmtree(temp_dir, ignore_errors=True)


def _read_manifest_version(main_code_dir) -> str | None:
    manifest_path = os.path.join(main_code_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        return None
    with open(manifest_path, encoding="utf-8") as f:
        return str(json.load(f).get("version", "")).strip()


def _bump_version_tag(version: str) -> str:
    return f"v{date.today().strftime('%Y%m%d')}"


def _write_manifest_version(main_code_dir, version: str):
    manifest_path = os.path.join(main_code_dir, "manifest.json")
    with open(manifest_path, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data["version"] = version
        f.seek(0)
        json.dump(data, f, indent=4)
        f.write("\n")
        f.truncate()


def should_keep_current_version() -> bool:
    argv = getattr(sys, "argv", [])
    if "--non-interactive" in argv or "--auto-bump" in argv:
        return False
    if "-y" in argv or "--yes" in argv or "--keep-version" in argv:
        return True
    if not hasattr(sys.stdin, "isatty") or not sys.stdin.isatty():
        return True
    answer = input("Giữ version hiện tại? (y/N): ").strip().lower()
    return answer in ("y", "yes")


def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    main_code_dir = os.path.join(root_dir, "main_code")

    print("\n" + "=" * 64)
    print("JAVIS LOCK - UNIVERSAL DYNAMIC ENCRYPTED BUILDER")
    print("=" * 64)

    current_version = _read_manifest_version(main_code_dir)
    keep_version = should_keep_current_version()
    if keep_version:
        new_version = current_version
        print(f"Keeping current version: {new_version}")
    else:
        new_version = _bump_version_tag(current_version)
        _write_manifest_version(main_code_dir, new_version)
        print(f"Bumped version: {current_version} -> {new_version}")

    # Build universal distribution directly into build/
    build_dir = os.path.join(root_dir, "build")
    print(f"\n[1/2] Building Universal Dynamic Encrypted Component into build/...")
    build_universal_package(main_code_dir, build_dir)

    print(f"[2/2] Running Automated 5-Milestone Architecture Validation...")
    results = {}
    for label, image in TEST_IMAGES:
        results[label] = run_docker_validation(label, image, build_dir)

    all_passed = all(results.values())
    print("\n" + "=" * 64)
    print("5-MILESTONE ARCHITECTURE TEST SUMMARY")
    print("=" * 64)
    for label, ok in results.items():
        st = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {st} : {label}")
    print("=" * 64)

    if not all_passed:
        print("\n❌ BUILD FAILED: One or more Docker verification tests failed!")
        sys.exit(1)

    # Clean any __pycache__
    for root, dirs, _ in os.walk(build_dir):
        for d in list(dirs):
            if d == "__pycache__":
                shutil.rmtree(os.path.join(root, d), ignore_errors=True)

    print(f"\n🎉 ALL DONE! Version {new_version} built successfully in build/ and validated 100% across all 5 HA milestones!")

if __name__ == "__main__":
    main()
