"""Device receiver/transmitter models for WyreStorm NetworkHD Integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wyrestorm_networkhd.models.api_query import DeviceInfo, DeviceJsonString, DeviceStatus


@dataclass
class DeviceBase:
    """The endpoint fields entities read (diagnostics also dump the library models)."""

    # From DeviceJsonString
    alias_name: str
    true_name: str
    device_type: str  # "Transmitter" or "Receiver"
    ip: str
    online: bool

    # From DeviceInfo (None when the controller has no info for the device, e.g. offline)
    mac: str | None = None
    version: str | None = None

    def get_device_display_name(self) -> str:
        """Return "DeviceType - DisplayName", preferring the alias, then the IP, then the true name."""
        return f"{self.device_type} - {self.alias_name or self.ip or self.true_name}"


@dataclass
class DeviceReceiver(DeviceBase):
    """A NetworkHD receiver (decoder), which outputs a transmitter's stream to a display."""

    hdmi_out_frame_rate: int | None = None  # from DeviceStatus


@dataclass
class DeviceTransmitter(DeviceBase):
    """A NetworkHD transmitter (encoder)."""

    hdmi_in_frame_rate: int | None = None  # from DeviceStatus


def create_device_from_wyrestorm_models(
    device_json: DeviceJsonString, device_status: DeviceStatus | None = None, device_info: DeviceInfo | None = None
) -> DeviceReceiver | DeviceTransmitter:
    """Create a receiver or transmitter from the library models (status/info are None for offline devices).

    Raises:
        ValueError: if the device type is neither receiver nor transmitter.
    """
    common = {
        "alias_name": device_json.aliasName,
        "true_name": device_json.trueName,
        "device_type": device_json.deviceType,
        "ip": device_json.ip,
        "online": device_json.online,
        "mac": getattr(device_info, "mac", None),
        "version": getattr(device_info, "version", None),
    }
    device_type = device_json.deviceType.lower()
    if device_type == "receiver":
        return DeviceReceiver(**common, hdmi_out_frame_rate=getattr(device_status, "hdmi_out_frame_rate", None))
    if device_type == "transmitter":
        return DeviceTransmitter(**common, hdmi_in_frame_rate=getattr(device_status, "hdmi_in_frame_rate", None))
    raise ValueError(f"Unknown device type: {device_json.deviceType}")
