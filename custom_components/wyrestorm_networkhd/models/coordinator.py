"""Coordinator model for WyreStorm NetworkHD Integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from wyrestorm_networkhd.models.api_query import Version

from .device_receiver_transmitter import DeviceReceiver, DeviceTransmitter


@dataclass
class CoordinatorData:
    """The data the coordinator shares with entities."""

    version: Version  # controller firmware versions
    device_transmitters: dict[str, DeviceTransmitter] = field(default_factory=dict)
    device_receivers: dict[str, DeviceReceiver] = field(default_factory=dict)

    # Matrix assignments: receiver alias -> source alias (None when disconnected)
    matrix_assignments: dict[str, str | None] = field(default_factory=dict)

    last_update: datetime = field(default_factory=datetime.now)  # last full refresh
