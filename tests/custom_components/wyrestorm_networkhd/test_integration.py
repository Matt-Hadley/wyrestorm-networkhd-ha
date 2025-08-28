"""Integration tests for WyreStorm NetworkHD custom component."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from custom_components.wyrestorm_networkhd import async_setup_entry, async_unload_entry
from custom_components.wyrestorm_networkhd.const import DOMAIN


class TestIntegrationSetup:
    """Test integration setup and teardown."""

    @pytest.mark.asyncio
    async def test_full_integration_setup(self, mock_coordinator_factory):
        """Test complete integration setup process."""
        # Mock Home Assistant and config entry
        hass = Mock()
        hass.data = {}

        config_entry = Mock()
        config_entry.entry_id = "test_integration"
        config_entry.data = {
            "host": "192.168.1.10",
            "port": 10022,
            "username": "wyrestorm",
            "password": "networkhd",
        }
        config_entry.options = {}

        # Mock coordinator and API - start with no data so wait_for_data gets called
        coordinator = mock_coordinator_factory(ready=True)
        coordinator.data = None  # Ensure no initial data to trigger wait_for_data

        with (
            patch("custom_components.wyrestorm_networkhd.NetworkHDClientSSH") as mock_client_class,
            patch("custom_components.wyrestorm_networkhd.NHDAPI") as mock_api_class,
            patch("custom_components.wyrestorm_networkhd.WyreStormCoordinator") as mock_coordinator_class,
            patch("custom_components.wyrestorm_networkhd.dr.async_get") as mock_device_registry,
            patch.object(hass, "config_entries") as mock_config_entries,
            patch("custom_components.wyrestorm_networkhd._async_register_services") as mock_register_services,
        ):
            # Setup mocks
            mock_client = Mock()
            mock_client.connect = AsyncMock()
            mock_client_class.return_value = mock_client

            mock_api = Mock()
            mock_api.api_query = Mock()
            mock_api.api_query.config_get_version = AsyncMock(return_value="1.2.3")
            mock_api_class.return_value = mock_api

            mock_coordinator_class.return_value = coordinator

            mock_device_reg = Mock()
            mock_device_reg.async_get_or_create.return_value = Mock(id="controller_device")
            mock_device_registry.return_value = mock_device_reg

            mock_config_entries.async_forward_entry_setups = AsyncMock()
            mock_register_services.return_value = AsyncMock()

            # Test setup
            result = await async_setup_entry(hass, config_entry)

            # Verify setup was successful
            assert result is True
            assert DOMAIN in hass.data
            assert config_entry.entry_id in hass.data[DOMAIN]
            assert hass.data[DOMAIN][config_entry.entry_id] == coordinator

            # Verify coordinator setup was called
            coordinator.async_setup.assert_called_once()
            coordinator.wait_for_data.assert_called_once()

            # Verify platforms were set up
            mock_config_entries.async_forward_entry_setups.assert_called_once()

            # Verify device registry was used
            mock_device_reg.async_get_or_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_integration_unload(self, mock_coordinator_factory):
        """Test integration unload process."""
        # Setup mock Home Assistant with existing data
        hass = Mock()
        coordinator = mock_coordinator_factory(data=None)
        coordinator.async_shutdown = AsyncMock()

        hass.data = {DOMAIN: {"test_entry": coordinator}}

        config_entry = Mock()
        config_entry.entry_id = "test_entry"

        with (
            patch.object(hass, "config_entries") as mock_config_entries,
            patch.object(hass, "services"),
        ):
            mock_config_entries.async_unload_platforms = AsyncMock(return_value=True)

            # Test unload
            result = await async_unload_entry(hass, config_entry)

            # Verify unload was successful
            assert result is True

            # Verify platforms were unloaded
            mock_config_entries.async_unload_platforms.assert_called_once()

            # Verify coordinator was shut down
            coordinator.async_shutdown.assert_called_once()

            # Verify data was cleaned up
            assert config_entry.entry_id not in hass.data[DOMAIN]

    @pytest.mark.asyncio
    async def test_setup_connection_failure(self):
        """Test setup with connection failure."""
        hass = Mock()
        hass.data = {}

        config_entry = Mock()
        config_entry.entry_id = "test_entry"
        config_entry.data = {
            "host": "192.168.1.10",
            "port": 10022,
            "username": "wyrestorm",
            "password": "networkhd",
        }
        config_entry.options = {}

        with (
            patch("custom_components.wyrestorm_networkhd.NetworkHDClientSSH"),
            patch("custom_components.wyrestorm_networkhd.NHDAPI"),
            patch("custom_components.wyrestorm_networkhd.WyreStormCoordinator") as mock_coordinator_class,
        ):
            from wyrestorm_networkhd.exceptions import NetworkHDError

            # Setup coordinator to fail on setup
            coordinator = Mock()
            coordinator.async_setup = AsyncMock(side_effect=NetworkHDError("Connection failed"))
            mock_coordinator_class.return_value = coordinator

            # Test setup should raise ConfigEntryNotReady
            from homeassistant.exceptions import ConfigEntryNotReady

            with pytest.raises(ConfigEntryNotReady):
                await async_setup_entry(hass, config_entry)

    @pytest.mark.asyncio
    async def test_setup_coordinator_timeout(self, mock_coordinator_factory):
        """Test setup with coordinator data timeout."""
        hass = Mock()
        hass.data = {}
        hass.config_entries = Mock()
        hass.config_entries.async_forward_entry_setups = AsyncMock()

        config_entry = Mock()
        config_entry.entry_id = "test_entry"
        config_entry.data = {
            "host": "192.168.1.10",
            "port": 10022,
            "username": "wyrestorm",
            "password": "networkhd",
        }
        config_entry.options = {}

        # Create coordinator that times out waiting for data
        coordinator = mock_coordinator_factory(ready=True)
        coordinator.data = None  # Ensure no initial data to trigger wait_for_data
        coordinator.wait_for_data = AsyncMock(return_value=False)  # Timeout

        with (
            patch("custom_components.wyrestorm_networkhd.NetworkHDClientSSH") as mock_client_class,
            patch("custom_components.wyrestorm_networkhd.NHDAPI") as mock_api_class,
            patch("custom_components.wyrestorm_networkhd.WyreStormCoordinator") as mock_coordinator_class,
        ):
            mock_coordinator_class.return_value = coordinator

            mock_client = Mock()
            mock_client.connect = AsyncMock()
            mock_client_class.return_value = mock_client

            mock_api = Mock()
            mock_api.api_query = Mock()
            mock_api.api_query.config_get_version = AsyncMock(return_value="1.2.3")
            mock_api_class.return_value = mock_api

            # Test setup should raise ConfigEntryNotReady
            from homeassistant.exceptions import ConfigEntryNotReady

            with pytest.raises(ConfigEntryNotReady):
                await async_setup_entry(hass, config_entry)

    @pytest.mark.asyncio
    async def test_unload_with_remaining_entries(self, mock_coordinator_factory):
        """Test unload when other entries remain (services should not be removed)."""
        hass = Mock()
        coordinator1 = mock_coordinator_factory()
        coordinator2 = mock_coordinator_factory()

        hass.data = {
            DOMAIN: {
                "entry1": coordinator1,
                "entry2": coordinator2,  # Another entry remains
            }
        }

        config_entry = Mock()
        config_entry.entry_id = "entry1"

        with (
            patch.object(hass, "config_entries") as mock_config_entries,
            patch.object(hass, "services") as mock_services,
        ):
            mock_config_entries.async_unload_platforms = AsyncMock(return_value=True)

            result = await async_unload_entry(hass, config_entry)

            assert result is True
            # Services should not be removed since other entries remain
            mock_services.async_remove.assert_not_called()
            # Only the specific entry should be removed
            assert "entry1" not in hass.data[DOMAIN]
            assert "entry2" in hass.data[DOMAIN]
