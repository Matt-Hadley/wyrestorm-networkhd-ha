"""Shared fixtures for WyreStorm NetworkHD 2 tests."""

import pytest
from wyrestorm_networkhd.models.api_query import (
    DeviceJsonString,
    DeviceJsonStringGroup,
    DeviceStatus,
    DeviceInfo,
    Version,
    IpSetting,
)

from custom_components.wyrestorm_networkhd_2.models.coordinator import CoordinatorData
from custom_components.wyrestorm_networkhd_2.models.device_controller import DeviceController
from custom_components.wyrestorm_networkhd_2.models.device_receiver_transmitter import (
    DeviceReceiver,
    DeviceTransmitter,
)


# Fixtures for wyrestorm-networkhd models
@pytest.fixture
def version_fixture():
    """Create a Version fixture."""
    return Version(api_version="1.0.0", web_version="2.1.0", core_version="3.0.1")


@pytest.fixture
def ip_setting_fixture():
    """Create an IpSetting fixture."""
    return IpSetting(ip4addr="192.168.1.100", netmask="255.255.255.0", gateway="192.168.1.1")


@pytest.fixture
def device_json_receiver_fixture():
    """Create a DeviceJsonString fixture for a receiver."""
    return DeviceJsonString(
        aliasName="Living Room RX",
        deviceType="Receiver",
        group=[DeviceJsonStringGroup(name="ungrouped", sequence=1)],
        ip="192.168.1.101",
        online=True,
        sequence=1,
        trueName="NHD-200-RX-01",
        txName="Apple TV",
    )


@pytest.fixture
def device_json_transmitter_fixture():
    """Create a DeviceJsonString fixture for a transmitter."""
    return DeviceJsonString(
        aliasName="Apple TV",
        deviceType="Transmitter",
        group=[DeviceJsonStringGroup(name="ungrouped", sequence=2)],
        ip="192.168.1.102",
        online=True,
        sequence=2,
        trueName="NHD-200-TX-01",
        nameoverlay=True,
    )


@pytest.fixture
def device_status_receiver_fixture():
    """Create a DeviceStatus fixture for a receiver."""
    return DeviceStatus(
        aliasname="Living Room RX",
        name="NHD-200-RX-01",
        # Common fields
        line_out_audio_enable=True,
        stream_frame_rate=60,
        stream_resolution="1920x1080",
        # RX specific
        audio_bitrate=192000,
        audio_input_format="PCM",
        hdcp_status="HDCP 2.2",
        hdmi_out_active=True,
        hdmi_out_audio_enable=True,
        hdmi_out_frame_rate=60,
        hdmi_out_resolution="1920x1080",
        stream_error_count=0,
    )


@pytest.fixture
def device_status_transmitter_fixture():
    """Create a DeviceStatus fixture for a transmitter."""
    return DeviceStatus(
        aliasname="Apple TV",
        name="NHD-200-TX-01",
        # Common fields
        line_out_audio_enable=False,
        stream_frame_rate=60,
        stream_resolution="1920x1080",
        # TX specific
        audio_stream_ip_address="239.0.0.2",
        encoding_enable=True,
        hdmi_in_active=True,
        hdmi_in_frame_rate=60,
        resolution="1920x1080",
        video_stream_ip_address="239.0.0.1",
    )


