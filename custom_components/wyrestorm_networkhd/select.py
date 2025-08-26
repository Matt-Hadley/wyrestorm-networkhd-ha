"""Select platform for WyreStorm NetworkHD integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import EntityCategory

from wyrestorm_networkhd.exceptions import NetworkHDError

from .const import DOMAIN
from .coordinator import WyreStormCoordinator
from .device_naming import get_device_display_name




_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WyreStorm NetworkHD select entities."""
    coordinator: WyreStormCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    # Safety checks
    if not coordinator.is_ready():
        _LOGGER.warning("Coordinator not ready, skipping select setup")
        return
    
    if coordinator.has_errors():
        _LOGGER.warning("Coordinator has errors, skipping select setup")
        return
    
    # Get devices data
    devices_data = coordinator.get_all_devices()
    if not devices_data:
        _LOGGER.warning("No devices data available for select setup")
        return
    
    # Create source selection entities for decoders only
    for device_id, device_info in devices_data.items():
        if device_info.get("type") == "decoder":
            entities.append(
                WyreStormSourceSelect(coordinator, device_id, device_info)
            )
    
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
        self._attr_name = "Input Source"  # Generic name without device prefix
        self._attr_icon = "mdi:video-switch"
        self._attr_entity_category = EntityCategory.CONFIG

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        device_data = self.coordinator.data.get("devices", {}).get(self._device_id, {}) if self.coordinator.data else {}
        model_name = self._device_info.get("model", f"NetworkHD {self._device_info.get('type', 'Device').title()}")
        device_name = get_device_display_name(self._device_id, self._device_info, device_data)
        
        return {
            "identifiers": {(DOMAIN, f"{self.coordinator.host}_{self._device_id}")},
            "name": device_name,
            "manufacturer": "WyreStorm",
            "model": model_name,
            "via_device": (DOMAIN, self.coordinator.host),
        }

    @property
    def current_option(self) -> str | None:
        """Return the current selected source."""
        if not self.coordinator.data:
            return None
        
        device_data = self.coordinator.data.get("devices", {}).get(self._device_id, {})
        current_source = device_data.get("current_source")
        
        # Make sure the current source is in our options list
        if current_source and current_source in self.options:
            return current_source
        
        return None

    @property
    def options(self) -> list[str]:
        """Return list of available source options."""
        if not self.coordinator.data:
            return []
        
        # Get all encoder devices as available sources
        devices_data = self.coordinator.data.get("devices", {})
        encoder_devices = [
            device_id for device_id, device_info in devices_data.items()
            if device_info.get("type") == "encoder"
        ]
        
        # Add a "None" option for disconnecting
        options = ["None"] + encoder_devices
        return options

    @property
    def available(self) -> bool:
        """Return True if the select entity is available."""
        if not self.coordinator.data:
            return False
        
        device_data = self.coordinator.data.get("devices", {}).get(self._device_id, {})
        return device_data.get("online", False)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return all available device attributes dynamically."""
        if not self.coordinator.data:
            return {}
        
        device_data = self.coordinator.data.get("devices", {}).get(self._device_id, {})
        
        # Start with base attributes
        attributes = {
            "device_id": self._device_id,
            "device_type": self._device_info.get("type", "unknown"),
            "model": self._device_info.get("model", "Unknown"),
        }
        
        # Add all available device data as attributes, excluding internal/duplicate fields
        excluded_fields = {"name", "type"}  # Already covered by device_id/device_type
        
        for key, value in device_data.items():
            if key not in excluded_fields and value is not None:
                # Clean up attribute names for better display
                clean_key = key.replace("_", " ").title()
                attributes[clean_key] = value
            
        return attributes

    async def async_select_option(self, option: str) -> None:
        """Select a new source for the decoder."""
        try:
            _LOGGER.info("Setting source for decoder %s to %s", self._device_id, option)
            
            if option == "None":
                # Disconnect the decoder (set to no source)
                await self.coordinator.api.media_stream_matrix_switch.matrix_set_null([self._device_id])
            else:
                # Set the selected encoder as the source
                await self.coordinator.api.media_stream_matrix_switch.matrix_set(
                    option, [self._device_id]
                )
            
            # Request a refresh to update the state
            await self.coordinator.async_request_refresh()
            
        except NetworkHDError as err:
            _LOGGER.error("Failed to set source for %s: %s", self._device_id, err)
            raise
        except Exception as err:
            _LOGGER.error("Unexpected error setting source for %s: %s", self._device_id, err)
            raise