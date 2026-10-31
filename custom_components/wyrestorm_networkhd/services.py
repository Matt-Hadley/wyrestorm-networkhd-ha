"""Services for the WyreStorm NetworkHD integration."""

from __future__ import annotations

from collections.abc import Callable

import probatio as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import (
    ATTR_CONFIG_ENTRY_ID,
    ATTR_DEVICES,
    ATTR_POWER_STATE,
    ATTR_SOURCE_DEVICE,
    ATTR_TARGET_DEVICE,
    DOMAIN,
    SERVICE_MATRIX_SET,
    SERVICE_POWER_CONTROL,
)
from .coordinator import WyreStormCoordinator
from .models.device_receiver_transmitter import DeviceReceiver, DeviceTransmitter

_NAMES = vol.All(cv.ensure_list, [cv.string], vol.Length(min=1))

MATRIX_SET_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,
        vol.Optional(ATTR_SOURCE_DEVICE): vol.All(cv.string, vol.Length(min=1)),  # omit to disconnect
        vol.Required(ATTR_TARGET_DEVICE): _NAMES,
    }
)

POWER_CONTROL_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,
        vol.Required(ATTR_DEVICES): _NAMES,
        vol.Required(ATTR_POWER_STATE): vol.In(["on", "off"]),
    }
)


def _find_receivers(coordinator: WyreStormCoordinator, names: list[str]) -> list[DeviceReceiver] | None:
    """Return the coordinator's receivers for all `names`, or None if any is not one of its receivers."""
    receivers = [r for name in names if (r := coordinator.find_receiver(name))]
    return receivers if len(receivers) == len(names) else None


def _resolve[T](
    hass: HomeAssistant, call: ServiceCall, names: list[str], resolve: Callable[[WyreStormCoordinator], T | None]
) -> tuple[WyreStormCoordinator, T]:
    """Find the one loaded controller on which `resolve` finds all the named devices."""
    if entry_id := call.data.get(ATTR_CONFIG_ENTRY_ID):
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry is None or entry.domain != DOMAIN or entry.state is not ConfigEntryState.LOADED:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="entry_not_loaded",
                translation_placeholders={"entry": entry_id},
            )
        entries = [entry]
    else:
        entries = hass.config_entries.async_loaded_entries(DOMAIN)

    matches = [(c, found) for e in entries if (found := resolve(c := e.runtime_data)) is not None]
    placeholders = {"devices": ", ".join(names)}
    if not matches:
        raise ServiceValidationError(
            translation_domain=DOMAIN, translation_key="device_not_found", translation_placeholders=placeholders
        )
    if len(matches) > 1:
        raise ServiceValidationError(
            translation_domain=DOMAIN, translation_key="device_ambiguous", translation_placeholders=placeholders
        )
    return matches[0]


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register the integration's services."""

    async def handle_matrix_set(call: ServiceCall) -> None:
        source: str | None = call.data.get(ATTR_SOURCE_DEVICE)
        targets: list[str] = call.data[ATTR_TARGET_DEVICE]

        def resolve(c: WyreStormCoordinator) -> tuple[DeviceTransmitter | None, list[DeviceReceiver]] | None:
            receivers = _find_receivers(c, targets)
            transmitter = c.find_transmitter(source) if source else None
            if receivers is None or (source and transmitter is None):
                return None
            return transmitter, receivers

        coordinator, (transmitter, receivers) = _resolve(hass, call, [*filter(None, [source]), *targets], resolve)
        await coordinator.async_set_matrix(transmitter, receivers)

    async def handle_power_control(call: ServiceCall) -> None:
        names: list[str] = call.data[ATTR_DEVICES]

        coordinator, receivers = _resolve(hass, call, names, lambda c: _find_receivers(c, names))
        await coordinator.async_set_power(receivers, call.data[ATTR_POWER_STATE])

    hass.services.async_register(DOMAIN, SERVICE_MATRIX_SET, handle_matrix_set, schema=MATRIX_SET_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_POWER_CONTROL, handle_power_control, schema=POWER_CONTROL_SCHEMA)
