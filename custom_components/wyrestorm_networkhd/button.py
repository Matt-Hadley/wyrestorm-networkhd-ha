"""Button platform for WyreStorm NetworkHD integration."""

from __future__ import annotations

from typing import Literal

from homeassistant.components.button import ButtonEntity
from homeassistant.components.button.const import ButtonDeviceClass
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WyreStormConfigEntry, WyreStormCoordinator
from .entity import WyreStormEndpointEntity, async_add_endpoint_entities
from .models.device_receiver_transmitter import DeviceReceiver, DeviceTransmitter

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WyreStormConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up WyreStorm NetworkHD button entities."""
    coordinator = entry.runtime_data
    async_add_entities([WyreStormControllerRebootButton(coordinator)])

    def create(device: DeviceReceiver | DeviceTransmitter) -> list[ButtonEntity]:
        if not isinstance(device, DeviceReceiver):
            return []
        return [
            WyreStormDisplayPowerButton(coordinator, device, "on"),
            WyreStormDisplayPowerButton(coordinator, device, "off"),
        ]

    async_add_endpoint_entities(entry, async_add_entities, create)


class WyreStormDisplayPowerButton(WyreStormEndpointEntity, ButtonEntity):
    """Send display power on/off to the display attached to a receiver."""

    def __init__(
        self, coordinator: WyreStormCoordinator, device: DeviceReceiver, power_state: Literal["on", "off"]
    ) -> None:
        """Initialize the power button."""
        super().__init__(coordinator, device, f"display_power_{power_state}")
        self._power_state: Literal["on", "off"] = power_state

    async def async_press(self) -> None:
        """Send the power command."""
        if isinstance(device := self.device, DeviceReceiver):
            await self.coordinator.async_set_power([device], self._power_state)


class WyreStormControllerRebootButton(CoordinatorEntity[WyreStormCoordinator], ButtonEntity):
    """Button to reboot the controller."""

    _attr_has_entity_name = True
    _attr_translation_key = "controller_reboot"
    _attr_device_class = ButtonDeviceClass.RESTART
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: WyreStormCoordinator) -> None:
        """Initialize the controller reboot button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{coordinator.controller_id}_controller_reboot"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, coordinator.controller_id)})

    async def async_press(self) -> None:
        """Reboot the controller."""
        await self.coordinator.async_reboot()
