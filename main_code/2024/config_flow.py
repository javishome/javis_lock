"""Config flow for TTLock."""
import logging
from typing import Any, Dict, Optional
from .const import DOMAIN
from .api import AUTH_SCHEMA, login



from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, CONF_URL
from homeassistant import config_entries
_LOGGER = logging.getLogger(__name__)



class GithubCustomConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Github Custom config flow."""

    data: Optional[Dict[str, Any]]

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Invoked when a user initiates a flow via the user interface."""
        errors: Dict[str, str] = {}
        try:
            if user_input is not None:
                try:
                    session = await login(user_input[CONF_USERNAME], user_input[CONF_PASSWORD], user_input[CONF_URL])
                    if not session.get("is_success"):
                        errors["base"] = session.get("error")
                except ValueError:
                    errors["base"] = "auth"
                if not errors:
                    # Input is valid, set data.
                    self.data = user_input
                    # Return the form of the next step.
                    _LOGGER.info("Login success")
                    await self.async_set_unique_id(user_input[CONF_USERNAME])

                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(title=user_input[CONF_USERNAME], data=self.data)
        except Exception as e:
            errors["base"] = str(e)

        return self.async_show_form(
            step_id="user", data_schema=AUTH_SCHEMA, errors=errors,
            description_placeholders={
                "username": "e.g. email or +84987654321"
            },
        )
