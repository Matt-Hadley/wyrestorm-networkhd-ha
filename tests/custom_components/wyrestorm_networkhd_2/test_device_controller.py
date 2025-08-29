"""Unit tests for DeviceController model."""

import pytest

from custom_components.wyrestorm_networkhd_2.models.device_controller import DeviceController
from ._fixtures import version_fixture, ip_setting_fixture, device_controller_fixture


class TestDeviceController:
    """Tests for DeviceController model."""

    def test_init(self):
        """Test direct initialization of DeviceController."""
        controller = DeviceController(
            api_version="1.0.0",
            web_version="2.1.0",
            core_version="3.0.1",
            ip4addr="192.168.1.100",
            netmask="255.255.255.0",
            gateway="192.168.1.1",
        )

        assert controller.api_version == "1.0.0"
        assert controller.web_version == "2.1.0"
        assert controller.core_version == "3.0.1"
        assert controller.ip4addr == "192.168.1.100"
        assert controller.netmask == "255.255.255.0"
        assert controller.gateway == "192.168.1.1"
        assert controller.manufacturer == "WyreStorm"
        assert controller.model == "NetworkHD Controller"

    def test_get_device_display_name(self):
        """Test get_device_display_name method."""
        controller = DeviceController(
            api_version="1.0.0",
            web_version="2.1.0",
            core_version="3.0.1",
            ip4addr="192.168.1.100",
            netmask="255.255.255.0",
            gateway="192.168.1.1",
        )

        assert controller.get_device_display_name() == "Controller - 192.168.1.100"

    def test_from_wyrestorm_models(self, version_fixture, ip_setting_fixture):
        """Test creating DeviceController from wyrestorm-networkhd models."""
        controller = DeviceController.from_wyrestorm_models(version_fixture, ip_setting_fixture)

        assert controller.api_version == "1.0.0"
        assert controller.web_version == "2.1.0"
        assert controller.core_version == "3.0.1"
        assert controller.ip4addr == "192.168.1.100"
        assert controller.netmask == "255.255.255.0"
        assert controller.gateway == "192.168.1.1"
        assert controller.manufacturer == "WyreStorm"
        assert controller.model == "NetworkHD Controller"
        assert controller.get_device_display_name() == "Controller - 192.168.1.100"
