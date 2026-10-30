"""Base entities for the WyreStorm NetworkHD integration."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable

from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WyreStormConfigEntry, WyreStormCoordinator
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
            model=re.sub("-[0-9A-F]{12}$", "", device.true_name, flags=re.IGNORECASE),  # e.g. NHD-400-RX
            serial_number=device.true_name,  # model and MAC
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


@callback
def async_add_endpoint_entities(
    entry: WyreStormConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
    create: Callable[[DeviceReceiver | DeviceTransmitter], Iterable[Entity]],
) -> None:
    """Add `create(endpoint)` for every endpoint now, and for endpoints that appear later, without a reload."""
    coordinator = entry.runtime_data
    dev_reg = dr.async_get(coordinator.hass)
    known: set[str] = set()

    @callback
    def add_new() -> None:
        data = coordinator.data
        endpoints: dict[str, DeviceReceiver | DeviceTransmitter] = {**data.device_transmitters, **data.device_receivers}
        # Forget endpoints whose device was removed (stale), so they get entities again if they come back.
        known.difference_update(
            [
                n
                for n in known - endpoints.keys()
                if not dev_reg.async_get_device_by_identifier((DOMAIN, n), entry.entry_id)
            ]
        )
        new = [device for name, device in endpoints.items() if name not in known]
        known.update(device.true_name for device in new)
        if entities := [entity for device in new for entity in create(device)]:
            async_add_entities(entities)

    add_new()
    entry.async_on_unload(coordinator.async_add_listener(add_new))
