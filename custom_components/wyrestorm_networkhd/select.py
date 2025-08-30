"""Select platform for WyreStorm NetworkHD integration."""

from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WyreStormCoordinator
from .models.device_receiver_transmitter import DeviceReceiver

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WyreStorm NetworkHD select entities."""
    coordinator: WyreStormCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    if not coordinator.is_ready():
        _LOGGER.warning("Coordinator data not ready for select setup")
        return

    entities = []

    # Create source selection entities for receivers only
    for device in coordinator.get_receivers():
        entities.append(WyreStormReceiverSourceSelect(coordinator, device))
        _LOGGER.debug("Created source select for receiver %s", device.true_name)

    if entities:
        async_add_entities(entities)
        _LOGGER.info("Added %d select entities", len(entities))
    else:
        _LOGGER.debug("No receiver devices found for source selection")


class WyreStormReceiverSourceSelect(CoordinatorEntity[WyreStormCoordinator], SelectEntity):
    """Representation of a WyreStorm NetworkHD receiver source selection."""

    def __init__(
        self,
        coordinator: WyreStormCoordinator,
        device: DeviceReceiver,
    ) -> None:
        """Initialize the source select entity."""
        super().__init__(coordinator)
        self.device_id = device.true_name

        # Set entity attributes
        self._attr_unique_id = f"{DOMAIN}_{self.device_id}_source"
        self._attr_name = "Input Source"
        self._attr_icon = "mdi:video-switch"
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_has_entity_name = True
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, self.device_id)})

    @property
    def current_option(self) -> str | None:
        """Return the currently selected source."""
        if not self.coordinator.data:
            return None

        # Check matrix assignments to see what's connected to this receiver
        receiver_alias = None
        if self.device_id in self.coordinator.data.device_receivers:
            receiver = self.coordinator.data.device_receivers[self.device_id]
            receiver_alias = receiver.alias_name

        if not receiver_alias:
            return None

        # Look up current assignment
        current_source_alias = self.coordinator.data.matrix_assignments.get(receiver_alias)

        # Return "None" if no assignment, otherwise return the source alias
        return current_source_alias if current_source_alias else "None"

    @property
    def options(self) -> list[str]:
        """Return list of available sources."""
        if not self.coordinator.data:
            return []

        # Return list of transmitter aliases with None option for disconnecting
        transmitter_options = [tx.alias_name for tx in self.coordinator.data.get_transmitters_list()]
        return ["None"] + transmitter_options

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.data is not None and self.device_id in self.coordinator.data.device_receivers

    async def async_select_option(self, option: str) -> None:
        """Change the selected source."""
        if not self.coordinator.data:
            return

        # Find receiver alias
        receiver_alias = None
        if self.device_id in self.coordinator.data.device_receivers:
            receiver = self.coordinator.data.device_receivers[self.device_id]
            receiver_alias = receiver.alias_name

        if not receiver_alias:
            _LOGGER.error("Could not find receiver alias for %s", self.device_id)
            return

        try:
            if option == "None":
                # Disconnect the receiver (set to no source)
                await self.coordinator.set_matrix(None, receiver_alias)
            else:
                # Connect the receiver to the selected source
                await self.coordinator.set_matrix(option, receiver_alias)
        except Exception as err:
            _LOGGER.error("Failed to set matrix routing: %s", err)
            raise
