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
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryError, HomeAssistantError
from homeassistant.helpers import (
    device_registry as dr,
    issue_registry as ir,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from wyrestorm_networkhd import NHDAPI, HostKeyMismatchError, NetworkHDClientSSH, normalize_fingerprints
from wyrestorm_networkhd.exceptions import AuthenticationError, NetworkHDError
from wyrestorm_networkhd.models.api_query import DeviceInfo, DeviceStatus, Matrix

from ._utils_coordinator import build_device_collections
from .const import (
    CONF_HOST_KEY_FINGERPRINT,
    DEFAULT_PORT,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    SSH_HOST_KEY_POLICY,
)
from .mdns import is_mac
from .models.coordinator import CoordinatorData
from .models.device_receiver_transmitter import DeviceReceiver, DeviceTransmitter

_LOGGER = logging.getLogger(__name__)

# Library errors subclass NetworkHDError; OSError/ValueError catch anything the transport or parsers raise raw.
API_ERRORS = (NetworkHDError, OSError, ValueError)
NOTIFICATION_TYPES = ("endpoint", "video")
DEVICE_INFO_TTL = 600  # seconds; device info (MAC, firmware, network) rarely changes
STALE_REFRESHES = 3  # successful refreshes a device must be missing from before it is removed

type WyreStormConfigEntry = ConfigEntry[WyreStormCoordinator]


def create_client(data: dict[str, Any]) -> NetworkHDClientSSH:
    """Create the SSH client from config entry data (pinning the host key when fingerprints are set)."""
    pinned = {"host_key_fingerprints": fps} if (fps := data.get(CONF_HOST_KEY_FINGERPRINT)) else {}
    return NetworkHDClientSSH(
        host=data[CONF_HOST],
        port=data.get(CONF_PORT, DEFAULT_PORT),
        username=data[CONF_USERNAME],
        password=data[CONF_PASSWORD],
        ssh_host_key_policy=SSH_HOST_KEY_POLICY,
        **pinned,
    )


def _assignments(matrix: Matrix) -> dict[str, str | None]:
    """Map receiver alias -> routed transmitter alias (None when disconnected)."""
    return {a.rx: a.tx for a in matrix.assignments}


class WyreStormCoordinator(DataUpdateCoordinator[CoordinatorData]):
    """Owns the controller connection and all API calls.

    Polls as a fallback; controller notifications trigger a debounced refresh. A dropped link
    makes the update fail (entities go unavailable) and the next update reconnects.
    """

    config_entry: WyreStormConfigEntry
    data: CoordinatorData

    def __init__(self, hass: HomeAssistant, entry: WyreStormConfigEntry) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name="WyreStorm NetworkHD",
            update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL),
        )
        self.host: str = entry.data[CONF_HOST]
        self.client = create_client(dict(entry.data))
        self.api: NHDAPI
        self.controller_device_id: str | None = None  # device registry id, set in async_setup_entry
        self._lock = asyncio.Lock()  # one command/response exchange at a time
        self._device_status: list[DeviceStatus] = []  # kept for diagnostics
        self._device_info: list[DeviceInfo] = []
        self._device_info_time = -float("inf")
        self._missing: dict[str, int] = {}  # device registry id -> consecutive refreshes without it

    @property
    def controller_id(self) -> str:
        """Identifier of the controller device: its MAC once known (the entry unique id), else the host.

        Not a host unique id: before 1.0.1 reconfigure left it at the old host while the device followed the new one.
        """
        return uid if is_mac(uid := self.config_entry.unique_id) else self.host

    def device_ids(self, data: CoordinatorData) -> set[str]:
        """Return the identifiers of the devices the controller currently reports, itself included."""
        return {self.controller_id, *data.device_transmitters, *data.device_receivers}

    async def _async_setup(self) -> None:
        """Connect and subscribe to notifications (runs once before the first refresh)."""
        self.api = NHDAPI(self.client)
        try:
            await self._connect()
        except HostKeyMismatchError as err:
            raise self._host_key_mismatch(ConfigEntryError, err) from err  # no retries until reconfigured
        except AuthenticationError as err:
            raise self._error(ConfigEntryAuthFailed, "invalid_auth") from err
        except API_ERRORS as err:
            raise self._error(UpdateFailed, "cannot_connect", error=str(err)) from err
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
        """Unsubscribe and disconnect (after any exchange in progress finishes)."""
        await super().async_shutdown()
        async with self._lock:
            for notification_type in NOTIFICATION_TYPES:
                with suppress(Exception):
                    self.client.notification_handler.unregister_callback(notification_type, self._on_notification)
            with suppress(*API_ERRORS):
                await self.client.disconnect()

    async def _ensure_connected(self) -> None:
        """Reconnect if the link dropped (call with `_lock` held)."""
        if not self.client.is_connected():
            _LOGGER.debug("Not connected to %s, reconnecting", self.host)
            await self._connect()

    def _error[E: HomeAssistantError](self, cls: type[E], key: str, **placeholders: str) -> E:
        """Build a translated exception about this controller."""
        return cls(
            translation_domain=DOMAIN,
            translation_key=key,
            translation_placeholders={"host": self.host, **placeholders},
        )

    def _host_key_mismatch[E: HomeAssistantError](self, cls: type[E], err: HostKeyMismatchError) -> E:
        return self._error(cls, "host_key_mismatch", fingerprint=err.presented_fingerprint)

    async def _connect(self) -> None:
        """Connect; pin the host key if none is stored; a key mismatch raises a repair issue (and re-raises)."""
        entry = self.config_entry
        issue_id = f"host_key_mismatch_{entry.entry_id}"
        try:
            await self.client.connect()
        except HostKeyMismatchError as err:
            # The library rejects the key before authenticating, so no credentials were sent.
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                issue_id,
                is_fixable=False,
                severity=ir.IssueSeverity.ERROR,
                translation_key="host_key_mismatch",
                translation_placeholders={"host": self.host, "fingerprint": err.presented_fingerprint},
            )
            raise
        ir.async_delete_issue(self.hass, DOMAIN, issue_id)
        # Entries from 1.0.x have no pinned key: trust the one presented now (TOFU).
        if CONF_HOST_KEY_FINGERPRINT not in entry.data and (fingerprint := self.client.host_key_fingerprint):
            self.hass.config_entries.async_update_entry(
                entry, data={**entry.data, CONF_HOST_KEY_FINGERPRINT: [fingerprint]}
            )
            self.client.host_key_fingerprints = normalize_fingerprints(fingerprint)  # pin later reconnects
            _LOGGER.info("Pinned the SSH host key of the controller at %s: %s", self.host, fingerprint)

    async def _async_update_data(self) -> CoordinatorData:
        """Fetch all data, reconnecting first if the link dropped."""
        async with self._lock:
            try:
                await self._ensure_connected()
                data = await self._fetch()
            except HostKeyMismatchError as err:
                # Keep polling (the key is rejected before login) so a returning pinned key recovers on its own.
                raise self._host_key_mismatch(UpdateFailed, err) from err
            except AuthenticationError as err:
                raise self._error(ConfigEntryAuthFailed, "invalid_auth") from err
            except API_ERRORS as err:
                # Drop the link so the next update starts from a clean connection.
                with suppress(*API_ERRORS):
                    await self.client.disconnect()
                raise self._error(UpdateFailed, "update_failed", error=str(err)) from err
        self._remove_stale_devices(data)
        return data

    def _remove_stale_devices(self, data: CoordinatorData) -> None:
        """Remove devices of this entry the controller has stopped reporting (removed endpoints, an old controller id).

        The controller lists every endpoint it knows, offline ones included. A device goes only after it is
        missing from STALE_REFRESHES successful refreshes in a row, and never while the controller reports no
        endpoints at all (as it may while it starts).
        """
        if not (data.device_transmitters or data.device_receivers):
            return
        current = self.device_ids(data)
        dev_reg = dr.async_get(self.hass)
        for device in dr.async_entries_for_config_entry(dev_reg, self.config_entry.entry_id):
            if any(domain == DOMAIN and name in current for domain, name in device.identifiers):
                self._missing.pop(device.id, None)
            elif (missing := self._missing.get(device.id, 0) + 1) < STALE_REFRESHES:
                self._missing[device.id] = missing
            else:
                _LOGGER.info("Removing device %s: the controller at %s no longer reports it", device.name, self.host)
                dev_reg.async_update_device(device.id, remove_config_entry_id=self.config_entry.entry_id)
                del self._missing[device.id]

    async def _fetch(self) -> CoordinatorData:
        query = self.api.api_query
        version = await query.config_get_version()
        device_json_list = await query.config_get_devicejsonstring()
        self._device_status = await query.config_get_device_status()
        if time.monotonic() - self._device_info_time > DEVICE_INFO_TTL:
            self._device_info = await query.config_get_device_info()
            self._device_info_time = time.monotonic()
        matrix = await query.matrix_get()

        transmitters, receivers = build_device_collections(
            device_json_list or [], self._device_status or [], self._device_info or []
        )
        return CoordinatorData(
            version=version,
            device_transmitters=transmitters,
            device_receivers=receivers,
            matrix_assignments=_assignments(matrix),
            last_update=datetime.now(),
        )

    def _command_failed(self, err: Exception) -> HomeAssistantError:
        return self._error(HomeAssistantError, "command_failed", error=str(err))

    # Lookups (by alias or true name)
    def find_receiver(self, name: str) -> DeviceReceiver | None:
        """Return the receiver whose alias or true name is `name`."""
        return next((d for d in self.data.device_receivers.values() if name in (d.alias_name, d.true_name)), None)

    def find_transmitter(self, name: str) -> DeviceTransmitter | None:
        """Return the transmitter whose alias or true name is `name`."""
        return next((d for d in self.data.device_transmitters.values() if name in (d.alias_name, d.true_name)), None)

    # Commands
    async def async_set_matrix(self, source: DeviceTransmitter | None, receivers: list[DeviceReceiver]) -> None:
        """Route `source` to `receivers` (None disconnects them), then re-read the matrix."""
        rx = [r.alias_name for r in receivers]
        async with self._lock:
            try:
                await self._ensure_connected()
                switch = self.api.media_stream_matrix_switch
                if source is None:
                    await switch.matrix_set_null(rx)
                else:
                    await switch.matrix_set(source.alias_name, rx)
            except API_ERRORS as err:
                raise self._command_failed(err) from err
            try:
                matrix = await self.api.api_query.matrix_get()
            except API_ERRORS as err:
                # The switch succeeded; only the read-back failed, so let a full refresh catch up.
                _LOGGER.debug("Matrix read-back from %s failed: %s", self.host, err)
                self.config_entry.async_create_background_task(
                    self.hass, self.async_request_refresh(), f"{DOMAIN} matrix refresh"
                )
                return
        # Not async_set_updated_data: that would cancel a pending debounced refresh and reset the poll timer.
        self.data = replace(self.data, matrix_assignments=_assignments(matrix))
        self.async_update_listeners()

    async def async_set_power(self, receivers: list[DeviceReceiver], power_state: Literal["on", "off"]) -> None:
        """Send display power on/off to the displays attached to `receivers` (no refresh needed)."""
        async with self._lock:
            try:
                await self._ensure_connected()
                await self.api.connected_device_control.config_set_device_sinkpower(
                    power=power_state, rx=[r.alias_name for r in receivers]
                )
            except API_ERRORS as err:
                raise self._command_failed(err) from err

    async def async_reboot(self) -> None:
        """Reboot the controller; entities are unavailable until an update reconnects once it is back."""
        async with self._lock:
            try:
                await self._ensure_connected()
                await self.api.reboot_reset.set_reboot()
            except API_ERRORS as err:
                raise self._command_failed(err) from err
            with suppress(*API_ERRORS):
                await self.client.disconnect()
        self.async_set_update_error(self._error(UpdateFailed, "rebooting"))
