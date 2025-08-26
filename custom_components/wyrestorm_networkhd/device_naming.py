"""Standardized device naming utilities for WyreStorm NetworkHD integration."""
from typing import Any


def get_device_display_name(device_id: str, device_info: dict[str, Any], device_data: dict[str, Any]) -> str:
    """Generate standardized device display name in format: (Encoder|Decoder) - AliasName or IP."""
    device_type = device_info.get("type", "device").title()
    
    # Use alias name (device_id) if available, otherwise fall back to IP address
    name_part = device_id
    if not name_part or name_part == "unknown":
        ip_address = device_data.get("ip_address")
        name_part = ip_address if ip_address else "Unknown"
    
    return f"{device_type} - {name_part}"