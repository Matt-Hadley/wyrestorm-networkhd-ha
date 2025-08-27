"""Entity-specific utilities for WyreStorm NetworkHD integration."""
from __future__ import annotations

import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)


def check_availability(coordinator, device_id: str | None = None) -> bool:
    """Check if entity should be available based on coordinator and device status.
    
    Args:
        coordinator: The WyreStorm coordinator instance
        device_id: Optional device ID for device-specific entities
        
    Returns:
        True if entity should be available, False otherwise
    """
    # Check if coordinator is ready first
    if not coordinator.is_ready():
        return False
        
    # Check if coordinator has errors
    if coordinator.has_errors():
        return False
        
    # For controller-level entities (device_id is None)
    if device_id is None:
        return True
        
    # For device-specific entities, check device data
    if not coordinator.data:
        return False
        
    device_data = coordinator.data.get("devices", {}).get(device_id)
    if not device_data:
        return False
        
    # Device is available if it's online (controller link)
    return device_data.get("online", False)


def log_device_setup(logger: logging.Logger, device_type: str, devices_data: dict[str, Any]) -> None:
    """Log device setup information consistently.
    
    Args:
        logger: Logger instance to use
        device_type: Type of devices being set up (e.g., "binary sensors")
        devices_data: Dictionary of device data
    """
    logger.info("Setting up WyreStorm NetworkHD %s...", device_type)
    logger.info("Found %d devices for %s", len(devices_data), device_type)


def validate_device_for_setup(coordinator, logger: logging.Logger, entity_type: str) -> dict[str, Any] | None:
    """Validate coordinator is ready for device setup.
    
    Args:
        coordinator: The WyreStorm coordinator instance
        logger: Logger instance to use
        entity_type: Type of entity being set up (for logging)
        
    Returns:
        Device data dictionary if valid, None if not ready
    """
    if not coordinator.is_ready():
        logger.warning("Coordinator not ready, skipping %s setup", entity_type)
        return None
        
    if coordinator.has_errors():
        logger.warning("Coordinator has errors, skipping %s setup", entity_type)
        return None
        
    devices_data = coordinator.data.get("devices", {})
    if not devices_data:
        logger.warning("No devices data available for %s setup", entity_type)
        return None
        
    return devices_data


class EntityConfigMixin:
    """Mixin class for common entity configuration."""
    
    def _set_entity_config(
        self,
        coordinator,
        device_id: str,
        entity_type: str,
        name: str,
        icon: str | None = None,
        entity_category=None
    ) -> None:
        """Set common entity configuration.
        
        Args:
            coordinator: The coordinator instance
            device_id: Device identifier
            entity_type: Type of entity (e.g., "online", "video_input")
            name: Display name for the entity
            icon: Optional icon for the entity
            entity_category: Optional entity category
        """
        self._attr_unique_id = f"{coordinator.host}_{device_id}_{entity_type}"
        self._attr_name = name
        
        if icon:
            self._attr_icon = icon
            
        if entity_category:
            self._attr_entity_category = entity_category