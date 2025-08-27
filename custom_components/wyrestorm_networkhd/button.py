"""Button platform for WyreStorm NetworkHD integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory

from wyrestorm_networkhd.exceptions import NetworkHDError

from .const import DOMAIN
from .coordinator import WyreStormCoordinator
from .device_naming import get_device_display_name

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WyreStorm NetworkHD button entities."""
    coordinator: WyreStormCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    _LOGGER.info("Setting up WyreStorm NetworkHD button entities...")
    
    if not coordinator.is_ready():
        _LOGGER.warning("Coordinator not ready, skipping button setup")
        return
        
    if coordinator.has_errors():
        _LOGGER.warning("Coordinator has errors, skipping button setup")
        return

    entities = []
    devices_data = coordinator.data.get("devices", {})
    _LOGGER.info("Found %d devices for button entities", len(devices_data))
    
    # Add reboot button for the controller
    entities.append(WyreStormRebootButton(coordinator))
    
    for device_id, device_data in devices_data.items():
        device_type = device_data.get("type")
        _LOGGER.debug("Processing device %s (type: %s)", device_id, device_type)
        
        if device_type == "decoder":
            # For decoders: add sink power control buttons
            _LOGGER.debug("Creating sink power buttons for decoder %s", device_id)
            entities.append(WyreStormSinkPowerOnButton(coordinator, device_id, device_data))
            entities.append(WyreStormSinkPowerOffButton(coordinator, device_id, device_data))

    _LOGGER.info("Created %d button entities", len(entities))
    async_add_entities(entities)


class WyreStormRebootButton(ButtonEntity):
    """Button to reboot the WyreStorm NetworkHD controller."""

    def __init__(self, coordinator: WyreStormCoordinator) -> None:
        """Initialize the reboot button."""
        super().__init__()
        self.coordinator = coordinator
        
        # Set entity attributes
        self._attr_unique_id = f"{coordinator.host}_controller_reboot"
        self._attr_name = "Reboot Controller"
        self._attr_icon = "mdi:restart"
        self._attr_entity_category = EntityCategory.CONFIG

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.is_ready() and not self.coordinator.has_errors()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.host)},
            name=f"Controller - {self.coordinator.host}",
            manufacturer="WyreStorm",
            model="NetworkHD Controller",
            via_device=None,  # This is the controller device itself
        )

    async def async_press(self) -> None:
        """Handle the button press - send reboot command to controller."""
        try:
            _LOGGER.info("Sending reboot command to controller at %s", self.coordinator.host)
            await self.coordinator.api.reboot_reset.set_reboot()
            _LOGGER.info("Reboot command sent successfully to controller at %s", self.coordinator.host)
            
            # Note: We don't refresh the coordinator here since the controller will be rebooting
            # and won't be available for a while
        except NetworkHDError as err:
            _LOGGER.error("Failed to send reboot command to controller at %s: %s", self.coordinator.host, err)
            raise
        except Exception as err:
            _LOGGER.error("Unexpected error sending reboot command to controller at %s: %s", self.coordinator.host, err)
            raise


class WyreStormSinkPowerOnButton(ButtonEntity):
    """Button to turn on display via sink power control."""

    def __init__(self, coordinator: WyreStormCoordinator, device_id: str, device_data: dict[str, Any]) -> None:
        """Initialize the sink power on button."""
        super().__init__()
        self.coordinator = coordinator
        self.device_id = device_id
        self.device_data = device_data
        self.device_type = device_data.get("type", "unknown")
        
        # Set entity attributes
        self._attr_unique_id = f"{coordinator.host}_{device_id}_display_power_on"
        self._attr_name = "Display Power On"
        self._attr_icon = "mdi:television"
        self._attr_entity_category = EntityCategory.CONFIG

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not self.coordinator.data:
            return False
            
        device_data = self.coordinator.data.get("devices", {}).get(self.device_id)
        if not device_data:
            return False
            
        # Device must be online to receive sink power commands
        return device_data.get("online", False)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        device_data = self.coordinator.data.get("devices", {}).get(self.device_id, {}) if self.coordinator.data else {}
        device_name = get_device_display_name(self.device_id, {"type": "decoder"}, device_data)
        
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.coordinator.host}_{self.device_id}")},
            name=device_name,
            manufacturer="WyreStorm",
            model=self.device_data.get("model", "NetworkHD Decoder"),
            via_device=(DOMAIN, self.coordinator.host),
        )

    async def async_press(self) -> None:
        """Handle the button press - send sink power on command."""
        try:
            _LOGGER.info("Sending sink power on command to %s", self.device_id)
            await self.coordinator.api.connected_device_control.config_set_device_sinkpower(
                power="on",
                rx=self.device_id
            )
            # Trigger a coordinator refresh to update states
            await self.coordinator.async_request_refresh()
            _LOGGER.info("Sink power on command sent successfully to %s", self.device_id)
        except NetworkHDError as err:
            _LOGGER.error("Failed to send sink power on command to %s: %s", self.device_id, err)
            raise
        except Exception as err:
            _LOGGER.error("Unexpected error sending sink power on command to %s: %s", self.device_id, err)
            raise


class WyreStormSinkPowerOffButton(ButtonEntity):
    """Button to turn off display via sink power control."""

    def __init__(self, coordinator: WyreStormCoordinator, device_id: str, device_data: dict[str, Any]) -> None:
        """Initialize the sink power off button."""
        super().__init__()
        self.coordinator = coordinator
        self.device_id = device_id
        self.device_data = device_data
        self.device_type = device_data.get("type", "unknown")
        
        # Set entity attributes
        self._attr_unique_id = f"{coordinator.host}_{device_id}_display_power_off"
        self._attr_name = "Display Power Off"
        self._attr_icon = "mdi:television-off"
        self._attr_entity_category = EntityCategory.CONFIG

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not self.coordinator.data:
            return False
            
        device_data = self.coordinator.data.get("devices", {}).get(self.device_id)
        if not device_data:
            return False
            
        # Device must be online to receive sink power commands
        return device_data.get("online", False)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        device_data = self.coordinator.data.get("devices", {}).get(self.device_id, {}) if self.coordinator.data else {}
        device_name = get_device_display_name(self.device_id, {"type": "decoder"}, device_data)
        
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.coordinator.host}_{self.device_id}")},
            name=device_name,
            manufacturer="WyreStorm",
            model=self.device_data.get("model", "NetworkHD Decoder"),
            via_device=(DOMAIN, self.coordinator.host),
        )

    async def async_press(self) -> None:
        """Handle the button press - send sink power off command."""
        try:
            _LOGGER.info("Sending sink power off command to %s", self.device_id)
            await self.coordinator.api.connected_device_control.config_set_device_sinkpower(
                power="off",
                rx=self.device_id
            )
            # Trigger a coordinator refresh to update states
            await self.coordinator.async_request_refresh()
            _LOGGER.info("Sink power off command sent successfully to %s", self.device_id)
        except NetworkHDError as err:
            _LOGGER.error("Failed to send sink power off command to %s: %s", self.device_id, err)
            raise
        except Exception as err:
            _LOGGER.error("Unexpected error sending sink power off command to %s: %s", self.device_id, err)
            raise