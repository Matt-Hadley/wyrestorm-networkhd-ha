"""Config flow for WyreStorm NetworkHD integration."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from contextlib import suppress
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    SOURCE_RECONFIGURE,
    ConfigFlow,
    ConfigFlowResult,
)
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
)
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig

from wyrestorm_networkhd import NHDAPI, HostKeyMismatchError, normalize_fingerprints
from wyrestorm_networkhd.exceptions import AuthenticationError

from .const import (
    CONF_HOST_KEY_FINGERPRINT,
    DEFAULT_PASSWORD,
    DEFAULT_PORT,
    DEFAULT_USERNAME,
    DOMAIN,
)
from .coordinator import API_ERRORS, create_client

_LOGGER = logging.getLogger(__name__)


def get_config_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Get the connection schema with optional defaults."""
    defaults = defaults or {}
    fingerprint = defaults.get(CONF_HOST_KEY_FINGERPRINT) or ""
    if not isinstance(fingerprint, str):  # stored entry data holds a list
        fingerprint = "\n".join(fingerprint)
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, "")): str,
            vol.Required(CONF_USERNAME, default=defaults.get(CONF_USERNAME, DEFAULT_USERNAME)): str,
            vol.Required(CONF_PASSWORD, default=defaults.get(CONF_PASSWORD, DEFAULT_PASSWORD)): str,
            vol.Optional(CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT)): int,
            # suggested_value (not default) so clearing the field removes the pin.
            vol.Optional(CONF_HOST_KEY_FINGERPRINT, description={"suggested_value": fingerprint}): TextSelector(
                TextSelectorConfig(multiline=True)
            ),
        }
    )


def parse_connection_input(
    user_input: dict[str, Any], base: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, str]]:
    """Merge form input onto `base`, storing the fingerprint(s) normalized; return (data, errors)."""
    data = {**base, **user_input}
    data.pop(CONF_HOST_KEY_FINGERPRINT, None)
    if raw := user_input.get(CONF_HOST_KEY_FINGERPRINT, "").strip():
        try:
            data[CONF_HOST_KEY_FINGERPRINT] = list(normalize_fingerprints(raw))
        except ValueError:
            return data, {CONF_HOST_KEY_FINGERPRINT: "invalid_host_key_fingerprint"}
    return data, {}


async def validate_connection(hass: HomeAssistant, data: dict[str, Any]) -> str | None:
    """Connect and query the controller version; return the presented host key fingerprint.

    Raises the library's errors on failure.
    """
    client = create_client(data)
    try:
        await client.connect()
        await NHDAPI(client).api_query.config_get_version()
        return client.host_key_fingerprint
    finally:
        with suppress(*API_ERRORS):
            await client.disconnect()


class WyreStormConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WyreStorm NetworkHD."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        self._pending: dict[str, Any] = {}  # validated data waiting for confirm_host_key
        self._placeholders: dict[str, str] = {"fingerprint": "-"}  # presented fingerprint, shown in errors
        self._presented: str | None = None  # fingerprint presented by the last successful connection test

    async def _async_try_connect(self, data: dict[str, Any]) -> dict[str, str]:
        """Return form errors for `data` (empty if the controller answered); learns the presented key."""
        try:
            self._presented = await validate_connection(self.hass, data)
            self._placeholders["fingerprint"] = self._presented or "-"
        except AuthenticationError:
            return {"base": "invalid_auth"}
        except HostKeyMismatchError as err:
            _LOGGER.debug("Host key mismatch for %s: %s", data[CONF_HOST], err)
            self._placeholders["fingerprint"] = err.presented_fingerprint
            return {"base": "host_key_mismatch"}
        except API_ERRORS as err:
            _LOGGER.debug("Cannot connect to %s: %s", data[CONF_HOST], err)
            return {"base": "cannot_connect"}
        except Exception:
            _LOGGER.exception("Unexpected error connecting to %s", data[CONF_HOST])
            return {"base": "unknown"}
        return {}

    async def _async_connect_and_finish(
        self, step_id: str, user_input: dict[str, Any], base: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Validate and test `user_input`; pin a supplied key, or confirm the presented one (TOFU)."""
        data, errors = parse_connection_input(user_input, base)
        if not errors and not (errors := await self._async_try_connect(data)):
            if CONF_HOST_KEY_FINGERPRINT in data or not self._presented:
                return self._async_finish(data)  # pinned by the user, or no key reported: store as is
            self._pending = {**data, CONF_HOST_KEY_FINGERPRINT: [self._presented]}
            return await self.async_step_confirm_host_key()
        return self.async_show_form(
            step_id=step_id,
            data_schema=get_config_schema(user_input),
            errors=errors,
            description_placeholders=self._placeholders,
        )

    async def async_step_confirm_host_key(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Show the presented host key fingerprint and pin it once confirmed."""
        if user_input is not None:
            return self._async_finish(self._pending)
        return self.async_show_form(step_id="confirm_host_key", description_placeholders=self._placeholders)

    def _async_finish(self, data: dict[str, Any]) -> ConfigFlowResult:
        """Create the entry, or save a reconfigured one."""
        host = data[CONF_HOST]
        if self.source != SOURCE_RECONFIGURE:
            return self.async_create_entry(title=f"WyreStorm NetworkHD ({host})", data=data)
        entry = self._get_reconfigure_entry()
        if host != entry.data[CONF_HOST]:
            self._move_controller_ids(entry.entry_id, entry.data[CONF_HOST], host)
        # data (not data_updates) so a cleared fingerprint is removed.
        return self.async_update_reload_and_abort(
            entry, unique_id=host, title=f"WyreStorm NetworkHD ({host})", data=data
        )

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=get_config_schema(), description_placeholders=self._placeholders
            )
        # shortcut: the controller exposes no MAC/serial over the API, so the host is the unique id.
        await self.async_set_unique_id(user_input[CONF_HOST])
        self._abort_if_unique_id_configured()
        return await self._async_connect_and_finish("user", user_input, {})

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Change the connection details or host key; a new host also becomes the new unique id."""
        entry = self._get_reconfigure_entry()
        if user_input is None:
            return self.async_show_form(
                step_id="reconfigure",
                data_schema=get_config_schema(dict(entry.data)),
                description_placeholders=self._placeholders,
            )
        if user_input[CONF_HOST] != entry.data[CONF_HOST]:
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()
        return await self._async_connect_and_finish("reconfigure", user_input, entry.data)

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
            description_placeholders={"host": entry.data[CONF_HOST], **self._placeholders},
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
