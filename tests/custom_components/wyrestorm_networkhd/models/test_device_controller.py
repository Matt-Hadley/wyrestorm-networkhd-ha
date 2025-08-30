# ruff: noqa: F811
"""Unit tests for the DeviceController model.

This module contains comprehensive tests for the DeviceController class,
which represents the central controller in a WyreStorm NetworkHD system.

Test Categories:
    - Initialization and Construction
    - Factory Methods
    - Display Name Generation
    - Equality and Comparison
    - String Representations
    - Data Model Properties
"""

from custom_components.wyrestorm_networkhd.models.device_controller import (
    DeviceController,
)

from .._fixtures import (  # noqa: F401
    alternative_ip_setting_fixture,
    alternative_version_fixture,
    device_controller_display_name_test_cases,
    device_controller_fixture,
    ip_setting_fixture,
    version_fixture,
)


class TestDeviceControllerInitialization:
    """Test DeviceController initialization and basic properties."""

    def test_init_with_all_parameters(self, device_controller_fixture):
        """Verify DeviceController initializes correctly with all parameters.

        Tests that all version and network configuration fields are properly
        set when creating a DeviceController instance.
        """
        controller = device_controller_fixture

        # Verify version fields
        assert controller.api_version == "1.0.0"
        assert controller.web_version == "2.1.0"
        assert controller.core_version == "3.0.1"

        # Verify network configuration fields
        assert controller.ip4addr == "192.168.1.100"
        assert controller.netmask == "255.255.255.0"
        assert controller.gateway == "192.168.1.1"

    def test_post_init_sets_manufacturer_and_model(self, device_controller_fixture):
        """Verify __post_init__ automatically sets manufacturer and model.

        The DeviceController should automatically set manufacturer to "WyreStorm"
        and model to "NetworkHD Controller" during initialization.
        """
        controller = device_controller_fixture

        assert controller.manufacturer == "WyreStorm"
        assert controller.model == "NetworkHD Controller"


class TestDeviceControllerFactoryMethods:
    """Test DeviceController factory methods and alternate construction."""

    def test_from_wyrestorm_models_factory_method(self, version_fixture, ip_setting_fixture):
        """Verify DeviceController can be created from WyreStorm API models.

        Tests the factory method that creates a DeviceController from
        Version and IpSetting objects from the wyrestorm-networkhd package.
        """
        controller = DeviceController.from_wyrestorm_models(version_fixture, ip_setting_fixture)

        # Verify version fields are correctly mapped
        assert controller.api_version == version_fixture.api_version
        assert controller.web_version == version_fixture.web_version
        assert controller.core_version == version_fixture.core_version

        # Verify IP setting fields are correctly mapped
        assert controller.ip4addr == ip_setting_fixture.ip4addr
        assert controller.netmask == ip_setting_fixture.netmask
        assert controller.gateway == ip_setting_fixture.gateway

        # Verify post-init fields are set
        assert controller.manufacturer == "WyreStorm"
        assert controller.model == "NetworkHD Controller"

    def test_factory_method_with_alternative_data(self, alternative_version_fixture, alternative_ip_setting_fixture):
        """Verify factory method handles different configurations correctly.

        Tests that the factory method properly maps fields when given
        alternative version and network configuration data.
        """
        controller = DeviceController.from_wyrestorm_models(alternative_version_fixture, alternative_ip_setting_fixture)

        # Verify alternative data is correctly mapped
        assert controller.api_version == "2.5.0"
        assert controller.web_version == "3.2.1"
        assert controller.core_version == "4.1.2"
        assert controller.ip4addr == "10.0.0.50"
        assert controller.netmask == "255.255.0.0"
        assert controller.gateway == "10.0.0.1"


class TestDeviceControllerDisplayName:
    """Test DeviceController display name generation."""

    def test_get_device_display_name_with_different_ips(self, device_controller_display_name_test_cases):
        """Verify display name generation for various IP addresses.

        Tests that the display name format is consistent across different
        IP address formats and ranges (parametrized test).
        """
        controller, expected_name = device_controller_display_name_test_cases
        assert controller.get_device_display_name() == expected_name


