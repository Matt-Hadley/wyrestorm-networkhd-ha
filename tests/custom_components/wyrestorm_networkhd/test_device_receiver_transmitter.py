"""Unit tests for DeviceReceiver and DeviceTransmitter models."""

from custom_components.wyrestorm_networkhd.models.device_receiver_transmitter import (
    DeviceReceiver,
    DeviceTransmitter,
    create_device_from_wyrestorm_models,
)


class TestDeviceReceiver:
    """Tests for DeviceReceiver model."""

    def test_init_from_factory_method(
        self, device_json_receiver_fixture, device_status_receiver_fixture, device_info_receiver_fixture
    ):
        """Test initialization of DeviceReceiver using factory method."""
        receiver = create_device_from_wyrestorm_models(
            device_json_receiver_fixture, device_status_receiver_fixture, device_info_receiver_fixture
        )

        assert isinstance(receiver, DeviceReceiver)
        assert receiver.alias_name == "Living Room RX"
        assert receiver.device_type == "Receiver"
        assert receiver.tx_name == "Apple TV"
        assert receiver.hdmi_out_active is True
        assert receiver.manufacturer == "WyreStorm"
        assert receiver.model == "NHD-200-RX-01"

    def test_get_device_display_name(
        self, device_json_receiver_fixture, device_status_receiver_fixture, device_info_receiver_fixture
    ):
        """Test get_device_display_name method for receiver."""
        receiver = create_device_from_wyrestorm_models(
            device_json_receiver_fixture, device_status_receiver_fixture, device_info_receiver_fixture
        )

        assert receiver.get_device_display_name() == "Receiver - Living Room RX"

    def test_get_device_display_name_no_alias(
        self, device_json_receiver_fixture, device_status_receiver_fixture, device_info_receiver_fixture
    ):
        """Test get_device_display_name when alias is empty."""
        device_json_receiver_fixture.aliasName = ""
        receiver = create_device_from_wyrestorm_models(
            device_json_receiver_fixture, device_status_receiver_fixture, device_info_receiver_fixture
        )

        assert receiver.get_device_display_name() == "Receiver - 192.168.1.101"


class TestDeviceTransmitter:
    """Tests for DeviceTransmitter model."""

    def test_init_from_factory_method(
        self, device_json_transmitter_fixture, device_status_transmitter_fixture, device_info_transmitter_fixture
    ):
        """Test initialization of DeviceTransmitter using factory method."""
        transmitter = create_device_from_wyrestorm_models(
            device_json_transmitter_fixture, device_status_transmitter_fixture, device_info_transmitter_fixture
        )

        assert isinstance(transmitter, DeviceTransmitter)
        assert transmitter.alias_name == "Apple TV"
        assert transmitter.device_type == "Transmitter"
        assert transmitter.nameoverlay is True
        assert transmitter.hdmi_in_active is True
        assert transmitter.manufacturer == "WyreStorm"
        assert transmitter.model == "NHD-200-TX-01"

    def test_get_device_display_name(
        self, device_json_transmitter_fixture, device_status_transmitter_fixture, device_info_transmitter_fixture
    ):
        """Test get_device_display_name method for transmitter."""
        transmitter = create_device_from_wyrestorm_models(
            device_json_transmitter_fixture, device_status_transmitter_fixture, device_info_transmitter_fixture
        )

        assert transmitter.get_device_display_name() == "Transmitter - Apple TV"


