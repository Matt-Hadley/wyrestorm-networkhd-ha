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

    # Mock API methods commonly used in tests for wyrestorm-networkhd v2.0.0
    coordinator.api = Mock()
    coordinator.api.reboot_reset = Mock()
    coordinator.api.reboot_reset.set_reboot = AsyncMock()
    coordinator.api.connected_device_control = Mock()
    coordinator.api.connected_device_control.config_set_device_sinkpower = AsyncMock()
    coordinator.api.media_stream_matrix_switch = Mock()
    coordinator.api.media_stream_matrix_switch.matrix_set = AsyncMock()
    coordinator.api.media_stream_matrix_switch.matrix_set_null = AsyncMock()
    coordinator.async_request_refresh = AsyncMock()

    # Add get_all_devices method for select platform
    def get_all_devices():
        return coordinator.data.get("devices", {})

    coordinator.get_all_devices.return_value = get_all_devices()

    return coordinator


@pytest.fixture
def mock_binary_sensor_coordinator():
    """Mock coordinator specifically for binary sensor tests."""
    from custom_components.wyrestorm_networkhd.coordinator import CoordinatorData, DeviceCollection, MergedDeviceData
    from tests.helpers.mocks import MockDeviceInfo, MockDeviceJsonString, MockDeviceStatus

    coordinator = Mock()
    coordinator.host = "192.168.1.10"
    coordinator.is_ready.return_value = True
    coordinator.has_errors.return_value = False

    # Create mock device objects for new structure
    encoder_device_json = MockDeviceJsonString(
        trueName="encoder1",
        deviceType="transmitter",
        online=True,
        resolution="1080p",
        device_id="encoder1",
        device_type="encoder",
    )
    encoder_device_status = MockDeviceStatus(name="encoder1", hdmi_in_active=True, ip_address="192.168.1.100")
    encoder_device_info = MockDeviceInfo(name="encoder1", model="NHD-TX", ip_address="192.168.1.100")

    decoder_device_json = MockDeviceJsonString(
        trueName="decoder1", deviceType="receiver", online=True, device_id="decoder1", device_type="decoder"
    )
    decoder_device_status = MockDeviceStatus(
        name="decoder1", hdmi_out_active=True, hdmi_out_resolution="1080p", ip_address="192.168.1.101"
    )
    decoder_device_info = MockDeviceInfo(name="decoder1", model="NHD-RX", ip_address="192.168.1.101")

    # Create device collection with new structure
    devices = DeviceCollection()

    encoder_device = MergedDeviceData("encoder1", encoder_device_info, encoder_device_json, encoder_device_status)
    encoder_device.online = True
    encoder_device.hdmi_in_active = True

    decoder_device = MergedDeviceData("decoder1", decoder_device_info, decoder_device_json, decoder_device_status)
    decoder_device.online = True
    decoder_device.hdmi_out_active = True

    devices.add_device(encoder_device)
    devices.add_device(decoder_device)

    # Create new coordinator data structure
    coordinator.data = CoordinatorData(
        devices=devices,
        matrix={},
        device_status=[decoder_device_status, encoder_device_status],
        device_info=[decoder_device_info, encoder_device_info],
    )

    # Add methods for new interface
    coordinator.get_device_info = Mock(side_effect=lambda device_id: devices.get_device(device_id))
    coordinator.get_all_devices = Mock(return_value=devices)

    # For backward compatibility with tests that access coordinator.data["devices"]["encoder1"] directly
    # Create a dict-like access that returns the legacy data format
    legacy_devices = {
        "encoder1": TestDataBuilder.create_device_data(
            device_id="encoder1",
            device_type="encoder",
            model="NHD-TX",
            online=True,
            ip_address="192.168.1.100",
            hdmi_in_active=True,
            resolution="1080p",
        ),
        "decoder1": TestDataBuilder.create_device_data(
            device_id="decoder1",
            device_type="decoder",
            model="NHD-RX",
            online=True,
            ip_address="192.168.1.101",
            hdmi_out_active=True,
            hdmi_out_resolution="1080p",
        ),
    }

    # Add a fake devices dict for backward compatibility
    coordinator.data.devices_dict = legacy_devices

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

    # Mock API methods for wyrestorm-networkhd v2.0.0
    coordinator.api = Mock()
    coordinator.api.reboot_reset = Mock()
    coordinator.api.reboot_reset.set_reboot = AsyncMock()
    coordinator.api.connected_device_control = Mock()
    coordinator.api.connected_device_control.config_set_device_sinkpower = AsyncMock()
    coordinator.async_request_refresh = AsyncMock()

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

    # Mock API for wyrestorm-networkhd v2.0.0
    coordinator.api = Mock()
    coordinator.api.media_stream_matrix_switch = Mock()
    coordinator.api.media_stream_matrix_switch.matrix_set = AsyncMock()
    coordinator.api.media_stream_matrix_switch.matrix_set_null = AsyncMock()
    coordinator.async_request_refresh = AsyncMock()

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
