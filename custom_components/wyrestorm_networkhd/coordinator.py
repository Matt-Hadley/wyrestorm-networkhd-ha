"""WyreStorm NetworkHD data coordinator."""

from __future__ import annotations

import asyncio
import logging
import time
from contextlib import suppress
from dataclasses import replace
from datetime import datetime, timedelta
from typing import Any, Literal

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from wyrestorm_networkhd import NHDAPI, NetworkHDClientSSH
from wyrestorm_networkhd.exceptions import AuthenticationError, NetworkHDError
from wyrestorm_networkhd.models.api_query import DeviceInfo

from ._utils_coordinator import build_device_collections, process_matrix_assignments
from .const import CONF_UPDATE_INTERVAL, DEFAULT_PORT, DEFAULT_UPDATE_INTERVAL, DOMAIN, SSH_HOST_KEY_POLICY
from .models.coordinator import CoordinatorData
from .models.device_controller import DeviceController
from .models.device_receiver_transmitter import DeviceReceiver, DeviceTransmitter

_LOGGER = logging.getLogger(__name__)

# Library 2.x raises NetworkHDError/builtins and plain ValueError from parsers; 3.x subclasses these.
API_ERRORS = (NetworkHDError, OSError, ValueError)
NOTIFICATION_TYPES = ("endpoint", "video")
DEVICE_INFO_TTL = 600  # seconds; device info (MAC, firmware, network) rarely changes

type WyreStormConfigEntry = ConfigEntry[WyreStormCoordinator]


def create_client(data: dict[str, Any]) -> NetworkHDClientSSH:
    """Create the SSH client from config entry data."""
    return NetworkHDClientSSH(
        host=data[CONF_HOST],
        port=data.get(CONF_PORT, DEFAULT_PORT),
        username=data[CONF_USERNAME],
        password=data[CONF_PASSWORD],
        ssh_host_key_policy=SSH_HOST_KEY_POLICY,
    )


