"""Comprehensive fixtures for WyreStorm NetworkHD tests.

This module provides all test fixtures organized by model and category
for better maintainability and discovery.

Organization by Model/Category:
    1. WyreStorm API Models - External API models (Version, IpSetting, etc.)
    2. DeviceController - Controller device fixtures
    3. DeviceReceiver - Receiver device fixtures
    4. DeviceTransmitter - Transmitter device fixtures
    5. CoordinatorData - Coordinator and data management fixtures
    6. Matrix Assignments - Routing assignment fixtures
    7. Multi-Device Systems - Integration testing fixtures
    8. Utility & Edge Cases - Error conditions and boundary testing
"""

import pytest
from wyrestorm_networkhd.models.api_query import (
    DeviceInfo,
    DeviceJsonString,
    DeviceJsonStringGroup,
    DeviceStatus,
    IpSetting,
    Matrix,
    MatrixAssignment,
    Version,
)

from custom_components.wyrestorm_networkhd.models.coordinator import CoordinatorData
from custom_components.wyrestorm_networkhd.models.device_controller import DeviceController
from custom_components.wyrestorm_networkhd.models.device_receiver_transmitter import (
    DeviceReceiver,
    DeviceTransmitter,
)

# =============================================================================
# WYRESTORM API MODELS
# =============================================================================
# Fixtures for external WyreStorm API models


@pytest.fixture
def version_fixture():
    """Standard Version with common version numbers."""
    return Version(api_version="1.0.0", web_version="2.1.0", core_version="3.0.1")


@pytest.fixture
def alternative_version_fixture():
    """Alternative Version with different version numbers for comparison tests."""
    return Version(api_version="2.5.0", web_version="3.2.1", core_version="4.1.2")


@pytest.fixture
def ip_setting_fixture():
    """Standard IpSetting with common network configuration."""
    return IpSetting(ip4addr="192.168.1.100", netmask="255.255.255.0", gateway="192.168.1.1")


@pytest.fixture
def alternative_ip_setting_fixture():
    """Alternative IpSetting with different network configuration for comparison tests."""
    return IpSetting(ip4addr="10.0.0.50", netmask="255.255.0.0", gateway="10.0.0.1")


