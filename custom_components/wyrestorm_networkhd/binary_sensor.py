"""Binary sensors for WyreStorm NetworkHD integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import WyreStormConfigEntry
from .entity import WyreStormEndpointEntity

PARALLEL_UPDATES = 0  # read-only; the coordinator does all fetching


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WyreStormConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up WyreStorm NetworkHD binary sensors."""
    coordinator = entry.runtime_data
    entities: list[BinarySensorEntity] = []
    for tx in coordinator.data.device_transmitters.values():
        entities += [
            WyreStormControllerLinkSensor(coordinator, tx, "controller_link"),
            WyreStormVideoInputSensor(coordinator, tx, "video_input"),
        ]
    for rx in coordinator.data.device_receivers.values():
        entities += [
            WyreStormControllerLinkSensor(coordinator, rx, "controller_link"),
            WyreStormVideoOutputSensor(coordinator, rx, "video_output"),
        ]
    async_add_entities(entities)


class WyreStormControllerLinkSensor(WyreStormEndpointEntity, BinarySensorEntity):
    """Whether the endpoint is online (linked to the controller)."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _requires_online = False  # this sensor reports the online state itself

    @property
    def is_on(self) -> bool | None:
        """Return True if the endpoint is online."""
        return bool(self.device.online) if self.device else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if not (device := self.device):
            return {}
        return {
            "device_type": device.device_type,
            "ip_address": device.ip,
            "mac_address": device.mac,
            "firmware_version": device.version,
        }


class _FrameRateSensor(WyreStormEndpointEntity, BinarySensorEntity):
    """Video active when the frame rate attribute is > 0."""

    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _frame_rate_attr: str

    @property
    def _frame_rate(self) -> Any:
        return getattr(self.device, self._frame_rate_attr, None)

    @property
    def is_on(self) -> bool | None:
        """Return True if video is active."""
        try:
            return float(self._frame_rate or 0) > 0
        except ValueError, TypeError:
            return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the raw frame rate."""
        return {self._frame_rate_attr: self._frame_rate}


class WyreStormVideoInputSensor(_FrameRateSensor):
    """Transmitter HDMI input active."""

    _frame_rate_attr = "hdmi_in_frame_rate"


class WyreStormVideoOutputSensor(_FrameRateSensor):
    """Receiver HDMI output active."""

    _frame_rate_attr = "hdmi_out_frame_rate"
