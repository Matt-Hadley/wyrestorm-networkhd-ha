"""WyreStorm NetworkHD Coordinator.

This module provides the main data coordinator for the WyreStorm NetworkHD
Home Assistant integration. The coordinator manages device connections,
data fetching, and real-time notifications from the NetworkHD controller.
"""

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from wyrestorm_networkhd import NHDAPI, NetworkHDClientSSH

try:
    from wyrestorm_networkhd.models.api_query import DeviceInfo, DeviceJsonString, DeviceStatus
except ImportError:
    # Fallback for testing or when models aren't available
    DeviceInfo = Any
    DeviceJsonString = Any
    DeviceStatus = Any

from .const import RETRY_ATTEMPTS, RETRY_DELAY

_LOGGER = logging.getLogger(__name__)


# =============================================================================
# CORE DATA CLASSES
# =============================================================================


class MergedDeviceData:
    """Represents merged device data from DeviceInfo, DeviceJsonString and DeviceStatus sources."""

    def __init__(
        self,
        device_id: str,
        device_info: DeviceInfo | None = None,
        device_json: DeviceJsonString | None = None,
        device_status: DeviceStatus | None = None,
    ):
        """Initialize with device data from all sources."""
        self.device_id: str = device_id
        self.device_info: DeviceInfo | None = device_info
        self.device_json: DeviceJsonString | None = device_json
        self.device_status: DeviceStatus | None = device_status
        # Matrix-related attributes (filled later by matrix processing)
        self.current_source: str | None = None
        self.available_sources: list[str] = []
        # Notification-updatable attributes
        self.online: bool = False
        self.hdmi_in_active: bool = False
        self.hdmi_out_active: bool = False


class DeviceCollection:
    """Collection of MergedDeviceData objects with convenient access methods."""

    def __init__(self):
        """Initialize empty device collection."""
        self._devices: dict[str, MergedDeviceData] = {}

    def add_device(self, device: MergedDeviceData) -> None:
        """Add a device to the collection."""
        self._devices[device.device_id] = device

    def get_device(self, device_id: str) -> MergedDeviceData | None:
        """Get a device by ID."""
        return self._devices.get(device_id)

    def __contains__(self, device_id: str) -> bool:
        """Check if device exists in collection."""
        return device_id in self._devices

    def __getitem__(self, device_id: str) -> MergedDeviceData:
        """Get device by ID (raises KeyError if not found)."""
        return self._devices[device_id]

    def __len__(self) -> int:
        """Get number of devices."""
        return len(self._devices)

    def __iter__(self):
        """Iterate over device IDs."""
        return iter(self._devices)

    def items(self):
        """Get device ID and device pairs."""
        return self._devices.items()

    def values(self):
        """Get all devices."""
        return self._devices.values()

    def get_encoders(self) -> list[str]:
        """Get list of encoder device IDs."""
        return [
            device_id
            for device_id, device in self._devices.items()
            if device.device_json
            and hasattr(device.device_json, "deviceType")
            and device.device_json.deviceType == "transmitter"
        ]

    def get_decoders(self) -> list[MergedDeviceData]:
        """Get list of decoder devices."""
        return [
            device
            for device in self._devices.values()
            if device.device_json
            and hasattr(device.device_json, "deviceType")
            and device.device_json.deviceType == "receiver"
        ]


