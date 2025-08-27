"""Device-specific utilities for WyreStorm NetworkHD integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def get_device_display_name(device_id: str, device_info: dict[str, Any], device_data: dict[str, Any]) -> str:
    """Generate standardized device display name.
    
    Creates a consistent display name format for WyreStorm NetworkHD devices
    used across all Home Assistant platforms and entity types.
    
    Args:
        device_id: The device identifier/alias name from the controller
        device_info: Basic device information dictionary containing at least 'type' field
        device_data: Extended device data dictionary, may contain 'ip_address' field
        
    Returns:
        Formatted display name in format: "{DeviceType} - {Name/IP}"
        Examples:
            - "Encoder - Office"
            - "Decoder - 192.168.1.100"
            - "Device - Unknown"
            
    Note:
        If device_id is empty or "unknown", falls back to IP address from device_data.
        If both device_id and IP are unavailable, uses "Unknown" as fallback.
    """
    device_type = device_info.get("type", "device").title()
    
    # Use alias name (device_id) if available, otherwise fall back to IP address
    name_part = device_id
    if not name_part or name_part == "unknown":
        ip_address = device_data.get("ip_address")
        name_part = ip_address if ip_address else "Unknown"
    
    return f"{device_type} - {name_part}"


def create_device_info(
    coordinator_host: str,
    device_id: str,
    device_info: dict[str, Any],
    device_data: dict[str, Any] | None = None,
    is_controller: bool = False
) -> DeviceInfo:
    """Create standardized device info for WyreStorm devices.
    
    Args:
        coordinator_host: The host of the coordinator/controller
        device_id: The device identifier
        device_info: Basic device information
        device_data: Extended device data from coordinator (optional)
        is_controller: Whether this is the controller device itself
        
    Returns:
        DeviceInfo object for Home Assistant device registry
    """
    if is_controller:
        return DeviceInfo(
            identifiers={(DOMAIN, coordinator_host)},
            name=f"Controller - {coordinator_host}",
            manufacturer="WyreStorm",
            model="NetworkHD Controller",
            via_device=None,  # Controller is the root device
        )
    
    device_data = device_data or {}
    device_name = get_device_display_name(device_id, device_info, device_data)
    device_type = device_info.get("type", "device").title()
    model_name = device_info.get("model", f"NetworkHD {device_type}")
    
    return DeviceInfo(
        identifiers={(DOMAIN, f"{coordinator_host}_{device_id}")},
        name=device_name,
        manufacturer="WyreStorm",
        model=model_name,
        via_device=(DOMAIN, coordinator_host),
    )


def get_device_attributes(device_id: str, device_type: str, device_data: dict[str, Any]) -> dict[str, Any]:
    """Get standardized device attributes for state attributes.
    
    Args:
        device_id: The device identifier
        device_type: The device type (encoder/decoder)
        device_data: Device data from coordinator
        
    Returns:
        Dictionary of attributes for entity state
    """
    # Start with base attributes
    attributes = {
        "device_id": device_id,
        "device_type": device_type,
    }
    
    # Add all available device data as attributes, excluding internal/duplicate fields
    excluded_fields = {"name", "type"}  # Already covered by device_id/device_type
    
    for key, value in device_data.items():
        if key not in excluded_fields and value is not None:
            # Clean up attribute names for better display
            clean_key = key.replace("_", " ").title()
            attributes[clean_key] = value
            
    return attributes


def extract_firmware_version(version_info: Any) -> str:
    """Extract firmware version from API response.
    
    Args:
        version_info: Version information from API
        
    Returns:
        Firmware version string or "Unknown" if not found
    """
    if hasattr(version_info, 'core_version'):
        # Version object with core_version attribute
        return version_info.core_version
    elif hasattr(version_info, 'web_version'):
        # Fall back to web_version if core_version not available
        return version_info.web_version  
    elif isinstance(version_info, dict):
        # Dictionary response structure
        return version_info.get("core_version", 
                              version_info.get("version", 
                              version_info.get("firmware", "Unknown")))
    elif isinstance(version_info, str):
        return version_info
    
    return "Unknown"