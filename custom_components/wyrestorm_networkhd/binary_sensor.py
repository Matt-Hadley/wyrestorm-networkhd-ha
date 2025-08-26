"""Binary sensors for WyreStorm NetworkHD integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WyreStormCoordinator
from .device_naming import get_device_display_name

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WyreStorm NetworkHD binary sensors."""
    coordinator: WyreStormCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    _LOGGER.info("Setting up WyreStorm NetworkHD binary sensors...")
    
    if not coordinator.is_ready():
        _LOGGER.warning("Coordinator not ready, skipping binary sensor setup")
        return
        
    if coordinator.has_errors():
        _LOGGER.warning("Coordinator has errors, skipping binary sensor setup")
        return

    entities = []
    devices_data = coordinator.data.get("devices", {})
    _LOGGER.info("Found %d devices for binary sensors", len(devices_data))
    
    for device_id, device_data in devices_data.items():
        device_type = device_data.get("type")
        _LOGGER.debug("Processing device %s (type: %s)", device_id, device_type)
        
        if device_type == "decoder":
            # For decoders: online status and video output status
            _LOGGER.debug("Creating decoder sensors for %s", device_id)
            entities.append(WyreStormOnlineSensor(coordinator, device_id, device_data))
            entities.append(WyreStormVideoOutputSensor(coordinator, device_id, device_data))
        elif device_type == "encoder":
            # For encoders: online status and video input status
            _LOGGER.debug("Creating encoder sensors for %s", device_id)
            entities.append(WyreStormOnlineSensor(coordinator, device_id, device_data))
            entities.append(WyreStormVideoInputSensor(coordinator, device_id, device_data))
        else:
            _LOGGER.warning("Unknown device type for %s: %s", device_id, device_type)

    _LOGGER.info("Created %d binary sensor entities", len(entities))
    async_add_entities(entities)


class WyreStormOnlineSensor(CoordinatorEntity[WyreStormCoordinator], BinarySensorEntity):
    """Binary sensor for device online status."""

    def __init__(self, coordinator: WyreStormCoordinator, device_id: str, device_data: dict[str, Any]) -> None:
        """Initialize the online sensor."""
        super().__init__(coordinator)
        self.device_id = device_id
        self.device_data = device_data
        self.device_type = device_data.get("type", "unknown")
        
        # Set entity attributes
        self._attr_unique_id = f"{coordinator.host}_{device_id}_online"
        self._attr_name = "Controller Link"  # Generic name without device prefix
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_icon = "mdi:ethernet"

    @property
    def is_on(self) -> bool | None:
        """Return true if the device is online."""
        if not self.coordinator.data:
            return None
            
        device_data = self.coordinator.data.get("devices", {}).get(self.device_id)
        if not device_data:
            return None
            
        # Return the actual online status from the device JSON data
        return device_data.get("online", False)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.data is not None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        device_data = self.coordinator.data.get("devices", {}).get(self.device_id, {}) if self.coordinator.data else {}
        device_name = get_device_display_name(self.device_id, {"type": self.device_type}, device_data)
        
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.coordinator.host}_{self.device_id}")},
            name=device_name,
            manufacturer="WyreStorm",
            model=self.device_data.get("model", "NetworkHD Device"),
            via_device=(DOMAIN, self.coordinator.host),
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return all available device attributes dynamically."""
        if not self.coordinator.data:
            return {}
            
        device_data = self.coordinator.data.get("devices", {}).get(self.device_id)
        if not device_data:
            return {}
            
        # Start with base attributes
        attributes = {
            "device_id": self.device_id,
            "device_type": self.device_type,
            "model": self.device_data.get("model", "Unknown"),
        }
        
        # Add all available device data as attributes, excluding internal/duplicate fields
        excluded_fields = {"name", "type"}  # Already covered by device_id/device_type
        
        for key, value in device_data.items():
            if key not in excluded_fields and value is not None:
                # Clean up attribute names for better display
                clean_key = key.replace("_", " ").title()
                attributes[clean_key] = value
                
        return attributes


class WyreStormVideoInputSensor(CoordinatorEntity[WyreStormCoordinator], BinarySensorEntity):
    """Binary sensor for encoder video input status."""

    def __init__(self, coordinator: WyreStormCoordinator, device_id: str, device_data: dict[str, Any]) -> None:
        """Initialize the video input sensor."""
        super().__init__(coordinator)
        self.device_id = device_id
        self.device_data = device_data
        self.device_type = device_data.get("type", "unknown")
        
        # Set entity attributes
        self._attr_unique_id = f"{coordinator.host}_{device_id}_video_input"
        self._attr_name = "Video Input"  # Generic name without device prefix
        self._attr_device_class = BinarySensorDeviceClass.RUNNING
        self._attr_icon = "mdi:arrow-left"  # Left arrow for input

    @property
    def is_on(self) -> bool | None:
        """Return true if video input is active."""
        if not self.coordinator.data:
            return None
            
        device_data = self.coordinator.data.get("devices", {}).get(self.device_id)
        if not device_data:
            return None
            
        # Check if HDMI input is active and has resolution
        hdmi_in_active = device_data.get("hdmi_in_active", False)
        resolution = device_data.get("resolution")
        return bool(hdmi_in_active and resolution)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not self.coordinator.data:
            return False
            
        device_data = self.coordinator.data.get("devices", {}).get(self.device_id)
        if not device_data:
            return False
            
        # Device is available if it's online (controller link)
        return device_data.get("online", False)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        device_data = self.coordinator.data.get("devices", {}).get(self.device_id, {}) if self.coordinator.data else {}
        device_name = get_device_display_name(self.device_id, {"type": "encoder"}, device_data)
        
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.coordinator.host}_{self.device_id}")},
            name=device_name,
            manufacturer="WyreStorm",
            model=self.device_data.get("model", "NetworkHD Encoder"),
            via_device=(DOMAIN, self.coordinator.host),
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return all available device attributes dynamically."""
        if not self.coordinator.data:
            return {}
            
        device_data = self.coordinator.data.get("devices", {}).get(self.device_id)
        if not device_data:
            return {}
            
        # Start with base attributes
        attributes = {
            "device_id": self.device_id,
            "device_type": self.device_type,
            "model": self.device_data.get("model", "Unknown"),
        }
        
        # Add all available device data as attributes, excluding internal/duplicate fields
        excluded_fields = {"name", "type"}  # Already covered by device_id/device_type
        
        for key, value in device_data.items():
            if key not in excluded_fields and value is not None:
                # Clean up attribute names for better display
                clean_key = key.replace("_", " ").title()
                attributes[clean_key] = value
                
        return attributes


