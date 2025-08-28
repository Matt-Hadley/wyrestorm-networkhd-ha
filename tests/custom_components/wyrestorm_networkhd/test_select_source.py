"""Test WyreStormSourceSelect for WyreStorm NetworkHD integration."""

import pytest
from homeassistant.helpers.entity import EntityCategory
from wyrestorm_networkhd.exceptions import NetworkHDError

from custom_components.wyrestorm_networkhd.const import DOMAIN
from custom_components.wyrestorm_networkhd.select import WyreStormSourceSelect
from tests.helpers.base import SelectTestBase


class TestWyreStormSourceSelect(SelectTestBase):
    """Test WyreStormSourceSelect class."""

    @pytest.fixture
    def source_select(self, mock_select_coordinator):
        """Create a source select entity."""
        device_info = mock_select_coordinator.get_all_devices.return_value["decoder1"]
        return WyreStormSourceSelect(mock_select_coordinator, "decoder1", device_info)

    def test_init(self, source_select, mock_select_coordinator):
        """Test select entity initialization."""
        self.assert_basic_entity_properties(
            source_select,
            expected_name="Input Source",
            expected_unique_id="192.168.1.10_decoder1_matrix_routing",
            expected_icon="mdi:video-switch",
            expected_category=EntityCategory.CONFIG,
        )
        assert source_select._device_id == "decoder1"
        self.assert_coordinator_dependency(source_select, mock_select_coordinator)

    def test_device_info(self, source_select):
        """Test device info generation."""
        device_info = source_select.device_info

        self.assert_device_info_properties(
            device_info,
            expected_identifiers={(DOMAIN, "192.168.1.10_decoder1")},
            expected_name="Decoder - decoder1",
            expected_model="NHD-RX",
        )
        assert device_info["via_device"] == (DOMAIN, "192.168.1.10")

    def test_current_option_valid_source(self, source_select):
        """Test current_option with valid source."""
        # Current source should be in options list
        self.assert_current_option(source_select, expected_option="encoder1")

    def test_current_option_invalid_source(self, source_select, mock_select_coordinator):
        """Test current_option with source not in options."""
        coordinator_data = {
            "devices": {
                **mock_select_coordinator.data["devices"],
                "decoder1": {
                    **mock_select_coordinator.data["devices"]["decoder1"],
                    "current_source": "invalid_encoder",
                },
            }
        }
        self.assert_current_option(source_select, expected_option=None, coordinator_data=coordinator_data)

    def test_current_option_no_source(self, source_select, mock_select_coordinator):
        """Test current_option with no current source."""
        coordinator_data = {
            "devices": {
                **mock_select_coordinator.data["devices"],
                "decoder1": {**mock_select_coordinator.data["devices"]["decoder1"], "current_source": None},
            }
        }
        self.assert_current_option(source_select, expected_option=None, coordinator_data=coordinator_data)

    def test_current_option_no_coordinator_data(self, source_select, mock_select_coordinator):
        """Test current_option when coordinator has no data."""
        mock_select_coordinator.data = None
        assert source_select.current_option is None

    def test_options_list(self, source_select):
        """Test options list generation."""
        expected_options = ["None", "encoder1", "encoder2"]
        self.assert_options_list(source_select, expected_options)

    def test_options_no_coordinator_data(self, source_select, mock_select_coordinator):
        """Test options when coordinator has no data."""
        mock_select_coordinator.data = None
        options = source_select.options
        assert options == []

    def test_available_device_online(self, source_select):
        """Test availability when device is online."""
        self.assert_availability_device_online(source_select, source_select.coordinator, "decoder1")

    def test_available_device_offline(self, source_select):
        """Test availability when device is offline."""
        self.assert_availability_device_offline(source_select, source_select.coordinator, "decoder1")

    def test_available_coordinator_not_ready(self, source_select):
        """Test availability when coordinator is not ready."""
        self.assert_availability_coordinator_not_ready(source_select, source_select.coordinator)

    def test_available_coordinator_has_errors(self, source_select):
        """Test availability when coordinator has errors."""
        self.assert_availability_coordinator_has_errors(source_select, source_select.coordinator)

    def test_extra_state_attributes(self, source_select):
        """Test extra state attributes."""
        attrs = source_select.extra_state_attributes

        assert attrs["device_id"] == "decoder1"
        assert attrs["device_type"] == "decoder"
        assert attrs["model"] == "NHD-RX"
        assert attrs["online"] is True
        assert attrs["current_source"] == "encoder1"
        assert attrs["ip_address"] == "192.168.1.101"

    def test_extra_state_attributes_no_data(self, source_select, mock_select_coordinator):
        """Test extra state attributes when no coordinator data."""
        mock_select_coordinator.data = None
        attrs = source_select.extra_state_attributes
        assert attrs == {}

    @pytest.mark.asyncio
    async def test_async_select_option_encoder(self, source_select, mock_select_coordinator):
        """Test selecting an encoder as source."""
        await self.assert_select_option_success(
            source_select, "encoder2", mock_select_coordinator.api.media_stream_matrix_switch.matrix_set
        )
        mock_select_coordinator.api.media_stream_matrix_switch.matrix_set.assert_called_with("encoder2", ["decoder1"])
        mock_select_coordinator.async_request_refresh.assert_called_once()
        mock_select_coordinator.api.media_stream_matrix_switch.matrix_set_null.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_select_option_none(self, source_select, mock_select_coordinator):
        """Test selecting None to disconnect."""
        await source_select.async_select_option("None")

        mock_select_coordinator.api.media_stream_matrix_switch.matrix_set_null.assert_called_once_with(["decoder1"])
        mock_select_coordinator.async_request_refresh.assert_called_once()
        mock_select_coordinator.api.media_stream_matrix_switch.matrix_set.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_select_option_network_error(self, source_select, mock_select_coordinator):
        """Test select option with network error."""
        await self.assert_select_option_error(
            source_select, "encoder1", mock_select_coordinator.api.media_stream_matrix_switch.matrix_set, NetworkHDError
        )

    @pytest.mark.asyncio
    async def test_async_select_option_generic_error(self, source_select, mock_select_coordinator):
        """Test select option with generic error."""
        await self.assert_select_option_error(
            source_select, "encoder1", mock_select_coordinator.api.media_stream_matrix_switch.matrix_set, RuntimeError
        )

    def test_device_info_with_ip_fallback(self, mock_select_coordinator):
        """Test device info with IP address fallback for device name."""
        # Create device with unknown ID but valid IP
        device_info = {"type": "decoder", "model": "NHD-RX"}
        mock_select_coordinator.data = {"devices": {"unknown": {"ip_address": "192.168.1.200", "online": True}}}

        source_select = WyreStormSourceSelect(mock_select_coordinator, "unknown", device_info)
        device_info_result = source_select.device_info

        assert device_info_result["name"] == "Decoder - 192.168.1.200"
