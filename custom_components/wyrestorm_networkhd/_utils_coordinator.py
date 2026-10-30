"""Utility functions for WyreStorm NetworkHD Coordinator."""

import logging

from wyrestorm_networkhd.models.api_query import DeviceInfo, DeviceJsonString, DeviceStatus

from .models.device_receiver_transmitter import (
    DeviceReceiver,
    DeviceTransmitter,
    create_device_from_wyrestorm_models,
)

_LOGGER = logging.getLogger(__name__)


def _json_from_name(name: str, status: DeviceStatus | None, info: DeviceInfo | None) -> DeviceJsonString | None:
    """Build a minimal DeviceJsonString for a device missing from the controller's device list."""
    upper = name.upper()
    if "-RX-" in upper:
        device_type = "Receiver"
    elif "-TX-" in upper:
        device_type = "Transmitter"
    else:
        return None
    source = status or info
    return DeviceJsonString(
        aliasName=source.aliasname if source else name,
        deviceType=device_type,
        group=[],
        ip=(info.ip4addr if info else None) or "",
        online=True,  # it answered a status/info query
        sequence=0,
        trueName=name,
    )


def build_device_collections(
    device_json_list: list[DeviceJsonString],
    device_status_list: list[DeviceStatus],
    device_info_list: list[DeviceInfo],
) -> tuple[dict[str, DeviceTransmitter], dict[str, DeviceReceiver]]:
    """Build device collections from the union of all data sources.

    Endpoints missing from status/info (typically offline ones) are kept so they show as offline
    instead of disappearing.
    """
    transmitters: dict[str, DeviceTransmitter] = {}
    receivers: dict[str, DeviceReceiver] = {}

    json_by_name = {d.trueName: d for d in device_json_list}
    status_by_name = {d.name: d for d in device_status_list}
    info_by_name = {d.name: d for d in device_info_list}

    for name in json_by_name | status_by_name | info_by_name:
        status = status_by_name.get(name)
        info = info_by_name.get(name)
        device_json = json_by_name.get(name) or _json_from_name(name, status, info)
        if device_json is None:
            _LOGGER.debug("Skipping %s: unknown device type", name)
            continue
        try:
            device = create_device_from_wyrestorm_models(device_json, status, info)
        except ValueError as err:
            _LOGGER.warning("Failed to create device %s: %s", name, err)
            continue
        if isinstance(device, DeviceTransmitter):
            transmitters[device.true_name] = device
        else:
            receivers[device.true_name] = device

    _LOGGER.debug("Processed %d transmitters and %d receivers", len(transmitters), len(receivers))
    return transmitters, receivers
