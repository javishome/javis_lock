"""The TTLock integration."""

from __future__ import annotations

import asyncio
import json
import logging
import secrets

from aiohttp.web import Request
import yaml
from homeassistant.components import cloud, persistent_notification, webhook
from homeassistant.components.webhook import (
    async_register as webhook_register,
    async_unregister as webhook_unregister,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_WEBHOOK_ID,
    EVENT_HOMEASSISTANT_STARTED,
    EVENT_HOMEASSISTANT_STOP,
    Platform,
)
from homeassistant.core import CoreState, Event, HomeAssistant
from homeassistant.helpers import (
    aiohttp_client,
    config_entry_oauth2_flow,
    issue_registry as ir,
)
from homeassistant.const import __version__ as ha_version
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.network import NoURLAvailableError
from .api import TTLockApi, ComponentOutdatedError
from .const import (
    CONF_WEBHOOK_STATUS,
    CONF_WEBHOOK_URL,
    COMPONENT_VERSION,
    DOMAIN,
    SIGNAL_NEW_DATA,
    TT_API,
    TT_LOCKS,
    SERVER_URL,
)
from .coordinator import LockUpdateCoordinator
from .models import WebhookEvent
from .services import Services
import traceback

PLATFORMS: list[Platform] = [Platform.LOCK, Platform.SENSOR, Platform.BINARY_SENSOR]

_LOGGER = logging.getLogger(__name__)


async def get_mac():
    mac_decimal, source, mac_address = _get_mac_details()
    _LOGGER.info(
        "Resolved Home Controller MAC: decimal=%s mac=%s source=%s",
        mac_decimal,
        mac_address,
        source,
    )
    return mac_decimal


def _mac_to_decimal(mac_address):
    normalized = mac_address.strip().lower().replace(":", "").replace("-", "")
    if len(normalized) != 12:
        raise ValueError(f"Invalid MAC address length: {mac_address}")
    return int(normalized, 16)


def _read_interface_mac(interface):
    if not interface:
        return None
    try:
        with open(
            f"/sys/class/net/{interface}/address", "r", encoding="utf-8"
        ) as mac_file:
            return mac_file.read().strip()
    except Exception as e:
        _LOGGER.warning("Unable to read MAC address for interface %s: %s", interface, e)
        return None


def _get_mac_details():
    for interface in ("eth0", "end0"):
        mac = _read_interface_mac(interface)
        if not mac:
            continue
        source = f"sysfs:{interface}"
        try:
            return _mac_to_decimal(mac), source, mac
        except ValueError as e:
            _LOGGER.warning("Invalid MAC address from interface %s: %s", interface, e)

    raise RuntimeError("Unable to resolve MAC address from eth0 or end0")


async def refactor_webhook_url(webhook_url, mac, host):
    base_url = f"https://{mac}.{host}/api/webhook"
    new_webhook_url = base_url + webhook_url.split("/api/webhook")[1]
    return new_webhook_url


def server_url_for_entry(entry: ConfigEntry) -> str:
    if SERVER_URL == "https://improved-liger-tops.ngrok-free.app":
        return SERVER_URL
    return SERVER_URL + entry.data.get("url")


async def active_webhooks_payload(
    hass: HomeAssistant,
    mac,
    *,
    exclude_entry_id: str | None = None,
    extra_webhooks: list[dict] | None = None,
) -> list[dict]:
    payload = list(extra_webhooks or [])

    async_entries = getattr(hass.config_entries, "async_entries", None)
    if not async_entries:
        return payload

    for config_entry in async_entries(DOMAIN):
        if config_entry.entry_id == exclude_entry_id:
            continue

        entry_payload = hass.data.get(DOMAIN, {}).get(config_entry.entry_id)
        if not entry_payload:
            continue

        entry_data = getattr(config_entry, "data", {})
        webhook_url = entry_data.get(CONF_WEBHOOK_URL)
        host = entry_data.get("url")
        if not webhook_url or not host:
            continue

        coordinators = entry_payload.get(TT_LOCKS, [])
        payload.append(
            {
                "webhook_url": await refactor_webhook_url(webhook_url, mac, host),
                "lock_ids": [coordinator.lock_id for coordinator in coordinators],
            }
        )

    return payload


async def sync_webhooks_to_server(
    hass: HomeAssistant, server_url: str, mac, webhooks: list[dict]
) -> None:
    websession = aiohttp_client.async_get_clientsession(hass)
    try:
        async with websession.post(
            f"{server_url}/api/sync_webhooks",
            json={"mac": mac, "webhooks": webhooks},
            headers={"X-Component-Version": COMPONENT_VERSION},
        ) as response:
            if response.status == 200:
                _LOGGER.info(
                    "Webhook sync complete for mac=%s active_urls=%s",
                    mac,
                    len(webhooks),
                )
            else:
                _LOGGER.warning(
                    "Webhook sync failed: status=%s body=%s",
                    response.status,
                    await response.text(),
                )
    except Exception as err:
        _LOGGER.warning("Webhook sync failed: %s", err)


