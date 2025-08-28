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
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ._device_utils import create_device_info, get_device_attributes
from ._entity_utils import (
    EntityConfigMixin,
    check_availability,
)
from .const import DOMAIN
from .coordinator import WyreStormCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WyreStorm NetworkHD binary sensors."""
    coordinator: WyreStormCoordinator = hass.data[DOMAIN][entry.entry_id]

    if not coordinator.is_ready():
        _LOGGER.warning("Coordinator data not ready for binary sensor setup")
        return

    devices = coordinator.get_all_devices()
    if not devices:
        _LOGGER.warning("No devices available for binary sensor setup")
        return

    _LOGGER.debug("Setting up binary sensors for %d devices", len(devices))
    entities = []

    for device_id in devices:
        device_data = devices.get_device(device_id)
        if not device_data or not device_data.device_json:
            continue

        device_type = getattr(device_data.device_json, "deviceType", "unknown")
        _LOGGER.debug("Processing device %s (type: %s)", device_id, device_type)

        # Create dict for backward compatibility with existing sensors
        compat_data = {
            "type": "decoder" if device_type == "receiver" else "encoder" if device_type == "transmitter" else "unknown"
        }

        if device_type == "receiver":
            # For decoders: online status and video output status
            _LOGGER.debug("Creating decoder sensors for %s", device_id)
            entities.append(WyreStormOnlineSensor(coordinator, device_id, compat_data))
            entities.append(WyreStormVideoOutputSensor(coordinator, device_id, compat_data))
        elif device_type == "transmitter":
            # For encoders: online status and video input status
            _LOGGER.debug("Creating encoder sensors for %s", device_id)
            entities.append(WyreStormOnlineSensor(coordinator, device_id, compat_data))
            entities.append(WyreStormVideoInputSensor(coordinator, device_id, compat_data))
        else:
            _LOGGER.warning("Unknown device type for %s: %s", device_id, device_type)

    _LOGGER.info("Created %d binary sensor entities", len(entities))
    async_add_entities(entities)


class WyreStormOnlineSensor(CoordinatorEntity[WyreStormCoordinator], BinarySensorEntity, EntityConfigMixin):
    """Binary sensor for device online status."""

    def __init__(
        self,
        coordinator: WyreStormCoordinator,
        device_id: str,
        device_data: dict[str, Any],
    ) -> None:
        """Initialize the online sensor."""
        super().__init__(coordinator)
        self.device_id = device_id
        self.device_data = device_data
        self.device_type = device_data.get("type", "unknown")

        # Set entity configuration using mixin
        self._set_entity_config(
            coordinator,
            device_id,
            "online",
            "Controller Link",
            icon="mdi:ethernet",
            entity_category=EntityCategory.DIAGNOSTIC,
        )
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    @property
    def is_on(self) -> bool | None:
        """Return true if the device is online."""
        if not self.coordinator.is_ready():
            return None

        device = self.coordinator.get_device_info(self.device_id)
        if not device:
            return None

        # Return the actual online status from the merged device data
        return device.online

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return check_availability(self.coordinator, self.device_id)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        device = self.coordinator.get_device_info(self.device_id) if self.coordinator.is_ready() else None
        device_attrs = {}
        if device and device.device_json:
            device_attrs = {
                attr: getattr(device.device_json, attr, None)
                for attr in dir(device.device_json)
                if not attr.startswith("_")
            }
        return create_device_info(
            self.coordinator.host,
            self.device_id,
            {
                "type": self.device_type,
                "model": self.device_data.get("model", "NetworkHD Device"),
            },
            device_attrs,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return all available device attributes dynamically."""
        if not self.coordinator.is_ready():
            return {}

        device = self.coordinator.get_device_info(self.device_id)
        if not device:
            return {}

        # Build attributes dict from device data sources
        device_attrs = {}
        if device.device_json:
            device_attrs.update(
                {
                    attr: getattr(device.device_json, attr, None)
                    for attr in dir(device.device_json)
                    if not attr.startswith("_")
                }
            )
        if device.device_status:
            device_attrs.update(
                {
                    attr: getattr(device.device_status, attr, None)
                    for attr in dir(device.device_status)
                    if not attr.startswith("_")
                }
            )

        attributes = get_device_attributes(self.device_id, self.device_type, device_attrs)
        attributes["model"] = self.device_data.get("model", "Unknown")
        return attributes


