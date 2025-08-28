"""Test entity utilities for WyreStorm NetworkHD integration."""

import logging
from unittest.mock import Mock, patch

from custom_components.wyrestorm_networkhd._entity_utils import (
    EntityConfigMixin,
    check_availability,
    log_device_setup,
    validate_device_for_setup,
)


class TestCheckAvailability:
    """Test check_availability function."""

    def test_coordinator_not_ready(self):
        """Test with coordinator not ready."""
        coordinator = Mock()
        coordinator.is_ready.return_value = False
        coordinator.has_errors.return_value = False

        result = check_availability(coordinator)
        assert result is False

    def test_coordinator_has_errors(self):
        """Test with coordinator having errors."""
        coordinator = Mock()
        coordinator.is_ready.return_value = True
        coordinator.has_errors.return_value = True

        result = check_availability(coordinator)
        assert result is False

    def test_controller_level_entity(self):
        """Test controller-level entity availability."""
        coordinator = Mock()
        coordinator.is_ready.return_value = True
        coordinator.has_errors.return_value = False

        result = check_availability(coordinator, device_id=None)
        assert result is True

    def test_device_specific_no_data(self):
        """Test device-specific entity with no coordinator data."""
        coordinator = Mock()
        coordinator.is_ready.return_value = True
        coordinator.has_errors.return_value = False
        coordinator.data = None

        result = check_availability(coordinator, device_id="test_device")
        assert result is False

    def test_device_specific_device_not_found(self):
        """Test device-specific entity with device not found."""
        coordinator = Mock()
        coordinator.is_ready.return_value = True
        coordinator.has_errors.return_value = False
        coordinator.data = {"devices": {}}

        result = check_availability(coordinator, device_id="test_device")
        assert result is False

    def test_device_specific_device_offline(self):
        """Test device-specific entity with device offline."""
        coordinator = Mock()
        coordinator.is_ready.return_value = True
        coordinator.has_errors.return_value = False
        coordinator.data = {"devices": {"test_device": {"online": False}}}

        result = check_availability(coordinator, device_id="test_device")
        assert result is False

    def test_device_specific_device_online(self):
        """Test device-specific entity with device online."""
        coordinator = Mock()
        coordinator.is_ready.return_value = True
        coordinator.has_errors.return_value = False
        coordinator.data = {"devices": {"test_device": {"online": True}}}

        result = check_availability(coordinator, device_id="test_device")
        assert result is True

    def test_device_specific_no_online_status(self):
        """Test device-specific entity with no online status."""
        coordinator = Mock()
        coordinator.is_ready.return_value = True
        coordinator.has_errors.return_value = False
        coordinator.data = {"devices": {"test_device": {}}}

        result = check_availability(coordinator, device_id="test_device")
        assert result is False


class TestLogDeviceSetup:
    """Test log_device_setup function."""

    @patch("custom_components.wyrestorm_networkhd._entity_utils._LOGGER")
    def test_log_device_setup(self, mock_logger):  # noqa: ARG002
        """Test device setup logging."""
        logger = Mock(spec=logging.Logger)
        device_type = "binary sensors"
        devices_data = {"device1": {}, "device2": {}}

        log_device_setup(logger, device_type, devices_data)

        logger.info.assert_any_call("Setting up WyreStorm NetworkHD %s...", device_type)
        logger.info.assert_any_call("Found %d devices for %s", 2, device_type)


class TestValidateDeviceForSetup:
    """Test validate_device_for_setup function."""

    def test_coordinator_not_ready(self):
        """Test with coordinator not ready."""
        coordinator = Mock()
        coordinator.is_ready.return_value = False
        logger = Mock(spec=logging.Logger)

        result = validate_device_for_setup(coordinator, logger, "test_entity")

        assert result is None
        logger.warning.assert_called_once_with("Coordinator not ready, skipping %s setup", "test_entity")

    def test_coordinator_has_errors(self):
        """Test with coordinator having errors."""
        coordinator = Mock()
        coordinator.is_ready.return_value = True
        coordinator.has_errors.return_value = True
        logger = Mock(spec=logging.Logger)

        result = validate_device_for_setup(coordinator, logger, "test_entity")

        assert result is None
        logger.warning.assert_called_once_with("Coordinator has errors, skipping %s setup", "test_entity")

    def test_no_devices_data(self):
        """Test with no devices data."""
        coordinator = Mock()
        coordinator.is_ready.return_value = True
        coordinator.has_errors.return_value = False
        coordinator.data = {"devices": {}}
        logger = Mock(spec=logging.Logger)

        result = validate_device_for_setup(coordinator, logger, "test_entity")

        assert result is None
        logger.warning.assert_called_once_with("No devices data available for %s setup", "test_entity")

    def test_valid_setup(self):
        """Test with valid setup conditions."""
        devices_data = {"device1": {}, "device2": {}}
        coordinator = Mock()
        coordinator.is_ready.return_value = True
        coordinator.has_errors.return_value = False
        coordinator.data = {"devices": devices_data}
        logger = Mock(spec=logging.Logger)

        result = validate_device_for_setup(coordinator, logger, "test_entity")

        assert result == devices_data
        logger.warning.assert_not_called()


class TestEntityConfigMixin:
    """Test EntityConfigMixin class."""

    def test_basic_entity_config(self):
        """Test basic entity configuration."""

        class TestEntity(EntityConfigMixin):
            pass

        entity = TestEntity()
        coordinator = Mock()
        coordinator.host = "192.168.1.10"

        entity._set_entity_config(coordinator, "test_device", "online", "Test Sensor")

        assert entity._attr_unique_id == "192.168.1.10_test_device_online"
        assert entity._attr_name == "Test Sensor"

    def test_entity_config_with_icon(self):
        """Test entity configuration with icon."""

        class TestEntity(EntityConfigMixin):
            pass

        entity = TestEntity()
        coordinator = Mock()
        coordinator.host = "192.168.1.10"

        entity._set_entity_config(coordinator, "test_device", "online", "Test Sensor", icon="mdi:test-icon")

        assert entity._attr_icon == "mdi:test-icon"

    def test_entity_config_with_category(self):
        """Test entity configuration with entity category."""
        from homeassistant.helpers.entity import EntityCategory

        class TestEntity(EntityConfigMixin):
            pass

        entity = TestEntity()
        coordinator = Mock()
        coordinator.host = "192.168.1.10"

        entity._set_entity_config(
            coordinator,
            "test_device",
            "online",
            "Test Sensor",
            entity_category=EntityCategory.DIAGNOSTIC,
        )

        assert entity._attr_entity_category == EntityCategory.DIAGNOSTIC

    def test_entity_config_complete(self):
        """Test complete entity configuration."""
        from homeassistant.helpers.entity import EntityCategory

        class TestEntity(EntityConfigMixin):
            pass

        entity = TestEntity()
        coordinator = Mock()
        coordinator.host = "test.local"

        entity._set_entity_config(
            coordinator,
            "my_device",
            "video_input",
            "Video Input Status",
            icon="mdi:video",
            entity_category=EntityCategory.DIAGNOSTIC,
        )

        assert entity._attr_unique_id == "test.local_my_device_video_input"
        assert entity._attr_name == "Video Input Status"
        assert entity._attr_icon == "mdi:video"
        assert entity._attr_entity_category == EntityCategory.DIAGNOSTIC