class CoordinatorData:
    """Type-safe data structure for coordinator data."""

    def __init__(
        self,
        devices: DeviceCollection,
        matrix: Any,
        device_status: list,
        device_info: list,
        last_update: str | None = None,
        error: str | None = None,
    ):
        self.devices = devices
        self.matrix = matrix
        self.device_status = device_status
        self.device_info = device_info
        self.last_update = last_update
        self.error = error

    def __getitem__(self, key):
        """Support dictionary-style access for backward compatibility."""
        if key == "devices":
            # Return a dictionary-like view of devices for backward compatibility
            devices_dict = {}
            for device_id, device in self.devices.items():
                # Convert MergedDeviceData to dictionary format for tests
                device_dict = {
                    "online": device.online,
                    "type": (
                        "encoder"
                        if (device.device_json and getattr(device.device_json, "deviceType", None) == "transmitter")
                        else "decoder"
                        if (device.device_json and getattr(device.device_json, "deviceType", None) == "receiver")
                        else "unknown"
                    ),
                    "hdmi_in_active": device.hdmi_in_active,
                    "hdmi_out_active": device.hdmi_out_active,
                }
                # Add attributes from device_json
                if device.device_json:
                    for attr in dir(device.device_json):
                        if not attr.startswith("_"):
                            device_dict[attr] = getattr(device.device_json, attr, None)
                # Add attributes from device_status
                if device.device_status:
                    for attr in dir(device.device_status):
                        if not attr.startswith("_"):
                            device_dict[attr] = getattr(device.device_status, attr, None)
                # Add attributes from device_info
                if device.device_info:
                    for attr in dir(device.device_info):
                        if not attr.startswith("_"):
                            device_dict[attr] = getattr(device.device_info, attr, None)
                devices_dict[device_id] = device_dict
            return devices_dict
        elif hasattr(self, key):
            return getattr(self, key)
        else:
            raise KeyError(f"Key '{key}' not found")

    def get(self, key, default=None):
        """Support dict.get() method for backward compatibility."""
        try:
            return self[key]
        except KeyError:
            return default


# =============================================================================
# MAIN COORDINATOR CLASS
# =============================================================================


