"""WyreStorm NetworkHD integration for Home Assistant."""

from __future__ import annotations

from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    config_validation as cv,
    device_registry as dr,
)
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, PLATFORMS
from .coordinator import WyreStormConfigEntry, WyreStormCoordinator
from .services import async_setup_services

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the integration's services (once, independent of config entries)."""
    async_setup_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: WyreStormConfigEntry) -> bool:
    """Set up WyreStorm NetworkHD from a config entry."""
    coordinator = WyreStormCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    host = entry.data[CONF_HOST]
    controller = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, host)},
        name=f"WyreStorm NetworkHD ({host})",
        manufacturer="WyreStorm",
        model="NetworkHD Controller",
        sw_version=coordinator.data.device_controller.core_version,
        configuration_url=f"http://{host}",
    )
    coordinator.controller_device_id = controller.id

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: WyreStormConfigEntry) -> bool:
    """Unload a config entry (the coordinator disconnects itself via async_shutdown)."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
