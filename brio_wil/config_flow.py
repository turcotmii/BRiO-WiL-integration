"""Config flow: just a host and port."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_HOST, CONF_PORT

from .api import BrioClient, BrioError
from .const import DEFAULT_PORT, DOMAIN


class BrioConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()
            try:
                await BrioClient(user_input[CONF_HOST], user_input[CONF_PORT]).async_get_status()
            except BrioError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"BRiO WiL ({user_input[CONF_HOST]})", data=user_input
                )
        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=(user_input or {}).get(CONF_HOST, "")): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
