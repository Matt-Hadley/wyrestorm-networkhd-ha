"""WyreStorm NetworkHD Coordinator.

This module provides the main data coordinator for the WyreStorm NetworkHD
Home Assistant integration using the new model structure.
"""

import asyncio
import logging
from contextlib import suppress
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from wyrestorm_networkhd import NHDAPI, NetworkHDClientSSH

from ._cache_utils import cache_for_seconds
from ._utils_coordinator import build_device_collections, process_matrix_assignments
from .const import (
    CONF_UPDATE_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_UPDATE_INTERVAL,
    SSH_HOST_KEY_POLICY,
)
from .models.coordinator import CoordinatorData
from .models.device_controller import DeviceController
from .models.device_receiver_transmitter import DeviceReceiver, DeviceTransmitter

_LOGGER = logging.getLogger(__name__)


class WyreStormCoordinator(DataUpdateCoordinator[CoordinatorData]):
    """WyreStorm NetworkHD data coordinator.

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
            name="WyreStorm NetworkHD",
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
        )

        # Create API wrapper
        self.api = NHDAPI(self.client)

    def _register_notification_handlers(self) -> None:
        """Register callbacks for real-time notifications from the device.

        Notifications provide instant updates for:
        - Device online/offline events (endpoint notifications)
        - Video signal found/lost events (video notifications)
        """
        if not hasattr(self.client, "notification_handler"):
            _LOGGER.warning("Client does not support notifications")
            return

        handler = self.client.notification_handler

        # Register for device online/offline notifications
        handler.register_callback("endpoint", lambda n: asyncio.create_task(self._on_endpoint_notification(n)))

        # Register for video found/lost notifications
        handler.register_callback("video", lambda n: asyncio.create_task(self._on_video_notification(n)))

        _LOGGER.info("Registered notification handlers for endpoint and video events")

    async def _on_endpoint_notification(self, notification) -> None:
        """Handle device online/offline notifications.

        Args:
            notification: NotificationEndpoint object with device status change
        """
        try:
            device_name = notification.device
            is_online = notification.online

            _LOGGER.info(
                "Device %s notification: %s is now %s",
                "online" if is_online else "offline",
                device_name,
                "online" if is_online else "offline",
            )

            # Refresh device JSON data to update online status
            await self.async_selective_refresh(["device_jsonstring"])

        except Exception as err:
            _LOGGER.error("Error handling endpoint notification: %s", err)

    async def _on_video_notification(self, notification) -> None:
        """Handle video found/lost notifications.

        Args:
            notification: NotificationVideo object with video status change
        """
        try:
            device_name = notification.device
            video_status = notification.status  # "found" or "lost"
            source_device = notification.source_device

            _LOGGER.info(
                "Video %s notification: %s %s %s",
                video_status,
                device_name,
                f"from {source_device}" if source_device else "",
                "video signal",
            )

            # Refresh device status to update video input state
            await self.async_selective_refresh(["device_status"])

        except Exception as err:
            _LOGGER.error("Error handling video notification: %s", err)

    @cache_for_seconds(600)  # Cache device info for 10 minutes
    async def _get_cached_device_info(self):
        """Get device info with caching to reduce API calls.

        Device info contains network configuration that rarely changes,
        so we cache it for 10 minutes to reduce API load.
        """
        _LOGGER.debug("Fetching device info from API (will be cached for 10 minutes)...")
        return await self.api.api_query.config_get_device_info()

    async def async_setup(self) -> None:
        """Set up the coordinator and establish connection."""
        try:
            _LOGGER.debug("Starting coordinator setup...")

            # Connect to device
            _LOGGER.debug("Connecting to device at %s...", self.host)
            await self.client.connect()
            _LOGGER.debug("Device connection successful")

            # Register notification callbacks
            self._register_notification_handlers()
            _LOGGER.debug("Notification handlers registered")

            # Initial data fetch using built-in method
            await self.async_config_entry_first_refresh()

            _LOGGER.info("WyreStorm NetworkHD coordinator setup complete")

        except Exception as err:
            _LOGGER.error("Coordinator setup failed: %s", err)
            # Ensure cleanup on failure
            if self.client and self.client.is_connected():
                with suppress(Exception):
                    await self.client.disconnect()
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

        _LOGGER.info("WyreStorm NetworkHD coordinator shutdown complete")

    async def async_selective_refresh(self, refresh_only: list[str]) -> None:
        """Perform selective data refresh for specific data types.

        This method allows targeted API calls to refresh only the data that has
        actually changed, reducing network overhead and improving performance.

        Args:
            refresh_only: List of data types to refresh. Options:
                - "matrix_assignments": Matrix routing data only (~200ms API call)
                - "device_status": Device status data only (~300ms API call)
                - "device_jsonstring": Device JSON data only (~250ms API call)

        Raises:
            UpdateFailed: If API calls fail and fallback full refresh also fails.

        Note:
            Device info is automatically cached and doesn't need selective refresh.
            Falls back to full refresh if selective refresh fails.
        """
        if not self.data:
            _LOGGER.warning("No existing coordinator data - performing full refresh")
            await self.async_request_refresh()
            return

        try:
            _LOGGER.debug("Starting selective data refresh for: %s", refresh_only)

            # Start with existing data
            updated_data = CoordinatorData(
                device_controller=self.data.device_controller,
                device_transmitters=self.data.device_transmitters.copy(),
                device_receivers=self.data.device_receivers.copy(),
                matrix_assignments=self.data.matrix_assignments.copy(),
            )

            # Selectively update requested data types
            if "matrix_assignments" in refresh_only:
                _LOGGER.debug("Refreshing matrix assignments...")
                matrix = await self.api.api_query.matrix_get()
                updated_data.matrix_assignments = process_matrix_assignments(matrix)

            if "device_status" in refresh_only:
                _LOGGER.debug("Refreshing device status only...")
                device_status_list = await self.api.api_query.config_get_device_status()

                # Reconstruct device JSON from existing device data (no API call needed)
                device_json_list = []
                for device in list(self.data.device_transmitters.values()) + list(self.data.device_receivers.values()):
                    from wyrestorm_networkhd.models.api_query import DeviceJsonString

                    device_json = DeviceJsonString(
                        aliasName=device.alias_name,
                        deviceType=device.device_type,
                        ip=device.ip,
                        online=device.online,  # This will be updated from fresh status if changed
                        sequence=device.sequence,
                        trueName=device.true_name,
                        group="",  # Default empty group
                    )
                    device_json_list.append(device_json)

                # Use existing device info cache
                device_info_list = await self._get_cached_device_info()

                # Rebuild device collections with fresh status but cached info
                transmitters, receivers = build_device_collections(
                    device_json_list, device_status_list, device_info_list
                )
                updated_data.device_transmitters = transmitters
                updated_data.device_receivers = receivers

            if "device_jsonstring" in refresh_only:
                _LOGGER.debug("Refreshing device JSON string only...")
                device_json_list = await self.api.api_query.config_get_devicejsonstring()

                # Use existing device status and device info cache
                device_status_list = []
                for device in list(self.data.device_transmitters.values()) + list(self.data.device_receivers.values()):
                    from wyrestorm_networkhd.models.api_query import DeviceStatus

                    device_status = DeviceStatus(
                        aliasName=device.alias_name,
                        online=device.online,
                        trueName=device.true_name,
                    )
                    device_status_list.append(device_status)

                device_info_list = await self._get_cached_device_info()

                # Rebuild device collections with fresh JSON but existing status/info
                transmitters, receivers = build_device_collections(
                    device_json_list, device_status_list, device_info_list
                )
                updated_data.device_transmitters = transmitters
                updated_data.device_receivers = receivers

            # Update timestamp and set data
            updated_data.last_update = datetime.now()
            self.async_set_updated_data(updated_data)

            _LOGGER.debug("Selective refresh completed for: %s", refresh_only)

        except Exception as err:
            _LOGGER.error("Selective refresh failed: %s", err)
            # Fall back to full refresh on error
            await self.async_request_refresh()

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

            # Use cached device info (automatically cached for 10 minutes)
            device_info_list = await self._get_cached_device_info()

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
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    # Service methods
    async def set_matrix(self, source: str | list[str] | None, target: str | list[str]) -> None:
        """Set matrix routing with validation.

        Args:
            source: Source device(s) alias name, or None to disconnect target(s)
            target: Target device(s) alias name
        """
        if isinstance(target, str):
            target = [target]

        # Validate target devices exist (common for both connect and disconnect)
        if self.data:
            valid_target_aliases = {rx.alias_name for rx in self.data.get_receivers_list()}
            for tgt in target:
                if tgt not in valid_target_aliases:
                    raise ValueError(f"Target device '{tgt}' not found")

        # Handle disconnect case (source is None)
        if source is None:
            # Disconnect targets (set to no source)
            await self.api.media_stream_matrix_switch.matrix_set_null(target)
            _LOGGER.info("Disconnected receivers: %s", target)
        else:
            # Handle normal matrix routing
            if isinstance(source, str):
                source = [source]

            # Validate source devices exist
            if self.data:
                valid_source_aliases = {tx.alias_name for tx in self.data.get_transmitters_list()}
                for src in source:
                    if src not in valid_source_aliases:
                        raise ValueError(f"Source device '{src}' not found")

            # Execute matrix commands using alias names
            for src in source:
                await self.api.media_stream_matrix_switch.matrix_set(src, target)

            _LOGGER.info("Matrix set successful: %s -> %s", source, target)

        # Refresh data - matrix assignments
        await self.async_selective_refresh(["matrix_assignments"])
        # Also refresh device status to update any video input changes (i.e. could have switched
        # to a source with no video, so video output will be affected)
        await self.async_selective_refresh(["device_status"])

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
            await self.api.connected_device_control.config_set_device_sinkpower(power=power_state, rx=device)

        # No refresh needed - sink power only affects connected displays, not device status
        _LOGGER.info("Power control successful: %s -> %s", devices, power_state)

    # Public API methods
    def is_ready(self) -> bool:
        """Check if coordinator is ready and has data.

        Returns:
            True if coordinator has successfully fetched data, False otherwise.

        Note:
            Used by entities to verify data availability before accessing properties.
        """
        return self.data is not None

    def get_device_count(self) -> int:
        """Get the total number of devices available.

        Returns:
            Total count of transmitters and receivers, or 0 if not ready.
        """
        if not self.is_ready():
            return 0
        return len(self.data.device_transmitters) + len(self.data.device_receivers)

    def get_transmitters(self) -> list[DeviceTransmitter]:
        """Get all transmitter devices.

        Returns:
            List of DeviceTransmitter objects, or empty list if not ready.

        Note:
            Returns a copy of the internal list to prevent external modifications.
        """
        if not self.is_ready():
            return []
        return list(self.data.device_transmitters.values())

    def get_receivers(self) -> list[DeviceReceiver]:
        """Get all receiver devices.

        Returns:
            List of DeviceReceiver objects, or empty list if not ready.

        Note:
            Returns a copy of the internal list to prevent external modifications.
        """
        if not self.is_ready():
            return []
        return list(self.data.device_receivers.values())

    def get_controller(self) -> DeviceController | None:
        """Get the controller device.

        Returns:
            DeviceController object if available, None if not ready.

        Note:
            The controller represents the NetworkHD matrix switching unit itself.
        """
        if not self.is_ready():
            return None
        controller = self.data.device_controller
        return controller if isinstance(controller, DeviceController) else None

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
