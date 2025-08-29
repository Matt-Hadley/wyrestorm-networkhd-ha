"""WyreStorm NetworkHD 2 integration for Home Assistant."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from .const import (
    ATTR_DEVICES,
    ATTR_SOURCE_DEVICE,
    ATTR_TARGET_DEVICE,
    DOMAIN,
    PLATFORMS,
    SERVICE_MATRIX_SET,
    SERVICE_POWER_CONTROL,
)
from .coordinator import WyreStormCoordinator

_LOGGER = logging.getLogger(__name__)

# Service schemas
MATRIX_SET_SCHEMA = vol.Schema({
    vol.Required(ATTR_SOURCE_DEVICE): vol.Union(str, [str]),
    vol.Required(ATTR_TARGET_DEVICE): vol.Union(str, [str]),
})

POWER_CONTROL_SCHEMA = vol.Schema({
    vol.Required(ATTR_DEVICES): vol.Union(str, [str]),
    vol.Required("power_state"): vol.In(["on", "off"]),
})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WyreStorm NetworkHD 2 from a config entry."""
    _LOGGER.debug("Setting up WyreStorm NetworkHD 2 integration")

    # Create coordinator with the config entry
    coordinator = WyreStormCoordinator(hass, entry)

    try:
        # Coordinator handles its own connection and initial data fetch
        await coordinator.async_setup()
        _LOGGER.info("Coordinator setup complete with %d devices", coordinator.get_device_count())
    except Exception as err:
        _LOGGER.error("Failed to setup: %s", err)
        raise ConfigEntryNotReady(f"Setup failed: {err}") from err

    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Register controller device
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, coordinator.host)},
        name=f"WyreStorm NetworkHD 2 ({coordinator.host})",
        manufacturer="WyreStorm",
        model="NetworkHD Controller",
        sw_version=coordinator.data.device_controller.core_version if coordinator.data else None,
        configuration_url=f"http://{coordinator.host}",
    )
    _LOGGER.debug("Registered controller device")

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    _register_services(hass)

    _LOGGER.info("WyreStorm NetworkHD 2 integration setup complete")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms first
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Get and cleanup coordinator
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()

        # Remove services if this was the last entry
        if not hass.data[DOMAIN]:
            _unregister_services(hass)

    return unload_ok


def _register_services(hass: HomeAssistant) -> None:
    """Register integration services once."""
    if hass.services.has_service(DOMAIN, SERVICE_MATRIX_SET):
        return  # Services already registered

    async def handle_matrix_set(call: ServiceCall) -> None:
        """Handle matrix set service call."""
        # Get first available coordinator (services are domain-wide)
        coordinator = next(iter(hass.data[DOMAIN].values()))
        await coordinator.set_matrix(
            call.data[ATTR_SOURCE_DEVICE],
            call.data[ATTR_TARGET_DEVICE]
        )

    async def handle_power_control(call: ServiceCall) -> None:
        """Handle power control service call."""
        # Get first available coordinator (services are domain-wide)
        coordinator = next(iter(hass.data[DOMAIN].values()))
        await coordinator.set_power(
            call.data[ATTR_DEVICES],
            call.data["power_state"]
        )

    hass.services.async_register(DOMAIN, SERVICE_MATRIX_SET, handle_matrix_set, schema=MATRIX_SET_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_POWER_CONTROL, handle_power_control, schema=POWER_CONTROL_SCHEMA)


def _unregister_services(hass: HomeAssistant) -> None:
    """Unregister integration services."""
    hass.services.async_remove(DOMAIN, SERVICE_MATRIX_SET)
    hass.services.async_remove(DOMAIN, SERVICE_POWER_CONTROL)