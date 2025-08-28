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

from .const import RETRY_ATTEMPTS, RETRY_DELAY

_LOGGER = logging.getLogger(__name__)


class WyreStormCoordinator(DataUpdateCoordinator[dict[str, Any]]):
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

    def _setup_notifications(self) -> None:
        """Set up real-time notifications."""

        def handle_endpoint_notification(notification) -> None:
            """Handle endpoint status notifications."""
            _LOGGER.debug("Endpoint notification: %s", notification)

            # Validate coordinator state before processing
            if not self.data or "devices" not in self.data:
                _LOGGER.warning("Coordinator data not available for notification processing")
                return

            try:
                # Extract device information from notification with validation
                device_id = self._extract_device_id_from_notification(notification)
                online_status = self._extract_online_status_from_notification(notification)

                # Update device data if we have valid device ID and status
                if device_id and device_id in self.data["devices"] and online_status is not None:
                    self.data["devices"][device_id]["online"] = bool(online_status)
                    _LOGGER.info("Updated online status for %s: %s", device_id, online_status)

                    # Trigger coordinator update
                    self.async_set_updated_data(self.data)
                else:
                    _LOGGER.debug(
                        "Invalid notification data: device_id=%s, status=%s",
                        device_id,
                        online_status,
                    )

            except (KeyError, AttributeError, TypeError) as err:
                _LOGGER.warning("Malformed endpoint notification: %s - %s", type(err).__name__, err)
            except Exception as err:
                _LOGGER.error("Critical error processing endpoint notification: %s", err)
                # Don't update coordinator data if processing failed critically

        def handle_video_notification(notification) -> None:
            """Handle video input notifications."""
            _LOGGER.debug("Video notification: %s", notification)

            # Validate coordinator state before processing
            if not self.data or "devices" not in self.data:
                _LOGGER.warning("Coordinator data not available for notification processing")
                return

            try:
                # Extract device information from notification with validation
                device_id = self._extract_device_id_from_notification(notification)
                hdmi_in_active = self._extract_hdmi_in_status_from_notification(notification)
                hdmi_out_active = self._extract_hdmi_out_status_from_notification(notification)

                # Update device data if we have device ID and valid status changes
                if device_id and device_id in self.data["devices"]:
                    updated = False
                    device_data = self.data["devices"][device_id]

                    if hdmi_in_active is not None:
                        device_data["hdmi_in_active"] = bool(hdmi_in_active)
                        updated = True
                    if hdmi_out_active is not None:
                        device_data["hdmi_out_active"] = bool(hdmi_out_active)
                        updated = True

                    if updated:
                        _LOGGER.info(
                            "Updated HDMI activity for %s: in=%s, out=%s",
                            device_id,
                            hdmi_in_active,
                            hdmi_out_active,
                        )
                        # Trigger coordinator update
                        self.async_set_updated_data(self.data)
                else:
                    _LOGGER.debug("Invalid video notification: device_id=%s", device_id)

            except (KeyError, AttributeError, TypeError) as err:
                _LOGGER.warning("Malformed video notification: %s - %s", type(err).__name__, err)
            except Exception as err:
                _LOGGER.error("Critical error processing video notification: %s", err)
                # Don't update coordinator data if processing failed critically

        # Register notification callbacks
        self.client.register_notification_callback("endpoint", handle_endpoint_notification)
        self.client.register_notification_callback("video", handle_video_notification)

    def _extract_device_id_from_notification(self, notification: Any) -> str | None:
        """Extract device ID from notification safely."""
        try:
            if hasattr(notification, "device_id"):
                device_id = getattr(notification, "device_id", None)
                return str(device_id) if device_id is not None else None
            elif hasattr(notification, "device"):
                device = getattr(notification, "device", None)
                return str(device) if device is not None else None
            elif isinstance(notification, dict):
                device_id = notification.get("device_id") or notification.get("device") or notification.get("aliasName")
                return str(device_id) if device_id is not None else None
        except (AttributeError, KeyError):
            pass
        return None

    def _extract_online_status_from_notification(self, notification: Any) -> bool | None:
        """Extract online status from notification safely."""
        try:
            if hasattr(notification, "online"):
                online_attr = getattr(notification, "online", None)
                return bool(online_attr) if online_attr is not None else None
            elif hasattr(notification, "status"):
                status_attr = getattr(notification, "status", None)
                return status_attr == "online" if status_attr is not None else None
            elif isinstance(notification, dict):
                online_status = notification.get("online")
                if online_status is not None:
                    return bool(online_status)
                if "status" in notification:
                    status_value = notification["status"]
                    return status_value == "online" if status_value is not None else None
        except (AttributeError, KeyError, TypeError):
            pass
        return None

    def _extract_hdmi_in_status_from_notification(self, notification: Any) -> bool | None:
        """Extract HDMI input status from notification safely."""
        try:
            if hasattr(notification, "hdmi_in_active"):
                hdmi_attr = getattr(notification, "hdmi_in_active", None)
                return bool(hdmi_attr) if hdmi_attr is not None else None
            elif isinstance(notification, dict):
                hdmi_in_active = notification.get("hdmi_in_active")
                if hdmi_in_active is not None:
                    return bool(hdmi_in_active)
                if "hdmi in active" in notification:
                    hdmi_value = notification["hdmi in active"]
                    return hdmi_value == "true" if hdmi_value is not None else None
        except (AttributeError, KeyError, TypeError):
            pass
        return None

    def _extract_hdmi_out_status_from_notification(self, notification: Any) -> bool | None:
        """Extract HDMI output status from notification safely."""
        try:
            if hasattr(notification, "hdmi_out_active"):
                hdmi_attr = getattr(notification, "hdmi_out_active", None)
                return bool(hdmi_attr) if hdmi_attr is not None else None
            elif isinstance(notification, dict):
                hdmi_out_active = notification.get("hdmi_out_active")
                if hdmi_out_active is not None:
                    return bool(hdmi_out_active)
                if "hdmi out active" in notification:
                    hdmi_value = notification["hdmi out active"]
                    return hdmi_value == "true" if hdmi_value is not None else None
        except (AttributeError, KeyError, TypeError):
            pass
        return None

    def _validate_device_json(self, device_json: Any) -> list[dict[str, Any]]:
        """Validate and clean device JSON response."""
        if not isinstance(device_json, list):
            _LOGGER.warning(
                "Invalid device JSON structure, expected list, got %s",
                type(device_json),
            )
            return []

        valid_devices = []
        for item in device_json:
            if isinstance(item, dict) and item.get("aliasName"):
                valid_devices.append(item)
            else:
                _LOGGER.debug("Skipping invalid device JSON item: %s", item)

        return valid_devices

    def _validate_device_status(self, device_status: Any) -> dict[str, Any]:
        """Validate and clean device status response."""
        if not isinstance(device_status, dict):
            _LOGGER.warning(
                "Invalid device status structure, expected dict, got %s",
                type(device_status),
            )
            return {}

        if "devices status" not in device_status:
            _LOGGER.warning("Device status missing 'devices status' key")
            return {}

        devices_status = device_status.get("devices status", [])
        if not isinstance(devices_status, list):
            _LOGGER.warning(
                "Device status 'devices status' should be list, got %s",
                type(devices_status),
            )
            return {"devices status": []}

        valid_status_list = []
        for item in devices_status:
            if isinstance(item, dict) and item.get("aliasname"):
                valid_status_list.append(item)
            else:
                _LOGGER.debug("Skipping invalid device status item: %s", item)

        return {"devices status": valid_status_list}

    def _validate_matrix_response(self, matrix: Any) -> dict[str, Any]:
        """Validate and clean matrix response."""
        if matrix is None:
            return {}

        # Handle both object and dict responses
        if hasattr(matrix, "assignments"):
            assignments = matrix.assignments
        elif isinstance(matrix, dict) and "assignments" in matrix:
            assignments = matrix["assignments"]
        else:
            _LOGGER.warning("Invalid matrix response structure: %s", type(matrix))
            return {}

        if not isinstance(assignments, list):
            _LOGGER.warning("Matrix assignments should be list, got %s", type(assignments))
            return {}

        valid_assignments = []
        for assignment in assignments:
            # Validate assignment has required fields
            if (
                hasattr(assignment, "tx")
                and hasattr(assignment, "rx")
                or isinstance(assignment, dict)
                and "tx" in assignment
                and "rx" in assignment
            ):
                valid_assignments.append(assignment)
            else:
                _LOGGER.debug("Skipping invalid matrix assignment: %s", assignment)

        return {"assignments": valid_assignments}

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

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the device."""
        _LOGGER.debug("Starting data update...")

        # Retry logic for data fetching
        for attempt in range(RETRY_ATTEMPTS):
            try:
                _LOGGER.debug("Data update attempt %d/%d", attempt + 1, RETRY_ATTEMPTS)

                # Get device JSON with online status and IP addresses
                device_json = None
                for dev_attempt in range(RETRY_ATTEMPTS):
                    try:
                        _LOGGER.debug(
                            "Fetching device JSON (attempt %d/%d)...",
                            dev_attempt + 1,
                            RETRY_ATTEMPTS,
                        )
                        device_json = await self.api.api_query.config_get_devicejsonstring()
                        _LOGGER.debug(
                            "Device JSON fetched: %s devices",
                            (len(device_json) if isinstance(device_json, list) else "unknown"),
                        )
                        break
                    except Exception as err:
                        if dev_attempt == RETRY_ATTEMPTS - 1:
                            _LOGGER.warning(
                                "Failed to get device JSON after %d attempts: %s",
                                RETRY_ATTEMPTS,
                                err,
                            )
                            device_json = []
                        else:
                            _LOGGER.debug(
                                "Device JSON attempt %d failed, retrying in %.1fs: %s",
                                dev_attempt + 1,
                                RETRY_DELAY,
                                err,
                            )
                            # Try to reconnect if this looks like a connection error
                            if "Not connected" in str(err) or "connection" in str(err).lower():
                                await self._attempt_reconnect()
                            await asyncio.sleep(RETRY_DELAY)

                # Get matrix status with retry
                matrix = None
                for matrix_attempt in range(RETRY_ATTEMPTS):
                    try:
                        _LOGGER.debug(
                            "Fetching matrix status (attempt %d/%d)...",
                            matrix_attempt + 1,
                            RETRY_ATTEMPTS,
                        )
                        matrix = await self.api.api_query.matrix_get()
                        _LOGGER.debug("Matrix status fetched: %s", type(matrix))
                        break
                    except Exception as err:
                        if matrix_attempt == RETRY_ATTEMPTS - 1:
                            _LOGGER.warning(
                                "Failed to get matrix status after %d attempts: %s",
                                RETRY_ATTEMPTS,
                                err,
                            )
                            matrix = {}
                        else:
                            _LOGGER.debug(
                                "Matrix status attempt %d failed, retrying in %.1fs: %s",
                                matrix_attempt + 1,
                                RETRY_DELAY,
                                err,
                            )
                            # Try to reconnect if this looks like a connection error
                            if "Not connected" in str(err) or "connection" in str(err).lower():
                                await self._attempt_reconnect()
                            await asyncio.sleep(RETRY_DELAY)

                # Get device status with retry
                device_status = None
                for status_attempt in range(RETRY_ATTEMPTS):
                    try:
                        _LOGGER.debug(
                            "Fetching device status (attempt %d/%d)...",
                            status_attempt + 1,
                            RETRY_ATTEMPTS,
                        )
                        device_status = await self.api.api_query.config_get_device_status()
                        _LOGGER.debug("Device status fetched: %s", type(device_status))
                        break
                    except Exception as err:
                        if status_attempt == RETRY_ATTEMPTS - 1:
                            _LOGGER.warning(
                                "Failed to get device status after %d attempts: %s",
                                RETRY_ATTEMPTS,
                                err,
                            )
                            device_status = {}
                        else:
                            _LOGGER.debug(
                                "Device status attempt %d failed, retrying in %.1fs: %s",
                                status_attempt + 1,
                                RETRY_DELAY,
                                err,
                            )
                            # Try to reconnect if this looks like a connection error
                            if "Not connected" in str(err) or "connection" in str(err).lower():
                                await self._attempt_reconnect()
                            await asyncio.sleep(RETRY_DELAY)

                # Validate and process the data we received
                validated_device_json = self._validate_device_json(device_json or [])
                validated_matrix = self._validate_matrix_response(matrix)
                validated_device_status = self._validate_device_status(device_status or {})

                # If we got any valid data, process it and return
                if validated_device_json or validated_matrix or validated_device_status:
                    _LOGGER.debug(
                        "Validated data: device_json=%d devices, matrix=%d assignments, device_status=%d devices",
                        len(validated_device_json),
                        len(validated_matrix.get("assignments", [])),
                        len(validated_device_status.get("devices status", [])),
                    )

                    # Raw data will be stored in the returned data structure

                    # Process devices by combining device JSON (online status) with device status (HDMI status)
                    processed_devices = {}

                    # Create lookup dictionaries from validated data sources
                    device_json_dict = {}
                    for device_data in validated_device_json:
                        device_id = device_data.get("aliasName", "unknown")
                        if device_id != "unknown":
                            device_json_dict[device_id] = device_data
                    _LOGGER.debug(
                        "Created device JSON lookup for %d devices",
                        len(device_json_dict),
                    )

                    device_status_dict = {}
                    for status_data in validated_device_status.get("devices status", []):
                        status_alias = status_data.get("aliasname", "unknown")
                        if status_alias != "unknown":
                            device_status_dict[status_alias] = status_data
                    _LOGGER.debug(
                        "Created device status lookup for %d devices",
                        len(device_status_dict),
                    )

                    # Combine data from both sources
                    if device_json_dict or device_status_dict:
                        _LOGGER.info("Processing devices from combined JSON and status data")

                        # Get all unique device IDs from both sources
                        all_device_ids = set(device_json_dict.keys()) | set(device_status_dict.keys())

                        for device_id in all_device_ids:
                            json_data = device_json_dict.get(device_id, {})
                            status_data = device_status_dict.get(device_id, {})

                            # Determine device type from device JSON (deviceType) or status (name)
                            device_type_str = json_data.get("deviceType", "").lower()
                            if device_type_str == "transmitter":
                                device_type = "encoder"
                            elif device_type_str == "receiver":
                                device_type = "decoder"
                            else:
                                # Fallback to checking model name from status
                                model_name = status_data.get("name", "")
                                if "TX" in model_name:
                                    device_type = "encoder"
                                elif "RX" in model_name:
                                    device_type = "decoder"
                                else:
                                    device_type = "decoder"  # Default

                            # Get model name from JSON or status
                            model_name = json_data.get("trueName") or status_data.get(
                                "name", f"NetworkHD {device_type.title()}"
                            )

                            # Create processed device entry combining both data sources
                            processed_devices[device_id] = {
                                "type": device_type,
                                "name": device_id,  # alias name
                                "model": model_name,
                                "online": json_data.get("online", False),  # Online status from device JSON
                                "ip_address": json_data.get("ip"),  # IP address from device JSON
                                "current_source": None,  # Will be filled from matrix data
                                "available_sources": [],  # Will be filled from matrix data
                                # Enhanced data from device status (if available)
                                "power_state": "unknown",
                                "hdmi_in_active": False,
                                "hdmi_out_active": False,
                                "resolution": None,
                                "hdmi_in_frame_rate": None,
                                "hdmi_out_frame_rate": None,
                                "hdmi_out_resolution": None,
                                "audio_input_format": None,
                                "audio_output_format": None,
                                "audio_bitrate": None,
                                "hdcp": None,
                            }

                            # Add device status data if available
                            if status_data:
                                # Determine power state from HDMI activity
                                hdmi_in_active = status_data.get("hdmi in active") == "true"
                                hdmi_out_active = status_data.get("hdmi out active") == "true"

                                processed_devices[device_id].update(
                                    {
                                        "power_state": ("on" if (hdmi_in_active or hdmi_out_active) else "off"),
                                        "hdmi_in_active": hdmi_in_active,
                                        "hdmi_out_active": hdmi_out_active,
                                        "resolution": status_data.get("resolution"),
                                        "hdmi_in_frame_rate": status_data.get("hdmi in frame rate"),
                                        "hdmi_out_frame_rate": status_data.get("hdmi out frame rate"),
                                        "hdmi_out_resolution": status_data.get("hdmi out resolution"),
                                        "audio_input_format": status_data.get("audio input format"),
                                        "audio_output_format": status_data.get("audio output format"),
                                        "audio_bitrate": status_data.get("audio bitrate"),
                                        "hdcp": status_data.get("hdcp"),
                                    }
                                )

                            _LOGGER.debug(
                                "Processed device %s: %s (%s) - Online: %s, IP: %s",
                                device_id,
                                device_type,
                                model_name,
                                processed_devices[device_id]["online"],
                                processed_devices[device_id]["ip_address"],
                            )

                        # Log successful processing
                        if processed_devices:
                            _LOGGER.info(
                                "Successfully processed %d real devices from device status",
                                len(processed_devices),
                            )
                        else:
                            _LOGGER.warning("No devices found in device status")
                    else:
                        _LOGGER.warning("No device status data available")

                    # Now process matrix information to fill in current_source and available_sources
                    if processed_devices and validated_matrix:
                        try:
                            # Process validated matrix assignments
                            matrix_assignments = validated_matrix.get("assignments", [])

                            # Process matrix assignments
                            for assignment in matrix_assignments:
                                if hasattr(assignment, "tx") and hasattr(assignment, "rx"):
                                    source = assignment.tx
                                    destination = assignment.rx
                                elif isinstance(assignment, dict):
                                    source = assignment.get("tx")
                                    destination = assignment.get("rx")
                                else:
                                    continue

                                # Update destination device with current source
                                if destination in processed_devices:
                                    processed_devices[destination]["current_source"] = source
                                    _LOGGER.debug("Matrix: %s -> %s", source, destination)

                            # Update available sources for all decoder devices
                            encoder_devices = [
                                dev_id
                                for dev_id, dev_info in processed_devices.items()
                                if dev_info.get("type") == "encoder"
                            ]

                            for _dev_id, dev_info in processed_devices.items():
                                if dev_info.get("type") == "decoder":
                                    dev_info["available_sources"] = encoder_devices

                        except Exception as err:
                            _LOGGER.warning("Failed to process matrix data: %s", err)

                    from datetime import datetime

                    data = {
                        "devices": processed_devices,
                        "matrix": validated_matrix,
                        "device_status": validated_device_status,
                        "last_update": datetime.utcnow().isoformat() + "Z",
                    }

                    _LOGGER.debug("Data update successful: %d devices", len(processed_devices))
                    _LOGGER.debug("Final data structure: %s", list(data.keys()))
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
        return {
            "devices": {},
            "matrix": {},
            "device_status": {},
            "last_update": None,
            "error": "All retry attempts failed",
        }

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

    def has_errors(self) -> bool:
        """Check if coordinator data contains errors."""
        if not self.data:
            return True
        return "error" in self.data

    def get_error_message(self) -> str | None:
        """Get error message if coordinator has errors."""
        if not self.has_errors():
            return None
        error_value = self.data.get("error")
        return str(error_value) if error_value is not None else None

    def is_ready(self) -> bool:
        """Check if coordinator is ready and has data."""
        return self.data is not None and "devices" in self.data

    def get_device_count(self) -> int:
        """Get the number of devices available."""
        if not self.is_ready():
            return 0
        return len(self.data.get("devices", {}))

    def get_device_info(self, device_id: str) -> dict[str, Any] | None:
        """Get information for a specific device."""
        if not self.is_ready():
            return None
        device_info = self.data.get("devices", {}).get(device_id)
        return dict(device_info) if device_info else None

    def get_all_devices(self) -> dict[str, Any]:
        """Get all device information."""
        if not self.is_ready():
            return {}
        devices_data = self.data.get("devices", {})
        return dict(devices_data) if isinstance(devices_data, dict) else {}

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
