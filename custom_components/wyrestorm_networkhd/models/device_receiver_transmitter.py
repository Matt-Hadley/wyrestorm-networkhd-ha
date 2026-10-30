"""Device receiver/transmitter models for WyreStorm NetworkHD Integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wyrestorm_networkhd.models.api_query import DeviceInfo, DeviceJsonString, DeviceStatus


@dataclass
class DeviceBase:
    """Base class for WyreStorm NetworkHD devices with common attributes."""

    # Device identification (from DeviceJsonString)
    alias_name: str
    true_name: str
    device_type: str  # "Transmitter" or "Receiver"
    ip: str
    online: bool
    sequence: int

    # Network info (from DeviceInfo; None when the controller has no info for the device, e.g. offline)
    mac: str | None = None
    gateway: str | None = None
    netmask: str | None = None
    version: str | None = None
    edid: str | None = None
    ip_mode: str | None = None

    # Common status fields (from DeviceStatus)
    line_out_audio_enable: bool | None = None
    stream_frame_rate: int | None = None
    stream_resolution: str | None = None

    def __post_init__(self):
        self.manufacturer: str = "WyreStorm"
        self.model: str = self.true_name

    # Display methods
    def get_device_display_name(self) -> str:
        """Get the display name for the device.

        Returns:
            Human-readable device name prioritizing alias over IP over true name.
            Format: "DeviceType - DisplayName"

        Example:
            "Receiver - Living Room TV" or "Transmitter - 192.168.1.100"
        """
        return f"{self.device_type} - {self.alias_name or self.ip or self.true_name}"


@dataclass
class DeviceReceiver(DeviceBase):
    """Model representing a WyreStorm NetworkHD Receiver device.

    Receivers (decoders) receive video streams from transmitters and output
    to connected displays. They support power control and audio features.

    Attributes:
        tx_name: Currently connected transmitter name (if any).
        audio_bitrate: Current audio stream bitrate in kbps.
        display_power_status: CEC/RS232/IR display power state.
    """

    # RX specific fields from DeviceJsonString
    tx_name: str | None = None

    # RX specific fields from DeviceStatus
    audio_bitrate: int | None = None
    audio_input_format: str | None = None
    hdcp_status: str | None = None
    hdmi_out_active: bool | None = None
    hdmi_out_audio_enable: bool | None = None
    hdmi_out_frame_rate: int | None = None
    hdmi_out_resolution: str | None = None
    stream_error_count: int | None = None

    # RX specific fields from DeviceInfo
    sourcein: str | None = None
    analog_audio_source: str | None = None
    hdmi_audio_source: str | None = None
    video_mode: str | None = None
    video_stretch_type: str | None = None
    video_timing: str | None = None


@dataclass
class DeviceTransmitter(DeviceBase):
    """Model representing a WyreStorm NetworkHD Transmitter device."""

    # TX specific fields from DeviceJsonString
    nameoverlay: bool | None = None

    # TX specific fields from DeviceStatus
    audio_stream_ip_address: str | None = None
    encoding_enable: bool | None = None
    hdmi_in_active: bool | None = None
    hdmi_in_frame_rate: int | None = None
    resolution: str | None = None
    video_stream_ip_address: str | None = None

    # TX specific fields from DeviceInfo
    audio_input_type: str | None = None
    analog_audio_direction: str | None = None
    bandwidth_adjust_mode: int | None = None
    bit_perpixel: int | None = None
    color_space: str | None = None
    stream0_enable: bool | None = None
    stream0fps_by2_enable: bool | None = None
    stream1_enable: bool | None = None
    stream1_scale: str | None = None
    stream1fps_by2_enable: bool | None = None
    video_input: bool | None = None
    video_source: str | None = None


def create_device_from_wyrestorm_models(
    device_json: DeviceJsonString, device_status: DeviceStatus | None = None, device_info: DeviceInfo | None = None
) -> DeviceReceiver | DeviceTransmitter:
    """Factory function to create appropriate device type from wyrestorm-networkhd models.

    Args:
        device_json: DeviceJsonString model from wyrestorm-networkhd package
        device_status: DeviceStatus model, or None if the controller reported no status (offline device)
        device_info: DeviceInfo model, or None if the controller reported no info (offline device)

    Returns:
        DeviceReceiver or DeviceTransmitter instance based on device type
    """
    # Common fields for both device types
    common_kwargs = {
        # From DeviceJsonString
        "alias_name": device_json.aliasName,
        "true_name": device_json.trueName,
        "device_type": device_json.deviceType,
        "ip": device_json.ip,
        "online": device_json.online,
        "sequence": device_json.sequence,
        # From DeviceInfo
        "mac": getattr(device_info, "mac", None),
        "gateway": getattr(device_info, "gateway", None),
        "netmask": getattr(device_info, "netmask", None),
        "version": getattr(device_info, "version", None),
        "edid": getattr(device_info, "edid", None),
        "ip_mode": getattr(device_info, "ip_mode", None),
        # From DeviceStatus (optional common fields)
        "line_out_audio_enable": getattr(device_status, "line_out_audio_enable", None),
        "stream_frame_rate": getattr(device_status, "stream_frame_rate", None),
        "stream_resolution": getattr(device_status, "stream_resolution", None),
    }

    # Create appropriate subclass based on device type (case insensitive)
    device_type_lower = device_json.deviceType.lower()
    if device_type_lower == "receiver":
        return DeviceReceiver(
            **common_kwargs,
            # RX specific fields from DeviceJsonString
            tx_name=device_json.txName,
            # RX specific fields from DeviceStatus
            audio_bitrate=getattr(device_status, "audio_bitrate", None),
            audio_input_format=getattr(device_status, "audio_input_format", None),
            hdcp_status=getattr(device_status, "hdcp_status", None),
            hdmi_out_active=getattr(device_status, "hdmi_out_active", None),
            hdmi_out_audio_enable=getattr(device_status, "hdmi_out_audio_enable", None),
            hdmi_out_frame_rate=getattr(device_status, "hdmi_out_frame_rate", None),
            hdmi_out_resolution=getattr(device_status, "hdmi_out_resolution", None),
            stream_error_count=getattr(device_status, "stream_error_count", None),
            # RX specific fields from DeviceInfo
            sourcein=getattr(device_info, "sourcein", None),
            analog_audio_source=getattr(device_info, "analog_audio_source", None),
            hdmi_audio_source=getattr(device_info, "hdmi_audio_source", None),
            video_mode=getattr(device_info, "video_mode", None),
            video_stretch_type=getattr(device_info, "video_stretch_type", None),
            video_timing=getattr(device_info, "video_timing", None),
        )

    elif device_type_lower == "transmitter":
        return DeviceTransmitter(
            **common_kwargs,
            # TX specific fields from DeviceJsonString
            nameoverlay=device_json.nameoverlay,
            # TX specific fields from DeviceStatus
            audio_stream_ip_address=getattr(device_status, "audio_stream_ip_address", None),
            encoding_enable=getattr(device_status, "encoding_enable", None),
            hdmi_in_active=getattr(device_status, "hdmi_in_active", None),
            hdmi_in_frame_rate=getattr(device_status, "hdmi_in_frame_rate", None),
            resolution=getattr(device_status, "resolution", None),
            video_stream_ip_address=getattr(device_status, "video_stream_ip_address", None),
            # TX specific fields from DeviceInfo
            audio_input_type=getattr(device_info, "audio_input_type", None),
            analog_audio_direction=getattr(device_info, "analog_audio_direction", None),
            bandwidth_adjust_mode=getattr(device_info, "bandwidth_adjust_mode", None),
            bit_perpixel=getattr(device_info, "bit_perpixel", None),
            color_space=getattr(device_info, "color_space", None),
            stream0_enable=getattr(device_info, "stream0_enable", None),
            stream0fps_by2_enable=getattr(device_info, "stream0fps_by2_enable", None),
            stream1_enable=getattr(device_info, "stream1_enable", None),
            stream1_scale=getattr(device_info, "stream1_scale", None),
            stream1fps_by2_enable=getattr(device_info, "stream1fps_by2_enable", None),
            video_input=getattr(device_info, "video_input", None),
            video_source=getattr(device_info, "video_source", None),
        )

    else:
        raise ValueError(f"Unknown device type: {device_json.deviceType}")
