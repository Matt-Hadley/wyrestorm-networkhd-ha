"""Select platform for WyreStorm NetworkHD integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ._command_utils import safe_device_command
from ._device_utils import create_device_info, get_device_attributes
from ._entity_utils import check_availability, validate_device_for_setup
from .const import DOMAIN
from .coordinator import WyreStormCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WyreStorm NetworkHD select entities."""
    coordinator: WyreStormCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []

    devices_data = validate_device_for_setup(coordinator, _LOGGER, "select")
    if devices_data is None:
        return

    # Create source selection entities for decoders only
    for device_id, device_info in devices_data.items():
        if device_info.get("type") == "decoder":
            entities.append(WyreStormSourceSelect(coordinator, device_id, device_info))

    if entities:
        async_add_entities(entities)
        _LOGGER.info("Added %d select entities", len(entities))
    else:
        _LOGGER.debug("No decoder devices found for source selection")


class WyreStormSourceSelect(CoordinatorEntity[WyreStormCoordinator], SelectEntity):
    """Representation of a WyreStorm NetworkHD decoder source selection."""

    def __init__(
        self,
        coordinator: WyreStormCoordinator,
        device_id: str,
        device_info: dict[str, Any],
    ) -> None:
        """Initialize the source select entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device_info = device_info
        # Set entity attributes
        self._attr_unique_id = f"{coordinator.host}_{device_id}_matrix_routing"
        self._attr_name = "Input Source"
        self._attr_icon = "mdi:video-switch"
        self._attr_entity_category = EntityCategory.CONFIG

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device_data = self.coordinator.data.get("devices", {}).get(self._device_id, {}) if self.coordinator.data else {}
        model_name = self._device_info.get("model", f"NetworkHD {self._device_info.get('type', 'Device').title()}")

        return create_device_info(
            self.coordinator.host,
            self._device_id,
            {"type": self._device_info.get("type", "device"), "model": model_name},
            device_data,
        )

    @property
    def current_option(self) -> str | None:
        """Return the current selected source."""
        if not self.coordinator.data:
            return None

        device_data = self.coordinator.data.get("devices", {}).get(self._device_id, {})
        current_source = device_data.get("current_source")

        # Make sure the current source is in our options list
        if current_source and current_source in self.options:
            return str(current_source)

        return None

    @property
    def options(self) -> list[str]:
        """Return list of available source options."""
        if not self.coordinator.data:
            return []

        # Get all encoder devices as available sources
        devices_data = self.coordinator.data.get("devices", {})
        encoder_devices = [
            device_id for device_id, device_info in devices_data.items() if device_info.get("type") == "encoder"
        ]

        # Add a "None" option for disconnecting
        options = ["None"] + encoder_devices
        return options

    @property
    def available(self) -> bool:
        """Return True if the select entity is available."""
        return check_availability(self.coordinator, self._device_id)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return all available device attributes dynamically."""
        if not self.coordinator.data:
            return {}

        device_data = self.coordinator.data.get("devices", {}).get(self._device_id, {})

        attributes = get_device_attributes(self._device_id, self._device_info.get("type", "unknown"), device_data)
        attributes["model"] = self._device_info.get("model", "Unknown")
        return attributes

    async def async_select_option(self, option: str) -> None:
        """Select a new source for the decoder."""

        @safe_device_command(_LOGGER, self._device_id, f"set source to {option}")
        async def _set_source():
            if option == "None":
                # Disconnect the decoder (set to no source)
                await self.coordinator.api.media_stream_matrix_switch.matrix_set_null([self._device_id])
            else:
                # Set the selected encoder as the source
                await self.coordinator.api.media_stream_matrix_switch.matrix_set(option, [self._device_id])
            # Request a refresh to update the state
            await self.coordinator.async_request_refresh()

        await _set_source()