class WyreStormCoordinator(DataUpdateCoordinator[CoordinatorData]):
    """WyreStorm NetworkHD data coordinator.

    Manages data fetching, device state synchronization, and real-time
    notifications for WyreStorm NetworkHD matrix switching systems.

    This coordinator handles:
    - Periodic device status polling
    - Real-time notification processing from SSH connection
    - Device discovery and state management
    - Matrix routing configuration
    - Connection recovery and retry logic

    Attributes:
        api: NHDAPI client for device communication
        client: SSH client for network connection
        host: Device hostname/IP address
        _notification_task: Background task for handling notifications
    """

    # =========================================================================
    # INITIALIZATION & SETUP
    # =========================================================================

    def __init__(
        self,
        hass: HomeAssistant,
        api: NHDAPI,
        client: NetworkHDClientSSH,
        host: str,
        update_interval_seconds: int = 60,
    ) -> None:
        """Initialize coordinator.

        Args:
            hass: Home Assistant instance
            api: Configured NHDAPI client for device communication
            client: SSH client connected to the NetworkHD controller
            host: Device hostname or IP address
            update_interval_seconds: Polling interval in seconds (default: 60)
        """
        from datetime import timedelta

        super().__init__(
            hass,
            _LOGGER,
            name="WyreStorm NetworkHD",
            update_interval=timedelta(seconds=update_interval_seconds),
        )
        self.api = api
        self.client = client
        self.host = host
        self._notification_task: asyncio.Task | None = None

    async def async_setup(self) -> None:
        """Set up the coordinator."""
        for attempt in range(RETRY_ATTEMPTS):
            try:
                _LOGGER.debug(
                    "Starting coordinator setup (attempt %d/%d)...",
                    attempt + 1,
                    RETRY_ATTEMPTS,
                )

                # Connect to device with retry
                _LOGGER.debug("Connecting to device...")
                await self.client.connect()
                _LOGGER.debug("Device connection successful")

                # Set up notification callbacks
                _LOGGER.debug("Setting up notification callbacks...")
                self._setup_notifications()

                # Initial data fetch
                _LOGGER.debug("Performing initial data fetch...")
                await self._async_update_data()
                _LOGGER.debug(
                    "Initial data fetch complete, data: %s",
                    "available" if self.data else "None",
                )

                _LOGGER.info("WyreStorm coordinator setup complete")
                return  # Success, exit retry loop

            except Exception as err:
                if attempt < RETRY_ATTEMPTS - 1:
                    _LOGGER.warning(
                        "Coordinator setup attempt %d failed, retrying in %.1fs: %s",
                        attempt + 1,
                        RETRY_DELAY,
                        err,
                    )
                    await asyncio.sleep(RETRY_DELAY)
                else:
                    _LOGGER.error(
                        "Coordinator setup failed after %d attempts: %s",
                        RETRY_ATTEMPTS,
                        err,
                    )
                    # Ensure we have at least empty data structure
                    _LOGGER.debug("Attempting to create empty data structure...")
                    await self._async_update_data()
                    raise

    async def async_shutdown(self) -> None:
        """Shut down the coordinator safely."""
        _LOGGER.debug("Starting coordinator shutdown...")

        # Cancel notification task first and wait for it to complete
        if self._notification_task and not self._notification_task.done():
            _LOGGER.debug("Cancelling notification task...")
            self._notification_task.cancel()
            try:
                await self._notification_task
            except asyncio.CancelledError:
                _LOGGER.debug("Notification task cancelled successfully")
            except Exception as err:
                _LOGGER.warning("Error during notification task cancellation: %s", err)

        # Then disconnect client
        if self.client and self.client.is_connected():
            try:
                _LOGGER.debug("Disconnecting client...")
                await self.client.disconnect()
                _LOGGER.debug("Client disconnected successfully")
            except Exception as err:
                _LOGGER.warning("Error disconnecting client: %s", err)

        _LOGGER.info("WyreStorm coordinator shutdown complete")

    # =========================================================================
    # DATA FETCHING & PROCESSING
    # =========================================================================

    async def _async_update_data(self) -> CoordinatorData:
        """Fetch data from the device."""
        _LOGGER.debug("Starting data update...")

        # Retry logic for data fetching
        for attempt in range(RETRY_ATTEMPTS):
            try:
                _LOGGER.debug("Data update attempt %d/%d", attempt + 1, RETRY_ATTEMPTS)

                # Get all device data using retry helper
                device_json = await self._retry_api_call("device JSON", self.api.api_query.config_get_devicejsonstring)
                matrix = await self._retry_api_call("matrix status", self.api.api_query.matrix_get, default_value={})
                device_status = await self._retry_api_call("device status", self.api.api_query.config_get_device_status)
                device_info = await self._retry_api_call("device info", self.api.api_query.config_get_device_info)

                # Process the typed responses directly
                device_json_list = device_json or []
                device_status_list = device_status or []
                device_info_list = device_info or []
                matrix_response = matrix

                # If we got any valid data, process it and return
                if device_json_list or matrix_response or device_status_list or device_info_list:
                    matrix_assignments_count = 0
                    if matrix_response and hasattr(matrix_response, "assignments"):
                        matrix_assignments_count = (
                            len(matrix_response.assignments) if matrix_response.assignments else 0
                        )
                    _LOGGER.debug(
                        "Retrieved data: device_json=%d devices, matrix=%d assignments, "
                        "device_status=%d devices, device_info=%d devices",
                        len(device_json_list),
                        matrix_assignments_count,
                        len(device_status_list),
                        len(device_info_list),
                    )

                    # Build device collection
                    devices = self._build_device_collection(device_json_list, device_status_list, device_info_list)

                    # Process matrix assignments to fill current_source and available_sources
                    self._process_matrix_assignments(devices, matrix_response)

                    from datetime import datetime

                    data = CoordinatorData(
                        devices=devices,
                        matrix=matrix_response,
                        device_status=device_status_list,
                        device_info=device_info_list,
                        last_update=datetime.now(datetime.UTC).isoformat() + "Z",
                    )

                    _LOGGER.debug("Data update successful: %d devices", len(devices))
                    return data

                # If we get here, all API calls failed but we should retry the whole operation
                if attempt < RETRY_ATTEMPTS - 1:
                    _LOGGER.warning(
                        "All API calls failed on attempt %d, retrying in %.1fs...",
                        attempt + 1,
                        RETRY_DELAY,
                    )
                    await asyncio.sleep(RETRY_DELAY)
                else:
                    _LOGGER.error("All API calls failed after %d attempts", RETRY_ATTEMPTS)
                    break

            except Exception as err:
                if attempt < RETRY_ATTEMPTS - 1:
                    _LOGGER.warning(
                        "Data update attempt %d failed, retrying in %.1fs: %s",
                        attempt + 1,
                        RETRY_DELAY,
                        err,
                    )
                    await asyncio.sleep(RETRY_DELAY)
                else:
                    _LOGGER.error("Data update failed after %d attempts: %s", RETRY_ATTEMPTS, err)
                    break

        # If we get here, all attempts failed
        _LOGGER.error("All data update attempts failed, returning empty data structure")
        return CoordinatorData(
            devices=DeviceCollection(),
            matrix={},
            device_status=[],
            device_info=[],
            last_update=None,
            error="All retry attempts failed",
        )

    def _build_device_collection(
        self, device_json_list: list, device_status_list: list, device_info_list: list
    ) -> DeviceCollection:
        """Build device collection from all data sources."""
        devices = DeviceCollection()

        # Collect all unique device names from all sources
        all_device_names = set()
        for device_data in device_json_list:
            if hasattr(device_data, "trueName") and device_data.trueName:
                all_device_names.add(device_data.trueName)
        for status_data in device_status_list:
            if hasattr(status_data, "name") and status_data.name:
                all_device_names.add(status_data.name)
        for info_data in device_info_list:
            if hasattr(info_data, "name") and info_data.name:
                all_device_names.add(info_data.name)

        # Create devices by matching data across all sources
        for device_name in all_device_names:
            # Find matching data from each source
            json_data = next(
                (d for d in device_json_list if hasattr(d, "trueName") and d.trueName == device_name), None
            )
            status_data = next((d for d in device_status_list if hasattr(d, "name") and d.name == device_name), None)
            info_data = next((d for d in device_info_list if hasattr(d, "name") and d.name == device_name), None)

            # Create device with all available data
            device = MergedDeviceData(device_name, info_data, json_data, status_data)

            # Initialize derived attributes
            device.online = json_data.online if json_data else False
            device.hdmi_in_active = (
                status_data.hdmi_in_active if status_data and hasattr(status_data, "hdmi_in_active") else False
            )
            device.hdmi_out_active = (
                status_data.hdmi_out_active if status_data and hasattr(status_data, "hdmi_out_active") else False
            )

            devices.add_device(device)

            _LOGGER.debug(
                "Created device %s: info=%s, json=%s, status=%s, online=%s",
                device_name,
                device.device_info is not None,
                device.device_json is not None,
                device.device_status is not None,
                device.online,
            )

        # Log successful processing
        if len(devices) > 0:
            _LOGGER.info("Successfully processed %d devices from all data sources", len(devices))
        else:
            _LOGGER.warning("No devices found in any data source")

        return devices

    def _process_matrix_assignments(self, devices: DeviceCollection, matrix_response: Any) -> None:
        """Process matrix assignments to fill current_source and available_sources."""
        if not (devices and matrix_response and hasattr(matrix_response, "assignments")):
            return
        try:
            # Process matrix assignments from typed response
            matrix_assignments = matrix_response.assignments or []

            # Process matrix assignments (typed objects only)
            for assignment in matrix_assignments:
                if hasattr(assignment, "tx") and hasattr(assignment, "rx"):
                    source = assignment.tx
                    destination = assignment.rx
                    # Update destination device with current source
                    if destination in devices:
                        devices[destination].current_source = source
                        _LOGGER.debug("Matrix: %s -> %s", source, destination)

            # Update available sources for all decoder devices using the collection's methods
            encoder_devices = devices.get_encoders()
            for device in devices.get_decoders():
                device.available_sources = encoder_devices

        except Exception as err:
            _LOGGER.warning("Failed to process matrix data: %s", err)

    # =========================================================================
    # NOTIFICATION HANDLING
    # =========================================================================

    def _setup_notifications(self) -> None:
        """Set up real-time notifications."""

        def handle_endpoint_notification(notification: Any) -> None:
            """Handle endpoint status notifications."""
            self._handle_notification("endpoint", notification, {"online": "_extract_online_status_from_notification"})

        def handle_video_notification(notification: Any) -> None:
            """Handle video input notifications."""
            self._handle_notification(
                "video",
                notification,
                {
                    "hdmi_in_active": "_extract_hdmi_in_status_from_notification",
                    "hdmi_out_active": "_extract_hdmi_out_status_from_notification",
                },
            )

        # Register notification callbacks
        self.client.register_notification_callback("endpoint", handle_endpoint_notification)
        self.client.register_notification_callback("video", handle_video_notification)

    def _handle_notification(self, notification_type: str, notification: Any, field_updates: dict[str, str]) -> None:
        """Generic notification handler for device updates."""
        _LOGGER.debug("%s notification: %s", notification_type.title(), notification)

        # Validate coordinator state before processing
        if not self.data or not self.data.devices:
            _LOGGER.warning("Coordinator data not available for notification processing")
            return

        try:
            # Extract device information from notification
            device_id = self._extract_device_id_from_notification(notification)
            if not device_id or device_id not in self.data.devices:
                _LOGGER.debug("Invalid notification: device_id=%s", device_id)
                return

            # Extract and update field values
            updated = False
            device: MergedDeviceData = self.data.devices[device_id]
            update_log_parts = []

            for field_name, extraction_method in field_updates.items():
                field_value = getattr(self, extraction_method)(notification)
                if field_value is not None and hasattr(device, field_name):
                    setattr(device, field_name, field_value)
                    update_log_parts.append(f"{field_name}={field_value}")
                    updated = True

            if updated:
                _LOGGER.info("Updated %s for %s: %s", notification_type, device_id, ", ".join(update_log_parts))
                # Trigger coordinator update
                self.async_set_updated_data(self.data)

        except (KeyError, AttributeError, TypeError) as err:
            _LOGGER.warning("Malformed %s notification: %s - %s", notification_type, type(err).__name__, err)
        except Exception as err:
            _LOGGER.error("Critical error processing %s notification: %s", notification_type, err)

    # =========================================================================
    # PUBLIC API METHODS
    # =========================================================================

    def is_ready(self) -> bool:
        """Check if coordinator is ready and has data."""
        return self.data is not None and self.data.devices is not None

    def has_errors(self) -> bool:
        """Check if coordinator data contains errors."""
        if not self.data:
            return True
        return self.data.error is not None

    def get_error_message(self) -> str | None:
        """Get error message if coordinator has errors."""
        if not self.has_errors():
            return None
        return self.data.error

    def get_device_count(self) -> int:
        """Get the number of devices available."""
        if not self.is_ready():
            return 0
        return len(self.data.devices)

    def get_device_info(self, device_id: str) -> MergedDeviceData | None:
        """Get information for a specific device."""
        if not self.is_ready():
            return None
        return self.data.devices.get_device(device_id)

    def get_all_devices(self) -> DeviceCollection:
        """Get all device information."""
        if not self.is_ready():
            return DeviceCollection()
        return self.data.devices

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

    async def force_refresh(self) -> bool:
        """Force a refresh and wait for completion."""
        try:
            await self.async_request_refresh()
            # Wait for the refresh to complete
            await asyncio.sleep(1)
            return self.data is not None
        except Exception as err:
            _LOGGER.error("Force refresh failed: %s", err)
            return False

    @property
    def device_info(self) -> dr.DeviceInfo:
        """Return device info for the main hub."""
        from .const import DOMAIN

        return dr.DeviceInfo(
            identifiers={(DOMAIN, self.host)},
            name=f"WyreStorm NetworkHD ({self.host})",
            manufacturer="WyreStorm",
            model="NetworkHD Controller",
            configuration_url=f"http://{self.host}",
        )

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    async def _retry_api_call(self, api_call_name: str, api_call_func, default_value=None):
        """Generic retry wrapper for API calls."""
        for attempt in range(RETRY_ATTEMPTS):
            try:
                _LOGGER.debug(
                    "Fetching %s (attempt %d/%d)...",
                    api_call_name,
                    attempt + 1,
                    RETRY_ATTEMPTS,
                )
                result = await api_call_func()
                _LOGGER.debug("%s fetched: %s", api_call_name, type(result))
                return result
            except Exception as err:
                if attempt == RETRY_ATTEMPTS - 1:
                    _LOGGER.warning(
                        "Failed to get %s after %d attempts: %s",
                        api_call_name,
                        RETRY_ATTEMPTS,
                        err,
                    )
                    return default_value if default_value is not None else []
                else:
                    _LOGGER.debug(
                        "%s attempt %d failed, retrying in %.1fs: %s",
                        api_call_name,
                        attempt + 1,
                        RETRY_DELAY,
                        err,
                    )
                    # Try to reconnect if this looks like a connection error
                    if "Not connected" in str(err) or "connection" in str(err).lower():
                        await self._attempt_reconnect()
                    await asyncio.sleep(RETRY_DELAY)

    async def _attempt_reconnect(self) -> bool:
        """Attempt to reconnect to the device."""
        try:
            _LOGGER.info("Attempting to reconnect to NetworkHD controller...")

            # Check if client is still connected
            if self.client.is_connected():
                _LOGGER.debug("Client is still connected, no reconnection needed")
                return True

            # Try to reconnect
            await self.client.connect()
            _LOGGER.info("Reconnection successful")
            return True

        except Exception as err:
            _LOGGER.error("Reconnection failed: %s", err)
            return False

    def _extract_from_notification(self, notification: Any, field_mappings: dict[str, list[str]]) -> dict[str, Any]:
        """Generic helper to extract multiple values from a notification object."""
        result = {}

        for result_key, field_names in field_mappings.items():
            value = None

            # Try to extract from object attributes
            for field_name in field_names:
                if hasattr(notification, field_name):
                    attr_value = getattr(notification, field_name, None)
                    if attr_value is not None:
                        value = attr_value
                        break

            # If not found and notification is a dict, try dict keys
            if value is None and isinstance(notification, dict):
                for field_name in field_names:
                    dict_value = notification.get(field_name)
                    if dict_value is not None:
                        value = dict_value
                        break

            result[result_key] = value

        return result

    def _extract_device_id_from_notification(self, notification: Any) -> str | None:
        """Extract device ID from notification safely."""
        try:
            result = self._extract_from_notification(
                notification, {"device_id": ["device_id", "device", "trueName", "name", "aliasName"]}
            )
            device_id = result.get("device_id")
            return str(device_id) if device_id is not None else None
        except (AttributeError, KeyError):
            return None

    def _extract_online_status_from_notification(self, notification: Any) -> bool | None:
        """Extract online status from notification safely."""
        try:
            result = self._extract_from_notification(notification, {"online": ["online"], "status": ["status"]})

            online_value = result.get("online")
            if online_value is not None:
                return bool(online_value)

            status_value = result.get("status")
            if status_value is not None:
                return status_value == "online"

            return None
        except (AttributeError, KeyError, TypeError):
            return None

    def _extract_hdmi_in_status_from_notification(self, notification: Any) -> bool | None:
        """Extract HDMI input status from notification safely."""
        try:
            result = self._extract_from_notification(
                notification, {"hdmi_in_active": ["hdmi_in_active", "hdmi in active"]}
            )

            hdmi_value = result.get("hdmi_in_active")
            if hdmi_value is not None:
                return bool(hdmi_value) if hdmi_value != "true" else True
            return None
        except (AttributeError, KeyError, TypeError):
            return None

    def _extract_hdmi_out_status_from_notification(self, notification: Any) -> bool | None:
        """Extract HDMI output status from notification safely."""
        try:
            result = self._extract_from_notification(
                notification, {"hdmi_out_active": ["hdmi_out_active", "hdmi out active"]}
            )

            hdmi_value = result.get("hdmi_out_active")
            if hdmi_value is not None:
                return bool(hdmi_value) if hdmi_value != "true" else True
            return None
        except (AttributeError, KeyError, TypeError):
            return None
