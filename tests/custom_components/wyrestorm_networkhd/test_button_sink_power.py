"""Test WyreStorm sink power buttons for WyreStorm NetworkHD integration."""


import pytest
from homeassistant.helpers.entity import EntityCategory
from wyrestorm_networkhd.exceptions import NetworkHDError

from custom_components.wyrestorm_networkhd.button import (
    WyreStormSinkPowerOffButton,
    WyreStormSinkPowerOnButton,
)
from custom_components.wyrestorm_networkhd.const import DOMAIN
from tests.helpers.base import ButtonTestBase


class TestWyreStormSinkPowerOnButton(ButtonTestBase):
    """Test WyreStormSinkPowerOnButton class."""

    @pytest.fixture
    def power_on_button(self, mock_button_coordinator):
        """Create a sink power on button."""
        device_data = mock_button_coordinator.data["devices"]["decoder1"]
        return WyreStormSinkPowerOnButton(mock_button_coordinator, "decoder1", device_data)

    def test_init(self, power_on_button, mock_button_coordinator):
        """Test button initialization."""
        self.assert_basic_entity_properties(
            power_on_button,
            expected_name="Display Power On",
            expected_unique_id="192.168.1.10_decoder1_display_power_on",
            expected_icon="mdi:television",
            expected_category=EntityCategory.CONFIG,
        )
        assert power_on_button.device_id == "decoder1"
        self.assert_coordinator_dependency(power_on_button, mock_button_coordinator)

    def test_available_device_online(self, power_on_button):
        """Test availability when device is online."""
        assert power_on_button.available is True

    def test_available_device_offline(self, power_on_button, mock_button_coordinator):
        """Test availability when device is offline."""
        mock_button_coordinator.data["devices"]["decoder1"]["online"] = False
        assert power_on_button.available is False

    def test_available_coordinator_has_errors(self, power_on_button, mock_button_coordinator):
        """Test availability when coordinator has errors."""
        mock_button_coordinator.has_errors.return_value = True
        assert power_on_button.available is False

    def test_device_info(self, power_on_button):
        """Test device info generation."""
        device_info = power_on_button.device_info

        self.assert_device_info_properties(
            device_info,
            expected_identifiers={(DOMAIN, "192.168.1.10_decoder1")},
            expected_name="Decoder - decoder1",
            expected_model="NHD-RX",
        )
        assert device_info["via_device"] == (DOMAIN, "192.168.1.10")

    def test_device_info_no_coordinator_data(self, power_on_button, mock_button_coordinator):
        """Test device info when coordinator has no data."""
        mock_button_coordinator.data = None
        device_info = power_on_button.device_info

        assert device_info["identifiers"] == {(DOMAIN, "192.168.1.10_decoder1")}
        assert device_info["name"] == "Decoder - decoder1"

    @pytest.mark.asyncio
    async def test_async_press_success(self, power_on_button, mock_button_coordinator):
        """Test successful sink power on button press."""
        await power_on_button.async_press()

        mock_button_coordinator.api.connected_device_control.config_set_device_sinkpower.assert_called_once_with(
            power="on", rx="decoder1"
        )
        mock_button_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_press_network_error(self, power_on_button, mock_button_coordinator):
        """Test sink power on button press with network error."""
        mock_button_coordinator.api.connected_device_control.config_set_device_sinkpower.side_effect = NetworkHDError(
            "Connection failed"
        )

        with pytest.raises(NetworkHDError):
            await power_on_button.async_press()


class TestWyreStormSinkPowerOffButton(ButtonTestBase):
    """Test WyreStormSinkPowerOffButton class."""

    @pytest.fixture
    def power_off_button(self, mock_button_coordinator):
        """Create a sink power off button."""
        device_data = mock_button_coordinator.data["devices"]["decoder1"]
        return WyreStormSinkPowerOffButton(mock_button_coordinator, "decoder1", device_data)

    def test_init(self, power_off_button, mock_button_coordinator):
        """Test button initialization."""
        self.assert_basic_entity_properties(
            power_off_button,
            expected_name="Display Power Off",
            expected_unique_id="192.168.1.10_decoder1_display_power_off",
            expected_icon="mdi:television-off",
            expected_category=EntityCategory.CONFIG,
        )
        assert power_off_button.device_id == "decoder1"
        self.assert_coordinator_dependency(power_off_button, mock_button_coordinator)

    @pytest.mark.asyncio
    async def test_async_press_success(self, power_off_button, mock_button_coordinator):
        """Test successful sink power off button press."""
        await power_off_button.async_press()

        mock_button_coordinator.api.connected_device_control.config_set_device_sinkpower.assert_called_once_with(
            power="off", rx="decoder1"
        )
        mock_button_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_press_generic_error(self, power_off_button, mock_button_coordinator):
        """Test sink power off button press with generic error."""
        mock_button_coordinator.api.connected_device_control.config_set_device_sinkpower.side_effect = RuntimeError(
            "Generic error"
        )

        with pytest.raises(RuntimeError):
            await power_off_button.async_press()

    def test_available_coordinator_not_ready(self, power_off_button, mock_button_coordinator):
        """Test availability when coordinator is not ready."""
        mock_button_coordinator.is_ready.return_value = False
        assert power_off_button.available is False

    def test_available_no_coordinator_data(self, power_off_button, mock_button_coordinator):
        """Test availability when coordinator has no data."""
        mock_button_coordinator.data = None
        assert power_off_button.available is False

    def test_available_device_not_found(self, power_off_button, mock_button_coordinator):
        """Test availability when device not found."""
        del mock_button_coordinator.data["devices"]["decoder1"]
        assert power_off_button.available is False