class WyreStormCoordinator(DataUpdateCoordinator[CoordinatorData]):
    """Owns the controller connection and all API calls.

    Polls as a fallback; controller notifications trigger a debounced refresh. A dropped link
    makes the update fail (entities go unavailable) and the next update reconnects.
    """

    config_entry: WyreStormConfigEntry

    def __init__(self, hass: HomeAssistant, entry: WyreStormConfigEntry) -> None:
        """Initialize coordinator."""
        interval = entry.options.get(
            CONF_UPDATE_INTERVAL, entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        )
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name="WyreStorm NetworkHD",
            update_interval=timedelta(seconds=interval),
        )
        self.host: str = entry.data[CONF_HOST]
        self.client = create_client(dict(entry.data))
        self.api: NHDAPI
        self.controller_device_id: str | None = None  # device registry id, set in async_setup_entry
        self._lock = asyncio.Lock()  # one command/response exchange at a time
        self._device_info: list[DeviceInfo] = []
        self._device_info_time = -float("inf")

    async def _async_setup(self) -> None:
        """Connect and subscribe to notifications (runs once before the first refresh)."""
        # NHDAPI 2.x discovers command modules with blocking imports, so build it off the loop.
        self.api = await self.hass.async_add_executor_job(NHDAPI, self.client)
        try:
            await self.client.connect()
        except AuthenticationError as err:
            raise ConfigEntryAuthFailed(f"Controller at {self.host} rejected the credentials") from err
        except API_ERRORS as err:
            raise UpdateFailed(f"Cannot connect to controller at {self.host}: {err}") from err
        for notification_type in NOTIFICATION_TYPES:
            self.client.notification_handler.register_callback(notification_type, self._on_notification)

    def _on_notification(self, notification: Any) -> None:
        """Handle a controller notification by requesting a debounced refresh."""
        _LOGGER.debug("Notification received: %s", notification)
        if hasattr(notification, "online"):  # endpoint came online/offline: its device info may change
            self._device_info_time = -float("inf")
        self.config_entry.async_create_background_task(
            self.hass, self.async_request_refresh(), f"{DOMAIN} notification refresh"
        )

    async def async_shutdown(self) -> None:
        """Unsubscribe and disconnect."""
        await super().async_shutdown()
        for notification_type in NOTIFICATION_TYPES:
            with suppress(Exception):
                self.client.notification_handler.unregister_callback(notification_type, self._on_notification)
        with suppress(*API_ERRORS):
            await self.client.disconnect()

    async def _async_update_data(self) -> CoordinatorData:
        """Fetch all data, reconnecting first if the link dropped."""
        async with self._lock:
            try:
                if not self.client.is_connected():
                    _LOGGER.debug("Not connected to %s, reconnecting", self.host)
                    await self.client.connect()
                return await self._fetch()
            except AuthenticationError as err:
                raise ConfigEntryAuthFailed(f"Controller at {self.host} rejected the credentials") from err
            except API_ERRORS as err:
                # Drop the link so the next update starts from a clean connection.
                with suppress(*API_ERRORS):
                    await self.client.disconnect()
                raise UpdateFailed(f"Error communicating with controller at {self.host}: {err}") from err

    async def _fetch(self) -> CoordinatorData:
        query = self.api.api_query
        version = await query.config_get_version()
        ip_settings = await query.config_get_ipsetting()
        device_json_list = await query.config_get_devicejsonstring()
        device_status_list = await query.config_get_device_status()
        if time.monotonic() - self._device_info_time > DEVICE_INFO_TTL:
            self._device_info = await query.config_get_device_info()
            self._device_info_time = time.monotonic()
        matrix = await query.matrix_get()

        transmitters, receivers = build_device_collections(
            device_json_list or [], device_status_list or [], self._device_info or []
        )
        return CoordinatorData(
            device_controller=DeviceController.from_wyrestorm_models(version, ip_settings),
            device_transmitters=transmitters,
            device_receivers=receivers,
            matrix_assignments=process_matrix_assignments(matrix),
            last_update=datetime.now(),
        )

    def _command_failed(self, err: Exception) -> HomeAssistantError:
        return HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="command_failed",
            translation_placeholders={"host": self.host, "error": str(err)},
        )

    # Lookups (by alias or true name)
    def find_receiver(self, name: str) -> DeviceReceiver | None:
        """Return the receiver whose alias or true name is `name`."""
        return next((d for d in self.data.device_receivers.values() if name in (d.alias_name, d.true_name)), None)

    def find_transmitter(self, name: str) -> DeviceTransmitter | None:
        """Return the transmitter whose alias or true name is `name`."""
        return next((d for d in self.data.device_transmitters.values() if name in (d.alias_name, d.true_name)), None)

    # Commands
    async def async_set_matrix(self, source: DeviceTransmitter | None, receivers: list[DeviceReceiver]) -> None:
        """Route `source` to `receivers` (None disconnects them), then refresh the matrix."""
        rx = [r.alias_name for r in receivers]
        switch = self.api.media_stream_matrix_switch
        async with self._lock:
            try:
                if source is None:
                    await switch.matrix_set_null(rx)
                else:
                    await switch.matrix_set(source.alias_name, rx)
                matrix = await self.api.api_query.matrix_get()
            except API_ERRORS as err:
                raise self._command_failed(err) from err
            self.async_set_updated_data(replace(self.data, matrix_assignments=process_matrix_assignments(matrix)))

    async def async_set_power(self, receivers: list[DeviceReceiver], power_state: Literal["on", "off"]) -> None:
        """Send display power on/off to the displays attached to `receivers` (no refresh needed)."""
        async with self._lock:
            try:
                await self.api.connected_device_control.config_set_device_sinkpower(
                    power=power_state, rx=[r.alias_name for r in receivers]
                )
            except API_ERRORS as err:
                raise self._command_failed(err) from err

    async def async_reboot(self) -> None:
        """Reboot the controller; the next update reconnects once it is back."""
        async with self._lock:
            try:
                await self.api.reboot_reset.set_reboot()
            except API_ERRORS as err:
                raise self._command_failed(err) from err
            with suppress(*API_ERRORS):
                await self.client.disconnect()
