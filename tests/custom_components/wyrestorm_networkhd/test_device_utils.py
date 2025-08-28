"""Test device utilities for WyreStorm NetworkHD integration."""

from custom_components.wyrestorm_networkhd._device_utils import (
    create_device_info,
    extract_firmware_version,
    get_device_attributes,
    get_device_display_name,
)


class TestGetDeviceDisplayName:
    """Test get_device_display_name function."""

    def test_with_device_id(self):
        """Test with valid device ID."""
        device_id = "office_encoder"
        device_info = {"type": "encoder"}
        device_data = {"ip_address": "192.168.1.100"}

        result = get_device_display_name(device_id, device_info, device_data)
        assert result == "Encoder - office_encoder"

    def test_with_ip_fallback(self):
        """Test fallback to IP address when device_id is unknown."""
        device_id = "unknown"
        device_info = {"type": "decoder"}
        device_data = {"ip_address": "192.168.1.101"}

        result = get_device_display_name(device_id, device_info, device_data)
        assert result == "Decoder - 192.168.1.101"

    def test_with_empty_device_id(self):
        """Test fallback to IP address when device_id is empty."""
        device_id = ""
        device_info = {"type": "encoder"}
        device_data = {"ip_address": "192.168.1.102"}

        result = get_device_display_name(device_id, device_info, device_data)
        assert result == "Encoder - 192.168.1.102"

    def test_with_unknown_fallback(self):
        """Test fallback to 'Unknown' when both device_id and IP are unavailable."""
        device_id = "unknown"
        device_info = {"type": "device"}
        device_data = {}

        result = get_device_display_name(device_id, device_info, device_data)
        assert result == "Device - Unknown"

    def test_with_missing_type(self):
        """Test with missing device type."""
        device_id = "test_device"
        device_info = {}
        device_data = {}

        result = get_device_display_name(device_id, device_info, device_data)
        assert result == "Device - test_device"


class TestCreateDeviceInfo:
    """Test create_device_info function."""

    def test_controller_device(self):
        """Test creating controller device info."""
        host = "192.168.1.10"

        result = create_device_info(host, "", {}, {}, is_controller=True)

        assert result["identifiers"] == {("wyrestorm_networkhd", host)}
        assert result["name"] == "Controller - 192.168.1.10"
        assert result["manufacturer"] == "WyreStorm"
        assert result["model"] == "NetworkHD Controller"
        assert result["via_device"] is None

    def test_encoder_device(self):
        """Test creating encoder device info."""
        host = "192.168.1.10"
        device_id = "encoder1"
        device_info = {"type": "encoder", "model": "NHD-TX"}
        device_data = {"ip_address": "192.168.1.100"}

        result = create_device_info(host, device_id, device_info, device_data)

        assert result["identifiers"] == {("wyrestorm_networkhd", f"{host}_{device_id}")}
        assert result["name"] == "Encoder - encoder1"
        assert result["manufacturer"] == "WyreStorm"
        assert result["model"] == "NHD-TX"
        assert result["via_device"] == ("wyrestorm_networkhd", host)

    def test_decoder_device_with_ip_fallback(self):
        """Test creating decoder device info with IP fallback."""
        host = "192.168.1.10"
        device_id = "unknown"
        device_info = {"type": "decoder"}
        device_data = {"ip_address": "192.168.1.101"}

        result = create_device_info(host, device_id, device_info, device_data)

        assert result["name"] == "Decoder - 192.168.1.101"
        assert result["model"] == "NetworkHD Decoder"

    def test_device_with_no_data(self):
        """Test creating device info with minimal data."""
        host = "192.168.1.10"
        device_id = "test_device"
        device_info = {"type": "device"}

        result = create_device_info(host, device_id, device_info)

        assert result["name"] == "Device - test_device"
        assert result["model"] == "NetworkHD Device"


class TestGetDeviceAttributes:
    """Test get_device_attributes function."""

    def test_basic_attributes(self):
        """Test basic attribute extraction."""
        device_id = "test_device"
        device_type = "encoder"
        device_data = {
            "online": True,
            "ip_address": "192.168.1.100",
            "resolution": "1080p",
            "name": "Test Device",  # Should be excluded
            "type": "encoder",  # Should be excluded
        }

        result = get_device_attributes(device_id, device_type, device_data)

        assert result["device_id"] == device_id
        assert result["device_type"] == device_type
        assert result["online"] is True
        assert result["ip_address"] == "192.168.1.100"
        assert result["resolution"] == "1080p"
        assert "name" not in result
        assert "type" not in result

    def test_with_none_values(self):
        """Test attribute extraction with None values."""
        device_id = "test_device"
        device_type = "decoder"
        device_data = {
            "online": True,
            "resolution": None,  # Should be excluded
            "power_state": "on",
        }

        result = get_device_attributes(device_id, device_type, device_data)

        assert "resolution" not in result
        assert result["power_state"] == "on"

    def test_empty_device_data(self):
        """Test with empty device data."""
        device_id = "test_device"
        device_type = "encoder"
        device_data = {}

        result = get_device_attributes(device_id, device_type, device_data)

        assert result["device_id"] == device_id
        assert result["device_type"] == device_type
        assert len(result) == 2


class TestExtractFirmwareVersion:
    """Test extract_firmware_version function."""

    def test_with_core_version_attribute(self):
        """Test with object having core_version attribute."""

        class MockVersion:
            def __init__(self):
                self.core_version = "1.2.3"

        version_info = MockVersion()
        result = extract_firmware_version(version_info)
        assert result == "1.2.3"

    def test_with_web_version_fallback(self):
        """Test fallback to web_version."""

        class MockVersion:
            def __init__(self):
                self.web_version = "1.2.4"

        version_info = MockVersion()
        result = extract_firmware_version(version_info)
        assert result == "1.2.4"

    def test_with_dict_core_version(self):
        """Test with dictionary containing core_version."""
        version_info = {"core_version": "2.0.0"}
        result = extract_firmware_version(version_info)
        assert result == "2.0.0"

    def test_with_dict_version_fallback(self):
        """Test with dictionary containing version key."""
        version_info = {"version": "2.1.0"}
        result = extract_firmware_version(version_info)
        assert result == "2.1.0"

    def test_with_dict_firmware_fallback(self):
        """Test with dictionary containing firmware key."""
        version_info = {"firmware": "2.2.0"}
        result = extract_firmware_version(version_info)
        assert result == "2.2.0"

    def test_with_string_version(self):
        """Test with string version."""
        version_info = "3.0.0"
        result = extract_firmware_version(version_info)
        assert result == "3.0.0"

    def test_with_unknown_format(self):
        """Test with unknown format returns Unknown."""
        version_info = 123
        result = extract_firmware_version(version_info)
        assert result == "Unknown"

    def test_with_empty_dict(self):
        """Test with empty dictionary."""
        version_info = {}
        result = extract_firmware_version(version_info)
        assert result == "Unknown"

    def test_with_none(self):
        """Test with None value."""
        version_info = None
        result = extract_firmware_version(version_info)
        assert result == "Unknown"