def is_new_version():
    year, version = ha_version.split(".")[:2]
    if int(year) >= 2024 and int(version) >= 7:
        return True
    return False


def setup(hass: HomeAssistant, config: ConfigEntry) -> bool:
    """Set up the TTLock component."""
    if is_new_version():
        Services(hass).register_new()
    else:
        Services(hass).register_old()

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    try:
        """Set up TTLock from a config entry."""
        username = entry.data.get("username")
        password = entry.data.get("password")
        url = server_url_for_entry(entry)

        _LOGGER.info(f"Setting up TTLock with url: {url}")
        client = TTLockApi(
            hass, aiohttp_client.async_get_clientsession(hass), username, password, url
        )

        lock_ids = await client.get_locks()
        if not lock_ids:
            _LOGGER.error("No locks found for this account")
            return False
        webhook_gen = WebhookHandler(hass, entry, client, url, lock_ids)
        await webhook_gen.setup()
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {TT_API: client}

        locks = [LockUpdateCoordinator(hass, client, lock_id) for lock_id in lock_ids]
        for coordinator in locks:
            try:
                await coordinator.async_config_entry_first_refresh()
            except Exception as e:
                _LOGGER.error(f"Lỗi khi cập nhật khóa {coordinator.lock_id}: {e}")
        # await asyncio.gather(
        #     *[coordinator.async_config_entry_first_refresh() for coordinator in locks]
        # )
        hass.data[DOMAIN][entry.entry_id][TT_LOCKS] = locks

        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        _LOGGER.info("TTLock setup complete")
    except ComponentOutdatedError:
        _LOGGER.error("Component version is outdated — server rejected the request.")
        persistent_notification.async_create(
            hass,
            "## ⚠️ Javis Lock cần cập nhật\n\n"
            "Server đã từ chối kết nối vì phiên bản **Javis Lock** đang dùng quá cũ.\n\n"
            "Vui lòng cập nhật integration lên phiên bản mới nhất qua **HACS** "
            "hoặc tải thủ công từ repository.",
            title="Javis Lock — Cần cập nhật",
            notification_id=f"{DOMAIN}_outdated",
        )
        ir.async_create_issue(
            hass,
            DOMAIN,
            "component_outdated",
            is_fixable=False,
            severity=ir.IssueSeverity.ERROR,
            translation_key="component_outdated",
        )
        return False
    except Exception as ex:
        _LOGGER.error(f"async_setup_new: {traceback.format_exc()}\n")
        return False
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        should_sync_webhooks = (
            CONF_WEBHOOK_ID in entry.data or CONF_WEBHOOK_URL in entry.data
        )
        if should_sync_webhooks:
            mac = await get_mac()
            server_url = server_url_for_entry(entry)
        hass.data[DOMAIN].pop(entry.entry_id)
        if should_sync_webhooks:
            webhooks = await active_webhooks_payload(
                hass, mac, exclude_entry_id=entry.entry_id
            )
            await sync_webhooks_to_server(hass, server_url, mac, webhooks)

    return unload_ok