@pytest.fixture
def device_info_receiver_fixture():
    """Create a DeviceInfo fixture for a receiver."""
    return DeviceInfo(
        aliasname="Living Room RX",
        name="NHD-200-RX-01",
        # Common fields
        edid="Custom EDID",
        gateway="192.168.1.1",
        ip4addr="192.168.1.101",
        ip_mode="static",
        mac="AA:BB:CC:DD:EE:01",
        netmask="255.255.255.0",
        version="1.2.3",
        # RX specific
        sourcein="192.168.1.102",
        analog_audio_source="HDMI",
        hdmi_audio_source="Auto",
        video_mode="Auto",
        video_stretch_type="Fit",
        video_timing="1080p60",
        audio=None,
        sinkpower=None,
        # TX fields (should be None for RX)
        audio_input_type=None,
        analog_audio_direction=None,
        bandwidth_adjust_mode=None,
        bit_perpixel=None,
        color_space=None,
        stream0_enable=None,
        stream0fps_by2_enable=None,
        stream1_enable=None,
        stream1_scale=None,
        stream1fps_by2_enable=None,
        video_input=None,
        video_source=None,
        # Other unused fields
        cbr_avg_bitrate=None,
        enc_fps=None,
        enc_gop=None,
        enc_rc_mode=None,
        fixqp_iqp=None,
        fixqp_pqp=None,
        profile=None,
        transport_type=None,
        vbr_max_bitrate=None,
        vbr_max_qp=None,
        vbr_min_qp=None,
        km_over_ip_enable=None,
        videodetection=None,
        serial_param=None,
        temperature=None,
        genlock_scaling_resolution=None,
    )


@pytest.fixture
def device_info_transmitter_fixture():
    """Create a DeviceInfo fixture for a transmitter."""
    return DeviceInfo(
        aliasname="Apple TV",
        name="NHD-200-TX-01",
        # Common fields
        edid="Default EDID",
        gateway="192.168.1.1",
        ip4addr="192.168.1.102",
        ip_mode="dhcp",
        mac="AA:BB:CC:DD:EE:02",
        netmask="255.255.255.0",
        version="1.2.3",
        # TX specific
        audio_input_type="HDMI",
        analog_audio_direction="Input",
        bandwidth_adjust_mode=1,
        bit_perpixel=8,
        color_space="YUV444",
        stream0_enable=True,
        stream0fps_by2_enable=False,
        stream1_enable=False,
        stream1_scale="1/2",
        stream1fps_by2_enable=False,
        video_input=True,
        video_source="HDMI",
        # RX fields (should be None for TX)
        sourcein=None,
        analog_audio_source=None,
        hdmi_audio_source=None,
        video_mode=None,
        video_stretch_type=None,
        video_timing=None,
        audio=None,
        sinkpower=None,
        # Other unused fields
        cbr_avg_bitrate=None,
        enc_fps=None,
        enc_gop=None,
        enc_rc_mode=None,
        fixqp_iqp=None,
        fixqp_pqp=None,
        profile=None,
        transport_type=None,
        vbr_max_bitrate=None,
        vbr_max_qp=None,
        vbr_min_qp=None,
        km_over_ip_enable=None,
        videodetection=None,
        serial_param=None,
        temperature=None,
        genlock_scaling_resolution=None,
    )


# Fixtures for our models
@pytest.fixture
def device_controller_fixture():
    """Create a DeviceController fixture."""
    return DeviceController(
        api_version="1.0.0",
        web_version="2.1.0",
        core_version="3.0.1",
        ip4addr="192.168.1.100",
        netmask="255.255.255.0",
        gateway="192.168.1.1",
    )


@pytest.fixture
def device_receiver_fixture():
    """Create a DeviceReceiver fixture."""
    return DeviceReceiver(
        alias_name="Living Room RX",
        true_name="NHD-200-RX-01",
        device_type="Receiver",
        ip="192.168.1.101",
        online=True,
        sequence=1,
        mac="AA:BB:CC:DD:EE:01",
        gateway="192.168.1.1",
        netmask="255.255.255.0",
        version="1.2.3",
        edid="Custom EDID",
        ip_mode="static",
    )


@pytest.fixture
def device_transmitter_fixture():
    """Create a DeviceTransmitter fixture."""
    return DeviceTransmitter(
        alias_name="Apple TV",
        true_name="NHD-200-TX-01",
        device_type="Transmitter",
        ip="192.168.1.102",
        online=True,
        sequence=2,
        mac="AA:BB:CC:DD:EE:02",
        gateway="192.168.1.1",
        netmask="255.255.255.0",
        version="1.2.3",
        edid="Default EDID",
        ip_mode="dhcp",
    )


@pytest.fixture
def coordinator_data_fixture(device_controller_fixture):
    """Create a CoordinatorData fixture."""
    return CoordinatorData(device_controller=device_controller_fixture)
