"""Config flow for WyreStorm NetworkHD integration."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from contextlib import suppress
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlowWithReload
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
)

from wyrestorm_networkhd import NHDAPI
from wyrestorm_networkhd.exceptions import AuthenticationError

from .const import (
    CONF_UPDATE_INTERVAL,
    DEFAULT_PASSWORD,
    DEFAULT_PORT,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_USERNAME,
    DOMAIN,
)
from .coordinator import API_ERRORS, create_client

_LOGGER = logging.getLogger(__name__)


def get_config_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Get the connection schema with optional defaults."""
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, "")): str,
            vol.Required(CONF_USERNAME, default=defaults.get(CONF_USERNAME, DEFAULT_USERNAME)): str,
            vol.Required(CONF_PASSWORD, default=defaults.get(CONF_PASSWORD, DEFAULT_PASSWORD)): str,
            vol.Optional(CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT)): int,
        }
    )


async def validate_connection(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Connect and query the controller version; raises the library's errors on failure."""
    client = create_client(data)
    try:
        await client.connect()
        api = await hass.async_add_executor_job(NHDAPI, client)
        await api.api_query.config_get_version()
    finally:
        with suppress(*API_ERRORS):
            await client.disconnect()


class WyreStormConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WyreStorm NetworkHD."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> WyreStormOptionsFlow:
        """Create the options flow."""
        return WyreStormOptionsFlow()

    async def _async_try_connect(self, data: dict[str, Any]) -> dict[str, str]:
        """Return form errors for `data` (empty if the controller answered)."""
        try:
            await validate_connection(self.hass, data)
        except AuthenticationError:
            return {"base": "invalid_auth"}
        except API_ERRORS as err:
            _LOGGER.debug("Cannot connect to %s: %s", data[CONF_HOST], err)
            return {"base": "cannot_connect"}
        except Exception:
            _LOGGER.exception("Unexpected error connecting to %s", data[CONF_HOST])
            return {"base": "unknown"}
        return {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            # shortcut: the controller exposes no MAC/serial over the API, so the host is the unique id.
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()
            if not (errors := await self._async_try_connect(user_input)):
                return self.async_create_entry(title=f"WyreStorm NetworkHD ({user_input[CONF_HOST]})", data=user_input)

        return self.async_show_form(step_id="user", data_schema=get_config_schema(user_input), errors=errors)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Change the connection details; a new host also becomes the new unique id."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            old_host, new_host = entry.data[CONF_HOST], user_input[CONF_HOST]
            if new_host != old_host:
                await self.async_set_unique_id(new_host)
                self._abort_if_unique_id_configured()
            if not (errors := await self._async_try_connect(user_input)):
                if new_host != old_host:
                    self._move_controller_ids(entry.entry_id, old_host, new_host)
                return self.async_update_reload_and_abort(
                    entry,
                    unique_id=new_host,
                    title=f"WyreStorm NetworkHD ({new_host})",
                    data_updates=user_input,
                )

        return self.async_show_form(
            step_id="reconfigure", data_schema=get_config_schema(user_input or dict(entry.data)), errors=errors
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        """Start reauthentication after the controller rejected the stored credentials."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Ask for new credentials and check them against the configured controller."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None and not (errors := await self._async_try_connect({**entry.data, **user_input})):
            return self.async_update_reload_and_abort(entry, data_updates=user_input)

        username = (user_input or entry.data)[CONF_USERNAME]
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {vol.Required(CONF_USERNAME, default=username): str, vol.Required(CONF_PASSWORD): str}
            ),
            description_placeholders={"host": entry.data[CONF_HOST]},
            errors=errors,
        )

    def _move_controller_ids(self, entry_id: str, old_host: str, new_host: str) -> None:
        """Keep the controller device and its reboot button when the host (their id) changes."""
        dev_reg = dr.async_get(self.hass)
        if device := dev_reg.async_get_device_by_identifier((DOMAIN, old_host), entry_id):
            dev_reg.async_update_device(device.id, new_identifiers={(DOMAIN, new_host)})
        ent_reg = er.async_get(self.hass)
        if entity_id := ent_reg.async_get_entity_id(Platform.BUTTON, DOMAIN, f"{DOMAIN}_{old_host}_controller_reboot"):
            ent_reg.async_update_entity(entity_id, new_unique_id=f"{DOMAIN}_{new_host}_controller_reboot")


class WyreStormOptionsFlow(OptionsFlowWithReload):
    """Edit the polling interval."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        entry = self.config_entry
        current = entry.options.get(CONF_UPDATE_INTERVAL, entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL))
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {vol.Required(CONF_UPDATE_INTERVAL, default=current): vol.All(int, vol.Range(min=10, max=300))}
            ),
        )
