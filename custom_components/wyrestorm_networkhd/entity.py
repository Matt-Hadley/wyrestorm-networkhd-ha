"""Base entities for the WyreStorm NetworkHD integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WyreStormCoordinator
from .models.device_receiver_transmitter import DeviceReceiver, DeviceTransmitter


class WyreStormEndpointEntity(CoordinatorEntity[WyreStormCoordinator]):
    """An entity belonging to a transmitter or receiver endpoint."""

    _attr_has_entity_name = True
    _requires_online = True  # unavailable while the endpoint is offline

    def __init__(self, coordinator: WyreStormCoordinator, device: DeviceReceiver | DeviceTransmitter, key: str) -> None:
        """Initialize the entity for `device`; `key` is the translation key and unique_id suffix."""
        super().__init__(coordinator)
        self._true_name = device.true_name
        self._is_receiver = isinstance(device, DeviceReceiver)
        self._attr_translation_key = key
        self._attr_unique_id = f"{DOMAIN}_{device.true_name}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.true_name)},
            connections={(CONNECTION_NETWORK_MAC, device.mac)} if device.mac else set(),
            name=device.get_device_display_name(),
            manufacturer="WyreStorm",
            model=device.true_name,
            sw_version=device.version,
            via_device_id=coordinator.controller_device_id,
        )

    @property
    def device(self) -> DeviceReceiver | DeviceTransmitter | None:
        """Return the endpoint's current data, or None if the controller no longer lists it."""
        devices = (
            self.coordinator.data.device_receivers if self._is_receiver else self.coordinator.data.device_transmitters
        )
        return devices.get(self._true_name)

    @property
    def available(self) -> bool:
        """Available while the controller is reachable and lists the endpoint (online, if required)."""
        device = self.device
        return super().available and device is not None and (device.online or not self._requires_online)