class TestDeviceControllerEquality:
    """Test DeviceController equality and comparison operations."""

    def test_equality_between_identical_controllers(
        self, device_controller_fixture, version_fixture, ip_setting_fixture
    ):
        """Verify two controllers with identical data are equal.

        Tests that DeviceController properly implements equality comparison
        when all fields match between two instances.
        """
        controller1 = device_controller_fixture

        # Create identical controller using factory method
        controller2 = DeviceController.from_wyrestorm_models(version_fixture, ip_setting_fixture)

        assert controller1 == controller2
        # Note: DeviceController is not hashable since it's not a frozen dataclass

    def test_inequality_when_fields_differ(self, device_controller_fixture):
        """Verify controllers with different fields are not equal.

        Tests that DeviceController inequality works correctly when
        any field differs between instances.
        """
        base_controller = device_controller_fixture

        # Test cases for each field that should trigger inequality
        field_variations = [
            {"api_version": "2.0.0"},  # Different API version
            {"web_version": "3.0.0"},  # Different web version
            {"core_version": "4.0.0"},  # Different core version
            {"ip4addr": "192.168.1.101"},  # Different IP address
            {"netmask": "255.255.0.0"},  # Different netmask
            {"gateway": "192.168.1.2"},  # Different gateway
        ]

        for field_change in field_variations:
            # Create controller with one field different
            controller_data = {
                "api_version": "1.0.0",
                "web_version": "2.1.0",
                "core_version": "3.0.1",
                "ip4addr": "192.168.1.100",
                "netmask": "255.255.255.0",
                "gateway": "192.168.1.1",
            }
            controller_data.update(field_change)

            different_controller = DeviceController(**controller_data)
            assert base_controller != different_controller, f"Failed for field change: {field_change}"


class TestDeviceControllerStringRepresentations:
    """Test DeviceController string representation methods."""

    def test_string_representation_contains_key_info(self, device_controller_fixture):
        """Verify string representation includes essential information.

        Tests that str() output contains the class name and key identifying
        information like the IP address.
        """
        controller = device_controller_fixture

        str_repr = str(controller)
        assert "DeviceController" in str_repr
        assert "192.168.1.100" in str_repr

    def test_repr_representation_is_detailed(self, device_controller_fixture):
        """Verify repr() provides detailed debugging information.

        Tests that repr() output contains enough detail to understand
        the object's state, including field names and values.
        """
        controller = device_controller_fixture

        repr_str = repr(controller)
        assert "DeviceController" in repr_str
        assert "api_version='1.0.0'" in repr_str
        assert "ip4addr='192.168.1.100'" in repr_str


class TestDeviceControllerDataModel:
    """Test DeviceController data model characteristics."""

    def test_dataclass_is_mutable(self, device_controller_fixture):
        """Verify DeviceController fields can be modified after creation.

        Tests that DeviceController is a regular (not frozen) dataclass,
        allowing field modifications after instantiation.
        """
        controller = device_controller_fixture

        # Verify fields can be modified
        controller.api_version = "2.0.0"
        assert controller.api_version == "2.0.0"

        controller.ip4addr = "192.168.1.200"
        assert controller.ip4addr == "192.168.1.200"

        controller.manufacturer = "Modified"
        assert controller.manufacturer == "Modified"

    def test_fixture_provides_valid_instance(self, device_controller_fixture):
        """Verify the test fixture provides a properly configured instance.

        Sanity check that our test fixture creates a valid DeviceController
        with expected default values.
        """
        assert isinstance(device_controller_fixture, DeviceController)
        assert device_controller_fixture.manufacturer == "WyreStorm"
        assert device_controller_fixture.model == "NetworkHD Controller"
        assert device_controller_fixture.api_version == "1.0.0"
        assert device_controller_fixture.get_device_display_name() == "Controller - 192.168.1.100"
