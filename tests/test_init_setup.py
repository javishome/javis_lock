"""Script tests for __init__ setup and webhook logic.

Run: python tests/test_init_setup.py
"""

import asyncio
import json
import sys
import types
from types import SimpleNamespace

from _component_test_stubs import PKG, clear_modules, install_package_root, load_module


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


def check_true(test_name, condition):
    global tests_run, tests_failed
    tests_run += 1
    if condition:
        print(f"  PASS: {test_name}")
    else:
        tests_failed += 1
        print(f"  FAIL: {test_name}")


def _install_homeassistant_stubs():
    ha = types.ModuleType("homeassistant")
    sys.modules["homeassistant"] = ha

    components = types.ModuleType("homeassistant.components")
    sys.modules["homeassistant.components"] = components

    cloud = types.ModuleType("homeassistant.components.cloud")
    cloud.async_active_subscription = lambda hass: False

    async def async_create_cloudhook(hass, webhook_id):
        return f"https://cloud/{webhook_id}"

    cloud.async_create_cloudhook = async_create_cloudhook
    cloud.CloudNotConnected = RuntimeError
    sys.modules["homeassistant.components.cloud"] = cloud

    persistent_notification = types.ModuleType(
        "homeassistant.components.persistent_notification"
    )
    persistent_notification.calls = []
    persistent_notification.dismiss_calls = []
    persistent_notification.async_create = (
        lambda *args, **kwargs: persistent_notification.calls.append((args, kwargs))
    )
    persistent_notification.async_dismiss = (
        lambda *args, **kwargs: persistent_notification.dismiss_calls.append(
            (args, kwargs)
        )
    )
    sys.modules["homeassistant.components.persistent_notification"] = (
        persistent_notification
    )

    webhook = types.ModuleType("homeassistant.components.webhook")
    webhook.registered = []
    webhook.unregistered = []
    webhook.async_generate_url = lambda hass, wid: f"https://ha/api/webhook/{wid}"
    webhook.async_register = lambda *args, **kwargs: webhook.registered.append(
        (args, kwargs)
    )
    webhook.async_unregister = lambda *args, **kwargs: webhook.unregistered.append(
        (args, kwargs)
    )
    sys.modules["homeassistant.components.webhook"] = webhook

    config_entries = types.ModuleType("homeassistant.config_entries")

    class ConfigEntry:
        def __init__(self, entry_id, data):
            self.entry_id = entry_id
            self.data = data

    config_entries.ConfigEntry = ConfigEntry
    sys.modules["homeassistant.config_entries"] = config_entries

    const = types.ModuleType("homeassistant.const")
    const.CONF_WEBHOOK_ID = "webhook_id"
    const.EVENT_HOMEASSISTANT_STARTED = "started"
    const.EVENT_HOMEASSISTANT_STOP = "stop"
    const.__version__ = "2024.12.0"

    class Platform:
        LOCK = "lock"
        SENSOR = "sensor"
        BINARY_SENSOR = "binary_sensor"

    const.Platform = Platform
    sys.modules["homeassistant.const"] = const

    core = types.ModuleType("homeassistant.core")

    class CoreState:
        running = "running"

    core.CoreState = CoreState
    core.Event = object
    core.HomeAssistant = object
    sys.modules["homeassistant.core"] = core

    helpers = types.ModuleType("homeassistant.helpers")
    sys.modules["homeassistant.helpers"] = helpers

    aiohttp_client = types.ModuleType("homeassistant.helpers.aiohttp_client")
    aiohttp_client.async_get_clientsession = lambda hass: hass._session
    sys.modules["homeassistant.helpers.aiohttp_client"] = aiohttp_client

    config_entry_oauth2_flow = types.ModuleType(
        "homeassistant.helpers.config_entry_oauth2_flow"
    )
    sys.modules["homeassistant.helpers.config_entry_oauth2_flow"] = (
        config_entry_oauth2_flow
    )

    issue_registry = types.ModuleType("homeassistant.helpers.issue_registry")
    issue_registry.created = []
    issue_registry.deleted = []

    class IssueSeverity:
        ERROR = "error"

    issue_registry.IssueSeverity = IssueSeverity
    issue_registry.async_create_issue = (
        lambda *args, **kwargs: issue_registry.created.append((args, kwargs))
    )
    issue_registry.async_delete_issue = (
        lambda *args, **kwargs: issue_registry.deleted.append((args, kwargs))
    )
    sys.modules["homeassistant.helpers.issue_registry"] = issue_registry

    dispatcher = types.ModuleType("homeassistant.helpers.dispatcher")
    dispatcher.sent = []
    dispatcher.async_dispatcher_send = lambda *args: dispatcher.sent.append(args)
    sys.modules["homeassistant.helpers.dispatcher"] = dispatcher

    network = types.ModuleType("homeassistant.helpers.network")

    class NoURLAvailableError(Exception):
        pass

    network.NoURLAvailableError = NoURLAvailableError
    sys.modules["homeassistant.helpers.network"] = network


