"""Mock classes and setup utilities for tests."""

import sys
from unittest.mock import MagicMock


# Mock exception classes
class MockConfigEntryNotReady(Exception):
    """Mock for ConfigEntryNotReady exception."""

    pass


class MockConfigEntry:
    """Mock for Home Assistant ConfigEntry."""

    def __init__(self):
        self.entry_id = "test_entry"
        self.data = {}
        self.options = {}


class MockHomeAssistant:
    """Mock for Home Assistant instance."""

    def __init__(self):
        self.data = {}
        self.config_entries = MagicMock()


class MockDeviceInfo:
    """Mock for Home Assistant DeviceInfo."""

    def __init__(self, **kwargs):
        self._data = kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __getitem__(self, key):
        return self._data[key]

    def __contains__(self, key):
        return key in self._data


class MockEntityCategory:
    """Mock for Home Assistant EntityCategory."""

    CONFIG = "config"
    DIAGNOSTIC = "diagnostic"


class MockBinarySensorDeviceClass:
    """Mock for Home Assistant BinarySensorDeviceClass."""

    CONNECTIVITY = "connectivity"
    PLUG = "plug"
    RUNNING = "running"


# Create a special mock that supports subscription for generic types
class SubscriptableMock(MagicMock):
    """Mock that supports generic type subscripting."""

    def __class_getitem__(cls, item):  # noqa: ARG002
        # Return a new class that can be used as a base class
        class CoordinatorEntityMock(MagicMock):
            def __init__(self, coordinator):
                super().__init__()
                self.coordinator = coordinator

        return CoordinatorEntityMock


def setup_home_assistant_mocks():
    """Set up all Home Assistant module mocks."""
    # Mock Home Assistant core modules
    sys.modules["homeassistant"] = MagicMock()
    sys.modules["homeassistant.core"] = MagicMock()
    sys.modules["homeassistant.config_entries"] = MagicMock()

    # Set up constants
    const_mock = MagicMock()
    const_mock.CONF_HOST = "host"
    const_mock.CONF_PORT = "port"
    const_mock.CONF_USERNAME = "username"
    const_mock.CONF_PASSWORD = "password"
    sys.modules["homeassistant.const"] = const_mock

    # Set up exception mocks
    exceptions_mock = MagicMock()
    exceptions_mock.ConfigEntryNotReady = MockConfigEntryNotReady
    sys.modules["homeassistant.exceptions"] = exceptions_mock

    # Set up helper mocks
    helpers_mock = MagicMock()
    sys.modules["homeassistant.helpers"] = helpers_mock
    sys.modules["homeassistant.helpers.entity"] = MagicMock()
    sys.modules["homeassistant.helpers.entity_platform"] = MagicMock()
    sys.modules["homeassistant.helpers.update_coordinator"] = MagicMock()
    sys.modules["homeassistant.helpers.device_registry"] = MagicMock()

    dispatcher_mock = MagicMock()
    dispatcher_mock.async_dispatcher_send = MagicMock()
    sys.modules["homeassistant.helpers.dispatcher"] = dispatcher_mock

    # Set up component mocks
    sys.modules["homeassistant.components.binary_sensor"] = MagicMock()
    sys.modules["homeassistant.components.button"] = MagicMock()
    sys.modules["homeassistant.components.select"] = MagicMock()
    sys.modules["homeassistant.data_entry_flow"] = MagicMock()

    # Set up the mocks with proper classes
    core_mock = MagicMock()
    core_mock.HomeAssistant = MockHomeAssistant
    sys.modules["homeassistant"] = core_mock

    config_entries_mock = MagicMock()
    config_entries_mock.ConfigEntry = MockConfigEntry
    sys.modules["homeassistant.config_entries"] = config_entries_mock

    entity_mock = MagicMock()
    entity_mock.DeviceInfo = MockDeviceInfo
    entity_mock.EntityCategory = MockEntityCategory
    sys.modules["homeassistant.helpers.entity"] = entity_mock

    binary_sensor_mock = MagicMock()
    binary_sensor_mock.BinarySensorDeviceClass = MockBinarySensorDeviceClass
    binary_sensor_mock.BinarySensorEntity = MagicMock
    sys.modules["homeassistant.components.binary_sensor"] = binary_sensor_mock

    button_mock = MagicMock()
    button_mock.ButtonEntity = MagicMock
    sys.modules["homeassistant.components.button"] = button_mock

    select_mock = MagicMock()
    select_mock.SelectEntity = MagicMock
    sys.modules["homeassistant.components.select"] = select_mock

    update_coordinator_mock = MagicMock()
    update_coordinator_mock.CoordinatorEntity = SubscriptableMock
    sys.modules["homeassistant.helpers.update_coordinator"] = update_coordinator_mock


def setup_wyrestorm_mocks():
    """Set up WyreStorm NetworkHD library mocks."""
    wyrestorm_mock = MagicMock()
    wyrestorm_mock.NHDAPI = MagicMock
    wyrestorm_mock.NetworkHDClientSSH = MagicMock
    wyrestorm_mock.exceptions = MagicMock()
    wyrestorm_mock.exceptions.NetworkHDError = Exception
    sys.modules["wyrestorm_networkhd"] = wyrestorm_mock
    sys.modules["wyrestorm_networkhd.exceptions"] = wyrestorm_mock.exceptions


def setup_third_party_mocks():
    """Set up third-party library mocks."""
    sys.modules["voluptuous"] = MagicMock()


def setup_all_mocks():
    """Set up all required mocks for testing."""
    setup_home_assistant_mocks()
    setup_wyrestorm_mocks()
    setup_third_party_mocks()
