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

    # Device management methods
    def update_device(self, device: DeviceReceiver | DeviceTransmitter) -> bool:
        """Update an existing device or add it if it doesn't exist.

        Args:
            device: The device to update

        Returns:
            True if device was updated, False if it was added (new device)
        """
        if isinstance(device, DeviceReceiver):
            key = device.true_name
            was_existing = key in self.device_receivers
            self.device_receivers[key] = device
        elif isinstance(device, DeviceTransmitter):
            key = device.true_name
            was_existing = key in self.device_transmitters
            self.device_transmitters[key] = device
        else:
            raise ValueError(f"Unknown device type: {type(device)}")

        self.last_update = datetime.now()
        return was_existing

    def remove_device(self, true_name: str) -> bool:
        """Remove a device by true name.

        Args:
            true_name: The true name of the device to remove

        Returns:
            True if a device was removed, False if no device was found
        """
        removed = False
        if true_name in self.device_receivers:
            del self.device_receivers[true_name]
            removed = True
        elif true_name in self.device_transmitters:
            del self.device_transmitters[true_name]
            removed = True

        if removed:
            self.last_update = datetime.now()

        return removed

    # Matrix assignment methods
    def update_matrix_assignment(self, receiver_alias: str, source_alias: str) -> bool:
        """Update or add a matrix assignment.

        Args:
            receiver_alias: The alias name of the receiver
            source_alias: The alias name of the source

        Returns:
            True if assignment was updated, False if it was added (new assignment)
        """
        was_existing = receiver_alias in self.matrix_assignments
        self.matrix_assignments[receiver_alias] = source_alias
        self.last_update = datetime.now()
        return was_existing

    def remove_matrix_assignment(self, receiver_alias: str) -> bool:
        """Remove a matrix assignment.

        Args:
            receiver_alias: The alias name of the receiver

        Returns:
            True if assignment was removed, False if no assignment was found
        """
        if receiver_alias in self.matrix_assignments:
            del self.matrix_assignments[receiver_alias]
            self.last_update = datetime.now()
            return True
        return False
