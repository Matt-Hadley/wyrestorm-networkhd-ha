# ruff: noqa: F811
"""Comprehensive unit tests for CoordinatorData model."""

from datetime import datetime
from unittest.mock import patch

from custom_components.wyrestorm_networkhd.models.coordinator import CoordinatorData

from .._fixtures import (  # noqa: F401
    coordinator_data_fixture,
    device_controller_fixture,
    device_receiver_bedroom_fixture,
    device_receiver_fixture,
    device_receiver_updated_fixture,
    device_transmitter_fixture,
)


class TestCoordinatorData:
    """Comprehensive test suite for CoordinatorData model."""

    def test_init(self, device_controller_fixture):
        """Test initialization of CoordinatorData."""
        coordinator_data = CoordinatorData(device_controller=device_controller_fixture)

        assert coordinator_data.device_controller is device_controller_fixture
        assert coordinator_data.device_transmitters == {}
        assert coordinator_data.device_receivers == {}
        assert coordinator_data.matrix_assignments == {}
        assert isinstance(coordinator_data.last_update, datetime)

    @patch("custom_components.wyrestorm_networkhd.models.coordinator.datetime")
    def test_post_init_updates_timestamp(self, mock_datetime, device_controller_fixture):
        """Test that __post_init__ updates the timestamp."""
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now

        coordinator_data = CoordinatorData(device_controller=device_controller_fixture)

        assert coordinator_data.last_update == mock_now
        mock_datetime.now.assert_called_once()

    def test_get_transmitters_list_empty(self, coordinator_data_fixture):
        """Test get_transmitters_list when no transmitters exist."""
        result = coordinator_data_fixture.get_transmitters_list()

        assert result == []
        assert isinstance(result, list)

    def test_get_receivers_list_empty(self, coordinator_data_fixture):
        """Test get_receivers_list when no receivers exist."""
        result = coordinator_data_fixture.get_receivers_list()

        assert result == []
        assert isinstance(result, list)

    def test_matrix_assignments_initialization(self, coordinator_data_fixture):
        """Test that matrix_assignments initializes as empty dict."""
        assert coordinator_data_fixture.matrix_assignments == {}
        assert isinstance(coordinator_data_fixture.matrix_assignments, dict)

    def test_matrix_assignments_manipulation(self, coordinator_data_fixture):
        """Test manipulating matrix assignments."""
        # Add some assignments
        coordinator_data_fixture.matrix_assignments["Living Room RX"] = "Apple TV"
        coordinator_data_fixture.matrix_assignments["Bedroom RX"] = "Cable Box"

        assert len(coordinator_data_fixture.matrix_assignments) == 2
        assert coordinator_data_fixture.matrix_assignments["Living Room RX"] == "Apple TV"
        assert coordinator_data_fixture.matrix_assignments["Bedroom RX"] == "Cable Box"

        # Update an assignment
        coordinator_data_fixture.matrix_assignments["Living Room RX"] = "PlayStation"
        assert coordinator_data_fixture.matrix_assignments["Living Room RX"] == "PlayStation"

        # Remove an assignment
        del coordinator_data_fixture.matrix_assignments["Bedroom RX"]
        assert len(coordinator_data_fixture.matrix_assignments) == 1
        assert "Bedroom RX" not in coordinator_data_fixture.matrix_assignments
