"""WyreStorm NetworkHD 2 Coordinator.

This module provides the main data coordinator for the WyreStorm NetworkHD 2
Home Assistant integration using the new model structure.
"""

import asyncio
import logging
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from wyrestorm_networkhd import NHDAPI, NetworkHDClientSSH

from .const import (
    CONF_SSH_TIMEOUT,
    CONF_UPDATE_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_SSH_TIMEOUT,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    SSH_HOST_KEY_POLICY,
)
from .models.coordinator import CoordinatorData
from .models.device_controller import DeviceController
from ._utils_coordinator import build_device_collections, process_matrix_assignments

_LOGGER = logging.getLogger(__name__)


class WyreStormCoordinator(DataUpdateCoordinator[CoordinatorData]):
    """WyreStorm NetworkHD 2 data coordinator.

    Manages data fetching and device state synchronization for WyreStorm NetworkHD
    matrix switching systems using the new model structure.

    This coordinator handles:
    - SSH connection management
    - Periodic device status polling
    - Device discovery and state management
    - Matrix routing configuration
    - Controller version and IP settings

    Attributes:
        entry: Config entry containing connection settings
        api: NHDAPI client for device communication
        client: SSH client for network connection
        host: Device hostname/IP address
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ) -> None:
        """Initialize coordinator.

        Args:
            hass: Home Assistant instance
            entry: ConfigEntry containing all connection settings
        """
        super().__init__(
            hass,
            _LOGGER,
            name="WyreStorm NetworkHD 2",
            update_interval=timedelta(seconds=entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)),
        )
        self.entry = entry
        self.host = entry.data[CONF_HOST]
        
        # Create SSH client from entry data
        self.client = NetworkHDClientSSH(
            host=self.host,
            port=entry.data.get(CONF_PORT, DEFAULT_PORT),
            username=entry.data[CONF_USERNAME],
            password=entry.data[CONF_PASSWORD],
            ssh_host_key_policy=SSH_HOST_KEY_POLICY,
            timeout=entry.data.get(CONF_SSH_TIMEOUT, DEFAULT_SSH_TIMEOUT),
        )
        
        # Create API wrapper
        self.api = NHDAPI(self.client)

    async def async_setup(self) -> None:
        """Set up the coordinator and establish connection."""
        try:
            _LOGGER.debug("Starting coordinator setup...")

            # Connect to device
            _LOGGER.debug("Connecting to device at %s...", self.host)
            await self.client.connect()
            _LOGGER.debug("Device connection successful")

            # Initial data fetch using built-in method
            await self.async_config_entry_first_refresh()

            _LOGGER.info("WyreStorm NetworkHD 2 coordinator setup complete")

        except Exception as err:
            _LOGGER.error("Coordinator setup failed: %s", err)
            # Ensure cleanup on failure
            if self.client and self.client.is_connected():
                try:
                    await self.client.disconnect()
                except Exception:
                    pass
            raise

    async def async_shutdown(self) -> None:
        """Shut down the coordinator safely."""
        _LOGGER.debug("Starting coordinator shutdown...")

        # Disconnect client
        if self.client and self.client.is_connected():
            try:
                _LOGGER.debug("Disconnecting client...")
                await self.client.disconnect()
                _LOGGER.debug("Client disconnected successfully")
            except Exception as err:
                _LOGGER.warning("Error disconnecting client: %s", err)

        _LOGGER.info("WyreStorm NetworkHD 2 coordinator shutdown complete")

    async def _async_update_data(self) -> CoordinatorData:
        """Fetch data from the device."""
        _LOGGER.debug("Starting data update...")

        try:
            # Fetch all required data from API (no retry wrapper since client handles retries)
            _LOGGER.debug("Fetching version data...")
            version = await self.api.api_query.config_get_version()

            _LOGGER.debug("Fetching IP settings...")
            ip_settings = await self.api.api_query.config_get_ipsetting()

            _LOGGER.debug("Fetching device JSON...")
            device_json_list = await self.api.api_query.config_get_devicejsonstring()

            _LOGGER.debug("Fetching device status...")
            device_status_list = await self.api.api_query.config_get_device_status()

            _LOGGER.debug("Fetching device info...")
            device_info_list = await self.api.api_query.config_get_device_info()

            _LOGGER.debug("Fetching matrix data...")
            matrix = await self.api.api_query.matrix_get()

            _LOGGER.debug(
                "Retrieved data: version=%s, ip_settings=%s, device_json=%d devices, "
                "device_status=%d devices, device_info=%d devices, matrix=%s",
                version is not None,
                ip_settings is not None,
                len(device_json_list) if device_json_list else 0,
                len(device_status_list) if device_status_list else 0,
                len(device_info_list) if device_info_list else 0,
                matrix is not None,
            )

            # Create controller device
            controller = DeviceController.from_wyrestorm_models(version, ip_settings)

            # Build device collections
            transmitters, receivers = build_device_collections(
                device_json_list or [], device_status_list or [], device_info_list or []
            )

            # Process matrix assignments
            matrix_assignments = process_matrix_assignments(matrix)

            # Create coordinator data
            data = CoordinatorData(
                device_controller=controller,
                device_transmitters=transmitters,
                device_receivers=receivers,
                matrix_assignments=matrix_assignments,
                last_update=datetime.now(),
            )

            _LOGGER.debug(
                "Data update successful: %d transmitters, %d receivers, %d matrix assignments",
                len(transmitters),
                len(receivers),
                len(matrix_assignments),
            )
            return data

        except Exception as err:
            _LOGGER.error("Data update failed: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}")

    # Service methods
    async def set_matrix(self, source: str | list[str], target: str | list[str]) -> None:
        """Set matrix routing with validation.
        
        Args:
            source: Source device(s) alias name
            target: Target device(s) alias name
        """
        if isinstance(source, str):
            source = [source]
        if isinstance(target, str):
            target = [target]
            
        # Validate devices exist by alias name
        if self.data:
            valid_source_aliases = {tx.alias_name for tx in self.data.get_transmitters_list()}
            valid_target_aliases = {rx.alias_name for rx in self.data.get_receivers_list()}
            
            for src in source:
                if src not in valid_source_aliases:
                    raise ValueError(f"Source device '{src}' not found")
            
            for tgt in target:
                if tgt not in valid_target_aliases:
                    raise ValueError(f"Target device '{tgt}' not found")
        
        # Execute matrix commands using alias names
        for src in source:
            await self.api.media_stream_matrix_switch.matrix_set(src, target)
        
        # Refresh data
        await self.async_request_refresh()
        _LOGGER.info("Matrix set successful: %s -> %s", source, target)

    async def set_power(self, devices: str | list[str], power_state: str) -> None:
        """Control device power with validation.
        
        Args:
            devices: Device(s) true name
            power_state: "on" or "off"
        """
        if isinstance(devices, str):
            devices = [devices]
        
        if power_state not in ["on", "off"]:
            raise ValueError(f"Invalid power state: {power_state}")
        
        # Validate devices exist and are receivers
        if self.data:
            valid_receivers = set(self.data.device_receivers.keys())
            
            for device in devices:
                if device not in valid_receivers:
                    raise ValueError(f"Device '{device}' not found or does not support power control")
        
        # Send power commands
        for device in devices:
            await self.api.connected_device_control.config_set_device_sinkpower(
                power=power_state, rx=device
            )
        
        # Refresh data
        await self.async_request_refresh()
        _LOGGER.info("Power control successful: %s -> %s", devices, power_state)

    # Public API methods
    def is_ready(self) -> bool:
        """Check if coordinator is ready and has data."""
        return self.data is not None

    def get_device_count(self) -> int:
        """Get the total number of devices available."""
        if not self.is_ready():
            return 0
        return len(self.data.device_transmitters) + len(self.data.device_receivers)

    def get_transmitters(self) -> list:
        """Get all transmitter devices."""
        if not self.is_ready():
            return []
        return self.data.get_transmitters_list()

    def get_receivers(self) -> list:
        """Get all receiver devices."""
        if not self.is_ready():
            return []
        return self.data.get_receivers_list()

    def get_controller(self) -> DeviceController | None:
        """Get the controller device."""
        if not self.is_ready():
            return None
        return self.data.device_controller

    async def wait_for_data(self, timeout: int = 30) -> bool:
        """Wait for data to be available with timeout."""
        start_time = asyncio.get_event_loop().time()

        while not self.is_ready() and (asyncio.get_event_loop().time() - start_time) < timeout:
            _LOGGER.debug(
                "Waiting for coordinator data... (%.1fs remaining)",
                timeout - (asyncio.get_event_loop().time() - start_time),
            )
            await asyncio.sleep(1)

            # Try to refresh if we don't have data
            if not self.data:
                try:
                    await self.async_request_refresh()
                except Exception as err:
                    _LOGGER.debug("Refresh attempt failed: %s", err)

        return self.is_ready()

    @property
    def device_info(self) -> dr.DeviceInfo:
        """Return device info for the main hub."""
        return dr.DeviceInfo(
            identifiers={(DOMAIN, self.host)},
            name=f"WyreStorm NetworkHD 2 ({self.host})",
            manufacturer="WyreStorm",
            model="NetworkHD Controller",
            sw_version=self.data.device_controller.version if self.data else None,
            configuration_url=f"http://{self.host}",
        )