def _install_component_stubs():
    api = types.ModuleType(f"{PKG}.api")

    class ComponentOutdatedError(Exception):
        pass

    class TTLockApi:
        def __init__(self, hass, session, username, password, url):
            self.url = url

        async def get_locks(self):
            return [101]

    api.ComponentOutdatedError = ComponentOutdatedError
    api.TTLockApi = TTLockApi
    sys.modules[f"{PKG}.api"] = api

    const = types.ModuleType(f"{PKG}.const")
    const.CONF_WEBHOOK_STATUS = "webhook_status"
    const.CONF_WEBHOOK_URL = "webhook_url"
    const.COMPONENT_VERSION = "v1"
    const.DOMAIN = "javis_lock"
    const.SIGNAL_NEW_DATA = "signal_new"
    const.TT_API = "api"
    const.TT_LOCKS = "locks"
    const.SERVER_URL = "https://api.test"
    sys.modules[f"{PKG}.const"] = const

    coordinator = types.ModuleType(f"{PKG}.coordinator")

    class LockUpdateCoordinator:
        def __init__(self, hass, client, lock_id):
            self.hass = hass
            self.lock_id = lock_id

        async def async_config_entry_first_refresh(self):
            return None

    coordinator.LockUpdateCoordinator = LockUpdateCoordinator
    sys.modules[f"{PKG}.coordinator"] = coordinator

    models = types.ModuleType(f"{PKG}.models")

    class WebhookEvent:
        @classmethod
        def parse_obj(cls, obj):
            return SimpleNamespace(**obj)

    models.WebhookEvent = WebhookEvent
    sys.modules[f"{PKG}.models"] = models

    services = types.ModuleType(f"{PKG}.services")

    class Services:
        last_register = None

        def __init__(self, hass):
            self.hass = hass

        def register_new(self):
            Services.last_register = "new"

        def register_old(self):
            Services.last_register = "old"

    services.Services = Services
    sys.modules[f"{PKG}.services"] = services


class FakeConfigEntries:
    def __init__(self):
        self.updated = []
        self.forwarded = []
        self.unloaded = []

    async def async_forward_entry_setups(self, entry, platforms):
        self.forwarded.append((entry.entry_id, tuple(platforms)))

    async def async_unload_platforms(self, entry, platforms):
        self.unloaded.append((entry.entry_id, tuple(platforms)))
        return True

    def async_update_entry(self, entry, data=None):
        entry.data = data
        self.updated.append((entry.entry_id, data))


class FakeBus:
    def __init__(self):
        self.once_calls = []

    def async_listen_once(self, event, cb):
        self.once_calls.append((event, cb))


class FakeSession:
    def __init__(self):
        self.posts = []

    def post(self, url, json=None, headers=None):
        self.posts.append({"url": url, "json": json, "headers": headers})

        class _CM:
            async def __aenter__(self_inner):
                return SimpleNamespace(status=200, text=lambda: "ok")

            async def __aexit__(self_inner, exc_type, exc, tb):
                return False

        return _CM()


