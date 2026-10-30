"""WyreStorm NetworkHD integration for Home Assistant."""

from __future__ import annotations

import logging

from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import (
    config_validation as cv,
    device_registry as dr,
    entity_registry as er,
    issue_registry as ir,
)
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, PLATFORMS
from .coordinator import WyreStormConfigEntry, WyreStormCoordinator
from .mdns import async_lookup_mac, is_mac
from .services import async_setup_services

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the integration's services (once, independent of config entries)."""
    async_setup_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: WyreStormConfigEntry) -> bool:
    """Set up WyreStorm NetworkHD from a config entry."""
    if not is_mac(entry.unique_id):
        await _async_adopt_mac(hass, entry)
    coordinator = WyreStormCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    host = entry.data[CONF_HOST]
    controller_id = coordinator.controller_id
    controller = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, controller_id)},
        connections={(dr.CONNECTION_NETWORK_MAC, controller_id)} if is_mac(controller_id) else set(),
        name=f"WyreStorm NetworkHD ({host})",
        manufacturer="WyreStorm",
        model="NetworkHD Controller",
        sw_version=coordinator.data.version.core_version,
        configuration_url=f"http://{host}",
    )
    coordinator.controller_device_id = controller.id

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: WyreStormConfigEntry) -> bool:
    """Unload a config entry (the coordinator disconnects itself via async_shutdown)."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: WyreStormConfigEntry) -> None:
    """Delete the entry's host key repair issue when the entry is removed."""
    ir.async_delete_issue(hass, DOMAIN, f"host_key_mismatch_{entry.entry_id}")


async def _async_adopt_mac(hass: HomeAssistant, entry: WyreStormConfigEntry) -> None:
    """Identify an entry set up by host (manually or before 1.2) by the controller's MAC, if it answers mDNS.

    Retried at every setup until it succeeds; setup goes on either way.
    """
    if not (mac := await async_lookup_mac(entry.data[CONF_HOST])):
        _LOGGER.debug("Controller MAC not found; %s keeps unique id %s", entry.title, entry.unique_id)
        return
    if hass.config_entries.async_entry_for_domain_unique_id(DOMAIN, mac):
        _LOGGER.debug("Another entry already has controller MAC %s; %s keeps its id", mac, entry.title)
        return
    async_move_controller_id(hass, entry, mac)
    hass.config_entries.async_update_entry(entry, unique_id=mac)
    _LOGGER.info("%s is now identified by the controller MAC %s", entry.title, mac)


@callback
def async_move_controller_id(hass: HomeAssistant, entry: WyreStormConfigEntry, new_id: str) -> None:
    """Move the controller device and its reboot button from the entry's unique id to `new_id`."""
    old_id = entry.unique_id
    dev_reg = dr.async_get(hass)
    if device := dev_reg.async_get_device_by_identifier((DOMAIN, old_id), entry.entry_id):
        dev_reg.async_update_device(device.id, new_identifiers={(DOMAIN, new_id)})
    ent_reg = er.async_get(hass)
    if entity_id := ent_reg.async_get_entity_id(Platform.BUTTON, DOMAIN, f"{DOMAIN}_{old_id}_controller_reboot"):
        ent_reg.async_update_entity(entity_id, new_unique_id=f"{DOMAIN}_{new_id}_controller_reboot")