class WebhookHandler:
    """Responsible for setting up/processing webhook data."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, client, url, lock_ids
    ) -> None:
        """Init the thing."""
        self.hass = hass
        self.entry = entry
        self.client = client
        self.url = url
        self.lock_ids = lock_ids

    async def setup(self) -> None:
        _LOGGER.debug("Setting up webhook")
        """Actually register the webhook."""
        if self.hass.state == CoreState.running:
            await self.register_webhook()
        else:
            self.hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_STARTED, self.register_webhook
            )

    async def get_url(self) -> str:
        _LOGGER.debug("Getting webhook url")
        """Get the webhook url depending on the setup."""
        if cloud.async_active_subscription(self.hass):
            if CONF_WEBHOOK_URL not in self.entry.data:
                try:
                    return await cloud.async_create_cloudhook(
                        self.hass, self.entry.data[CONF_WEBHOOK_ID]
                    )
                except cloud.CloudNotConnected:
                    return webhook.async_generate_url(
                        self.hass, self.entry.data[CONF_WEBHOOK_ID]
                    )
            else:
                return self.entry.data[CONF_WEBHOOK_URL]
        else:
            return webhook.async_generate_url(
                self.hass, self.entry.data[CONF_WEBHOOK_ID]
            )

    async def register_webhook(self, event: Event | None = None) -> None:
        """Set up a webhook to receive pushed data."""
        _LOGGER.debug("Registering webhook")
        if CONF_WEBHOOK_ID not in self.entry.data:
            _LOGGER.debug("Webhook not found in config entry, creating new one")
            data = {**self.entry.data, CONF_WEBHOOK_ID: secrets.token_hex()}
            self.hass.config_entries.async_update_entry(self.entry, data=data)

        try:
            webhook_url = await self.get_url()
            mac = await get_mac()
            new_webhook_url = await refactor_webhook_url(
                webhook_url, mac, self.entry.data.get("url")
            )
            _LOGGER.debug("Registering webhook at old url %s", webhook_url)
            _LOGGER.debug("Registering webhook at new url %s", new_webhook_url)
            await self.sync_webhooks(mac, new_webhook_url)
            data = {**self.entry.data, CONF_WEBHOOK_URL: webhook_url}
            self.hass.config_entries.async_update_entry(self.entry, data=data)
        except NoURLAvailableError:
            _LOGGER.exception("Could not find base URL for installation")
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                "no_webhook_url",
                is_fixable=False,
                severity=ir.IssueSeverity.ERROR,
                translation_key="no_webhook_url",
            )
            return
        else:
            ir.async_delete_issue(self.hass, DOMAIN, "no_webhook_url")

        if CONF_WEBHOOK_STATUS not in self.entry.data:
            self.async_show_setup_message(webhook_url)

        # Ensure the webhook is not registered already
        webhook_unregister(self.hass, self.entry.data[CONF_WEBHOOK_ID])

        webhook_register(
            self.hass,
            DOMAIN,
            "TTLock",
            self.entry.data[CONF_WEBHOOK_ID],
            self.handle_webhook,
        )

        self.hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP, self.unregister_webhook
        )

    async def sync_webhooks(self, mac, current_webhook_url: str) -> None:
        webhooks = await active_webhooks_payload(
            self.hass,
            mac,
            exclude_entry_id=self.entry.entry_id,
            extra_webhooks=[
                {
                    "webhook_url": current_webhook_url,
                    "lock_ids": self.lock_ids,
                }
            ],
        )
        await sync_webhooks_to_server(self.hass, self.url, mac, webhooks)

    async def handle_webhook(
        self, hass: HomeAssistant, webhook_id: str, request: Request
    ) -> None:
        """Handle webhook callback."""
        _LOGGER.debug("Webhook received: webhook_id=%s", webhook_id)

        success = False
        dispatched_count = 0
        try:
            # {'lockId': ['7252408'], 'notifyType': ['1'], 'records': ['[{"lockId":7252408,"electricQuantity":93,"serverDate":1680810180029,"recordTypeFromLock":17,"recordType":7,"success":1,"lockMac":"16:72:4C:CC:01:C4","keyboardPwd":"<digits>","lockDate":1680810186000,"username":"Jonas"}]'], 'admin': ['jonas@lemon.nz'], 'lockMac': ['16:72:4C:CC:01:C4']}
            if data := await request.post():
                raw_records = data.getall("records", [])
                _LOGGER.debug(
                    "Webhook payload received with %s records",
                    len(raw_records),
                )
                for raw_record_batch in raw_records:
                    for record in json.loads(raw_record_batch):
                        async_dispatcher_send(
                            hass, SIGNAL_NEW_DATA, WebhookEvent.parse_obj(record)
                        )
                        dispatched_count += 1
                        success = True
                _LOGGER.debug(
                    "Webhook processed: webhook_id=%s dispatched_events=%s",
                    webhook_id,
                    dispatched_count,
                )
            else:
                _LOGGER.warning("Webhook received empty payload: webhook_id=%s", webhook_id)
        except ValueError as ex:
            _LOGGER.warning(
                "Exception parsing webhook data: webhook_id=%s error=%s",
                webhook_id,
                ex,
            )
            return

        if success and CONF_WEBHOOK_STATUS not in self.entry.data:
            self.async_dismiss_setup_message()

    async def unregister_webhook(self, event: Event | None = None) -> None:
        _LOGGER.debug("Unregistering webhook")
        """Remove the webhook (before stop)."""
        webhook_unregister(self.hass, self.entry.data[CONF_WEBHOOK_ID])

    def async_show_setup_message(self, uri: str) -> None:
        _LOGGER.debug("Showing setup message")
        """Display persistent notification with setup information."""
        persistent_notification.async_create(
            self.hass, f"Webhook url: {uri}", "TTLock Setup", self.entry.entry_id
        )

    def async_dismiss_setup_message(self) -> None:
        _LOGGER.debug("Dismissing setup message")
        """Dismiss persistent notification."""
        data = {**self.entry.data, CONF_WEBHOOK_STATUS: True}
        self.hass.config_entries.async_update_entry(self.entry, data=data)
        persistent_notification.async_dismiss(self.hass, self.entry.entry_id)
