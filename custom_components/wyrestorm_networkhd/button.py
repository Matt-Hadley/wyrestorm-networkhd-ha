"""Button platform for WyreStorm NetworkHD integration."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
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
    """Set up WyreStorm NetworkHD button entities."""
    coordinator: WyreStormCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    if not coordinator.is_ready():
        _LOGGER.warning("Coordinator data not ready for button setup")
        return

    entities = []

    # Create controller reboot button
    entities.append(WyreStormControllerRebootButton(coordinator))
    _LOGGER.debug("Created controller reboot button")

    # Create power control buttons for receivers only
    for device in coordinator.get_receivers():
        entities.append(WyreStormReceiverDisplayPowerOnButton(coordinator, device))
        entities.append(WyreStormReceiverDisplayPowerOffButton(coordinator, device))
        _LOGGER.debug("Created power buttons for receiver %s", device.true_name)

    if entities:
        async_add_entities(entities)
        _LOGGER.info("Added %d button entities", len(entities))
    else:
        _LOGGER.debug("No receiver devices found for power buttons")


class WyreStormReceiverDisplayPowerButton(CoordinatorEntity[WyreStormCoordinator], ButtonEntity):
    """Base class for WyreStorm receiver display power buttons."""

    def __init__(
        self,
        coordinator: WyreStormCoordinator,
        device: DeviceReceiver,
        power_state: str,
    ) -> None:
        """Initialize the power button."""
        super().__init__(coordinator)
        self.device_id = device.true_name
        self.power_state = power_state

        # Set entity attributes
        action = "on" if power_state == "on" else "off"
        self._attr_unique_id = f"{DOMAIN}_{self.device_id}_display_power_{action}"
        self._attr_name = f"Display Power {action.title()}"
        self._attr_icon = "mdi:television" if power_state == "on" else "mdi:television-off"
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_has_entity_name = True
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, self.device_id)})

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.data is not None and self.device_id in self.coordinator.data.device_receivers

    async def async_press(self) -> None:
        """Handle the button press."""
        if not self.coordinator.data:
            return

        # Find receiver alias for the API call
        receiver_alias = None
        if self.device_id in self.coordinator.data.device_receivers:
            receiver = self.coordinator.data.device_receivers[self.device_id]
            receiver_alias = receiver.alias_name

        if not receiver_alias:
            _LOGGER.error("Could not find receiver alias for %s", self.device_id)
            return

        try:
            await self.coordinator.api.connected_device_control.config_set_device_sinkpower(
                power=self.power_state, rx=receiver_alias
            )
            _LOGGER.info("Set display power %s for receiver %s", self.power_state, receiver_alias)

            # No refresh needed - display power only affects connected TV/monitor, not device status
        except Exception as err:
            _LOGGER.error("Failed to set display power: %s", err)
            raise


class WyreStormReceiverDisplayPowerOnButton(WyreStormReceiverDisplayPowerButton):
    """Button to turn receiver display power on."""

    def __init__(
        self,
        coordinator: WyreStormCoordinator,
        device: DeviceReceiver,
    ) -> None:
        """Initialize the display power on button."""
        super().__init__(coordinator, device, "on")


class WyreStormReceiverDisplayPowerOffButton(WyreStormReceiverDisplayPowerButton):
    """Button to turn receiver display power off."""

    def __init__(
        self,
        coordinator: WyreStormCoordinator,
        device: DeviceReceiver,
    ) -> None:
        """Initialize the display power off button."""
        super().__init__(coordinator, device, "off")


class WyreStormControllerRebootButton(CoordinatorEntity[WyreStormCoordinator], ButtonEntity):
    """Button to reboot the controller."""

    def __init__(
        self,
        coordinator: WyreStormCoordinator,
    ) -> None:
        """Initialize the controller reboot button."""
        super().__init__(coordinator)

        # Set entity attributes
        self._attr_unique_id = f"{DOMAIN}_{coordinator.host}_controller_reboot"
        self._attr_name = "Reboot Controller"
        self._attr_icon = "mdi:restart"
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_has_entity_name = True
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, coordinator.host)})

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.data is not None

    async def async_press(self) -> None:
        """Handle the button press to reboot controller."""
        try:
            await self.coordinator.api.reboot_reset.set_reboot()
            _LOGGER.info("Controller reboot initiated")

            # Note: Don't request refresh immediately as controller will be rebooting
            # The coordinator will handle reconnection automatically during its next update cycle
        except Exception as err:
            _LOGGER.error("Failed to reboot controller: %s", err)
            raise