class WyreStormVideoInputSensor(CoordinatorEntity[WyreStormCoordinator], BinarySensorEntity, EntityConfigMixin):
    """Binary sensor for encoder video input status."""

    def __init__(
        self,
        coordinator: WyreStormCoordinator,
        device_id: str,
        device_data: dict[str, Any],
    ) -> None:
        """Initialize the video input sensor."""
        super().__init__(coordinator)
        self.device_id = device_id
        self.device_data = device_data
        self.device_type = device_data.get("type", "unknown")

        # Set entity configuration using mixin
        self._set_entity_config(coordinator, device_id, "video_input", "Video Input", icon="mdi:arrow-left")
        self._attr_device_class = BinarySensorDeviceClass.RUNNING

    @property
    def is_on(self) -> bool | None:
        """Return true if video input is active."""
        if not self.coordinator.is_ready():
            return None

        device = self.coordinator.get_device_info(self.device_id)
        if not device:
            return None

        # Check if HDMI input is active and has resolution
        hdmi_in_active = device.hdmi_in_active
        resolution = getattr(device.device_json, "resolution", None) if device.device_json else None
        return bool(hdmi_in_active and resolution)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return check_availability(self.coordinator, self.device_id)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        device = self.coordinator.get_device_info(self.device_id) if self.coordinator.is_ready() else None
        device_attrs = {}
        if device and device.device_json:
            device_attrs = {
                attr: getattr(device.device_json, attr, None)
                for attr in dir(device.device_json)
                if not attr.startswith("_")
            }
        return create_device_info(
            self.coordinator.host,
            self.device_id,
            {
                "type": "encoder",
                "model": self.device_data.get("model", "NetworkHD Encoder"),
            },
            device_attrs,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return all available device attributes dynamically."""
        if not self.coordinator.is_ready():
            return {}

        device = self.coordinator.get_device_info(self.device_id)
        if not device:
            return {}

        # Build attributes dict from device data sources
        device_attrs = {}
        if device.device_json:
            device_attrs.update(
                {
                    attr: getattr(device.device_json, attr, None)
                    for attr in dir(device.device_json)
                    if not attr.startswith("_")
                }
            )
        if device.device_status:
            device_attrs.update(
                {
                    attr: getattr(device.device_status, attr, None)
                    for attr in dir(device.device_status)
                    if not attr.startswith("_")
                }
            )

        attributes = get_device_attributes(self.device_id, self.device_type, device_attrs)
        attributes["model"] = self.device_data.get("model", "Unknown")
        return attributes


class WyreStormVideoOutputSensor(CoordinatorEntity[WyreStormCoordinator], BinarySensorEntity, EntityConfigMixin):
    """Binary sensor for decoder video output status."""

    def __init__(
        self,
        coordinator: WyreStormCoordinator,
        device_id: str,
        device_data: dict[str, Any],
    ) -> None:
        """Initialize the video output sensor."""
        super().__init__(coordinator)
        self.device_id = device_id
        self.device_data = device_data
        self.device_type = device_data.get("type", "unknown")

        # Set entity configuration using mixin
        self._set_entity_config(
            coordinator,
            device_id,
            "video_output",
            "Video Output",
            icon="mdi:arrow-right",
        )
        self._attr_device_class = BinarySensorDeviceClass.RUNNING

    @property
    def is_on(self) -> bool | None:
        """Return true if video output is active."""
        if not self.coordinator.is_ready():
            return None

        device = self.coordinator.get_device_info(self.device_id)
        if not device:
            return None

        # Check if HDMI output is active and has resolution
        hdmi_out_active = device.hdmi_out_active
        hdmi_out_resolution = (
            getattr(device.device_status, "hdmi_out_resolution", None) if device.device_status else None
        )
        return bool(hdmi_out_active and hdmi_out_resolution)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return check_availability(self.coordinator, self.device_id)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        device = self.coordinator.get_device_info(self.device_id) if self.coordinator.is_ready() else None
        device_attrs = {}
        if device and device.device_json:
            device_attrs = {
                attr: getattr(device.device_json, attr, None)
                for attr in dir(device.device_json)
                if not attr.startswith("_")
            }
        return create_device_info(
            self.coordinator.host,
            self.device_id,
            {
                "type": "decoder",
                "model": self.device_data.get("model", "NetworkHD Decoder"),
            },
            device_attrs,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return all available device attributes dynamically."""
        if not self.coordinator.is_ready():
            return {}

        device = self.coordinator.get_device_info(self.device_id)
        if not device:
            return {}

        # Build attributes dict from device data sources
        device_attrs = {}
        if device.device_json:
            device_attrs.update(
                {
                    attr: getattr(device.device_json, attr, None)
                    for attr in dir(device.device_json)
                    if not attr.startswith("_")
                }
            )
        if device.device_status:
            device_attrs.update(
                {
                    attr: getattr(device.device_status, attr, None)
                    for attr in dir(device.device_status)
                    if not attr.startswith("_")
                }
            )

        attributes = get_device_attributes(self.device_id, self.device_type, device_attrs)
        attributes["model"] = self.device_data.get("model", "Unknown")
        return attributes
