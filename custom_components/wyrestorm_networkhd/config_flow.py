"""Config flow for WyreStorm NetworkHD integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult

from wyrestorm_networkhd import NHDAPI, NetworkHDClientSSH

from .const import (
    CONF_UPDATE_INTERVAL,
    DEFAULT_PASSWORD,
    DEFAULT_PORT,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_USERNAME,
    DOMAIN,
    SSH_HOST_KEY_POLICY,
)

_LOGGER = logging.getLogger(__name__)


def get_config_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Get the configuration schema with optional defaults."""
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, "")): str,
            vol.Required(CONF_USERNAME, default=defaults.get(CONF_USERNAME, DEFAULT_USERNAME)): str,
            vol.Required(CONF_PASSWORD, default=defaults.get(CONF_PASSWORD, DEFAULT_PASSWORD)): str,
            vol.Optional(CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT)): int,
            vol.Optional(
                CONF_UPDATE_INTERVAL, default=defaults.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
            ): vol.All(int, vol.Range(min=10, max=300)),
        }
    )


async def test_connection(user_input: dict[str, Any]) -> dict[str, str]:
    """Test connection to the controller and return any errors."""
    errors = {}
    client = None

    try:
        client = NetworkHDClientSSH(
            host=user_input[CONF_HOST],
            port=user_input.get(CONF_PORT, DEFAULT_PORT),
            username=user_input[CONF_USERNAME],
            password=user_input[CONF_PASSWORD],
            ssh_host_key_policy=SSH_HOST_KEY_POLICY,
        )

        await client.connect()
        api = NHDAPI(client)
        await api.api_query.config_get_version()

    except Exception as err:
        _LOGGER.error("Connection test failed: %s", err)
        errors["base"] = str(err)
    finally:
        if client and client.is_connected():
            try:
                await client.disconnect()
            except Exception as disconnect_err:
                _LOGGER.debug("Error disconnecting client: %s", disconnect_err)

    return errors


class ConfigFlow(config_entries.ConfigFlow):
    """Handle a config flow for WyreStorm NetworkHD."""

    VERSION = 1
    DOMAIN = DOMAIN

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> OptionsFlow:
        """Create the options flow."""
        return OptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()

            errors = await test_connection(user_input)
            if not errors:
                return self.async_create_entry(
                    title=f"WyreStorm NetworkHD ({user_input[CONF_HOST]})",
                    data=user_input,
                )
        else:
            errors = {}

        return self.async_show_form(
            step_id="user",
            data_schema=get_config_schema(),
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle reconfiguration of the integration."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])

        if user_input is not None:
            errors = await test_connection(user_input)
            if not errors:
                self.hass.config_entries.async_update_entry(
                    entry,
                    data=user_input,
                    title=f"WyreStorm NetworkHD ({user_input[CONF_HOST]})",
                )
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reconfigure_successful")
        else:
            errors = {}

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=get_config_schema(entry.data),
            errors=errors,
        )


class OptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for WyreStorm NetworkHD integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            new_data = {**self.config_entry.data, **user_input}
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=new_data,
                title=f"WyreStorm NetworkHD ({new_data[CONF_HOST]})",
            )
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="init",
            data_schema=get_config_schema(self.config_entry.data),
        )
