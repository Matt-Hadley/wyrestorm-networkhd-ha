"""Test select platform setup for WyreStorm NetworkHD integration."""

from unittest.mock import Mock

import pytest

from custom_components.wyrestorm_networkhd.const import DOMAIN
from custom_components.wyrestorm_networkhd.select import WyreStormSourceSelect, async_setup_entry
from tests.helpers.base import AsyncSetupTestBase


class TestAsyncSetupEntry(AsyncSetupTestBase):
    """Test async_setup_entry function."""

    @pytest.mark.asyncio
    async def test_setup_success(self, mock_hass, mock_config_entry, mock_select_coordinator):
        """Test successful setup of select entities."""
        entities = await self.run_successful_setup_test(
            async_setup_entry,
            mock_hass,
            mock_config_entry,
            Mock(),
            mock_select_coordinator,
            expected_entity_count=2,  # 2 decoder select entities
        )

        # Check all entities are source selects
        for entity in entities:
            assert isinstance(entity, WyreStormSourceSelect)

    @pytest.mark.asyncio
    async def test_setup_no_decoders(self, mock_hass, mock_config_entry, mock_select_coordinator):
        """Test setup with no decoder devices."""
        # Remove decoders, keep only encoders
        devices = {
            k: v for k, v in mock_select_coordinator.get_all_devices.return_value.items() if v.get("type") == "encoder"
        }
        mock_select_coordinator.get_all_devices.return_value = devices
        mock_select_coordinator.data = {"devices": devices}

        mock_hass.data = {DOMAIN: {mock_config_entry.entry_id: mock_select_coordinator}}
        mock_add_entities = Mock()

        await async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)

        # Should not add any entities
        mock_add_entities.assert_not_called()

    @pytest.mark.asyncio
    async def test_setup_coordinator_not_ready(self, mock_hass, mock_config_entry, mock_select_coordinator):
        """Test setup when coordinator is not ready."""
        await self.run_coordinator_not_ready_test(
            async_setup_entry, mock_hass, mock_config_entry, Mock(), mock_select_coordinator
        )
