"""Real Home Assistant Docker Integration Test Runner.

Pulls official Home Assistant Core Docker images and runs:
1. Real HA Component Loader (async_get_integration & async_get_component)
2. Real HA Service Registration on Core Event Bus (comp.setup & hass.services)
3. Real HA Config Check CLI (hass --script check_config)
4. Module Reload Idempotency in Real HA Container

Supports:
- HA 2024.4.4 (ghcr.io/home-assistant/home-assistant:2024.4.4) -> build/2024_4_4
- HA 2024.12.4 (ghcr.io/home-assistant/home-assistant:2024.12.4) -> build/2024_12_4

Usage:
    python tests/test_in_docker_ha.py
"""

import os
import shutil
import subprocess
import sys
import tempfile

DOMAIN = "javis_lock"
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BUILD_2024_4_4 = os.path.join(BASE_DIR, "build", "2024_4_4")
BUILD_2024_12_4 = os.path.join(BASE_DIR, "build", "2024_12_4")

TARGETS = [
    {
        "version": "2024.4.4",
        "image": "ghcr.io/home-assistant/home-assistant:2024.4.4",
        "build_dir": BUILD_2024_4_4,
    },
    {
        "version": "2024.12.4",
        "image": "ghcr.io/home-assistant/home-assistant:2024.12.4",
        "build_dir": BUILD_2024_12_4,
    },
]


def check_docker_available():
    try:
        res = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=10)
        return res.returncode == 0
    except Exception:
        return False


LOADER_SCRIPT = """
import asyncio
import sys
import importlib
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration, async_setup

async def main():
    hass = HomeAssistant("/config")
    async_setup(hass)
    domain = sys.argv[1]
    
    # 1. Integration Loader
    try:
        integration = await async_get_integration(hass, domain)
        print(f"  PASS: Found integration {domain} (manifest version: {integration.version})")
    except Exception as e:
        print(f"  FAIL: async_get_integration raised: {e}")
        sys.exit(1)

    # 2. Component Loading & Service Registration
    try:
        comp = await integration.async_get_component()
        if comp is None:
            print("  FAIL: async_get_component returned None")
            sys.exit(1)
        print(f"  PASS: async_get_component loaded successfully: {comp}")

        # Execute component setup to register domain services
        comp.setup(hass, {})
        services = list(hass.services.async_services().get(domain, {}).keys())
        print(f"  PASS: Registered {len(services)} services for {domain} in HA Core: {services}")
        if not services:
            print(f"  FAIL: No services registered for {domain}")
            sys.exit(1)
    except Exception as e:
        print(f"  FAIL: Component setup/services raised: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 3. Reload Idempotency
    try:
        mod = importlib.import_module(f"custom_components.{domain}")
        importlib.reload(mod)
        print("  PASS: Module reload idempotency verified in real HA container!")
    except Exception as e:
        print(f"  FAIL: Module reload raised: {e}")
        sys.exit(1)
    
    import os
    os._exit(0)

if __name__ == "__main__":
    asyncio.run(main())
"""


def run_container_test(target):
    version = target["version"]
    image = target["image"]
    build_dir = target["build_dir"]

    print(f"\n=======================================================")
    print(f"  RUNNING TEST IN REAL HA CONTAINER: {version}")
    print(f"  Image: {image}")
    print(f"  Build Directory: {build_dir}")
    print(f"=======================================================")

    if not os.path.exists(build_dir):
        print(f"  FAIL: Build directory {build_dir} does not exist. Run auto_encode.py first!")
        return False

    ver_tag = version.replace(".", "_")
    temp_dir = tempfile.mkdtemp(prefix=f"ha_test_javis_lock_{ver_tag}_")
    try:
        custom_components_dir = os.path.join(temp_dir, "custom_components", DOMAIN)
        os.makedirs(os.path.dirname(custom_components_dir), exist_ok=True)
        shutil.copytree(build_dir, custom_components_dir)

        # Create basic configuration.yaml
        config_yaml_path = os.path.join(temp_dir, "configuration.yaml")
        with open(config_yaml_path, "w", encoding="utf-8") as f:
            f.write(f"default_config:\n\njavis_lock:\n")

        # Create test_loader.py in temp_dir
        loader_path = os.path.join(temp_dir, "test_loader.py")
        with open(loader_path, "w", encoding="utf-8") as f:
            f.write(LOADER_SCRIPT)

        # 1. Pull docker image if needed
        print(f"[*] Ensuring Docker image {image} is available...")
        pull_proc = subprocess.run(["docker", "pull", image], timeout=600)
        if pull_proc.returncode != 0:
            print(f"  FAIL: Failed to pull image {image}")
            return False

        # 2. Run Real HA Component Loader Test in container
        print("[*] Executing HA Loader, Service Registry & Validator tests in container...")
        cmd = [
            "docker", "run", "--rm", "--entrypoint", "python3",
            "-v", f"{temp_dir}:/config",
            image,
            "/config/test_loader.py", DOMAIN,
        ]
        test_proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        print(test_proc.stdout)
        if test_proc.returncode != 0:
            print(test_proc.stderr)
            print(f"  FAIL: HA {version} loader test failed with exit code {test_proc.returncode}")
            return False

        # 3. Run check_config
        print("[*] Running hass --script check_config inside container...")
        check_cmd = [
            "docker", "run", "--rm", "--entrypoint", "hass",
            "-v", f"{temp_dir}:/config",
            image,
            "--config", "/config", "--script", "check_config",
        ]
        check_proc = subprocess.run(check_cmd, capture_output=True, text=True, timeout=120)
        if check_proc.returncode == 0:
            print("  PASS: hass check_config passed!")
        else:
            print(check_proc.stdout)
            print(check_proc.stderr)
            print(f"  FAIL: check_config exited with code {check_proc.returncode}")
            return False

        print(f"  >>> ALL REAL DOCKER TESTS PASSED FOR HA {version}!")
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    print("\n" + "=" * 64)
    print("OFFICIAL HOME ASSISTANT DOCKER TEST RUNNER")
    print("=" * 64)

    if not check_docker_available():
        print("ERROR: Docker daemon is not accessible. Please start Docker first!")
        sys.exit(1)

    results = {}
    for target in TARGETS:
        results[target["version"]] = run_container_test(target)

    print("\n" + "=" * 64)
    print("DOCKER TEST SUMMARY")
    print("=" * 64)
    all_passed = True
    for ver, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}  Home Assistant {ver}")
        if not passed:
            all_passed = False

    print("=" * 64 + "\n")
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
