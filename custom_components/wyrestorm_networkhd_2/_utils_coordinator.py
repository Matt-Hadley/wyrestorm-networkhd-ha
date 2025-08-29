"""Utility functions for WyreStorm NetworkHD 2 Coordinator."""

import logging
from typing import Any

try:
    from wyrestorm_networkhd.models.api_query import DeviceInfo, DeviceJsonString, DeviceStatus
except ImportError:
    # Fallback for testing or when models aren't available
    DeviceInfo = Any
    DeviceJsonString = Any
    DeviceStatus = Any

from .models.device_receiver_transmitter import create_device_from_wyrestorm_models

_LOGGER = logging.getLogger(__name__)


def build_device_collections(
    device_json_list: list[DeviceJsonString],
    device_status_list: list[DeviceStatus],
    device_info_list: list[DeviceInfo],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build device collections from all data sources."""
    transmitters = {}
    receivers = {}

    # Create device mapping by true name from device_json (primary source)
    for device_json in device_json_list:
        device_name = device_json.trueName
        
        # Find corresponding status and info
        device_status = next((d for d in device_status_list if d.name == device_name), None)
        device_info = next((d for d in device_info_list if d.name == device_name), None)
        
        if device_status and device_info:
            try:
                device = create_device_from_wyrestorm_models(device_json, device_status, device_info)
                
                if device.device_type == "Transmitter":
                    transmitters[device.true_name] = device
                else:  # Receiver
                    receivers[device.true_name] = device

                _LOGGER.debug(
                    "Created %s device: %s (%s)",
                    device.device_type.lower(),
                    device.alias_name,
                    device.true_name,
                )
            except Exception as err:
                _LOGGER.warning("Failed to create device %s: %s", device_name, err)

    _LOGGER.info(
        "Successfully processed %d transmitters and %d receivers",
        len(transmitters),
        len(receivers),
    )

    return transmitters, receivers


def process_matrix_assignments(matrix_response: Any) -> dict[str, str]:
    """Process matrix assignments into receiver alias -> source alias mapping."""
    matrix_assignments = {}

    if not (matrix_response and hasattr(matrix_response, "assignments")):
        _LOGGER.debug("No matrix assignments found")
        return matrix_assignments

    try:
        assignments = matrix_response.assignments or []
        
        for assignment in assignments:
            if hasattr(assignment, "tx") and hasattr(assignment, "rx"):
                source_alias = assignment.tx
                receiver_alias = assignment.rx
                matrix_assignments[receiver_alias] = source_alias
                _LOGGER.debug("Matrix assignment: %s -> %s", source_alias, receiver_alias)

        _LOGGER.info("Processed %d matrix assignments", len(matrix_assignments))

    except Exception as err:
        _LOGGER.warning("Failed to process matrix data: %s", err)

    return matrix_assignments