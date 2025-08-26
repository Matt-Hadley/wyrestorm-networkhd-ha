"""WyreStorm NetworkHD Coordinator."""
import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers import device_registry as dr

from wyrestorm_networkhd import NetworkHDClientSSH, NHDAPI

from .const import (
    UPDATE_INTERVAL_FAST,
    RETRY_ATTEMPTS,
    RETRY_DELAY,
)

_LOGGER = logging.getLogger(__name__)


class WyreStormCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """WyreStorm NetworkHD data coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: NHDAPI,
        client: NetworkHDClientSSH,
        host: str,
        update_interval_seconds: int = 60,
    ) -> None:
        """Initialize coordinator."""
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
                _LOGGER.debug("Starting coordinator setup (attempt %d/%d)...", attempt + 1, RETRY_ATTEMPTS)
                
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
                _LOGGER.debug("Initial data fetch complete, data: %s", 
                             "available" if self.data else "None")
                
                _LOGGER.info("WyreStorm coordinator setup complete")
                return  # Success, exit retry loop
                
            except Exception as err:
                if attempt < RETRY_ATTEMPTS - 1:
                    _LOGGER.warning("Coordinator setup attempt %d failed, retrying in %.1fs: %s", 
                                   attempt + 1, RETRY_DELAY, err)
                    await asyncio.sleep(RETRY_DELAY)
                else:
                    _LOGGER.error("Coordinator setup failed after %d attempts: %s", RETRY_ATTEMPTS, err)
                    # Ensure we have at least empty data structure
                    _LOGGER.debug("Attempting to create empty data structure...")
                    await self._async_update_data()
                    raise

    async def async_shutdown(self) -> None:
        """Shut down the coordinator."""
        # Cancel notification task
        if self._notification_task and not self._notification_task.done():
            self._notification_task.cancel()
            
        # Disconnect client
        if self.client.is_connected():
            await self.client.disconnect()
            
        _LOGGER.debug("WyreStorm coordinator shutdown complete")

    def _setup_notifications(self) -> None:
        """Set up real-time notifications."""
        
        def handle_endpoint_notification(notification):
            """Handle endpoint status notifications."""
            _LOGGER.debug("Endpoint notification: %s", notification)
            
            # Parse endpoint notification and update device online status
            if self.data and "devices" in self.data:
                try:
                    # Extract device information from notification
                    device_id = None
                    online_status = None
                    
                    if hasattr(notification, 'device_id'):
                        device_id = notification.device_id
                    elif hasattr(notification, 'device'):
                        device_id = notification.device
                    elif isinstance(notification, dict):
                        device_id = notification.get('device_id') or notification.get('device') or notification.get('aliasName')
                    
                    if hasattr(notification, 'online'):
                        online_status = notification.online
                    elif hasattr(notification, 'status'):
                        online_status = notification.status == 'online'
                    elif isinstance(notification, dict):
                        online_status = notification.get('online')
                        if online_status is None and 'status' in notification:
                            online_status = notification['status'] == 'online'
                    
                    # Update device data if we have both device ID and status
                    if device_id and device_id in self.data["devices"] and online_status is not None:
                        self.data["devices"][device_id]["online"] = bool(online_status)
                        _LOGGER.info("Updated online status for %s: %s", device_id, online_status)
                    
                except Exception as err:
                    _LOGGER.error("Error processing endpoint notification: %s", err)
            
            # Trigger coordinator update
            self.async_set_updated_data(self.data)
            
        def handle_video_notification(notification):
            """Handle video input notifications."""
            _LOGGER.debug("Video notification: %s", notification)
            
            # Parse video notification and update HDMI activity status
            if self.data and "devices" in self.data:
                try:
                    # Extract device information from notification
                    device_id = None
                    hdmi_in_active = None
                    hdmi_out_active = None
                    
                    if hasattr(notification, 'device_id'):
                        device_id = notification.device_id
                    elif hasattr(notification, 'device'):
                        device_id = notification.device
                    elif isinstance(notification, dict):
                        device_id = notification.get('device_id') or notification.get('device') or notification.get('aliasName')
                    
                    # Check for HDMI input activity
                    if hasattr(notification, 'hdmi_in_active'):
                        hdmi_in_active = notification.hdmi_in_active
                    elif isinstance(notification, dict):
                        hdmi_in_active = notification.get('hdmi_in_active')
                        if hdmi_in_active is None and 'hdmi in active' in notification:
                            hdmi_in_active = notification['hdmi in active'] == 'true'
                    
                    # Check for HDMI output activity
                    if hasattr(notification, 'hdmi_out_active'):
                        hdmi_out_active = notification.hdmi_out_active
                    elif isinstance(notification, dict):
                        hdmi_out_active = notification.get('hdmi_out_active')
                        if hdmi_out_active is None and 'hdmi out active' in notification:
                            hdmi_out_active = notification['hdmi out active'] == 'true'
                    
                    # Update device data if we have device ID and status changes
                    if device_id and device_id in self.data["devices"]:
                        updated = False
                        if hdmi_in_active is not None:
                            self.data["devices"][device_id]["hdmi_in_active"] = bool(hdmi_in_active)
                            updated = True
                        if hdmi_out_active is not None:
                            self.data["devices"][device_id]["hdmi_out_active"] = bool(hdmi_out_active)
                            updated = True
                        
                        if updated:
                            _LOGGER.info("Updated HDMI activity for %s: in=%s, out=%s", 
                                        device_id, hdmi_in_active, hdmi_out_active)
                    
                except Exception as err:
                    _LOGGER.error("Error processing video notification: %s", err)
            
            # Trigger coordinator update
            self.async_set_updated_data(self.data)

        # Register notification callbacks
        self.client.register_notification_callback("endpoint", handle_endpoint_notification)
        self.client.register_notification_callback("video", handle_video_notification)

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
                        _LOGGER.debug("Fetching device JSON (attempt %d/%d)...", dev_attempt + 1, RETRY_ATTEMPTS)
                        device_json = await self.api.api_query.config_get_devicejsonstring()
                        _LOGGER.debug("Device JSON fetched: %s devices", len(device_json) if isinstance(device_json, list) else "unknown")
                        break
                    except Exception as err:
                        if dev_attempt == RETRY_ATTEMPTS - 1:
                            _LOGGER.warning("Failed to get device JSON after %d attempts: %s", RETRY_ATTEMPTS, err)
                            device_json = []
                        else:
                            _LOGGER.debug("Device JSON attempt %d failed, retrying in %.1fs: %s", 
                                         dev_attempt + 1, RETRY_DELAY, err)
                            # Try to reconnect if this looks like a connection error
                            if "Not connected" in str(err) or "connection" in str(err).lower():
                                await self._attempt_reconnect()
                            await asyncio.sleep(RETRY_DELAY)
                
                # Get matrix status with retry
                matrix = None
                for matrix_attempt in range(RETRY_ATTEMPTS):
                    try:
                        _LOGGER.debug("Fetching matrix status (attempt %d/%d)...", matrix_attempt + 1, RETRY_ATTEMPTS)
                        matrix = await self.api.api_query.matrix_get()
                        _LOGGER.debug("Matrix status fetched: %s", type(matrix))
                        break
                    except Exception as err:
                        if matrix_attempt == RETRY_ATTEMPTS - 1:
                            _LOGGER.warning("Failed to get matrix status after %d attempts: %s", RETRY_ATTEMPTS, err)
                            matrix = {}
                        else:
                            _LOGGER.debug("Matrix status attempt %d failed, retrying in %.1fs: %s", 
                                         matrix_attempt + 1, RETRY_DELAY, err)
                            # Try to reconnect if this looks like a connection error
                            if "Not connected" in str(err) or "connection" in str(err).lower():
                                await self._attempt_reconnect()
                            await asyncio.sleep(RETRY_DELAY)
                
                # Get device status with retry
                device_status = None
                for status_attempt in range(RETRY_ATTEMPTS):
                    try:
                        _LOGGER.debug("Fetching device status (attempt %d/%d)...", status_attempt + 1, RETRY_ATTEMPTS)
                        device_status = await self.api.api_query.config_get_device_status()
                        _LOGGER.debug("Device status fetched: %s", type(device_status))
                        break
                    except Exception as err:
                        if status_attempt == RETRY_ATTEMPTS - 1:
                            _LOGGER.warning("Failed to get device status after %d attempts: %s", RETRY_ATTEMPTS, err)
                            device_status = {}
                        else:
                            _LOGGER.debug("Device status attempt %d failed, retrying in %.1fs: %s", 
                                         status_attempt + 1, RETRY_DELAY, err)
                            # Try to reconnect if this looks like a connection error
                            if "Not connected" in str(err) or "connection" in str(err).lower():
                                await self._attempt_reconnect()
                            await asyncio.sleep(RETRY_DELAY)
                
                # If we got any data, process it and return
                if device_json or matrix or device_status:
                    _LOGGER.debug("Raw data: device_json=%s devices, matrix=%s (type: %s), device_status=%s (type: %s)", 
                                 len(device_json) if isinstance(device_json, list) else "unknown", 
                                 matrix, type(matrix), device_status, type(device_status))
                    
                    # Raw data will be stored in the returned data structure
                    
                    # Process devices by combining device JSON (online status) with device status (HDMI status)
                    processed_devices = {}
                    
                    # Create lookup dictionaries from both data sources
                    device_json_dict = {}
                    if isinstance(device_json, list):
                        for device_data in device_json:
                            if isinstance(device_data, dict):
                                device_id = device_data.get("aliasName", "unknown")
                                device_json_dict[device_id] = device_data
                        _LOGGER.debug("Created device JSON lookup for %d devices", len(device_json_dict))
                    
                    device_status_dict = {}
                    if isinstance(device_status, dict) and "devices status" in device_status:
                        for status_data in device_status.get("devices status", []):
                            if isinstance(status_data, dict):
                                status_alias = status_data.get("aliasname", "unknown")
                                device_status_dict[status_alias] = status_data
                        _LOGGER.debug("Created device status lookup for %d devices", len(device_status_dict))
                    
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
                            model_name = json_data.get("trueName") or status_data.get("name", f"NetworkHD {device_type.title()}")
                            
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
                                
                                processed_devices[device_id].update({
                                    "power_state": "on" if (hdmi_in_active or hdmi_out_active) else "off",
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
                                })
                            
                            _LOGGER.debug("Processed device %s: %s (%s) - Online: %s, IP: %s", 
                                         device_id, device_type, model_name, 
                                         processed_devices[device_id]["online"],
                                         processed_devices[device_id]["ip_address"])
                        
                        # Log successful processing
                        if processed_devices:
                            _LOGGER.info("Successfully processed %d real devices from device status", len(processed_devices))
                        else:
                            _LOGGER.warning("No devices found in device status")
                    else:
                        _LOGGER.warning("No device status data available")
                    
                    # Now process matrix information to fill in current_source and available_sources
                    if processed_devices and matrix:
                        try:
                            # Extract matrix assignments
                            matrix_assignments = []
                            if hasattr(matrix, 'assignments'):
                                matrix_assignments = matrix.assignments
                            elif isinstance(matrix, dict) and 'assignments' in matrix:
                                matrix_assignments = matrix['assignments']
                            
                            # Process matrix assignments
                            for assignment in matrix_assignments:
                                if hasattr(assignment, 'tx') and hasattr(assignment, 'rx'):
                                    source = assignment.tx
                                    destination = assignment.rx
                                elif isinstance(assignment, dict):
                                    source = assignment.get('tx')
                                    destination = assignment.get('rx')
                                else:
                                    continue
                                
                                # Update destination device with current source
                                if destination in processed_devices:
                                    processed_devices[destination]["current_source"] = source
                                    _LOGGER.debug("Matrix: %s -> %s", source, destination)
                            
                            # Update available sources for all decoder devices
                            encoder_devices = [dev_id for dev_id, dev_info in processed_devices.items() 
                                             if dev_info.get("type") == "encoder"]
                            
                            for dev_id, dev_info in processed_devices.items():
                                if dev_info.get("type") == "decoder":
                                    dev_info["available_sources"] = encoder_devices
                                    
                        except Exception as err:
                            _LOGGER.warning("Failed to process matrix data: %s", err)
                    
                    from datetime import datetime
                    data = {
                        "devices": processed_devices,
                        "matrix": matrix,
                        "device_status": device_status,
                        "last_update": datetime.utcnow().isoformat() + "Z",
                    }
                    
                    _LOGGER.debug("Data update successful: %d devices", len(processed_devices))
                    _LOGGER.debug("Final data structure: %s", list(data.keys()))
                    return data
                
                # If we get here, all API calls failed but we should retry the whole operation
                if attempt < RETRY_ATTEMPTS - 1:
                    _LOGGER.warning("All API calls failed on attempt %d, retrying in %.1fs...", 
                                   attempt + 1, RETRY_DELAY)
                    await asyncio.sleep(RETRY_DELAY)
                else:
                    _LOGGER.error("All API calls failed after %d attempts", RETRY_ATTEMPTS)
                    break
                    
            except Exception as err:
                if attempt < RETRY_ATTEMPTS - 1:
                    _LOGGER.warning("Data update attempt %d failed, retrying in %.1fs: %s", 
                                   attempt + 1, RETRY_DELAY, err)
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
            "error": "All retry attempts failed"
        }


    async def wait_for_data(self, timeout: int = 30) -> bool:
        """Wait for data to be available with timeout."""
        start_time = asyncio.get_event_loop().time()
        
        while not self.is_ready() and (asyncio.get_event_loop().time() - start_time) < timeout:
            _LOGGER.debug("Waiting for coordinator data... (%.1fs remaining)", 
                         timeout - (asyncio.get_event_loop().time() - start_time))
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
        return self.data.get("error")

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
        return self.data.get("devices", {}).get(device_id)

    def get_all_devices(self) -> dict[str, Any]:
        """Get all device information."""
        if not self.is_ready():
            return {}
        return self.data.get("devices", {})

    @property
    def device_info(self) -> dr.DeviceInfo:
        """Return device info for the main hub."""
        return dr.DeviceInfo(
            identifiers={(self.host, self.host)},
            name=f"WyreStorm NetworkHD ({self.host})",
            manufacturer="WyreStorm",
            model="NetworkHD Controller",
            configuration_url=f"http://{self.host}",
        )