async def _run_async_tests(mod):
    services_cls = sys.modules[f"{PKG}.services"].Services
    mod.is_new_version = lambda: True
    mod.setup(SimpleNamespace(), SimpleNamespace())
    check(
        "setup registers new services on new version", services_cls.last_register, "new"
    )

    mod.is_new_version = lambda: False
    mod.setup(SimpleNamespace(), SimpleNamespace())
    check(
        "setup registers old services on old version", services_cls.last_register, "old"
    )

    hass = SimpleNamespace(
        state="running",
        data={},
        bus=FakeBus(),
        config_entries=FakeConfigEntries(),
        _session=FakeSession(),
    )
    entry = SimpleNamespace(
        entry_id="entry-1", data={"username": "u", "password": "p", "url": "x"}
    )

    async def fake_setup(self):
        return None

    original_setup = mod.WebhookHandler.setup
    mod.WebhookHandler.setup = fake_setup
    ok = await mod.async_setup_entry(hass, entry)
    mod.WebhookHandler.setup = original_setup
    check("async_setup_entry returns True on success", ok, True)
    check_true(
        "hass data includes domain entry",
        "javis_lock" in hass.data and "entry-1" in hass.data["javis_lock"],
    )
    check_true("platform forwarding called", len(hass.config_entries.forwarded) == 1)

    webhook_handler = mod.WebhookHandler(
        hass,
        SimpleNamespace(entry_id="entry-2", data={"url": "x", "webhook_id": "wid"}),
        client=SimpleNamespace(),
        url="https://api.test",
        lock_ids=[1, 2],
    )

    class FakeRequest:
        async def post(self):
            class _PostData(dict):
                def getall(self, key, default=None):
                    value = self.get(key, default if default is not None else [])
                    return value if isinstance(value, list) else [value]

            return _PostData(
                {
                    "records": [
                        json.dumps(
                            [
                                {
                                    "lockId": 1,
                                    "lockMac": "AA",
                                    "electricQuantity": 90,
                                    "serverDate": 1710000000000,
                                    "lockDate": 1710000000000,
                                    "recordType": 1,
                                    "username": "user1",
                                    "success": 1,
                                }
                            ]
                        )
                    ]
                }
            )

        async def text(self):
            return ""

    await webhook_handler.handle_webhook(hass, "wid", FakeRequest())
    dispatcher = sys.modules["homeassistant.helpers.dispatcher"]
    check_true("webhook dispatches event", len(dispatcher.sent) >= 1)

    # async_unload_entry happy path
    unload_ok = await mod.async_unload_entry(hass, entry)
    check("async_unload_entry returns True", unload_ok, True)
    check_true(
        "async_unload_entry removes entry data",
        "entry-1" not in hass.data.get("javis_lock", {}),
    )

    # setup() branch when HA is not running yet
    waiting_hass = SimpleNamespace(
        state="starting",
        bus=FakeBus(),
        config_entries=FakeConfigEntries(),
        data={},
        _session=FakeSession(),
    )
    waiting_handler = mod.WebhookHandler(
        waiting_hass,
        SimpleNamespace(entry_id="entry-3", data={"url": "x", "webhook_id": "wid3"}),
        client=SimpleNamespace(),
        url="https://api.test",
        lock_ids=[99],
    )
    await waiting_handler.setup()
    check_true(
        "setup registers startup listener when not running",
        len(waiting_hass.bus.once_calls) == 1,
    )

    # register_webhook handles NoURLAvailableError by creating issue
    issue_registry = sys.modules["homeassistant.helpers.issue_registry"]
    issue_registry.created.clear()
    no_url_hass = SimpleNamespace(
        state="running",
        bus=FakeBus(),
        config_entries=FakeConfigEntries(),
        data={},
        _session=FakeSession(),
    )
    no_url_entry = SimpleNamespace(
        entry_id="entry-4", data={"url": "x", "webhook_id": "wid4"}
    )
    no_url_handler = mod.WebhookHandler(
        no_url_hass,
        no_url_entry,
        client=SimpleNamespace(),
        url="https://api.test",
        lock_ids=[55],
    )
    no_url_error = sys.modules["homeassistant.helpers.network"].NoURLAvailableError

    async def raise_no_url():
        raise no_url_error("no base url")

    no_url_handler.get_url = raise_no_url
    await no_url_handler.register_webhook()
    check_true(
        "register_webhook creates issue on NoURLAvailableError",
        len(issue_registry.created) >= 1,
    )

    # async_setup_entry returns False when no lock is returned
    class NoLocksApi:
        def __init__(self, hass, session, username, password, url):
            pass

        async def get_locks(self):
            return []

    old_api = mod.TTLockApi
    mod.TTLockApi = NoLocksApi
    no_lock_hass = SimpleNamespace(
        state="running",
        data={},
        bus=FakeBus(),
        config_entries=FakeConfigEntries(),
        _session=FakeSession(),
    )
    no_lock_entry = SimpleNamespace(
        entry_id="entry-5", data={"username": "u", "password": "p", "url": "x"}
    )
    no_lock_ok = await mod.async_setup_entry(no_lock_hass, no_lock_entry)
    check("async_setup_entry returns False when no locks", no_lock_ok, False)

    # async_setup_entry handles ComponentOutdatedError and notifies
    class OutdatedApi:
        def __init__(self, hass, session, username, password, url):
            pass

        async def get_locks(self):
            raise mod.ComponentOutdatedError("outdated")

    mod.TTLockApi = OutdatedApi
    pn = sys.modules["homeassistant.components.persistent_notification"]
    pn.calls.clear()
    outdated_hass = SimpleNamespace(
        state="running",
        data={},
        bus=FakeBus(),
        config_entries=FakeConfigEntries(),
        _session=FakeSession(),
    )
    outdated_entry = SimpleNamespace(
        entry_id="entry-6", data={"username": "u", "password": "p", "url": "x"}
    )
    outdated_ok = await mod.async_setup_entry(outdated_hass, outdated_entry)
    check("async_setup_entry returns False when outdated", outdated_ok, False)
    check_true("outdated path creates persistent notification", len(pn.calls) >= 1)

    mod.TTLockApi = old_api


def main():
    print("\n" + "=" * 64)
    print("TEST INIT SETUP")
    print("=" * 64)

    clear_modules(PKG)
    install_package_root()
    _install_homeassistant_stubs()
    _install_component_stubs()

    mod = load_module("__init__", "__init__.py")
    asyncio.run(_run_async_tests(mod))

    print("\n" + "=" * 64)
    if tests_failed == 0:
        print(f"ALL {tests_run} TESTS PASSED")
    else:
        print(f"FAILED: {tests_failed}/{tests_run}")
    print("=" * 64 + "\n")
    raise SystemExit(0 if tests_failed == 0 else 1)


if __name__ == "__main__":
    main()
