"""Unit tests for CoordinatorData model."""

from datetime import datetime
from unittest.mock import patch

import pytest

from custom_components.wyrestorm_networkhd_2.models.coordinator import CoordinatorData
from custom_components.wyrestorm_networkhd_2.models.device_receiver_transmitter import (
    DeviceReceiver,
    DeviceTransmitter,
)
from ._fixtures import (
    device_controller_fixture,
    device_receiver_fixture,
    device_transmitter_fixture,
    coordinator_data_fixture,
)


class TestCoordinatorData:
    """Tests for CoordinatorData model."""

    def test_init(self, device_controller_fixture):
        """Test initialization of CoordinatorData."""
        coordinator_data = CoordinatorData(device_controller=device_controller_fixture)

        assert coordinator_data.device_controller is device_controller_fixture
        assert coordinator_data.device_transmitters == {}
        assert coordinator_data.device_receivers == {}
        assert coordinator_data.matrix_assignments == {}
        assert isinstance(coordinator_data.last_update, datetime)

    @patch("custom_components.wyrestorm_networkhd_2.models.coordinator.datetime")
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

    def test_update_device_add_receiver(self, coordinator_data_fixture, device_receiver_fixture):
        """Test adding a new receiver with update_device."""
        was_existing = coordinator_data_fixture.update_device(device_receiver_fixture)

        assert was_existing is False  # New device
        assert device_receiver_fixture.true_name in coordinator_data_fixture.device_receivers
        assert coordinator_data_fixture.device_receivers[device_receiver_fixture.true_name] is device_receiver_fixture
        assert len(coordinator_data_fixture.device_transmitters) == 0

    def test_update_device_add_transmitter(self, coordinator_data_fixture, device_transmitter_fixture):
        """Test adding a new transmitter with update_device."""
        was_existing = coordinator_data_fixture.update_device(device_transmitter_fixture)

        assert was_existing is False  # New device
        assert device_transmitter_fixture.true_name in coordinator_data_fixture.device_transmitters
        assert (
            coordinator_data_fixture.device_transmitters[device_transmitter_fixture.true_name]
            is device_transmitter_fixture
        )
        assert len(coordinator_data_fixture.device_receivers) == 0

    def test_update_device_existing_receiver(self, coordinator_data_fixture, device_receiver_fixture):
        """Test updating an existing receiver."""
        # Add the receiver first
        coordinator_data_fixture.update_device(device_receiver_fixture)

        # Create a modified version
        updated_receiver = DeviceReceiver(
            alias_name="Updated Living Room RX",
            true_name=device_receiver_fixture.true_name,  # Same true_name
            device_type="Receiver",
            ip="192.168.1.201",  # Different IP
            online=False,  # Different online status
            sequence=1,
            mac="AA:BB:CC:DD:EE:01",
            gateway="192.168.1.1",
            netmask="255.255.255.0",
            version="1.2.3",
            edid="Custom EDID",
            ip_mode="static",
        )

        was_existing = coordinator_data_fixture.update_device(updated_receiver)

        assert was_existing is True  # Existing device
        assert coordinator_data_fixture.device_receivers[device_receiver_fixture.true_name] is updated_receiver
        assert (
            coordinator_data_fixture.device_receivers[device_receiver_fixture.true_name].alias_name
            == "Updated Living Room RX"
        )
        assert coordinator_data_fixture.device_receivers[device_receiver_fixture.true_name].ip == "192.168.1.201"
        assert coordinator_data_fixture.device_receivers[device_receiver_fixture.true_name].online is False

    @patch("custom_components.wyrestorm_networkhd_2.models.coordinator.datetime")
    def test_update_device_updates_timestamp(self, mock_datetime, coordinator_data_fixture, device_receiver_fixture):
        """Test that update_device updates the timestamp."""
        mock_now = datetime(2023, 1, 1, 13, 0, 0)
        mock_datetime.now.return_value = mock_now

        coordinator_data_fixture.update_device(device_receiver_fixture)

        assert coordinator_data_fixture.last_update == mock_now
        mock_datetime.now.assert_called()

    def test_update_device_invalid_type(self, coordinator_data_fixture):
        """Test update_device with invalid device type."""
        invalid_device = "not a device"

        with pytest.raises(ValueError, match="Unknown device type"):
            coordinator_data_fixture.update_device(invalid_device)

    def test_remove_device_receiver(self, coordinator_data_fixture, device_receiver_fixture):
        """Test removing a receiver device."""
        # Add the receiver first
        coordinator_data_fixture.update_device(device_receiver_fixture)
        assert device_receiver_fixture.true_name in coordinator_data_fixture.device_receivers

        # Remove it
        was_removed = coordinator_data_fixture.remove_device(device_receiver_fixture.true_name)

        assert was_removed is True
        assert device_receiver_fixture.true_name not in coordinator_data_fixture.device_receivers
        assert len(coordinator_data_fixture.device_receivers) == 0

    def test_remove_device_transmitter(self, coordinator_data_fixture, device_transmitter_fixture):
        """Test removing a transmitter device."""
        # Add the transmitter first
        coordinator_data_fixture.update_device(device_transmitter_fixture)
        assert device_transmitter_fixture.true_name in coordinator_data_fixture.device_transmitters

        # Remove it
        was_removed = coordinator_data_fixture.remove_device(device_transmitter_fixture.true_name)

        assert was_removed is True
        assert device_transmitter_fixture.true_name not in coordinator_data_fixture.device_transmitters
        assert len(coordinator_data_fixture.device_transmitters) == 0

    def test_remove_device_not_found(self, coordinator_data_fixture):
        """Test removing a device that doesn't exist."""
        was_removed = coordinator_data_fixture.remove_device("nonexistent-device")

        assert was_removed is False

    @patch("custom_components.wyrestorm_networkhd_2.models.coordinator.datetime")
    def test_remove_device_updates_timestamp_when_successful(
        self, mock_datetime, coordinator_data_fixture, device_receiver_fixture
    ):
        """Test that remove_device updates timestamp when successful."""
        # Add device first
        coordinator_data_fixture.update_device(device_receiver_fixture)

        # Set up mock for removal
        mock_now = datetime(2023, 1, 1, 14, 0, 0)
        mock_datetime.now.return_value = mock_now

        coordinator_data_fixture.remove_device(device_receiver_fixture.true_name)

        assert coordinator_data_fixture.last_update == mock_now
        mock_datetime.now.assert_called()

    @patch("custom_components.wyrestorm_networkhd_2.models.coordinator.datetime")
    def test_remove_device_does_not_update_timestamp_when_not_found(self, mock_datetime, coordinator_data_fixture):
        """Test that remove_device does not update timestamp when device not found."""
        original_timestamp = coordinator_data_fixture.last_update

        coordinator_data_fixture.remove_device("nonexistent-device")

        # Timestamp should not have been updated
        assert coordinator_data_fixture.last_update == original_timestamp
        # datetime.now() should not have been called for the removal
        mock_datetime.now.assert_not_called()

    def test_get_lists_with_devices(
        self, coordinator_data_fixture, device_receiver_fixture, device_transmitter_fixture
    ):
        """Test getting device lists when devices exist."""
        # Add devices
        coordinator_data_fixture.update_device(device_receiver_fixture)
        coordinator_data_fixture.update_device(device_transmitter_fixture)

        receivers = coordinator_data_fixture.get_receivers_list()
        transmitters = coordinator_data_fixture.get_transmitters_list()

        assert len(receivers) == 1
        assert receivers[0] is device_receiver_fixture
        assert len(transmitters) == 1
        assert transmitters[0] is device_transmitter_fixture

    def test_multiple_devices_same_type(self, coordinator_data_fixture):
        """Test managing multiple devices of the same type."""
        receiver1 = DeviceReceiver(
            alias_name="Living Room RX",
            true_name="NHD-200-RX-01",
            device_type="Receiver",
            ip="192.168.1.101",
            online=True,
            sequence=1,
            mac="AA:BB:CC:DD:EE:01",
            gateway="192.168.1.1",
            netmask="255.255.255.0",
            version="1.2.3",
            edid="Custom EDID",
            ip_mode="static",
        )

        receiver2 = DeviceReceiver(
            alias_name="Bedroom RX",
            true_name="NHD-200-RX-02",
            device_type="Receiver",
            ip="192.168.1.103",
            online=True,
            sequence=3,
            mac="AA:BB:CC:DD:EE:03",
            gateway="192.168.1.1",
            netmask="255.255.255.0",
            version="1.2.3",
            edid="Custom EDID",
            ip_mode="static",
        )

        # Add both receivers
        coordinator_data_fixture.update_device(receiver1)
        coordinator_data_fixture.update_device(receiver2)

        receivers = coordinator_data_fixture.get_receivers_list()
        assert len(receivers) == 2
        assert receiver1 in receivers
        assert receiver2 in receivers

        # Remove one
        coordinator_data_fixture.remove_device(receiver1.true_name)
        receivers = coordinator_data_fixture.get_receivers_list()
        assert len(receivers) == 1
        assert receiver2 in receivers
        assert receiver1 not in receivers

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

    def test_update_matrix_assignment_new(self, coordinator_data_fixture):
        """Test adding a new matrix assignment with update_matrix_assignment."""
        was_existing = coordinator_data_fixture.update_matrix_assignment("Living Room RX", "Apple TV")

        assert was_existing is False  # New assignment
        assert coordinator_data_fixture.matrix_assignments["Living Room RX"] == "Apple TV"
        assert len(coordinator_data_fixture.matrix_assignments) == 1

    def test_update_matrix_assignment_existing(self, coordinator_data_fixture):
        """Test updating an existing matrix assignment."""
        # Add initial assignment
        coordinator_data_fixture.matrix_assignments["Living Room RX"] = "Cable Box"

        # Update it
        was_existing = coordinator_data_fixture.update_matrix_assignment("Living Room RX", "Apple TV")

        assert was_existing is True  # Existing assignment
        assert coordinator_data_fixture.matrix_assignments["Living Room RX"] == "Apple TV"
        assert len(coordinator_data_fixture.matrix_assignments) == 1

    @patch("custom_components.wyrestorm_networkhd_2.models.coordinator.datetime")
    def test_update_matrix_assignment_updates_timestamp(self, mock_datetime, coordinator_data_fixture):
        """Test that update_matrix_assignment updates the timestamp."""
        mock_now = datetime(2023, 1, 1, 15, 0, 0)
        mock_datetime.now.return_value = mock_now

        coordinator_data_fixture.update_matrix_assignment("Living Room RX", "Apple TV")

        assert coordinator_data_fixture.last_update == mock_now
        mock_datetime.now.assert_called()

    def test_remove_matrix_assignment_existing(self, coordinator_data_fixture):
        """Test removing an existing matrix assignment."""
        # Add assignment first
        coordinator_data_fixture.matrix_assignments["Living Room RX"] = "Apple TV"
        assert "Living Room RX" in coordinator_data_fixture.matrix_assignments

        # Remove it
        was_removed = coordinator_data_fixture.remove_matrix_assignment("Living Room RX")

        assert was_removed is True
        assert "Living Room RX" not in coordinator_data_fixture.matrix_assignments
        assert len(coordinator_data_fixture.matrix_assignments) == 0

    def test_remove_matrix_assignment_not_found(self, coordinator_data_fixture):
        """Test removing a matrix assignment that doesn't exist."""
        was_removed = coordinator_data_fixture.remove_matrix_assignment("nonexistent-receiver")

        assert was_removed is False
        assert len(coordinator_data_fixture.matrix_assignments) == 0

    @patch("custom_components.wyrestorm_networkhd_2.models.coordinator.datetime")
    def test_remove_matrix_assignment_updates_timestamp_when_successful(self, mock_datetime, coordinator_data_fixture):
        """Test that remove_matrix_assignment updates timestamp when successful."""
        # Add assignment first
        coordinator_data_fixture.matrix_assignments["Living Room RX"] = "Apple TV"

        # Set up mock for removal
        mock_now = datetime(2023, 1, 1, 16, 0, 0)
        mock_datetime.now.return_value = mock_now

        coordinator_data_fixture.remove_matrix_assignment("Living Room RX")

        assert coordinator_data_fixture.last_update == mock_now
        mock_datetime.now.assert_called()

    @patch("custom_components.wyrestorm_networkhd_2.models.coordinator.datetime")
    def test_remove_matrix_assignment_does_not_update_timestamp_when_not_found(
        self, mock_datetime, coordinator_data_fixture
    ):
        """Test that remove_matrix_assignment does not update timestamp when assignment not found."""
        original_timestamp = coordinator_data_fixture.last_update

        coordinator_data_fixture.remove_matrix_assignment("nonexistent-receiver")

        # Timestamp should not have been updated
        assert coordinator_data_fixture.last_update == original_timestamp
        # datetime.now() should not have been called for the removal
        mock_datetime.now.assert_not_called()
