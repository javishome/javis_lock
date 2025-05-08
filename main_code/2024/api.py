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
from aiohttp import ClientResponse, ClientSession, ClientTimeout
from .const import SERVER_URL
import traceback
from aiohttp_retry import RetryClient, ExponentialRetry

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
import aiohttp

from .const import SERVER_URL, HOST1, HOST2, HOST3
from .models import (
    AddPasscodeConfig,
    Features,
    Lock,
    LockState,
    PassageModeConfig,
    Passcode,
)

GW_LOCK = asyncio.Lock()

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, CONF_URL
import traceback


_LOGGER = logging.getLogger(__name__)
AUTH_SCHEMA = vol.Schema(
    {vol.Required(CONF_USERNAME): cv.string, 
     vol.Required(CONF_PASSWORD): cv.string,
     vol.Required(CONF_URL, default=HOST3): vol.In(
                    [HOST1, HOST2, HOST3]
                )}
)



async def login(username: str, password: str, url_cloud: str):
    url_login = SERVER_URL + url_cloud + "/api/login"
    # url_login = SERVER_URL + "/api/login"
    data = {
        "username": username,
        "password": password
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url_login, json=data) as response:
                is_error = (await response.json()).get("errcode")
                if is_error is None:
                    return {"error": '', "is_success": True}
                else:
                    return {"error": "Invalid username or password", "is_success": False}
    except Exception as e:
        _LOGGER.error(f"login error 1: {traceback.format_exc()}\n")
        return {"error": "Server disconected", "is_success": False}


class RequestFailed(Exception):
    """Exception when TTLock API returns an error."""

    pass


class TTLockApi:
    """Provide TTLock authentication tied to an OAuth2 based config entry."""
    def __init__(
        self,
        hass,
        websession: ClientSession,
        username,
        password,
        url
    ) -> None:
        """Initialize TTLock auth."""
        self.hass = hass
        self._web_session = websession
        self.username = username
        self.password = password
        self.base_url = f"{url}/api/"
    
    async def login(self):
        url_login = self.base_url + "login"
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
            _LOGGER.error(f"login error 1: {traceback.format_exc()}\n")
    
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
        log_id = token_hex(2)

        url = urljoin(self.base_url, path)
        _LOGGER.debug("[%s] Sending request to %s with args=%s", log_id, url, kwargs)
        statuses_to_retry = {400}
        retry_exceptions = {asyncio.exceptions.CancelledError}
        retry_options = ExponentialRetry(
                attempts=3,
                start_timeout=2,
                statuses=statuses_to_retry,
                exceptions=retry_exceptions
        )
        retry_client = RetryClient(self._web_session, retry_options=retry_options, raise_for_status=False)
        
        try:
            async with retry_client.get(
                url,
                params=kwargs,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=ClientTimeout(total=180),
            ) as resp:
                return await self._parse_resp(resp, log_id)
        except Exception as e:
            _LOGGER.error("[%s] Exception occurred after retries: %s", log_id, str(e))
            return None
        except asyncio.CancelledError as err:
            _LOGGER.error("[%s] Exception occurred after retries: %s", log_id, str(err))
            return None

    async def post(self, path: str, **kwargs: Any) -> Mapping[str, Any]:
        await self.ensure_valid_token()
        kwargs["access_token"] = self.token
        """Make GET request to the API with kwargs as query params."""
        log_id = token_hex(2)
        url = urljoin(self.base_url, path)
        _LOGGER.info("[%s] Sending request to %s with args=%s", log_id, url, kwargs)
        max_retries = 3  # Số lần thử lại tối đa
        retry_delay = 2  # Thời gian chờ giữa các lần thử lại (giây)

        for attempt in range(max_retries):
            try:
                resp = await self._web_session.post(
                            url,
                            json=kwargs
                        )
                return await self._parse_resp(resp, log_id)
    
            except asyncio.CancelledError:
                _LOGGER.error("[%s] Request was cancelled!", log_id)
            except Exception as e:
                _LOGGER.error("[%s] Exception occurred: %s", log_id, str(e))
    
            if attempt < max_retries:
                await asyncio.sleep(retry_delay)  # Chờ trước khi thử lại

        return None

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

        if res and res.get("errcode") != 0:
            msg = f"❌ Failed to lock {lock_id}: {res.get('errmsg', 'Unknown error')}"
            _LOGGER.error(msg)
            return False

        if not res:
            msg = f"❌ Failed to lock {lock_id}"
            _LOGGER.error(msg)
            return False
        return True

    async def unlock(self, lock_id: int) -> bool:
        """Try to unlock the lock."""
        async with GW_LOCK:
            res = await self.get("lock/unlock", lockId=lock_id)

        if res and res.get("errcode") != 0:
            # handle error
            msg = f"❌ Failed to lock {lock_id}: {res.get('errmsg', 'Unknown error')}"
            _LOGGER.error(msg)
            return False
        
        if not res:
            msg = f"❌ Failed to lock {lock_id}"
            _LOGGER.error(msg)
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

        if res and res.get("errcode") != 0:
    # handle error

            _LOGGER.error("Failed to unlock %s: %s", lock_id, res["errmsg"])
            return False
        
        return (await res.json())

    async def add_passcode(self, lock_id: int, config: AddPasscodeConfig) -> bool:
        """Add new passcode."""
        _LOGGER.info(f"Passcode start create for {lock_id}")
        async with GW_LOCK:
            res = await self.post(
                "keyboardPwd/get",
                lockId=lock_id,
                keyboardPwdName=config.passcode_name,
                keyboardPwdType=config.type,
                startDate=config.start_minute,
                endDate=config.end_minute,
            )

        if res and res.get("errcode") != 0:
    # handle error

            _LOGGER.error(
                "Failed to create passcode for %s: %s", lock_id, res["errmsg"]
            )
            return False
        _LOGGER.info(f"Passcode created for {lock_id}")
        _LOGGER.info("res: %s", res)
        return res

    async def list_passcodes(self, lock_id: int, is_parse = True) -> list[Passcode]:
        """Get currently configured passcodes from lock."""

        res = await self.get(
            "lock/listKeyboardPwd", lockId=lock_id
        )
        if is_parse:
            return [Passcode.parse_obj(passcode) for passcode in res["list"]]
        else:
            _LOGGER.info("res list passcode: %s", res)
            return res
        
    async def list_unlock_records(self, lock_id: int,page_no:int, page_size:int, is_parse = False):
        """Get currently configured passcodes from lock."""

        res = await self.get(
            "lockRecord/list", lockId=lock_id, pageNo=page_no, pageSize=page_size
        )
        if is_parse:
            return [Passcode.parse_obj(passcode) for passcode in res["list"]]
        else:
            _LOGGER.info("res list unlock records: %s", res)
            return res

    async def delete_passcode(self, lock_id: int, passcode_id: int):
        """Delete a passcode from lock."""

        async with GW_LOCK:
            resDel = await self.post(
                "keyboardPwd/delete",
                lockId=lock_id,
                deleteType=2,  # via gateway
                keyboardPwdId=passcode_id,
            )

        return resDel
    
    async def change_passcode(self, lock_id: int, keyboardPwdId: int, newKeyboardPwd: str, keyboardPwdName: str):
        """Delete a passcode from lock."""

        async with GW_LOCK:
            resDel = await self.post(
                "keyboardPwd/change",
                lockId=lock_id,
                keyboardPwdId=keyboardPwdId,
                keyboardPwdName=keyboardPwdName,
                newKeyboardPwd=newKeyboardPwd
            )


        return resDel
