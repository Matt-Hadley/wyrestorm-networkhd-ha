"""Button platform for WyreStorm NetworkHD integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ._command_utils import safe_device_command
from ._device_utils import create_device_info
from ._entity_utils import check_availability, log_device_setup
from .const import DOMAIN
from .coordinator import WyreStormCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WyreStorm NetworkHD button entities."""
    coordinator: WyreStormCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Check if coordinator is ready for setup
    if not coordinator.is_ready():
        _LOGGER.warning("Coordinator not ready, skipping button setup")
        return

    if coordinator.has_errors():
        _LOGGER.warning("Coordinator has errors, skipping button setup")
        return

    devices_data = coordinator.data.get("devices", {})
    if devices_data:
        log_device_setup(_LOGGER, "button entities", devices_data)
    else:
        _LOGGER.warning("No devices data available for button setup")

    entities = []

    # Add reboot button for the controller (always add this)
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
        # Controller-level buttons need only coordinator availability
        return check_availability(self.coordinator)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return create_device_info(self.coordinator.host, "", {}, {}, is_controller=True)

    @safe_device_command(_LOGGER, "controller", "reboot")
    async def async_press(self) -> None:
        """Handle the button press - send reboot command to controller."""
        await self.coordinator.api.reboot_reset.set_reboot()
        # Note: We don't refresh the coordinator here since the controller will be rebooting


class WyreStormSinkPowerOnButton(ButtonEntity):
    """Button to turn on display via sink power control."""

    def __init__(
        self,
        coordinator: WyreStormCoordinator,
        device_id: str,
        device_data: dict[str, Any],
    ) -> None:
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
        # Check if coordinator is ready first
        if not self.coordinator.is_ready():
            return False

        # Check if coordinator has errors
        if self.coordinator.has_errors():
            return False

        # Device-specific buttons need device to be online
        return check_availability(self.coordinator, self.device_id)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        device_data = self.coordinator.data.get("devices", {}).get(self.device_id, {}) if self.coordinator.data else {}
        return create_device_info(
            self.coordinator.host,
            self.device_id,
            {
                "type": "decoder",
                "model": self.device_data.get("model", "NetworkHD Decoder"),
            },
            device_data,
        )

    async def async_press(self) -> None:
        """Handle the button press - send sink power on command."""

        @safe_device_command(_LOGGER, self.device_id, "sink power on")
        async def _send_command():
            await self.coordinator.api.connected_device_control.config_set_device_sinkpower(
                power="on", rx=self.device_id
            )
            await self.coordinator.async_request_refresh()

        await _send_command()


class WyreStormSinkPowerOffButton(ButtonEntity):
    """Button to turn off display via sink power control."""

    def __init__(
        self,
        coordinator: WyreStormCoordinator,
        device_id: str,
        device_data: dict[str, Any],
    ) -> None:
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
        # Check if coordinator is ready first
        if not self.coordinator.is_ready():
            return False

        # Check if coordinator has errors
        if self.coordinator.has_errors():
            return False

        # Device-specific buttons need device to be online
        return check_availability(self.coordinator, self.device_id)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        device_data = self.coordinator.data.get("devices", {}).get(self.device_id, {}) if self.coordinator.data else {}
        return create_device_info(
            self.coordinator.host,
            self.device_id,
            {
                "type": "decoder",
                "model": self.device_data.get("model", "NetworkHD Decoder"),
            },
            device_data,
        )

    async def async_press(self) -> None:
        """Handle the button press - send sink power off command."""

        @safe_device_command(_LOGGER, self.device_id, "sink power off")
        async def _send_command():
            await self.coordinator.api.connected_device_control.config_set_device_sinkpower(
                power="off", rx=self.device_id
            )
            await self.coordinator.async_request_refresh()

        await _send_command()
