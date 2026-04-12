import importlib.util
import os
import sys
import types
from datetime import datetime


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MAIN_CODE_DIR = os.path.join(BASE_DIR, "main_code", "2024")
PKG = "component_2024"


def clear_modules(prefix):
    for key in list(sys.modules.keys()):
        if key == prefix or key.startswith(prefix + "."):
            sys.modules.pop(key, None)


def install_package_root():
    pkg = types.ModuleType(PKG)
    pkg.__path__ = [MAIN_CODE_DIR]
    sys.modules[PKG] = pkg


def load_module(module_name, relative_path):
    full_name = f"{PKG}.{module_name}"
    file_path = os.path.join(MAIN_CODE_DIR, relative_path)
    spec = importlib.util.spec_from_file_location(full_name, file_path)
    module = importlib.util.module_from_spec(spec)
    module.__package__ = PKG
    sys.modules[full_name] = module
    spec.loader.exec_module(module)
    return module


def stub_voluptuous():
    vol = types.ModuleType("voluptuous")
    vol.Required = lambda x, **kwargs: x
    vol.Optional = lambda x, **kwargs: x
    vol.Schema = lambda x: x
    vol.In = lambda choices: (lambda value: value)
    sys.modules["voluptuous"] = vol


def stub_homeassistant_minimal():
    ha = types.ModuleType("homeassistant")
    sys.modules["homeassistant"] = ha

    ha_const = types.ModuleType("homeassistant.const")
    ha_const.ATTR_ENTITY_ID = "entity_id"
    ha_const.CONF_ENABLED = "enabled"
    ha_const.CONF_PASSWORD = "password"
    ha_const.CONF_USERNAME = "username"
    ha_const.CONF_URL = "url"
    ha_const.WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    sys.modules["homeassistant.const"] = ha_const

    ha_core = types.ModuleType("homeassistant.core")

    class HomeAssistant:
        pass

    class ServiceCall:
        def __init__(self, data):
            self.data = data

    class SupportsResponse:
        OPTIONAL = "optional"
        NONE = "none"

    def callback(func):
        return func

    ha_core.HomeAssistant = HomeAssistant
    ha_core.ServiceCall = ServiceCall
    ha_core.ServiceResponse = dict
    ha_core.SupportsResponse = SupportsResponse
    ha_core.callback = callback
    ha_core.Event = object
    sys.modules["homeassistant.core"] = ha_core

    ha_helpers = types.ModuleType("homeassistant.helpers")
    sys.modules["homeassistant.helpers"] = ha_helpers

    ha_cv = types.ModuleType("homeassistant.helpers.config_validation")
    ha_cv.entity_ids = lambda x: x
    ha_cv.string = str
    ha_cv.datetime = datetime
    sys.modules["homeassistant.helpers.config_validation"] = ha_cv

    ha_issue = types.ModuleType("homeassistant.helpers.issue_registry")

    class _IssueSeverity:
        ERROR = "error"

    ha_issue.IssueSeverity = _IssueSeverity
    ha_issue.async_create_issue = lambda *args, **kwargs: None
    sys.modules["homeassistant.helpers.issue_registry"] = ha_issue

    ha_dispatcher = types.ModuleType("homeassistant.helpers.dispatcher")
    ha_dispatcher.async_dispatcher_connect = lambda *args, **kwargs: None
    sys.modules["homeassistant.helpers.dispatcher"] = ha_dispatcher

    ha_entity = types.ModuleType("homeassistant.helpers.entity")

    class DeviceInfo(dict):
        pass

    class Entity:
        pass

    ha_entity.DeviceInfo = DeviceInfo
    ha_entity.Entity = Entity
    sys.modules["homeassistant.helpers.entity"] = ha_entity

    ha_update = types.ModuleType("homeassistant.helpers.update_coordinator")

    class DataUpdateCoordinator:
        def __class_getitem__(cls, _item):
            return cls

        def __init__(self, *args, **kwargs):
            self.hass = args[0] if args else None
            self.data = None
            self._listeners = {}

        def async_update_listeners(self):
            return None

        def async_set_updated_data(self, data):
            self.data = data

    class UpdateFailed(Exception):
        pass

    class CoordinatorEntity:
        def __class_getitem__(cls, _item):
            return cls

        def __init__(self, coordinator):
            self.coordinator = coordinator
            self._write_called = False

        def async_write_ha_state(self):
            self._write_called = True

    ha_update.DataUpdateCoordinator = DataUpdateCoordinator
    ha_update.UpdateFailed = UpdateFailed
    ha_update.CoordinatorEntity = CoordinatorEntity
    sys.modules["homeassistant.helpers.update_coordinator"] = ha_update

    ha_components = types.ModuleType("homeassistant.components")
    sys.modules["homeassistant.components"] = ha_components

    ha_pn = types.ModuleType("homeassistant.components.persistent_notification")
    ha_pn.async_create = lambda *args, **kwargs: None
    sys.modules["homeassistant.components.persistent_notification"] = ha_pn

    ha_config_entries = types.ModuleType("homeassistant.config_entries")

    class ConfigFlow:
        def __init_subclass__(cls, **kwargs):
            return

        async def async_set_unique_id(self, unique_id):
            self._unique_id = unique_id

        def _abort_if_unique_id_configured(self):
            if getattr(self, "_force_abort", False):
                raise RuntimeError("already configured")

        def async_create_entry(self, title, data):
            return {"type": "create_entry", "title": title, "data": data}

        def async_show_form(
            self, step_id, data_schema, errors, description_placeholders
        ):
            return {
                "type": "form",
                "step_id": step_id,
                "data_schema": data_schema,
                "errors": errors,
                "description_placeholders": description_placeholders,
            }

    class ConfigEntry:
        pass

    ha_config_entries.ConfigFlow = ConfigFlow
    ha_config_entries.ConfigEntry = ConfigEntry
    sys.modules["homeassistant.config_entries"] = ha_config_entries

    ha_util = types.ModuleType("homeassistant.util")
    sys.modules["homeassistant.util"] = ha_util

    ha_dt = types.ModuleType("homeassistant.util.dt")
    ha_dt.as_utc = lambda dt_value: dt_value
    ha_dt.now = lambda: datetime.now()
    ha_dt.as_local = lambda dt_value: dt_value
    ha_dt.utc_from_timestamp = lambda value: datetime.fromtimestamp(value)
    sys.modules["homeassistant.util.dt"] = ha_dt


