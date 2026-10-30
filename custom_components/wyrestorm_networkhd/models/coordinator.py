"""Coordinator model for WyreStorm NetworkHD Integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .device_controller import DeviceController
from .device_receiver_transmitter import DeviceReceiver, DeviceTransmitter


@dataclass
class CoordinatorData:
    """Data model for WyreStorm NetworkHD Coordinator.

    This class holds all the device data and state information
    that the coordinator manages and shares with entities.
    """

    # Core device data
    device_controller: DeviceController
    device_transmitters: dict[str, DeviceTransmitter] = field(default_factory=dict)
    device_receivers: dict[str, DeviceReceiver] = field(default_factory=dict)

    # Matrix assignments: receiver alias -> source alias
    matrix_assignments: dict[str, str] = field(default_factory=dict)

    # Metadata
    last_update: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Update timestamp after initialization."""
        self.last_update = datetime.now()

    # Device list getters
    def get_transmitters_list(self) -> list[DeviceTransmitter]:
        """Get all transmitters as a list.

        Returns:
            List of all transmitters
        """
        return list(self.device_transmitters.values())

    def get_receivers_list(self) -> list[DeviceReceiver]:
        """Get all receivers as a list.

        Returns:
            List of all receivers
        """
        return list(self.device_receivers.values())