@pytest.fixture
def device_json_receiver_fixture():
    """DeviceJsonString for a typical receiver device."""
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
    """DeviceJsonString for a typical transmitter device."""
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
    """DeviceStatus for a receiver with comprehensive status data."""
    return DeviceStatus(
        aliasname="Living Room RX",
        name="NHD-200-RX-01",
        # Common device status fields
        line_out_audio_enable=True,
        stream_frame_rate=60,
        stream_resolution="1920x1080",
        # Receiver-specific status fields
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
    """DeviceStatus for a transmitter with comprehensive status data."""
    return DeviceStatus(
        aliasname="Apple TV",
        name="NHD-200-TX-01",
        # Common device status fields
        line_out_audio_enable=False,
        stream_frame_rate=60,
        stream_resolution="1920x1080",
        # Transmitter-specific status fields
        audio_stream_ip_address="239.0.0.2",
        encoding_enable=True,
        hdmi_in_active=True,
        hdmi_in_frame_rate=60,
        resolution="1920x1080",
        video_stream_ip_address="239.0.0.1",
    )


@pytest.fixture
def device_info_receiver_fixture():
    """DeviceInfo for a receiver with complete device information."""
    return DeviceInfo(
        aliasname="Living Room RX",
        name="NHD-200-RX-01",
        # Common device information fields
        edid="Custom EDID",
        gateway="192.168.1.1",
        ip4addr="192.168.1.101",
        ip_mode="static",
        mac="AA:BB:CC:DD:EE:01",
        netmask="255.255.255.0",
        version="1.2.3",
        # Receiver-specific fields
        sourcein="192.168.1.102",
        analog_audio_source="HDMI",
        hdmi_audio_source="Auto",
        video_mode="Auto",
        video_stretch_type="Fit",
        video_timing="1080p60",
        audio=None,
        sinkpower=None,
        # Transmitter fields (None for receivers)
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
        # Unused/optional fields set to None
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
    """DeviceInfo for a transmitter with complete device information."""
    return DeviceInfo(
        aliasname="Apple TV",
        name="NHD-200-TX-01",
        # Common device information fields
        edid="Default EDID",
        gateway="192.168.1.1",
        ip4addr="192.168.1.102",
        ip_mode="dhcp",
        mac="AA:BB:CC:DD:EE:02",
        netmask="255.255.255.0",
        version="1.2.3",
        # Transmitter-specific fields
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
        # Receiver fields (None for transmitters)
        sourcein=None,
        analog_audio_source=None,
        hdmi_audio_source=None,
        video_mode=None,
        video_stretch_type=None,
        video_timing=None,
        audio=None,
        sinkpower=None,
        # Unused/optional fields set to None
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


# =============================================================================
# DEVICE CONTROLLER FIXTURES
# =============================================================================
# Fixtures for DeviceController model testing


@pytest.fixture
def device_controller_fixture():
    """Standard DeviceController for most test scenarios."""
    return DeviceController(
        api_version="1.0.0",
        web_version="2.1.0",
        core_version="3.0.1",
        ip4addr="192.168.1.100",
        netmask="255.255.255.0",
        gateway="192.168.1.1",
    )


@pytest.fixture
def device_controller_alternative_fixture():
    """Alternative DeviceController for comparison tests."""
    return DeviceController(
        api_version="2.5.0",
        web_version="3.2.1",
        core_version="4.1.2",
        ip4addr="10.0.0.50",
        netmask="255.255.0.0",
        gateway="10.0.0.1",
    )


@pytest.fixture(
    params=[
        ("192.168.1.100", "Controller - 192.168.1.100"),
        ("10.0.0.1", "Controller - 10.0.0.1"),
        ("172.16.0.254", "Controller - 172.16.0.254"),
    ]
)
def device_controller_display_name_test_cases(request):
    """Parametrized fixture for testing DeviceController display names with different IPs.

    Returns:
        tuple: (DeviceController instance, expected_display_name)
    """
    ip_addr, expected_name = request.param
    controller = DeviceController(
        api_version="1.0.0",
        web_version="2.1.0",
        core_version="3.0.1",
        ip4addr=ip_addr,
        netmask="255.255.255.0",
        gateway="192.168.1.1",
    )
    return controller, expected_name


# =============================================================================
# DEVICE RECEIVER FIXTURES
# =============================================================================
# Fixtures for DeviceReceiver model testing


@pytest.fixture
def device_receiver_fixture():
    """Standard DeviceReceiver for testing receiver functionality."""
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
def device_receiver_bedroom_fixture():
    """Secondary DeviceReceiver for multi-device testing."""
    return DeviceReceiver(
        alias_name="Bedroom RX",
        true_name="NHD-200-RX-02",
        device_type="Receiver",
        ip="192.168.1.103",
        online=True,
        sequence=3,
        mac="AA:BB:CC:DD:EE:03",
        gateway="192.168.1.1",
        netmask="255.255.255.0",
        version="1.2.3",
        edid="Custom EDID",
        ip_mode="static",
    )


@pytest.fixture
def device_receiver_updated_fixture():
    """DeviceReceiver for testing updates - modified version of standard receiver."""
    return DeviceReceiver(
        alias_name="Updated Living Room RX",
        true_name="NHD-200-RX-01",  # Same as device_receiver_fixture
        device_type="Receiver",
        ip="192.168.1.201",  # Different IP
        online=False,  # Different online status
        sequence=1,
        mac="AA:BB:CC:DD:EE:01",
        gateway="192.168.1.1",
        netmask="255.255.255.0",
        version="1.2.3",
        edid="Custom EDID",
        ip_mode="static",
    )


@pytest.fixture
def device_receiver_minimal_fixture():
    """Minimal DeviceReceiver with required fields only."""
    return DeviceReceiver(
        alias_name="Minimal RX",
        true_name="MIN-RX-01",
        device_type="Receiver",
        ip="10.0.0.100",
        online=False,
        sequence=5,
        mac="11:22:33:44:55:66",
        gateway="10.0.0.1",
        netmask="255.255.255.0",
        version="2.0.0",
        edid="Minimal EDID",
        ip_mode="dhcp",
    )


@pytest.fixture
def device_receiver_full_fixture():
    """DeviceReceiver with all optional fields populated."""
    return DeviceReceiver(
        alias_name="Full RX",
        true_name="FULL-RX-01",
        device_type="Receiver",
        ip="172.16.0.50",
        online=True,
        sequence=10,
        mac="AA:BB:CC:DD:EE:FF",
        gateway="172.16.0.1",
        netmask="255.255.0.0",
        version="3.1.0",
        edid="Full EDID",
        ip_mode="static",
        # Optional RX fields
        tx_name="Source TX",
        hdmi_out_active=True,
        hdmi_out_frame_rate=30,
        hdmi_out_resolution="1280x720",
        hdcp_status="HDCP 1.4",
        sourcein="172.16.0.51",
        video_mode="Manual",
    )


@pytest.fixture
def device_receiver_no_alias_fixture():
    """DeviceReceiver with empty alias for display name fallback testing."""
    return DeviceReceiver(
        alias_name="",  # Empty alias
        true_name="NO-ALIAS-RX-01",
        device_type="Receiver",
        ip="192.168.0.200",
        online=True,
        sequence=1,
        mac="AA:BB:CC:DD:EE:FF",
        gateway="192.168.0.1",
        netmask="255.255.255.0",
        version="1.0.0",
        edid="Test EDID",
        ip_mode="static",
    )


@pytest.fixture
def device_receiver_no_ip_fixture():
    """DeviceReceiver with empty IP for display name fallback testing."""
    return DeviceReceiver(
        alias_name="",  # Empty alias
        true_name="NO-IP-RX-01",
        device_type="Receiver",
        ip="",  # Empty IP
        online=True,
        sequence=1,
        mac="AA:BB:CC:DD:EE:FF",
        gateway="192.168.0.1",
        netmask="255.255.255.0",
        version="1.0.0",
        edid="Test EDID",
        ip_mode="static",
    )


@pytest.fixture
def device_receiver_for_equality_fixture():
    """DeviceReceiver specifically for equality testing."""
    return DeviceReceiver(
        alias_name="Test RX",
        true_name="TEST-RX-01",
        device_type="Receiver",
        ip="192.168.1.100",
        online=True,
        sequence=1,
        mac="AA:BB:CC:DD:EE:FF",
        gateway="192.168.1.1",
        netmask="255.255.255.0",
        version="1.0.0",
        edid="Test EDID",
        ip_mode="static",
    )


# =============================================================================
# DEVICE TRANSMITTER FIXTURES
# =============================================================================
# Fixtures for DeviceTransmitter model testing


@pytest.fixture
def device_transmitter_fixture():
    """Standard DeviceTransmitter for testing transmitter functionality."""
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
def device_transmitter_minimal_fixture():
    """Minimal DeviceTransmitter with required fields only."""
    return DeviceTransmitter(
        alias_name="Minimal TX",
        true_name="MIN-TX-01",
        device_type="Transmitter",
        ip="10.0.0.101",
        online=True,
        sequence=3,
        mac="66:55:44:33:22:11",
        gateway="10.0.0.1",
        netmask="255.255.255.0",
        version="2.1.0",
        edid="Minimal TX EDID",
        ip_mode="static",
    )


@pytest.fixture
def device_transmitter_full_fixture():
    """DeviceTransmitter with all optional fields populated."""
    return DeviceTransmitter(
        alias_name="Full TX",
        true_name="FULL-TX-01",
        device_type="Transmitter",
        ip="172.16.0.52",
        online=False,
        sequence=15,
        mac="FF:EE:DD:CC:BB:AA",
        gateway="172.16.0.1",
        netmask="255.255.0.0",
        version="4.0.0",
        edid="Full TX EDID",
        ip_mode="dhcp",
        # Optional TX fields
        nameoverlay=False,
        hdmi_in_active=False,
        hdmi_in_frame_rate=24,
        resolution="4K",
        video_stream_ip_address="239.1.1.1",
        audio_stream_ip_address="239.1.1.2",
        color_space="RGB",
        video_source="DisplayPort",
    )


@pytest.fixture
def device_transmitter_for_equality_fixture():
    """DeviceTransmitter specifically for equality testing."""
    return DeviceTransmitter(
        alias_name="Test TX",
        true_name="TEST-TX-01",
        device_type="Transmitter",
        ip="192.168.1.100",
        online=True,
        sequence=1,
        mac="AA:BB:CC:DD:EE:FF",
        gateway="192.168.1.1",
        netmask="255.255.255.0",
        version="1.0.0",
        edid="Test EDID",
        ip_mode="static",
    )


# =============================================================================
# COORDINATOR DATA FIXTURES
# =============================================================================
# Fixtures for CoordinatorData model testing


@pytest.fixture
def coordinator_data_fixture(device_controller_fixture):
    """Standard CoordinatorData for testing coordination functionality."""
    return CoordinatorData(device_controller=device_controller_fixture)


# =============================================================================
# MATRIX ASSIGNMENT FIXTURES
# =============================================================================
# Fixtures for testing matrix routing assignments


@pytest.fixture
def single_matrix_assignment_fixture():
    """Matrix with a single assignment for basic testing."""
    return Matrix(assignments=[MatrixAssignment(rx="Living Room RX", tx="Apple TV")])


@pytest.fixture
def multiple_matrix_assignments_fixture():
    """Matrix with multiple assignments for comprehensive testing."""
    return Matrix(
        assignments=[
            MatrixAssignment(rx="Living Room RX", tx="Apple TV"),
            MatrixAssignment(rx="Bedroom RX", tx="Cable Box"),
            MatrixAssignment(rx="Kitchen RX", tx="Streaming Device"),
        ]
    )


@pytest.fixture
def matrix_with_none_values_fixture():
    """Matrix with None values for edge case testing."""
    return Matrix(
        assignments=[
            MatrixAssignment(rx="Living Room RX", tx="Apple TV"),
            MatrixAssignment(rx="Bedroom RX", tx=None),  # Unconnected receiver
            MatrixAssignment(rx=None, tx="Orphan TX"),  # Orphan transmitter
        ]
    )


@pytest.fixture
def matrix_with_empty_strings_fixture():
    """Matrix with empty strings for edge case testing."""
    return Matrix(
        assignments=[
            MatrixAssignment(rx="Living Room RX", tx="Apple TV"),
            MatrixAssignment(rx="Bedroom RX", tx=""),  # Empty transmitter
            MatrixAssignment(rx="", tx="Orphan TX"),  # Empty receiver
            MatrixAssignment(rx="Kitchen RX", tx="   "),  # Whitespace transmitter
        ]
    )


@pytest.fixture
def matrix_duplicate_receivers_fixture():
    """Matrix with duplicate receivers for testing override behavior."""
    return Matrix(
        assignments=[
            MatrixAssignment(rx="Living Room RX", tx="Apple TV"),
            MatrixAssignment(rx="Living Room RX", tx="Cable Box"),  # Override
        ]
    )


@pytest.fixture
def matrix_mixed_valid_invalid_fixture():
    """Matrix with mixed valid and invalid assignments for comprehensive testing."""
    return Matrix(
        assignments=[
            MatrixAssignment(rx="Valid RX 1", tx="Valid TX 1"),
            MatrixAssignment(rx="Valid RX 2", tx="Valid TX 2"),
            MatrixAssignment(rx="", tx="Invalid TX"),  # Empty receiver
            MatrixAssignment(rx="Invalid RX", tx=""),  # Empty transmitter
            MatrixAssignment(rx=None, tx="Invalid TX 2"),  # None receiver
            MatrixAssignment(rx="Invalid RX 2", tx=None),  # None transmitter
            MatrixAssignment(rx="Valid RX 3", tx="Valid TX 3"),
        ]
    )


@pytest.fixture
def partial_connection_matrix_fixture():
    """Matrix with partial device connections for integration testing."""
    return Matrix(
        assignments=[
            MatrixAssignment(rx="Living Room RX", tx="Apple TV")
            # Bedroom RX is not connected
        ]
    )


# =============================================================================
# MULTI-DEVICE SYSTEM FIXTURES
# =============================================================================
# Fixtures for integration testing scenarios with multiple devices


@pytest.fixture
def multi_device_system_json_fixtures():
    """Collection of DeviceJsonString objects for integration testing."""
    return [
        DeviceJsonString(
            aliasName="Living Room RX",
            deviceType="Receiver",
            group=[DeviceJsonStringGroup(name="ungrouped", sequence=1)],
            ip="192.168.1.101",
            online=True,
            sequence=1,
            trueName="RX-01",
        ),
        DeviceJsonString(
            aliasName="Bedroom RX",
            deviceType="Receiver",
            group=[DeviceJsonStringGroup(name="ungrouped", sequence=2)],
            ip="192.168.1.102",
            online=True,
            sequence=2,
            trueName="RX-02",
        ),
        DeviceJsonString(
            aliasName="Apple TV",
            deviceType="Transmitter",
            group=[DeviceJsonStringGroup(name="ungrouped", sequence=3)],
            ip="192.168.1.201",
            online=True,
            sequence=3,
            trueName="TX-01",
            nameoverlay=True,
        ),
    ]


@pytest.fixture
def multi_device_system_status_fixtures():
    """Collection of DeviceStatus objects for integration testing."""
    return [
        DeviceStatus(aliasname="Living Room RX", name="RX-01"),
        DeviceStatus(aliasname="Bedroom RX", name="RX-02"),
        DeviceStatus(aliasname="Apple TV", name="TX-01"),
    ]


@pytest.fixture
def multi_device_system_info_fixtures():
    """Collection of DeviceInfo objects for integration testing."""
    return [
        DeviceInfo(
            aliasname="Living Room RX",
            name="RX-01",
            ip4addr="192.168.1.101",
            mac="AA:BB:CC:DD:EE:01",
            gateway="192.168.1.1",
            netmask="255.255.255.0",
            version="1.0.0",
        ),
        DeviceInfo(
            aliasname="Bedroom RX",
            name="RX-02",
            ip4addr="192.168.1.102",
            mac="AA:BB:CC:DD:EE:02",
            gateway="192.168.1.1",
            netmask="255.255.255.0",
            version="1.0.0",
        ),
        DeviceInfo(
            aliasname="Apple TV",
            name="TX-01",
            ip4addr="192.168.1.201",
            mac="AA:BB:CC:DD:EE:03",
            gateway="192.168.1.1",
            netmask="255.255.255.0",
            version="1.0.0",
        ),
    ]


# =============================================================================
# UTILITY & EDGE CASE FIXTURES
# =============================================================================
# Fixtures for testing error conditions and boundary cases


@pytest.fixture
def device_json_incomplete_fixture():
    """DeviceJsonString for testing incomplete device scenarios."""
    return DeviceJsonString(
        aliasName="Incomplete Device",
        deviceType="Receiver",
        group=[DeviceJsonStringGroup(name="ungrouped", sequence=1)],
        ip="192.168.1.1",
        online=True,
        sequence=1,
        trueName="INCOMPLETE-RX-01",
    )


@pytest.fixture
def device_json_complete_fixture():
    """DeviceJsonString for testing complete device scenarios."""
    return DeviceJsonString(
        aliasName="Complete Device",
        deviceType="Receiver",
        group=[DeviceJsonStringGroup(name="ungrouped", sequence=1)],
        ip="192.168.1.1",
        online=True,
        sequence=1,
        trueName="COMPLETE-RX-01",
    )


@pytest.fixture
def device_status_complete_fixture():
    """DeviceStatus for testing complete device scenarios."""
    return DeviceStatus(
        aliasname="Complete Device",
        name="COMPLETE-RX-01",
    )


@pytest.fixture
def device_info_complete_fixture():
    """DeviceInfo for testing complete device scenarios."""
    return DeviceInfo(
        aliasname="Complete Device",
        name="COMPLETE-RX-01",
        ip4addr="192.168.1.1",
        mac="00:00:00:00:00:00",
        gateway="192.168.1.1",
        netmask="255.255.255.0",
        version="1.0.0",
    )


@pytest.fixture
def device_json_orphan_fixture():
    """DeviceJsonString for testing orphan device scenarios."""
    return DeviceJsonString(
        aliasName="Orphan Device",
        deviceType="Transmitter",
        group=[DeviceJsonStringGroup(name="ungrouped", sequence=2)],
        ip="192.168.1.2",
        online=True,
        sequence=2,
        trueName="ORPHAN-TX-01",
    )


@pytest.fixture
def device_json_invalid_type_fixture():
    """DeviceJsonString with invalid device type for testing error handling."""
    return DeviceJsonString(
        aliasName="Invalid Device",
        deviceType="InvalidType",  # Invalid device type
        group=[DeviceJsonStringGroup(name="ungrouped", sequence=1)],
        ip="192.168.1.1",
        online=True,
        sequence=1,
        trueName="INVALID-01",
    )


@pytest.fixture
def device_status_invalid_fixture():
    """DeviceStatus for invalid device testing."""
    return DeviceStatus(
        aliasname="Invalid Device",
        name="INVALID-01",
    )


@pytest.fixture
def device_info_invalid_fixture():
    """DeviceInfo for invalid device testing."""
    return DeviceInfo(
        aliasname="Invalid Device",
        name="INVALID-01",
        ip4addr="192.168.1.1",
        mac="00:00:00:00:00:00",
        gateway="192.168.1.1",
        netmask="255.255.255.0",
        version="1.0.0",
    )
