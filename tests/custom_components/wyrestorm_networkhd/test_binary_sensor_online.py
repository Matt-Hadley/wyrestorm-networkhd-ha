"""Test WyreStormOnlineSensor for WyreStorm NetworkHD integration."""

import pytest
from homeassistant.helpers.entity import EntityCategory

from custom_components.wyrestorm_networkhd.binary_sensor import WyreStormOnlineSensor
from custom_components.wyrestorm_networkhd.const import DOMAIN
from tests.helpers.base import BinarySensorTestBase


class TestWyreStormOnlineSensor(BinarySensorTestBase):
    """Test WyreStormOnlineSensor class."""

    @pytest.fixture
    def online_sensor(self, mock_binary_sensor_coordinator):
        """Create an online sensor."""
        device_data = mock_binary_sensor_coordinator.data["devices"]["encoder1"]
        return WyreStormOnlineSensor(mock_binary_sensor_coordinator, "encoder1", device_data)

    def test_init(self, online_sensor, mock_binary_sensor_coordinator):
        """Test sensor initialization."""
        self.assert_basic_entity_properties(
            online_sensor,
            expected_name="Controller Link",
            expected_unique_id="192.168.1.10_encoder1_online",
            expected_icon="mdi:ethernet",
            expected_category=EntityCategory.DIAGNOSTIC,
        )
        self.assert_coordinator_dependency(online_sensor, mock_binary_sensor_coordinator)

    def test_is_on_device_online(self, online_sensor):
        """Test is_on when device is online."""
        self.assert_sensor_state(online_sensor, expected_state=True)

    def test_is_on_device_offline(self, online_sensor, mock_binary_sensor_coordinator):
        """Test is_on when device is offline."""
        coordinator_data = {"devices": {"encoder1": {"online": False}}}
        self.assert_sensor_state(online_sensor, expected_state=False, coordinator_data=coordinator_data)

    def test_is_on_no_coordinator_data(self, online_sensor, mock_binary_sensor_coordinator):
        """Test is_on when coordinator has no data."""
        mock_binary_sensor_coordinator.data = None
        assert online_sensor.is_on is None

    def test_device_info(self, online_sensor):
        """Test device info generation."""
        device_info = online_sensor.device_info

        self.assert_device_info_properties(
            device_info,
            expected_identifiers={(DOMAIN, "192.168.1.10_encoder1")},
            expected_name="Encoder - encoder1",
            expected_model="NHD-TX",
        )

    def test_extra_state_attributes(self, online_sensor):
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
        self.assert_sensor_attributes(online_sensor, expected_attrs)

    def test_extra_state_attributes_no_data(self, online_sensor, mock_binary_sensor_coordinator):
        """Test extra state attributes when no coordinator data."""
        mock_binary_sensor_coordinator.data = None
        attrs = online_sensor.extra_state_attributes
        assert attrs == {}

    def test_available_device_online(self, online_sensor):
        """Test availability when device is online."""
        self.assert_availability_device_online(online_sensor, online_sensor.coordinator, "encoder1")

    def test_available_device_offline(self, online_sensor):
        """Test availability when device is offline."""
        self.assert_availability_device_offline(online_sensor, online_sensor.coordinator, "encoder1")

    def test_available_device_not_found(self, online_sensor):
        """Test availability when device not found."""
        self.assert_availability_device_not_found(online_sensor, online_sensor.coordinator)

    def test_available_coordinator_not_ready(self, online_sensor):
        """Test availability when coordinator not ready."""
        self.assert_availability_coordinator_not_ready(online_sensor, online_sensor.coordinator)

    def test_available_coordinator_has_errors(self, online_sensor):
        """Test availability when coordinator has errors."""
        self.assert_availability_coordinator_has_errors(online_sensor, online_sensor.coordinator)
