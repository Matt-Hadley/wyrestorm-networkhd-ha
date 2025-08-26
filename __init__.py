"""WyreStorm NetworkHD integration - minimal version."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.dispatcher import async_dispatcher_send
import voluptuous as vol

from wyrestorm_networkhd import WyrestormNetworkHDClientSSH

_LOGGER = logging.getLogger(__name__)

DOMAIN = "wyrestorm_networkhd"

# Service schema
CONTROL_SCHEMA = vol.Schema({
    vol.Required("device"): vol.Any(cv.string, [cv.string]),
    vol.Required("action"): vol.In(["power_on", "power_off", "route_to", "clear_route"]),
    vol.Optional("target"): cv.string,
})

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WyreStorm NetworkHD from a config entry."""
    
    # Create client
    client = WyrestormNetworkHDClientSSH(
        host=entry.data["host"],
        username=entry.data["username"],
        password=entry.data["password"],
        port=entry.data.get("port", 22)
    )
    
    # Create coordinator
    coordinator = NetworkHDCoordinator(hass, client)
    await coordinator.async_connect()
    
    # Store in hass data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Set up entities
    await hass.config_entries.async_forward_entry_setups(entry, [Platform.SWITCH])
    
    # Set up service
    async def control_device(call: ServiceCall) -> None:
        """Control NetworkHD devices."""
        devices = call.data["device"]
        action = call.data["action"]
        target = call.data.get("target")
        
        if isinstance(devices, str):
            devices = [devices]
            
        try:
            if action == "power_on":
                await coordinator.set_display_power(devices, "on")
            elif action == "power_off":
                await coordinator.set_display_power(devices, "off")
            elif action == "route_to":
                if not target:
                    _LOGGER.error("Target required for route_to")
                    return
                await coordinator.matrix_set(target, devices)
            elif action == "clear_route":
                await coordinator.matrix_set_null(devices)
                
            await coordinator.async_request_refresh()
            
        except Exception as err:
            _LOGGER.error("Service error: %s", err)
    
    hass.services.async_register(DOMAIN, "control_device", control_device, CONTROL_SCHEMA)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hass.services.async_remove(DOMAIN, "control_device")
    
    unload_ok = await hass.config_entries.async_unload_platforms(entry, [Platform.SWITCH])
    
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_disconnect()
    
    return unload_ok


class NetworkHDCoordinator(DataUpdateCoordinator):
    """NetworkHD coordinator."""
    
    def __init__(self, hass: HomeAssistant, client: WyrestormNetworkHDClientSSH):
        """Initialize coordinator."""
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=30)
        self.client = client
        self.host = client.host
        self.devices = {}
        self.matrix_assignments = {}
        
    async def async_connect(self):
        """Connect to NetworkHD."""
        try:
            await self.client.connect()
            await self._discover_devices()
            await self._get_matrix_status()
        except Exception as err:
            _LOGGER.error("Connection failed: %s", err)
            raise
    
    async def async_disconnect(self):
        """Disconnect from NetworkHD."""
        try:
            await self.client.disconnect()
        except Exception as err:
            _LOGGER.error("Disconnect error: %s", err)
    
    async def _discover_devices(self):
        """Discover devices."""
        try:
            devices = await self.client.config_get_devicejsonstring()
            self.devices = {d["id"]: d for d in devices if d.get("alias")}
        except Exception as err:
            _LOGGER.error("Device discovery failed: %s", err)
    
    async def _get_matrix_status(self):
        """Get matrix status."""
        try:
            matrix = await self.client.matrix_get()
            self.matrix_assignments = {m["rx"]: m["tx"] for m in matrix}
        except Exception as err:
            _LOGGER.error("Matrix status failed: %s", err)
    
    async def set_display_power(self, devices: list[str], power: str) -> bool:
        """Set display power."""
        try:
            for device in devices:
                await self.client.config_set_device_sinkpower(device, power)
            return True
        except Exception as err:
            _LOGGER.error("Power control failed: %s", err)
            return False
    
    async def matrix_set(self, source: str, destinations: list[str]) -> bool:
        """Set matrix routing."""
        try:
            for dest in destinations:
                await self.client.matrix_set(source, dest)
            return True
        except Exception as err:
            _LOGGER.error("Matrix routing failed: %s", err)
            return False
    
    async def matrix_set_null(self, destinations: list[str]) -> bool:
        """Clear matrix routing."""
        try:
            for dest in destinations:
                await self.client.matrix_set_null(dest)
            return True
        except Exception as err:
            _LOGGER.error("Matrix clear failed: %s", err)
            return False
    
    async def _async_update_data(self):
        """Update data."""
        try:
            await self._discover_devices()
            await self._get_matrix_status()
            return {"devices": self.devices, "matrix": self.matrix_assignments}
        except Exception as err:
            raise UpdateFailed(f"Update failed: {err}")


async def async_setup_entry_switch(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Wait for initial data
    await coordinator.async_request_refresh()
    
    entities = []
    for device_id, device_data in coordinator.devices.items():
        if device_data.get("alias"):
            entities.append(NetworkHDSwitch(coordinator, device_id, device_data))
    
    if entities:
        async_add_entities(entities)


class NetworkHDSwitch(coordinator.CoordinatorEntity):
    """NetworkHD device switch."""
    
    def __init__(self, coordinator: NetworkHDCoordinator, device_id: str, device_data: dict):
        """Initialize switch."""
        super().__init__(coordinator)
        
        self.device_id = device_id
        self.device_data = device_data
        self.alias = device_data.get("alias", device_id)
        self.hostname = device_data.get("hostname", device_id)
        self.device_type = device_data.get("type", "unknown")
        
        self._attr_unique_id = f"{coordinator.host}_{self.hostname}"
        self._attr_name = self.alias
        self._attr_icon = "mdi:monitor" if "RX" in self.device_type else "mdi:video-input-component"
        self._attr_has_entity_name = False
    
    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.hostname)},
            name=self.alias,
            manufacturer="WyreStorm",
            model=self.device_type,
            via_device=(DOMAIN, self.coordinator.host),
        )
    
    @property
    def is_on(self) -> bool:
        """Return true if device is active."""
        if "RX" in self.device_type:
            # Decoder: check if it has a matrix assignment
            return self.coordinator.matrix_assignments.get(self.alias) is not None
        else:
            # Encoder: always on if online
            return self.device_data.get("status") == "online"
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity attributes."""
        attrs = {
            "device_type": self.device_type,
            "status": self.device_data.get("status", "unknown"),
        }
        
        if "RX" in self.device_type:
            attrs["matrix_assignment"] = self.coordinator.matrix_assignments.get(self.alias, "None")
        
        return attrs
    
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on - no-op for encoders, would route to default for decoders."""
        if "RX" in self.device_type:
            _LOGGER.info("Turn on not implemented for decoder %s", self.alias)
        else:
            _LOGGER.info("Turn on not implemented for encoder %s", self.alias)
    
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off - clear routing for decoders, no-op for encoders."""
        if "RX" in self.device_type:
            try:
                await self.coordinator.matrix_set_null([self.alias])
                await self.coordinator.async_request_refresh()
            except Exception as err:
                _LOGGER.error("Failed to clear routing for %s: %s", self.alias, err)
                raise
        else:
            _LOGGER.info("Turn off not implemented for encoder %s", self.alias)
