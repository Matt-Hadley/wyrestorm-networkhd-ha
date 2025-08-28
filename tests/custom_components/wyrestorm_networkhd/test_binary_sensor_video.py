"""Test WyreStorm video binary sensors for WyreStorm NetworkHD integration."""

import pytest
from homeassistant.helpers.entity import EntityCategory

from custom_components.wyrestorm_networkhd.binary_sensor import (
    WyreStormVideoInputSensor,
    WyreStormVideoOutputSensor,
)
from custom_components.wyrestorm_networkhd.const import DOMAIN
from tests.helpers.base import BinarySensorTestBase


class TestWyreStormVideoInputSensor(BinarySensorTestBase):
    """Test WyreStormVideoInputSensor class."""

    @pytest.fixture
    def video_input_sensor(self, mock_binary_sensor_coordinator):
        """Create a video input sensor."""
        device_data = mock_binary_sensor_coordinator.data["devices"]["encoder1"]
        return WyreStormVideoInputSensor(mock_binary_sensor_coordinator, "encoder1", device_data)

    def test_init(self, video_input_sensor, mock_binary_sensor_coordinator):
        """Test sensor initialization."""
        self.assert_basic_entity_properties(
            video_input_sensor,
            expected_name="Video Input",
            expected_unique_id="192.168.1.10_encoder1_video_input",
            expected_icon="mdi:arrow-left",
            expected_category=EntityCategory.DIAGNOSTIC,
        )
        self.assert_coordinator_dependency(video_input_sensor, mock_binary_sensor_coordinator)

    def test_is_on_hdmi_active(self, video_input_sensor):
        """Test is_on when HDMI input is active."""
        self.assert_sensor_state(video_input_sensor, expected_state=True)

    def test_is_on_hdmi_inactive(self, video_input_sensor, mock_binary_sensor_coordinator):
        """Test is_on when HDMI input is inactive."""
        coordinator_data = {"devices": {"encoder1": {"hdmi_in_active": False}}}
        self.assert_sensor_state(video_input_sensor, expected_state=False, coordinator_data=coordinator_data)

    def test_is_on_no_hdmi_data(self, video_input_sensor, mock_binary_sensor_coordinator):
        """Test is_on when no HDMI input data."""
        coordinator_data = {
            "devices": {
                "encoder1": {}  # No hdmi_in_active key
            }
        }
        # Should return False when device data exists but hdmi_in_active is missing
        self.assert_sensor_state(video_input_sensor, expected_state=False, coordinator_data=coordinator_data)

    def test_is_on_no_coordinator_data(self, video_input_sensor, mock_binary_sensor_coordinator):
        """Test is_on when coordinator has no data."""
        mock_binary_sensor_coordinator.data = None
        mock_binary_sensor_coordinator.is_ready.return_value = False
        assert video_input_sensor.is_on is None

    def test_device_info(self, video_input_sensor):
        """Test device info generation."""
        device_info = video_input_sensor.device_info

        self.assert_device_info_properties(
            device_info,
            expected_identifiers={(DOMAIN, "192.168.1.10_encoder1")},
            expected_name="Encoder - encoder1",
            expected_model="NHD-TX",
        )

    def test_extra_state_attributes(self, video_input_sensor):
        """Test extra state attributes."""
        expected_attrs = {
            "device_id": "encoder1",
            "device_type": "encoder",
            "model": "NHD-TX",
            "online": True,
            "hdmi_in_active": True,
            "resolution": "1080p",
            "ip_address": "192.168.1.100",
        }
        self.assert_sensor_attributes(video_input_sensor, expected_attrs)

    def test_available_device_online(self, video_input_sensor):
        """Test availability when device is online."""
        self.assert_availability_device_online(video_input_sensor, video_input_sensor.coordinator, "encoder1")

    def test_available_device_offline(self, video_input_sensor):
        """Test availability when device is offline."""
        self.assert_availability_device_offline(video_input_sensor, video_input_sensor.coordinator, "encoder1")

    def test_available_device_not_found(self, video_input_sensor):
        """Test availability when device not found."""
        self.assert_availability_device_not_found(video_input_sensor, video_input_sensor.coordinator)


class TestWyreStormVideoOutputSensor(BinarySensorTestBase):
    """Test WyreStormVideoOutputSensor class."""

    @pytest.fixture
    def video_output_sensor(self, mock_binary_sensor_coordinator):
        """Create a video output sensor."""
        device_data = mock_binary_sensor_coordinator.data["devices"]["decoder1"]
        return WyreStormVideoOutputSensor(mock_binary_sensor_coordinator, "decoder1", device_data)

    def test_init(self, video_output_sensor, mock_binary_sensor_coordinator):
        """Test sensor initialization."""
        self.assert_basic_entity_properties(
            video_output_sensor,
            expected_name="Video Output",
            expected_unique_id="192.168.1.10_decoder1_video_output",
            expected_icon="mdi:arrow-right",
            expected_category=EntityCategory.DIAGNOSTIC,
        )
        self.assert_coordinator_dependency(video_output_sensor, mock_binary_sensor_coordinator)

    def test_is_on_hdmi_active(self, video_output_sensor):
        """Test is_on when HDMI output is active."""
        self.assert_sensor_state(video_output_sensor, expected_state=True)

    def test_is_on_hdmi_inactive(self, video_output_sensor, mock_binary_sensor_coordinator):
        """Test is_on when HDMI output is inactive."""
        coordinator_data = {"devices": {"decoder1": {"hdmi_out_active": False}}}
        self.assert_sensor_state(video_output_sensor, expected_state=False, coordinator_data=coordinator_data)

    def test_is_on_no_hdmi_data(self, video_output_sensor, mock_binary_sensor_coordinator):
        """Test is_on when no HDMI output data."""
        coordinator_data = {
            "devices": {
                "decoder1": {}  # No hdmi_out_active key
            }
        }
        # Should return False when device data exists but hdmi_out_active is missing
        self.assert_sensor_state(video_output_sensor, expected_state=False, coordinator_data=coordinator_data)

    def test_device_info(self, video_output_sensor):
        """Test device info generation."""
        device_info = video_output_sensor.device_info

        self.assert_device_info_properties(
            device_info,
            expected_identifiers={(DOMAIN, "192.168.1.10_decoder1")},
            expected_name="Decoder - decoder1",
            expected_model="NHD-RX",
        )

    def test_extra_state_attributes(self, video_output_sensor):
        """Test extra state attributes."""
        expected_attrs = {
            "device_id": "decoder1",
            "device_type": "decoder",
            "model": "NHD-RX",
            "online": True,
            "hdmi_out_active": True,
            "hdmi_out_resolution": "1080p",
            "ip_address": "192.168.1.101",
        }
        self.assert_sensor_attributes(video_output_sensor, expected_attrs)
