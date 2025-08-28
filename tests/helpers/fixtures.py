"""Essential test fixtures for WyreStorm NetworkHD tests."""

from unittest.mock import AsyncMock, Mock

import pytest

from tests.helpers.builders import MockSetup, TestDataBuilder


@pytest.fixture
def mock_coordinator_factory():
    """Factory for creating mock coordinators with consistent interface."""

    def _create_coordinator(**kwargs):
        return MockSetup.create_mock_coordinator(**kwargs)

    return _create_coordinator


@pytest.fixture
def mock_coordinator():
    """Standard mock coordinator with comprehensive test data."""
    coordinator = Mock()
    coordinator.host = "192.168.1.10"
    coordinator.is_ready.return_value = True
    coordinator.has_errors.return_value = False

    # Standard test data using TestDataBuilder
    coordinator.data = TestDataBuilder.create_coordinator_data(num_encoders=2, num_decoders=2, num_controllers=1)

    # Mock API methods commonly used in tests
    coordinator.api = Mock()
    coordinator.api.reboot_reset = Mock()
    coordinator.api.reboot_reset.set_reboot = AsyncMock()
    coordinator.api.command_decoder = Mock()
    coordinator.api.command_decoder.set_sink_power_on = AsyncMock()
    coordinator.api.command_decoder.set_sink_power_off = AsyncMock()
    coordinator.api.command_decoder.set_input = AsyncMock()

    # Add get_all_devices method for select platform
    def get_all_devices():
        return coordinator.data.get("devices", {})

    coordinator.get_all_devices.return_value = get_all_devices()

    return coordinator


@pytest.fixture
def mock_binary_sensor_coordinator():
    """Mock coordinator specifically for binary sensor tests."""
    coordinator = Mock()
    coordinator.host = "192.168.1.10"
    coordinator.is_ready.return_value = True
    coordinator.has_errors.return_value = False

    # Create encoder with binary sensor specific properties
    encoder_data = TestDataBuilder.create_device_data(
        device_id="encoder1",
        device_type="encoder",
        model="NHD-TX",
        online=True,
        ip_address="192.168.1.100",
        hdmi_in_active=True,
        resolution="1080p",
    )

    # Create decoder with binary sensor specific properties
    decoder_data = TestDataBuilder.create_device_data(
        device_id="decoder1",
        device_type="decoder",
        model="NHD-RX",
        online=True,
        ip_address="192.168.1.101",
        hdmi_out_active=True,
        hdmi_out_resolution="1080p",
    )

    coordinator.data = {
        "devices": {
            "encoder1": encoder_data,
            "decoder1": decoder_data,
        }
    }
    return coordinator


@pytest.fixture
def mock_button_coordinator():
    """Mock coordinator specifically for button tests."""
    coordinator = Mock()
    coordinator.host = "192.168.1.10"
    coordinator.is_ready.return_value = True
    coordinator.has_errors.return_value = False

    # Use TestDataBuilder for consistent device creation
    devices = {
        "decoder1": TestDataBuilder.create_device_data(
            device_id="decoder1", device_type="decoder", model="NHD-RX", online=True, ip_address="192.168.1.101"
        ),
        "decoder2": TestDataBuilder.create_device_data(
            device_id="decoder2", device_type="decoder", model="NHD-RX2", online=False, ip_address="192.168.1.102"
        ),
        "encoder1": TestDataBuilder.create_device_data(
            device_id="encoder1", device_type="encoder", model="NHD-TX", online=True, ip_address="192.168.1.100"
        ),
    }
    coordinator.data = {"devices": devices}

    # Mock API methods
    coordinator.api = Mock()
    coordinator.api.reboot_reset = Mock()
    coordinator.api.reboot_reset.set_reboot = AsyncMock()
    coordinator.api.command_decoder = Mock()
    coordinator.api.command_decoder.set_sink_power_on = AsyncMock()
    coordinator.api.command_decoder.set_sink_power_off = AsyncMock()

    return coordinator


@pytest.fixture
def mock_select_coordinator():
    """Mock coordinator specifically for select tests."""
    coordinator = Mock()
    coordinator.host = "192.168.1.10"
    coordinator.is_ready.return_value = True
    coordinator.has_errors.return_value = False

    # Use TestDataBuilder for consistent device creation
    devices_data = {
        "encoder1": TestDataBuilder.create_device_data(
            device_id="encoder1", device_type="encoder", model="NHD-TX", online=True, ip_address="192.168.1.100"
        ),
        "encoder2": TestDataBuilder.create_device_data(
            device_id="encoder2", device_type="encoder", model="NHD-TX2", online=True, ip_address="192.168.1.110"
        ),
        "decoder1": TestDataBuilder.create_device_data(
            device_id="decoder1",
            device_type="decoder",
            model="NHD-RX",
            online=True,
            ip_address="192.168.1.101",
            current_source="encoder1",
        ),
        "decoder2": TestDataBuilder.create_device_data(
            device_id="decoder2",
            device_type="decoder",
            model="NHD-RX2",
            online=False,
            ip_address="192.168.1.102",
            current_source=None,
        ),
    }

    coordinator.data = {"devices": devices_data}
    coordinator.get_all_devices.return_value = devices_data

    # Mock API
    coordinator.api = Mock()
    coordinator.api.command_decoder = Mock()
    coordinator.api.command_decoder.set_input = AsyncMock()

    return coordinator


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    return MockSetup.create_mock_hass()


@pytest.fixture
def mock_config_entry():
    """Mock config entry."""
    return MockSetup.create_mock_config_entry()


@pytest.fixture
def mock_add_entities():
    """Mock add_entities callback."""
    return Mock()


@pytest.fixture
def sample_device_data():
    """Sample device data for basic testing."""
    return TestDataBuilder.create_device_data(device_id="test_device", device_type="encoder", online=True)


@pytest.fixture
def sample_coordinator_data():
    """Sample coordinator data for basic testing."""
    return TestDataBuilder.create_coordinator_data(num_encoders=1, num_decoders=1, num_controllers=1)
