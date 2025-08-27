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
from ._device_utils import create_device_info, get_device_attributes
from ._entity_utils import (
    check_availability,
    validate_device_for_setup,
    log_device_setup,
    EntityConfigMixin,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WyreStorm NetworkHD binary sensors."""
    coordinator: WyreStormCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    devices_data = validate_device_for_setup(coordinator, _LOGGER, "binary sensor")
    if devices_data is None:
        return

    log_device_setup(_LOGGER, "binary sensors", devices_data)
    entities = []
    
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


class WyreStormOnlineSensor(CoordinatorEntity[WyreStormCoordinator], BinarySensorEntity, EntityConfigMixin):
    """Binary sensor for device online status."""

    def __init__(self, coordinator: WyreStormCoordinator, device_id: str, device_data: dict[str, Any]) -> None:
        """Initialize the online sensor."""
        super().__init__(coordinator)
        self.device_id = device_id
        self.device_data = device_data
        self.device_type = device_data.get("type", "unknown")
        
        # Set entity configuration using mixin
        self._set_entity_config(
            coordinator, device_id, "online", "Controller Link",
            icon="mdi:ethernet", entity_category=EntityCategory.DIAGNOSTIC
        )
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

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
        # Allow brief data gaps for online sensors - they show controller connectivity
        return check_availability(self.coordinator)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        device_data = self.coordinator.data.get("devices", {}).get(self.device_id, {}) if self.coordinator.data else {}
        return create_device_info(
            self.coordinator.host,
            self.device_id,
            {"type": self.device_type, "model": self.device_data.get("model", "NetworkHD Device")},
            device_data
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return all available device attributes dynamically."""
        if not self.coordinator.data:
            return {}
            
        device_data = self.coordinator.data.get("devices", {}).get(self.device_id)
        if not device_data:
            return {}
            
        attributes = get_device_attributes(self.device_id, self.device_type, device_data)
        attributes["model"] = self.device_data.get("model", "Unknown")
        return attributes


class WyreStormVideoInputSensor(CoordinatorEntity[WyreStormCoordinator], BinarySensorEntity, EntityConfigMixin):
    """Binary sensor for encoder video input status."""

    def __init__(self, coordinator: WyreStormCoordinator, device_id: str, device_data: dict[str, Any]) -> None:
        """Initialize the video input sensor."""
        super().__init__(coordinator)
        self.device_id = device_id
        self.device_data = device_data
        self.device_type = device_data.get("type", "unknown")
        
        # Set entity configuration using mixin
        self._set_entity_config(
            coordinator, device_id, "video_input", "Video Input", icon="mdi:arrow-left"
        )
        self._attr_device_class = BinarySensorDeviceClass.RUNNING

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
        return check_availability(self.coordinator, self.device_id)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        device_data = self.coordinator.data.get("devices", {}).get(self.device_id, {}) if self.coordinator.data else {}
        return create_device_info(
            self.coordinator.host,
            self.device_id,
            {"type": "encoder", "model": self.device_data.get("model", "NetworkHD Encoder")},
            device_data
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return all available device attributes dynamically."""
        if not self.coordinator.data:
            return {}
            
        device_data = self.coordinator.data.get("devices", {}).get(self.device_id)
        if not device_data:
            return {}
            
        attributes = get_device_attributes(self.device_id, self.device_type, device_data)
        attributes["model"] = self.device_data.get("model", "Unknown")
        return attributes


class WyreStormVideoOutputSensor(CoordinatorEntity[WyreStormCoordinator], BinarySensorEntity, EntityConfigMixin):
    """Binary sensor for decoder video output status."""

    def __init__(self, coordinator: WyreStormCoordinator, device_id: str, device_data: dict[str, Any]) -> None:
        """Initialize the video output sensor."""
        super().__init__(coordinator)
        self.device_id = device_id
        self.device_data = device_data
        self.device_type = device_data.get("type", "unknown")
        
        # Set entity configuration using mixin
        self._set_entity_config(
            coordinator, device_id, "video_output", "Video Output", icon="mdi:arrow-right"
        )
        self._attr_device_class = BinarySensorDeviceClass.RUNNING

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
        return check_availability(self.coordinator, self.device_id)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        device_data = self.coordinator.data.get("devices", {}).get(self.device_id, {}) if self.coordinator.data else {}
        return create_device_info(
            self.coordinator.host,
            self.device_id,
            {"type": "decoder", "model": self.device_data.get("model", "NetworkHD Decoder")},
            device_data
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return all available device attributes dynamically."""
        if not self.coordinator.data:
            return {}
            
        device_data = self.coordinator.data.get("devices", {}).get(self.device_id)
        if not device_data:
            return {}
            
        attributes = get_device_attributes(self.device_id, self.device_type, device_data)
        attributes["model"] = self.device_data.get("model", "Unknown")
        return attributes


