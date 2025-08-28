"""Test WyreStormRebootButton for WyreStorm NetworkHD integration."""

import pytest
from homeassistant.helpers.entity import EntityCategory

from custom_components.wyrestorm_networkhd.button import WyreStormRebootButton
from custom_components.wyrestorm_networkhd.const import DOMAIN
from tests.helpers.base import ButtonTestBase


class TestWyreStormRebootButton(ButtonTestBase):
    """Test WyreStormRebootButton class."""

    @pytest.fixture
    def reboot_button(self, mock_button_coordinator):
        """Create a reboot button."""
        return WyreStormRebootButton(mock_button_coordinator)

    def test_init(self, reboot_button, mock_button_coordinator):
        """Test button initialization."""
        self.assert_basic_entity_properties(
            reboot_button,
            expected_name="Reboot Controller",
            expected_unique_id="192.168.1.10_controller_reboot",
            expected_icon="mdi:restart",
            expected_category=EntityCategory.CONFIG,
        )
        self.assert_coordinator_dependency(reboot_button, mock_button_coordinator)

    def test_available_coordinator_ready(self, reboot_button):
        """Test availability when coordinator is ready."""
        assert reboot_button.available is True

    def test_available_coordinator_not_ready(self, reboot_button, mock_button_coordinator):
        """Test availability when coordinator is not ready."""
        mock_button_coordinator.is_ready.return_value = False
        assert reboot_button.available is False

    def test_available_coordinator_has_errors(self, reboot_button, mock_button_coordinator):
        """Test availability when coordinator has errors."""
        mock_button_coordinator.has_errors.return_value = True
        assert reboot_button.available is False

    def test_device_info(self, reboot_button):
        """Test device info for controller."""
        device_info = reboot_button.device_info

        self.assert_device_info_properties(
            device_info,
            expected_identifiers={(DOMAIN, "192.168.1.10")},
            expected_name="Controller - 192.168.1.10",
            expected_model="NetworkHD Controller",
        )
        assert device_info["via_device"] is None

    @pytest.mark.asyncio
    async def test_async_press_success(self, reboot_button, mock_button_coordinator):
        """Test successful reboot button press."""
        await reboot_button.async_press()

        mock_button_coordinator.api.reboot_reset.set_reboot.assert_called_once()
        # Should not refresh after reboot command
        mock_button_coordinator.async_request_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_press_network_error(self, reboot_button, mock_button_coordinator):
        """Test reboot button press with network error."""
        await self.assert_button_press_network_error(
            reboot_button, mock_button_coordinator, mock_button_coordinator.api.reboot_reset.set_reboot
        )

    @pytest.mark.asyncio
    async def test_async_press_generic_error(self, reboot_button, mock_button_coordinator):
        """Test reboot button press with generic error."""
        await self.assert_button_press_generic_error(
            reboot_button, mock_button_coordinator, mock_button_coordinator.api.reboot_reset.set_reboot
        )
