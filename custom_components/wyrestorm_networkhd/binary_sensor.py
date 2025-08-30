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

from .const import DOMAIN
from .coordinator import WyreStormCoordinator
from .models.device_receiver_transmitter import DeviceReceiver, DeviceTransmitter

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

    entities = []

    # Add controller link sensors for transmitters
    for transmitter_device in coordinator.get_transmitters():
        entities.append(WyreStormControllerLinkSensor(coordinator, transmitter_device, "transmitter"))
        entities.append(WyreStormVideoInputSensor(coordinator, transmitter_device))
        _LOGGER.debug(
            "Created controller link and video input sensors for transmitter %s", transmitter_device.true_name
        )

    # Add controller link sensors for receivers
    for receiver_device in coordinator.get_receivers():
        entities.append(WyreStormControllerLinkSensor(coordinator, receiver_device, "receiver"))
        entities.append(WyreStormVideoOutputSensor(coordinator, receiver_device))
        _LOGGER.debug("Created controller link and video output sensors for receiver %s", receiver_device.true_name)

    _LOGGER.info("Created %d binary sensor entities", len(entities))
    async_add_entities(entities)


class WyreStormControllerLinkSensor(CoordinatorEntity[WyreStormCoordinator], BinarySensorEntity):
    """Binary sensor for device controller link status."""

    def __init__(
        self,
        coordinator: WyreStormCoordinator,
        device: DeviceReceiver | DeviceTransmitter,
        device_class: str,
    ) -> None:
        """Initialize the controller link sensor."""
        super().__init__(coordinator)
        self.device_id = device.true_name
        self.device_class_str = device_class

        # Set entity attributes
        self._attr_unique_id = f"{DOMAIN}_{self.device_id}_controller_link"
        self._attr_name = "Controller Link"
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_has_entity_name = True

        # Set device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.device_id)},
            name=device.get_device_display_name(),
            manufacturer=device.manufacturer,
            model=device.model,
            sw_version=device.version,
            via_device=(DOMAIN, coordinator.host),  # Link to controller
        )

    @property
    def is_on(self) -> bool | None:
        """Return True if device has controller link (is online)."""
        if not self.coordinator.data:
            return None

        # Check in transmitters or receivers based on device class
        if self.device_class_str == "transmitter":
            device = self.coordinator.data.device_transmitters.get(self.device_id)
        else:  # receiver
            device = self.coordinator.data.device_receivers.get(self.device_id)

        if device:
            return bool(device.online)

        return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        # Entity is available if coordinator has data
        return self.coordinator.data is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return {}

        # Get device from appropriate collection
        if self.device_class_str == "transmitter":
            device = self.coordinator.data.device_transmitters.get(self.device_id)
        else:  # receiver
            device = self.coordinator.data.device_receivers.get(self.device_id)

        if not device:
            return {}

        return {
            "device_type": device.device_type,
            "ip_address": device.ip,
            "mac_address": device.mac,
            "firmware_version": device.version,
        }


class WyreStormVideoInputSensor(CoordinatorEntity[WyreStormCoordinator], BinarySensorEntity):
    """Binary sensor for transmitter video input status based on HDMI in frame rate."""

    def __init__(
        self,
        coordinator: WyreStormCoordinator,
        device: DeviceTransmitter,
    ) -> None:
        """Initialize the video input sensor."""
        super().__init__(coordinator)
        self.device_id = device.true_name

        # Set entity attributes
        self._attr_unique_id = f"{DOMAIN}_{self.device_id}_video_input"
        self._attr_name = "Video Input"
        self._attr_icon = "mdi:arrow-left"
        self._attr_device_class = BinarySensorDeviceClass.RUNNING
        self._attr_has_entity_name = True
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, self.device_id)})

    @property
    def is_on(self) -> bool | None:
        """Return True if video input is active (HDMI in frame rate > 0)."""
        if not self.coordinator.data:
            return None

        device = self.coordinator.data.device_transmitters.get(self.device_id)
        if device and hasattr(device, "hdmi_in_frame_rate"):
            try:
                frame_rate = float(device.hdmi_in_frame_rate or 0)
                return frame_rate > 0
            except (ValueError, TypeError):
                return False

        return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.data is not None and self.device_id in self.coordinator.data.device_transmitters

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return {}

        device = self.coordinator.data.device_transmitters.get(self.device_id)
        if not device:
            return {}

        return {
            "hdmi_in_frame_rate": device.hdmi_in_frame_rate,
        }


class WyreStormVideoOutputSensor(CoordinatorEntity[WyreStormCoordinator], BinarySensorEntity):
    """Binary sensor for receiver video output status based on HDMI out frame rate."""

    def __init__(
        self,
        coordinator: WyreStormCoordinator,
        device: DeviceReceiver,
    ) -> None:
        """Initialize the video output sensor."""
        super().__init__(coordinator)
        self.device_id = device.true_name

        # Set entity attributes
        self._attr_unique_id = f"{DOMAIN}_{self.device_id}_video_output"
        self._attr_name = "Video Output"
        self._attr_icon = "mdi:arrow-right"
        self._attr_device_class = BinarySensorDeviceClass.RUNNING
        self._attr_has_entity_name = True
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, self.device_id)})

    @property
    def is_on(self) -> bool | None:
        """Return True if video output is active (HDMI out frame rate > 0)."""
        if not self.coordinator.data:
            return None

        device = self.coordinator.data.device_receivers.get(self.device_id)
        if device and hasattr(device, "hdmi_out_frame_rate"):
            try:
                frame_rate = float(device.hdmi_out_frame_rate or 0)
                return frame_rate > 0
            except (ValueError, TypeError):
                return False

        return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.data is not None and self.device_id in self.coordinator.data.device_receivers

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return {}

        device = self.coordinator.data.device_receivers.get(self.device_id)
        if not device:
            return {}

        return {
            "hdmi_out_frame_rate": device.hdmi_out_frame_rate,
        }
