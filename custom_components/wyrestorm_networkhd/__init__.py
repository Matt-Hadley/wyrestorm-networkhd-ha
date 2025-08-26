"""WyreStorm NetworkHD integration for Home Assistant."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import voluptuous as vol

from wyrestorm_networkhd import NHDAPI, NetworkHDClientSSH
from wyrestorm_networkhd.exceptions import NetworkHDError

from .const import (
    DOMAIN,
    PLATFORMS,
    DEFAULT_PORT,
    DEFAULT_UPDATE_INTERVAL,
    CONF_UPDATE_INTERVAL,
    ATTR_SOURCE_DEVICE,
    ATTR_TARGET_DEVICE,
    ATTR_DEVICES,
    SERVICE_MATRIX_SET,
    SERVICE_POWER_CONTROL,
    RETRY_ATTEMPTS,
    RETRY_DELAY,
)
from .coordinator import WyreStormCoordinator

_LOGGER = logging.getLogger(__name__)

# Service schemas
MATRIX_SET_SCHEMA = vol.Schema({
    vol.Required(ATTR_SOURCE_DEVICE): vol.Any(str, [str]),
    vol.Required(ATTR_TARGET_DEVICE): vol.Any(str, [str]),
})

POWER_CONTROL_SCHEMA = vol.Schema({
    vol.Required(ATTR_DEVICES): vol.Any(str, [str]),
    vol.Required("power_state"): vol.In(["on", "off"]),
})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WyreStorm NetworkHD from a config entry."""
    _LOGGER.debug("Setting up WyreStorm NetworkHD integration")

    # Extract configuration
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    username = entry.data[CONF_USERNAME] 
    password = entry.data[CONF_PASSWORD]
    # Check options first, then config data, then default
    update_interval = entry.options.get(CONF_UPDATE_INTERVAL) or entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)

    # Create client
    client = NetworkHDClientSSH(
        host=host,
        port=port,
        username=username,
        password=password,
        ssh_host_key_policy="auto_add",  # For HA integration
        timeout=15.0,
    )

    # Create API wrapper
    api = NHDAPI(client)

    # Create coordinator
    coordinator = WyreStormCoordinator(hass, api, client, host, update_interval)
    _LOGGER.info("Using polling interval of %d seconds", update_interval)

    try:
        # Initial connection and data fetch
        await coordinator.async_setup()
        
        # Ensure we have initial data before proceeding
        if not coordinator.data:
            _LOGGER.info("Waiting for coordinator data to be available...")
            if not await coordinator.wait_for_data(timeout=30):
                _LOGGER.error("Timeout waiting for coordinator data")
                raise ConfigEntryNotReady("Timeout waiting for initial data from device")
        
        _LOGGER.info("Coordinator setup complete with %d devices", 
                     len(coordinator.data.get("devices", {})) if coordinator.data else 0)
        
    except NetworkHDError as err:
        _LOGGER.error("Failed to connect to WyreStorm NetworkHD at %s: %s", host, err)
        raise ConfigEntryNotReady(f"Failed to connect: {err}") from err
    except Exception as err:
        _LOGGER.error("Unexpected error during setup: %s", err)
        raise ConfigEntryNotReady(f"Setup failed: {err}") from err

    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Get firmware version from the API
    firmware_version = "Unknown"
    try:
        version_info = await api.api_query.config_get_version()
        
        if hasattr(version_info, 'core_version'):
            # Version object with core_version attribute
            firmware_version = version_info.core_version
        elif hasattr(version_info, 'web_version'):
            # Fall back to web_version if core_version not available
            firmware_version = version_info.web_version  
        elif isinstance(version_info, dict):
            # Dictionary response structure
            firmware_version = version_info.get("core_version", 
                              version_info.get("version", 
                              version_info.get("firmware", "Unknown")))
        elif isinstance(version_info, str):
            firmware_version = version_info
        _LOGGER.debug("Retrieved firmware version: %s", firmware_version)
    except Exception as err:
        _LOGGER.warning("Failed to get firmware version: %s", err)

    # Create controller device
    device_registry = dr.async_get(hass)
    controller_device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, host)},
        name=f"Controller - {host}",
        manufacturer="WyreStorm",
        model="NetworkHD Controller",
        sw_version=firmware_version,
    )
    _LOGGER.debug("Created controller device: %s", controller_device.id)

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    await _async_register_services(hass, coordinator)

    # Register options update listener
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    _LOGGER.info("WyreStorm NetworkHD integration setup complete for %s", host)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the integration when options are updated."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading WyreStorm NetworkHD integration")

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Clean up coordinator
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()

        # Remove services if this was the last entry
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_MATRIX_SET)
            hass.services.async_remove(DOMAIN, SERVICE_POWER_CONTROL)

    return unload_ok


async def _async_register_services(hass: HomeAssistant, coordinator: WyreStormCoordinator) -> None:
    """Register integration services."""
    
    async def handle_matrix_set(call: ServiceCall) -> None:
        """Handle matrix set service call."""
        source = call.data[ATTR_SOURCE_DEVICE]
        target = call.data[ATTR_TARGET_DEVICE]
        
        # Convert single strings to lists
        if isinstance(source, str):
            source = [source]
        if isinstance(target, str):
            target = [target]
            
        try:
            for src in source:
                await coordinator.api.media_stream_matrix_switch.matrix_set(src, target)
            await coordinator.async_request_refresh()
            _LOGGER.info("Matrix set: %s -> %s", source, target)
        except NetworkHDError as err:
            _LOGGER.error("Matrix set failed: %s", err)
            raise

    async def handle_power_control(call: ServiceCall) -> None:
        """Handle power control service call."""
        devices = call.data[ATTR_DEVICES]
        power_state = call.data["power_state"]
        
        # Convert single string to list
        if isinstance(devices, str):
            devices = [devices]
            
        try:
            # Send power command to each device individually
            for device in devices:
                await coordinator.api.connected_device_control.config_set_device_sinkpower(
                    power=power_state, rx=device
                )
            await coordinator.async_request_refresh()
            _LOGGER.info("Power control: %s -> %s", devices, power_state)
        except NetworkHDError as err:
            _LOGGER.error("Power control failed: %s", err)
            raise

    # Register services (only once per domain)
    if not hass.services.has_service(DOMAIN, SERVICE_MATRIX_SET):
        hass.services.async_register(
            DOMAIN, SERVICE_MATRIX_SET, handle_matrix_set, schema=MATRIX_SET_SCHEMA
        )

    if not hass.services.has_service(DOMAIN, SERVICE_POWER_CONTROL):
        hass.services.async_register(
            DOMAIN, SERVICE_POWER_CONTROL, handle_power_control, schema=POWER_CONTROL_SCHEMA
        )


