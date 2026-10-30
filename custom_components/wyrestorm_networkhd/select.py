"""Select platform for WyreStorm NetworkHD integration."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import WyreStormConfigEntry
from .entity import WyreStormEndpointEntity, async_add_endpoint_entities
from .models.device_receiver_transmitter import DeviceReceiver, DeviceTransmitter

PARALLEL_UPDATES = 1
NO_SOURCE = "None"  # option that disconnects the receiver


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WyreStormConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up WyreStorm NetworkHD select entities."""

    def create(device: DeviceReceiver | DeviceTransmitter) -> list[SelectEntity]:
        if not isinstance(device, DeviceReceiver):
            return []
        return [WyreStormReceiverSourceSelect(entry.runtime_data, device, "source")]

    async_add_endpoint_entities(entry, async_add_entities, create)


class WyreStormReceiverSourceSelect(WyreStormEndpointEntity, SelectEntity):
    """The transmitter routed to a receiver."""

    @property
    def options(self) -> list[str]:
        """Return list of available sources."""
        return [NO_SOURCE, *(tx.alias_name for tx in self.coordinator.data.device_transmitters.values())]

    @property
    def current_option(self) -> str | None:
        """Return the currently selected source."""
        if not (device := self.device):
            return None
        source = self.coordinator.data.matrix_assignments.get(device.alias_name)
        return source if source in self.options else NO_SOURCE

    async def async_select_option(self, option: str) -> None:
        """Route the selected source to this receiver."""
        receiver = self.coordinator.find_receiver(self._true_name)
        source = None if option == NO_SOURCE else self.coordinator.find_transmitter(option)
        if receiver is None or (source is None and option != NO_SOURCE):
            return  # options come from current data, so this only races with a refresh
        await self.coordinator.async_set_matrix(source, [receiver])
