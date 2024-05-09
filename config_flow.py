"""Config flow for TTLock."""
import logging
from typing import Any, Dict, Optional


import voluptuous as vol

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, CONF_URL
import aiohttp
from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, HOST1, HOST2, HOST3,SERVER_URL
import traceback
_LOGGER = logging.getLogger(__name__)
AUTH_SCHEMA = vol.Schema(
    {vol.Required(CONF_USERNAME): cv.string, 
     vol.Required(CONF_PASSWORD): cv.string,
     vol.Required(CONF_URL, default=HOST1): vol.In(
                    [HOST1, HOST2, HOST3]
                )}
)

lock_server_url = f"{SERVER_URL}/api/login"

async def login(username: str, password: str):
    url_login = lock_server_url
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

class GithubCustomConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Github Custom config flow."""

    data: Optional[Dict[str, Any]]

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Invoked when a user initiates a flow via the user interface."""
        errors: Dict[str, str] = {}
        try:
            if user_input is not None:
                try:
                    session = await login(user_input[CONF_USERNAME], user_input[CONF_PASSWORD])
                    if not session.get("is_success"):
                        errors["base"] = session.get("error")
                except ValueError:
                    errors["base"] = "auth"
                if not errors:
                    # Input is valid, set data.
                    self.data = user_input
                    # Return the form of the next step.
                    _LOGGER.info("Login success")
                    return self.async_create_entry(title="GitHub Custom", data=self.data)
        except Exception as e:
            errors["base"] = str(e)

        return self.async_show_form(
            step_id="user", data_schema=AUTH_SCHEMA, errors=errors,
            description_placeholders={
                "username": "e.g. email or +84987654321"
            },
        )
