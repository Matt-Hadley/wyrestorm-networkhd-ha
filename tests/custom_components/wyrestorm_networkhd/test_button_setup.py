"""Test button platform setup for WyreStorm NetworkHD integration."""

from unittest.mock import Mock

import pytest

from custom_components.wyrestorm_networkhd.button import (
    WyreStormRebootButton,
    async_setup_entry,
)
from custom_components.wyrestorm_networkhd.const import DOMAIN
from tests.helpers.base import AsyncSetupTestBase


class TestAsyncSetupEntry(AsyncSetupTestBase):
    """Test async_setup_entry function."""

    @pytest.mark.asyncio
    async def test_setup_success(self, mock_hass, mock_config_entry, mock_button_coordinator):
        """Test successful setup of button entities."""
        entities = await self.run_successful_setup_test(
            async_setup_entry,
            mock_hass,
            mock_config_entry,
            Mock(),
            mock_button_coordinator,
            expected_entity_count=5,  # 1 reboot + 2 decoders * 2 buttons each
        )

        # Check entity types
        entity_types = [type(entity).__name__ for entity in entities]
        assert "WyreStormRebootButton" in entity_types
        assert "WyreStormSinkPowerOnButton" in entity_types
        assert "WyreStormSinkPowerOffButton" in entity_types

    @pytest.mark.asyncio
    async def test_setup_no_devices(self, mock_hass, mock_config_entry, mock_button_coordinator):
        """Test setup with no devices."""
        mock_button_coordinator.data = {"devices": {}}
        mock_hass.data = {DOMAIN: {mock_config_entry.entry_id: mock_button_coordinator}}
        mock_add_entities = Mock()

        await async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)

        # Should only create reboot button
        entities = mock_add_entities.call_args[0][0]
        assert len(entities) == 1
        assert isinstance(entities[0], WyreStormRebootButton)

    @pytest.mark.asyncio
    async def test_setup_coordinator_not_ready(self, mock_hass, mock_config_entry, mock_button_coordinator):
        """Test setup when coordinator is not ready."""
        await self.run_coordinator_not_ready_test(
            async_setup_entry, mock_hass, mock_config_entry, Mock(), mock_button_coordinator
        )

    @pytest.mark.asyncio
    async def test_setup_coordinator_has_errors(self, mock_hass, mock_config_entry, mock_button_coordinator):
        """Test setup when coordinator has errors."""
        await self.run_coordinator_has_errors_test(
            async_setup_entry, mock_hass, mock_config_entry, Mock(), mock_button_coordinator
        )
