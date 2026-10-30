"""Diagnostics for the WyreStorm NetworkHD integration."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .coordinator import WyreStormConfigEntry

# The host is also the unique id and part of the title.
TO_REDACT = {CONF_HOST, CONF_PASSWORD, CONF_USERNAME, "unique_id", "title", "ip", "ip4addr", "gateway", "mac"}


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: WyreStormConfigEntry) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    return {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "last_update_success": coordinator.last_update_success,
        "data": async_redact_data(asdict(coordinator.data), TO_REDACT),
        # Raw library models, which carry many more fields than the entities use.
        "device_status": async_redact_data([asdict(d) for d in coordinator._device_status], TO_REDACT),
        "device_info": async_redact_data([asdict(d) for d in coordinator._device_info], TO_REDACT),
    }
