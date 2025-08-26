"""Config flow for WyreStorm NetworkHD integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, CONF_PORT
from homeassistant.data_entry_flow import FlowResult

from wyrestorm_networkhd import NetworkHDClientSSH
from wyrestorm_networkhd.exceptions import NetworkHDError

from .const import DOMAIN, DEFAULT_PORT, DEFAULT_USERNAME, DEFAULT_PASSWORD, DEFAULT_UPDATE_INTERVAL, CONF_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class WyrestormNetworkHDConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WyreStorm NetworkHD."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> WyreStormOptionsFlow:
        """Create the options flow."""
        return WyreStormOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Check for existing entries with same host
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()

            try:
                # Test connection
                client = NetworkHDClientSSH(
                    host=user_input[CONF_HOST],
                    port=user_input.get(CONF_PORT, DEFAULT_PORT),
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD],
                    ssh_host_key_policy="auto_add",
                    timeout=10.0,
                )
                
                # Test connection
                await client.connect()
                
                # Test a basic API call
                from wyrestorm_networkhd import NHDAPI
                api = NHDAPI(client)
                await api.api_query.config_get_version()
                
                await client.disconnect()
                
                # Create entry
                return self.async_create_entry(
                    title=f"WyreStorm NetworkHD Controller ({user_input[CONF_HOST]})",
                    data=user_input,
                )
                
            except NetworkHDError as err:
                _LOGGER.error("Connection test failed: %s", err)
                if "authentication" in str(err).lower():
                    errors["base"] = "invalid_auth"
                elif "timeout" in str(err).lower():
                    errors["base"] = "timeout"
                else:
                    errors["base"] = "cannot_connect"
            except Exception as err:
                _LOGGER.error("Unexpected error during setup: %s", err)
                errors["base"] = "unknown"
            finally:
                # Ensure client is disconnected
                try:
                    if client.is_connected():
                        await client.disconnect()
                except Exception as disconnect_err:
                    _LOGGER.debug("Error disconnecting client during cleanup: %s", disconnect_err)

        # Show form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_USERNAME, default=DEFAULT_USERNAME): str,
                    vol.Required(CONF_PASSWORD, default=DEFAULT_PASSWORD): str,
                    vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                    vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.All(
                        int, vol.Range(min=10, max=300)
                    ),
                }
            ),
            errors=errors,
            description_placeholders={
                "controller_info": "This integration connects to your WyreStorm NetworkHD controller via SSH to manage matrix switching, device control, and monitoring. The update interval controls how often the integration polls for device status (10-300 seconds)."
            }
        )


class WyreStormOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for WyreStorm NetworkHD integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Check options first, then config data, then default
        current_interval = self.config_entry.options.get(CONF_UPDATE_INTERVAL) or self.config_entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(CONF_UPDATE_INTERVAL, default=current_interval): vol.All(
                    int, vol.Range(min=10, max=300)
                ),
            }),
            description_placeholders={
                "current_interval": f"Current polling interval is {current_interval} seconds. You can change this to any value between 10-300 seconds."
            }
        )