class WyreStormVideoOutputSensor(CoordinatorEntity[WyreStormCoordinator], BinarySensorEntity):
    """Binary sensor for decoder video output status."""

    def __init__(self, coordinator: WyreStormCoordinator, device_id: str, device_data: dict[str, Any]) -> None:
        """Initialize the video output sensor."""
        super().__init__(coordinator)
        self.device_id = device_id
        self.device_data = device_data
        self.device_type = device_data.get("type", "unknown")
        
        # Set entity attributes
        self._attr_unique_id = f"{coordinator.host}_{device_id}_video_output"
        self._attr_name = "Video Output"  # Generic name without device prefix
        self._attr_device_class = BinarySensorDeviceClass.RUNNING
        self._attr_icon = "mdi:arrow-right"  # Right arrow for output

    @property
    def is_on(self) -> bool | None:
        """Return true if video output is active."""
        if not self.coordinator.data:
            return None
            
        device_data = self.coordinator.data.get("devices", {}).get(self.device_id)
        if not device_data:
            return None
            
        # Check if HDMI output is active and has resolution
        hdmi_out_active = device_data.get("hdmi_out_active", False)
        hdmi_out_resolution = device_data.get("hdmi_out_resolution")
        return bool(hdmi_out_active and hdmi_out_resolution)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not self.coordinator.data:
            return False
            
        device_data = self.coordinator.data.get("devices", {}).get(self.device_id)
        if not device_data:
            return False
            
        # Device is available if it's online (controller link)
        return device_data.get("online", False)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        device_data = self.coordinator.data.get("devices", {}).get(self.device_id, {}) if self.coordinator.data else {}
        device_name = get_device_display_name(self.device_id, {"type": "decoder"}, device_data)
        
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.coordinator.host}_{self.device_id}")},
            name=device_name,
            manufacturer="WyreStorm",
            model=self.device_data.get("model", "NetworkHD Decoder"),
            via_device=(DOMAIN, self.coordinator.host),
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return all available device attributes dynamically."""
        if not self.coordinator.data:
            return {}
            
        device_data = self.coordinator.data.get("devices", {}).get(self.device_id)
        if not device_data:
            return {}
            
        # Start with base attributes
        attributes = {
            "device_id": self.device_id,
            "device_type": self.device_type,
            "model": self.device_data.get("model", "Unknown"),
        }
        
        # Add all available device data as attributes, excluding internal/duplicate fields
        excluded_fields = {"name", "type"}  # Already covered by device_id/device_type
        
        for key, value in device_data.items():
            if key not in excluded_fields and value is not None:
                # Clean up attribute names for better display
                clean_key = key.replace("_", " ").title()
                attributes[clean_key] = value
                
        return attributes


