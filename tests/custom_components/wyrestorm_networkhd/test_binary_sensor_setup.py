"""Test binary sensor platform setup for WyreStorm NetworkHD integration."""

from unittest.mock import Mock

import pytest

from custom_components.wyrestorm_networkhd.binary_sensor import async_setup_entry
from custom_components.wyrestorm_networkhd.const import DOMAIN
from tests.helpers.base import AsyncSetupTestBase


class TestAsyncSetupEntry(AsyncSetupTestBase):
    """Test async_setup_entry function."""

    @pytest.mark.asyncio
    async def test_setup_success(self, mock_hass, mock_config_entry, mock_binary_sensor_coordinator):
        """Test successful setup of binary sensor entities."""
        entities = await self.run_successful_setup_test(
            async_setup_entry,
            mock_hass,
            mock_config_entry,
            Mock(),
            mock_binary_sensor_coordinator,
            expected_entity_count=4,  # 2 online + 1 video input + 1 video output
        )

        # Check entity types
        entity_types = [type(entity).__name__ for entity in entities]
        assert "WyreStormOnlineSensor" in entity_types
        assert "WyreStormVideoInputSensor" in entity_types
        assert "WyreStormVideoOutputSensor" in entity_types

    @pytest.mark.asyncio
    async def test_setup_no_devices(self, mock_hass, mock_config_entry, mock_binary_sensor_coordinator):
        """Test setup with no devices."""
        from custom_components.wyrestorm_networkhd.coordinator import CoordinatorData, DeviceCollection

        # Create empty coordinator data
        empty_devices = DeviceCollection()
        mock_binary_sensor_coordinator.data = CoordinatorData(
            devices=empty_devices, matrix={}, device_status=[], device_info=[]
        )
        mock_binary_sensor_coordinator.get_all_devices.return_value = empty_devices
        mock_binary_sensor_coordinator.is_ready.return_value = True

        mock_hass.data = {DOMAIN: {mock_config_entry.entry_id: mock_binary_sensor_coordinator}}
        mock_add_entities = Mock()

        await async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)

        # Should not add any entities
        mock_add_entities.assert_not_called()

    @pytest.mark.asyncio
    async def test_setup_coordinator_not_ready(self, mock_hass, mock_config_entry, mock_binary_sensor_coordinator):
        """Test setup when coordinator is not ready."""
        await self.run_coordinator_not_ready_test(
            async_setup_entry, mock_hass, mock_config_entry, Mock(), mock_binary_sensor_coordinator
        )

    @pytest.mark.asyncio
    async def test_setup_coordinator_has_errors(self, mock_hass, mock_config_entry, mock_binary_sensor_coordinator):
        """Test setup when coordinator has errors."""
        await self.run_coordinator_has_errors_test(
            async_setup_entry, mock_hass, mock_config_entry, Mock(), mock_binary_sensor_coordinator
        )