class TestCreateDeviceFromWyrestormModels:
    """Tests for create_device_from_wyrestorm_models factory function."""

    def test_create_receiver(
        self, device_json_receiver_fixture, device_status_receiver_fixture, device_info_receiver_fixture
    ):
        """Test creating a DeviceReceiver from wyrestorm models."""
        device = create_device_from_wyrestorm_models(
            device_json_receiver_fixture, device_status_receiver_fixture, device_info_receiver_fixture
        )

        # Check it's the right type
        assert isinstance(device, DeviceReceiver)
        assert not isinstance(device, DeviceTransmitter)

        # Check base fields
        assert device.alias_name == "Living Room RX"
        assert device.true_name == "NHD-200-RX-01"
        assert device.device_type == "Receiver"
        assert device.ip == "192.168.1.101"
        assert device.online is True
        assert device.sequence == 1

        # Check DeviceInfo fields
        assert device.mac == "AA:BB:CC:DD:EE:01"
        assert device.gateway == "192.168.1.1"
        assert device.netmask == "255.255.255.0"
        assert device.version == "1.2.3"
        assert device.edid == "Custom EDID"
        assert device.ip_mode == "static"

        # Check common status fields
        assert device.line_out_audio_enable is True
        assert device.stream_frame_rate == 60
        assert device.stream_resolution == "1920x1080"

        # Check RX specific fields
        assert device.tx_name == "Apple TV"
        assert device.hdmi_out_active is True
        assert device.hdmi_out_resolution == "1920x1080"
        assert device.hdcp_status == "HDCP 2.2"
        assert device.sourcein == "192.168.1.102"
        assert device.video_mode == "Auto"

        # TX fields should not exist
        assert not hasattr(device, "nameoverlay")
        assert not hasattr(device, "hdmi_in_active")
        assert not hasattr(device, "video_stream_ip_address")

    def test_create_transmitter(
        self, device_json_transmitter_fixture, device_status_transmitter_fixture, device_info_transmitter_fixture
    ):
        """Test creating a DeviceTransmitter from wyrestorm models."""
        device = create_device_from_wyrestorm_models(
            device_json_transmitter_fixture, device_status_transmitter_fixture, device_info_transmitter_fixture
        )

        # Check it's the right type
        assert isinstance(device, DeviceTransmitter)
        assert not isinstance(device, DeviceReceiver)

        # Check base fields
        assert device.alias_name == "Apple TV"
        assert device.true_name == "NHD-200-TX-01"
        assert device.device_type == "Transmitter"
        assert device.ip == "192.168.1.102"
        assert device.online is True
        assert device.sequence == 2

        # Check DeviceInfo fields
        assert device.mac == "AA:BB:CC:DD:EE:02"
        assert device.gateway == "192.168.1.1"
        assert device.netmask == "255.255.255.0"
        assert device.version == "1.2.3"
        assert device.edid == "Default EDID"
        assert device.ip_mode == "dhcp"

        # Check common status fields
        assert device.line_out_audio_enable is False
        assert device.stream_frame_rate == 60
        assert device.stream_resolution == "1920x1080"

        # Check TX specific fields
        assert device.nameoverlay is True
        assert device.hdmi_in_active is True
        assert device.resolution == "1920x1080"
        assert device.video_stream_ip_address == "239.0.0.1"
        assert device.audio_stream_ip_address == "239.0.0.2"
        assert device.color_space == "YUV444"
        assert device.video_source == "HDMI"

        # RX fields should not exist
        assert not hasattr(device, "tx_name")
        assert not hasattr(device, "hdmi_out_active")
        assert not hasattr(device, "sourcein")

    def test_handle_none_values(
        self, device_json_receiver_fixture, device_status_receiver_fixture, device_info_receiver_fixture
    ):
        """Test that None values are properly handled."""
        # Set some fields to None
        device_info_receiver_fixture.edid = None
        device_info_receiver_fixture.version = None
        device_status_receiver_fixture.line_out_audio_enable = None

        device = create_device_from_wyrestorm_models(
            device_json_receiver_fixture, device_status_receiver_fixture, device_info_receiver_fixture
        )

        # None values should be preserved
        assert device.edid is None
        assert device.version is None
        assert device.line_out_audio_enable is None

        # Other fields should still work
        assert device.alias_name == "Living Room RX"
        assert device.mac == "AA:BB:CC:DD:EE:01"
