"""API for TTLock bound to Home Assistant OAuth."""
import asyncio
from collections.abc import Mapping
from hashlib import md5
import json
import logging
from secrets import token_hex
import time
from typing import Any, cast
from urllib.parse import urljoin
from aiohttp import ClientResponse, ClientSession
from .const import SERVER_URL


from .models import (
    AddPasscodeConfig,
    Features,
    Lock,
    LockState,
    PassageModeConfig,
    Passcode,
)

_LOGGER = logging.getLogger(__name__)
GW_LOCK = asyncio.Lock()


class RequestFailed(Exception):
    """Exception when TTLock API returns an error."""

    pass


class TTLockApi:
    """Provide TTLock authentication tied to an OAuth2 based config entry."""

    BASE = f"{SERVER_URL}/api/"

    def __init__(
        self,
        websession: ClientSession,
        username,
        password
    ) -> None:
        """Initialize TTLock auth."""
        self._web_session = websession
        self.username = username
        self.password = password
    
    async def login(self):
        url_login = self.BASE + "login"
        data = {
            "username": self.username,
            "password": self.password
        }
        try:
            async with self._web_session.post(url_login, json=data) as response:
                if response.status == 200:
                    self.token = (await response.json())["access_token"]
                    self.start_time = int(time.time() * 1000)
                    self.expires_in = (await response.json())["expires_in"]
                    _LOGGER.info("login success")
                else:
                     _LOGGER.error(f"login error: {str(await response.text())}")
        except Exception as e:
            _LOGGER.error(f"login error: {str(e)}")
    
    async def ensure_valid_token(self):
        if not hasattr(self, "token"):
            await self.login()
        elif int(time.time() * 1000) - self.start_time > self.expires_in:
            await self.login()

    async def _parse_resp(self, resp: ClientResponse, log_id: str) -> Mapping[str, Any]:
        if resp.status >= 400:
            body = await resp.text()
            _LOGGER.debug(
                "[%s] Request failed: status=%s, body=%s", log_id, resp.status, body
            )
        else:
            body = await resp.json()
            _LOGGER.debug(
                "[%s] Received response: status=%s: body=%s", log_id, resp.status, body
            )

        resp.raise_for_status()

        res = cast(dict, await resp.json())
        if res.get("errcode", 0) != 0:
            _LOGGER.debug("[%s] API returned: %s", log_id, res)
            raise RequestFailed(f"API returned: {res}")

        return cast(dict, await resp.json())

    async def get(self, path: str, **kwargs: Any) -> Mapping[str, Any]:
        await self.ensure_valid_token()
        kwargs["access_token"] = self.token
        """Make GET request to the API with kwargs as query params."""
        log_id = token_hex(2)

        url = urljoin(self.BASE, path)
        _LOGGER.debug("[%s] Sending request to %s with args=%s", log_id, url, kwargs)
        resp = await self._web_session.get(
            url,
            params = kwargs,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        return await self._parse_resp(resp, log_id)

    async def post(self, path: str, **kwargs: Any) -> Mapping[str, Any]:
        await self.ensure_valid_token()
        kwargs["access_token"] = self.token
        """Make GET request to the API with kwargs as query params."""
        log_id = token_hex(2)

        url = urljoin(self.BASE, path)
        _LOGGER.debug("[%s] Sending request to %s with args=%s", log_id, url, kwargs)
        resp = await self._web_session.post(
            url,
            data=kwargs,
        )
        return await self._parse_resp(resp, log_id)
    


    async def get_locks(self) -> list[int]:
        """Enumerate all locks in the account."""
        res = await self.get("lock/list")

        def lock_connectable(lock) -> bool:
            has_gateway = lock.get("hasGateway") != 0
            has_wifi = Features.wifi in Features.from_feature_value(
                lock.get("featureValue")
            )
            return has_gateway or has_wifi

        return [lock["lockId"] for lock in res["list"] if lock_connectable(lock)]

    async def get_lock(self, lock_id: int) -> Lock:
        """Get a lock by ID."""
        res = await self.get("lock/detail", lockId=lock_id)
        return Lock.parse_obj(res)

    async def get_lock_state(self, lock_id: int) -> LockState:
        """Get the state of a lock."""
        async with GW_LOCK:
            res = await self.get("lock/queryOpenState", lockId=lock_id)
        return LockState.parse_obj(res)

    async def get_lock_passage_mode_config(self, lock_id: int) -> PassageModeConfig:
        """Get the passage mode configuration of a lock."""
        res = await self.get("lock/getPassageModeConfig", lockId=lock_id)
        return PassageModeConfig.parse_obj(res)

    async def lock(self, lock_id: int) -> bool:
        """Try to lock the lock."""
        async with GW_LOCK:
            res = await self.get("lock/lock", lockId=lock_id)

        if "errcode" in res and res["errcode"] != 0:
            _LOGGER.error("Failed to lock %s: %s", lock_id, res["errmsg"])
            return False

        return True

    async def unlock(self, lock_id: int) -> bool:
        """Try to unlock the lock."""
        async with GW_LOCK:
            res = await self.get("lock/unlock", lockId=lock_id)

        if "errcode" in res and res["errcode"] != 0:
            _LOGGER.error("Failed to unlock %s: %s", lock_id, res["errmsg"])
            return False

        return True

    async def set_passage_mode(self, lock_id: int, config: PassageModeConfig) -> bool:
        """Configure passage mode."""

        async with GW_LOCK:
            res = await self.post(
                "lock/configPassageMode",
                lockId=lock_id,
                type=2,  # via gateway
                passageMode=1 if config.enabled else 2,
                autoUnlock=1 if config.auto_unlock else 2,
                isAllDay=1 if config.all_day else 2,
                startDate=config.start_minute,
                endDate=config.end_minute,
                weekDays=json.dumps(config.week_days),
            )

        if "errcode" in res and res["errcode"] != 0:
            _LOGGER.error("Failed to unlock %s: %s", lock_id, res["errmsg"])
            return False

        return True

    async def add_passcode(self, lock_id: int, config: AddPasscodeConfig) -> bool:
        """Add new passcode."""

        async with GW_LOCK:
            res = await self.post(
                "keyboardPwd/add",
                lockId=lock_id,
                addType=2,  # via gateway
                keyboardPwd=config.passcode,
                keyboardPwdName=config.passcode_name,
                keyboardPwdType=3,  # Only temporary passcode supported
                startDate=config.start_minute,
                endDate=config.end_minute,
            )

        if "errcode" in res and res["errcode"] != 0:
            _LOGGER.error(
                "Failed to create passcode for %s: %s", lock_id, res["errmsg"]
            )
            return False

        return True

    async def list_passcodes(self, lock_id: int) -> list[Passcode]:
        """Get currently configured passcodes from lock."""

        res = await self.get(
            "lock/listKeyboardPwd", lockId=lock_id
        )
        return [Passcode.parse_obj(passcode) for passcode in res["list"]]

    async def delete_passcode(self, lock_id: int, passcode_id: int) -> bool:
        """Delete a passcode from lock."""

        async with GW_LOCK:
            resDel = await self.post(
                "keyboardPwd/delete",
                lockId=lock_id,
                deleteType=2,  # via gateway
                keyboardPwdId=passcode_id,
            )

        if "errcode" in resDel and resDel["errcode"] != 0:
            _LOGGER.error(
                "Failed to delete passcode for %s: %s",
                lock_id,
                resDel["errmsg"],
            )
            return False

        return True