def stub_component_modules_for_services():
    const = types.ModuleType(f"{PKG}.const")
    const.CONF_ALL_DAY = "all_day"
    const.CONF_AUTO_UNLOCK = "auto_unlock"
    const.CONF_END_TIME = "end_time"
    const.CONF_START_TIME = "start_time"
    const.CONF_WEEK_DAYS = "days"
    const.DOMAIN = "javis_lock"
    const.SVC_CLEANUP_PASSCODES = "cleanup_passcodes"
    const.SVC_CONFIG_PASSAGE_MODE = "configure_passage_mode"
    const.SVC_CREATE_PASSCODE = "create_passcode"
    const.SVC_LIST_PASSCODES = "list_passcodes"
    const.SVC_LIST_UNLOCK_RECORDS = "list_unlock_records"
    const.SVC_DELETE_PASSCODE = "delete_passcode"
    const.SVC_CHANGE_PASSCODE = "change_passcode"
    const.SVC_UPDATE_LOCK = "update_lock"
    sys.modules[f"{PKG}.const"] = const

    coordinator = types.ModuleType(f"{PKG}.coordinator")

    class LockUpdateCoordinator:
        pass

    coordinator.LockUpdateCoordinator = LockUpdateCoordinator
    coordinator.coordinator_for = lambda hass, entity_id: None
    sys.modules[f"{PKG}.coordinator"] = coordinator

    models = types.ModuleType(f"{PKG}.models")

    class AddPasscodeConfig:
        def __init__(self, **kwargs):
            self.type = kwargs.get("type")
            self.passcode_name = kwargs.get("passcodeName")
            self.start_minute = kwargs.get("startDate", 0)
            self.end_minute = kwargs.get("endDate", 0)

    class OnOff:
        on = 1
        off = 2

    class PassageModeConfig:
        pass

    models.AddPasscodeConfig = AddPasscodeConfig
    models.OnOff = OnOff
    models.PassageModeConfig = PassageModeConfig
    sys.modules[f"{PKG}.models"] = models


def stub_component_modules_for_config_flow():
    const = types.ModuleType(f"{PKG}.const")
    const.DOMAIN = "javis_lock"
    sys.modules[f"{PKG}.const"] = const

    api = types.ModuleType(f"{PKG}.api")
    api.AUTH_SCHEMA = {"dummy": "schema"}

    async def login(*args, **kwargs):
        return {"is_success": True, "error": ""}

    api.login = login
    sys.modules[f"{PKG}.api"] = api


def stub_component_modules_for_coordinator():
    const = types.ModuleType(f"{PKG}.const")
    const.DOMAIN = "javis_lock"
    const.SIGNAL_NEW_DATA = "signal_new_data"
    const.TT_LOCKS = "locks"
    sys.modules[f"{PKG}.const"] = const

    api = types.ModuleType(f"{PKG}.api")

    class TTLockApi:
        pass

    class ComponentOutdatedError(Exception):
        pass

    api.TTLockApi = TTLockApi
    api.ComponentOutdatedError = ComponentOutdatedError
    sys.modules[f"{PKG}.api"] = api

    models = types.ModuleType(f"{PKG}.models")

    class Features:
        @classmethod
        def from_feature_value(cls, _value):
            return cls()

    class PassageModeConfig:
        pass

    class State:
        locked = 0
        unlocked = 1

    class WebhookEvent:
        pass

    models.Features = Features
    models.PassageModeConfig = PassageModeConfig
    models.State = State
    models.WebhookEvent = WebhookEvent
    sys.modules[f"{PKG}.models"] = models


def stub_aiohttp_retry():
    module = types.ModuleType("aiohttp_retry")

    class ExponentialRetry:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class RetryClient:
        def __init__(self, websession, retry_options=None, raise_for_status=False):
            self.websession = websession
            self.retry_options = retry_options
            self.raise_for_status = raise_for_status

        def get(self, *args, **kwargs):
            return self.websession.get(*args, **kwargs)

    module.ExponentialRetry = ExponentialRetry
    module.RetryClient = RetryClient
    sys.modules["aiohttp_retry"] = module
