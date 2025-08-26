"""Standardized device naming utilities for WyreStorm NetworkHD integration."""
from typing import Any


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