"""Device receiver/transmitter models for WyreStorm NetworkHD Integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wyrestorm_networkhd.models.api_query import DeviceInfo, DeviceJsonString, DeviceStatus

DOMAIN = "wyrestorm_networkhd_2"


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

    # Network info (from DeviceInfo)
    mac: str
    gateway: str
    netmask: str
    version: str
    edid: str
    ip_mode: str

    # Common status fields (from DeviceStatus)
    line_out_audio_enable: bool | None = None
    stream_frame_rate: int | None = None
    stream_resolution: str | None = None

    def __post_init__(self):
        self.manufacturer: str = "WyreStorm"
        self.model: str = self.true_name

    # Display methods
    def get_device_display_name(self) -> str:
        """Get the display name for the device."""
        return f"{self.device_type} - {self.alias_name or self.ip or self.true_name}"


@dataclass
class DeviceReceiver(DeviceBase):
    """Model representing a WyreStorm NetworkHD Receiver device."""

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
    device_json: DeviceJsonString, device_status: DeviceStatus, device_info: DeviceInfo
) -> DeviceReceiver | DeviceTransmitter:
    """Factory function to create appropriate device type from wyrestorm-networkhd models.

    Args:
        device_json: DeviceJsonString model from wyrestorm-networkhd package
        device_status: DeviceStatus model from wyrestorm-networkhd package
        device_info: DeviceInfo model from wyrestorm-networkhd package

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
        "mac": device_info.mac,
        "gateway": device_info.gateway,
        "netmask": device_info.netmask,
        "version": device_info.version,
        "edid": device_info.edid,
        "ip_mode": device_info.ip_mode,
        # From DeviceStatus (optional common fields)
        "line_out_audio_enable": device_status.line_out_audio_enable,
        "stream_frame_rate": device_status.stream_frame_rate,
        "stream_resolution": device_status.stream_resolution,
    }

    # Create appropriate subclass based on device type (case insensitive)
    device_type_lower = device_json.deviceType.lower()
    if device_type_lower == "receiver":
        return DeviceReceiver(
            **common_kwargs,
            # RX specific fields from DeviceJsonString
            tx_name=device_json.txName,
            # RX specific fields from DeviceStatus
            audio_bitrate=device_status.audio_bitrate,
            audio_input_format=device_status.audio_input_format,
            hdcp_status=device_status.hdcp_status,
            hdmi_out_active=device_status.hdmi_out_active,
            hdmi_out_audio_enable=device_status.hdmi_out_audio_enable,
            hdmi_out_frame_rate=device_status.hdmi_out_frame_rate,
            hdmi_out_resolution=device_status.hdmi_out_resolution,
            stream_error_count=device_status.stream_error_count,
            # RX specific fields from DeviceInfo
            sourcein=device_info.sourcein,
            analog_audio_source=device_info.analog_audio_source,
            hdmi_audio_source=device_info.hdmi_audio_source,
            video_mode=device_info.video_mode,
            video_stretch_type=device_info.video_stretch_type,
            video_timing=device_info.video_timing,
        )

    elif device_type_lower == "transmitter":
        return DeviceTransmitter(
            **common_kwargs,
            # TX specific fields from DeviceJsonString
            nameoverlay=device_json.nameoverlay,
            # TX specific fields from DeviceStatus
            audio_stream_ip_address=device_status.audio_stream_ip_address,
            encoding_enable=device_status.encoding_enable,
            hdmi_in_active=device_status.hdmi_in_active,
            hdmi_in_frame_rate=device_status.hdmi_in_frame_rate,
            resolution=device_status.resolution,
            video_stream_ip_address=device_status.video_stream_ip_address,
            # TX specific fields from DeviceInfo
            audio_input_type=device_info.audio_input_type,
            analog_audio_direction=device_info.analog_audio_direction,
            bandwidth_adjust_mode=device_info.bandwidth_adjust_mode,
            bit_perpixel=device_info.bit_perpixel,
            color_space=device_info.color_space,
            stream0_enable=device_info.stream0_enable,
            stream0fps_by2_enable=device_info.stream0fps_by2_enable,
            stream1_enable=device_info.stream1_enable,
            stream1_scale=device_info.stream1_scale,
            stream1fps_by2_enable=device_info.stream1fps_by2_enable,
            video_input=device_info.video_input,
            video_source=device_info.video_source,
        )

    else:
        raise ValueError(f"Unknown device type: {device_json.deviceType}")
