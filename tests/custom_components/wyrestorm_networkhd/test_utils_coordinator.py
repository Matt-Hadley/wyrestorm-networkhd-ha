"""Unit tests for coordinator utility functions.

This module tests utility functions that support the WyreStorm NetworkHD
coordinator, including device collection building and matrix assignment processing.

Test Categories:
    - Device Collection Building
    - Matrix Assignment Processing
    - Integration Scenarios
    - Error Handling and Edge Cases
"""

from wyrestorm_networkhd.models.api_query import DeviceInfo, DeviceStatus

from custom_components.wyrestorm_networkhd._utils_coordinator import (
    build_device_collections,
    process_matrix_assignments,
)
from custom_components.wyrestorm_networkhd.models.device_receiver_transmitter import (
    DeviceReceiver,
    DeviceTransmitter,
)

from ._fixtures import *  # noqa: F403, F401


class TestBuildDeviceCollections:
    """Test the build_device_collections utility function.

    This function builds dictionaries of transmitter and receiver devices
    from WyreStorm API response data.
    """

    # =============================================================================
    # Basic Functionality Tests
    # =============================================================================

    def test_empty_input_lists_return_empty_collections(self):
        """Verify empty inputs produce empty device collections.

        Tests that the function handles empty lists gracefully and returns
        empty dictionaries rather than None or raising exceptions.
        """
        transmitters, receivers = build_device_collections([], [], [])

        assert transmitters == {}
        assert receivers == {}
        assert isinstance(transmitters, dict)
        assert isinstance(receivers, dict)

    def test_single_receiver_device_processing(
        self,
        device_json_receiver_fixture,
        device_status_receiver_fixture,
        device_info_receiver_fixture,
    ):
        """Verify correct processing of a single receiver device.

        Tests that a receiver device is properly created and placed in the
        receivers dictionary while transmitters remains empty.
        """
        device_json_list = [device_json_receiver_fixture]
        device_status_list = [device_status_receiver_fixture]
        device_info_list = [device_info_receiver_fixture]

        transmitters, receivers = build_device_collections(device_json_list, device_status_list, device_info_list)

        # Verify receiver was created and transmitters is empty
        assert transmitters == {}
        assert len(receivers) == 1
        assert device_json_receiver_fixture.trueName in receivers

        # Verify receiver properties
        device = receivers[device_json_receiver_fixture.trueName]
        assert isinstance(device, DeviceReceiver)
        assert device.alias_name == device_json_receiver_fixture.aliasName
        assert device.true_name == device_json_receiver_fixture.trueName

    def test_single_transmitter_device_processing(
        self,
        device_json_transmitter_fixture,
        device_status_transmitter_fixture,
        device_info_transmitter_fixture,
    ):
        """Verify correct processing of a single transmitter device.

        Tests that a transmitter device is properly created and placed in the
        transmitters dictionary while receivers remains empty.
        """
        device_json_list = [device_json_transmitter_fixture]
        device_status_list = [device_status_transmitter_fixture]
        device_info_list = [device_info_transmitter_fixture]

        transmitters, receivers = build_device_collections(device_json_list, device_status_list, device_info_list)

        # Verify transmitter was created and receivers is empty
        assert receivers == {}
        assert len(transmitters) == 1
        assert device_json_transmitter_fixture.trueName in transmitters

        # Verify transmitter properties
        device = transmitters[device_json_transmitter_fixture.trueName]
        assert isinstance(device, DeviceTransmitter)
        assert device.alias_name == device_json_transmitter_fixture.aliasName
        assert device.true_name == device_json_transmitter_fixture.trueName

    def test_mixed_device_types_processing(
        self,
        device_json_receiver_fixture,
        device_json_transmitter_fixture,
        device_status_receiver_fixture,
        device_status_transmitter_fixture,
        device_info_receiver_fixture,
        device_info_transmitter_fixture,
    ):
        """Verify correct processing of mixed device types.

        Tests that both receivers and transmitters are properly sorted
        into their respective dictionaries when processed together.
        """
        device_json_list = [
            device_json_receiver_fixture,
            device_json_transmitter_fixture,
        ]
        device_status_list = [
            device_status_receiver_fixture,
            device_status_transmitter_fixture,
        ]
        device_info_list = [
            device_info_receiver_fixture,
            device_info_transmitter_fixture,
        ]

        transmitters, receivers = build_device_collections(device_json_list, device_status_list, device_info_list)

        # Verify both collections have devices
        assert len(transmitters) == 1
        assert len(receivers) == 1

        # Verify receiver is in correct collection
        assert device_json_receiver_fixture.trueName in receivers
        receiver = receivers[device_json_receiver_fixture.trueName]
        assert isinstance(receiver, DeviceReceiver)

        # Verify transmitter is in correct collection
        assert device_json_transmitter_fixture.trueName in transmitters
        transmitter = transmitters[device_json_transmitter_fixture.trueName]
        assert isinstance(transmitter, DeviceTransmitter)

    # =============================================================================
    # Data Matching and Error Handling Tests
    # =============================================================================

    def test_devices_without_status_or_info_are_kept(self, device_json_incomplete_fixture):
        """Devices the controller reports no status/info for (offline) are kept, without that data."""
        transmitters, receivers = build_device_collections([device_json_incomplete_fixture], [], [])

        assert transmitters == {}
        receiver = receivers["INCOMPLETE-RX-01"]
        assert receiver.alias_name == "Incomplete Device"
        assert receiver.mac is None
        assert receiver.hdmi_out_frame_rate is None

    def test_union_of_sources(
        self,
        device_json_complete_fixture,
        device_status_complete_fixture,
        device_info_complete_fixture,
        device_json_orphan_fixture,
    ):
        """Every device in any source is created; missing data stays None."""
        transmitters, receivers = build_device_collections(
            [device_json_complete_fixture, device_json_orphan_fixture],
            [device_status_complete_fixture],
            [device_info_complete_fixture],
        )

        assert receivers["COMPLETE-RX-01"].mac == "00:00:00:00:00:00"
        assert transmitters["ORPHAN-TX-01"].mac is None

    def test_status_only_device_type_inferred_from_name(self):
        """A device only in status/info gets its type from its true name; unknown types are skipped."""
        transmitters, receivers = build_device_collections(
            [],
            [DeviceStatus(aliasname="Src", name="NHD-400-TX-AA"), DeviceStatus(aliasname="X", name="NHD-600-TRX-AA")],
            [DeviceInfo(aliasname="Disp", name="NHD-400-RX-BB", ip4addr="192.0.2.5")],
        )

        assert transmitters["NHD-400-TX-AA"].alias_name == "Src"
        assert transmitters["NHD-400-TX-AA"].online is True
        assert receivers["NHD-400-RX-BB"].ip == "192.0.2.5"
        assert len(transmitters) + len(receivers) == 2

    def test_invalid_device_type_is_skipped(
        self, device_json_invalid_type_fixture, device_status_invalid_fixture, device_info_invalid_fixture
    ):
        """Verify devices with invalid types are skipped gracefully.

        Tests that the function handles invalid device types without
        raising exceptions, simply excluding them from output.
        """
        transmitters, receivers = build_device_collections(
            [device_json_invalid_type_fixture], [device_status_invalid_fixture], [device_info_invalid_fixture]
        )

        # Invalid device should be skipped
        assert transmitters == {}
        assert receivers == {}


class TestProcessMatrixAssignments:
    """Test the process_matrix_assignments utility function.

    This function processes matrix routing assignments from the API,
    creating a mapping of receiver aliases to their assigned transmitters.
    """

    # =============================================================================
    # Basic Functionality Tests
    # =============================================================================

    def test_empty_or_none_matrix_returns_empty_dict(self):
        """Verify empty or None matrix data returns empty dictionary.

        Tests that the function handles missing matrix data gracefully
        without raising exceptions.
        """
        # Test with None
        result = process_matrix_assignments(None)
        assert result == {}

        # Test with empty list
        result = process_matrix_assignments([])
        assert result == {}

    def test_single_assignment_processing(self, single_matrix_assignment_fixture):
        """Verify correct processing of a single matrix assignment.

        Tests that a single receiver-to-transmitter assignment is
        properly converted to a dictionary entry.
        """
        result = process_matrix_assignments(single_matrix_assignment_fixture)

        assert result == {"Living Room RX": "Apple TV"}
        assert len(result) == 1

    def test_multiple_assignments_processing(self, multiple_matrix_assignments_fixture):
        """Verify correct processing of multiple matrix assignments.

        Tests that multiple assignments are all properly included
        in the output dictionary.
        """
        result = process_matrix_assignments(multiple_matrix_assignments_fixture)

        expected = {
            "Living Room RX": "Apple TV",
            "Bedroom RX": "Cable Box",
            "Kitchen RX": "Streaming Device",
        }
        assert result == expected
        assert len(result) == 3

    # =============================================================================
    # Edge Cases and Special Scenarios
    # =============================================================================

    def test_assignments_with_none_values_are_included(self, matrix_with_none_values_fixture):
        """Verify assignments with None values are preserved.

        Tests that None transmitter assignments (unconnected receivers)
        are included in the output for proper state representation.
        """
        result = process_matrix_assignments(matrix_with_none_values_fixture)

        # All assignments should be included, even with None values
        expected = {"Living Room RX": "Apple TV", "Bedroom RX": None, None: "Orphan TX"}
        assert result == expected
        assert len(result) == 3

    def test_empty_string_assignments_are_preserved(self, matrix_with_empty_strings_fixture):
        """Verify assignments with empty strings are preserved.

        Tests that empty string values are maintained rather than
        being converted to None or excluded.
        """
        result = process_matrix_assignments(matrix_with_empty_strings_fixture)

        # All assignments should be preserved as-is
        expected = {
            "Living Room RX": "Apple TV",
            "Bedroom RX": "",
            "": "Orphan TX",
            "Kitchen RX": "   ",
        }
        assert result == expected
        assert len(result) == 4

    def test_duplicate_receivers_last_assignment_wins(self, matrix_duplicate_receivers_fixture):
        """Verify later assignments override earlier ones for same receiver.

        Tests that when a receiver appears multiple times in assignments,
        the last assignment takes precedence.
        """
        result = process_matrix_assignments(matrix_duplicate_receivers_fixture)

        # Should have the last assignment
        assert result == {"Living Room RX": "Cable Box"}
        assert len(result) == 1

    def test_mixed_valid_and_invalid_assignments(self, matrix_mixed_valid_invalid_fixture):
        """Verify all assignments are processed regardless of validity.

        Tests that the function includes all assignments without filtering,
        leaving validation to higher-level code.
        """
        result = process_matrix_assignments(matrix_mixed_valid_invalid_fixture)

        # All assignments should be included
        expected = {
            "Valid RX 1": "Valid TX 1",
            "Valid RX 2": "Valid TX 2",
            "": "Invalid TX",
            "Invalid RX": "",
            None: "Invalid TX 2",
            "Invalid RX 2": None,
            "Valid RX 3": "Valid TX 3",
        }
        assert result == expected
        assert len(result) == 7


class TestIntegrationScenarios:
    """Test realistic integration scenarios combining both utility functions."""

    def test_complete_system_with_devices_and_matrix(
        self,
        device_json_receiver_fixture,
        device_json_transmitter_fixture,
        device_status_receiver_fixture,
        device_status_transmitter_fixture,
        device_info_receiver_fixture,
        device_info_transmitter_fixture,
    ):
        """Verify complete system setup with devices and matrix routing.

        Tests a realistic scenario where devices are created and then
        matrix assignments connect them together.
        """
        # Build device collections
        device_json_list = [
            device_json_receiver_fixture,
            device_json_transmitter_fixture,
        ]
        device_status_list = [
            device_status_receiver_fixture,
            device_status_transmitter_fixture,
        ]
        device_info_list = [
            device_info_receiver_fixture,
            device_info_transmitter_fixture,
        ]

        transmitters, receivers = build_device_collections(device_json_list, device_status_list, device_info_list)

        # Create matrix assignments linking the devices
        from wyrestorm_networkhd.models.api_query import Matrix, MatrixAssignment

        matrix = Matrix(
            assignments=[
                MatrixAssignment(
                    rx=device_json_receiver_fixture.aliasName,
                    tx=device_json_transmitter_fixture.aliasName,
                )
            ]
        )

        assignments = process_matrix_assignments(matrix)

        # Verify complete system state
        assert len(transmitters) == 1
        assert len(receivers) == 1
        assert len(assignments) == 1

        receiver_name = device_json_receiver_fixture.aliasName
        transmitter_name = device_json_transmitter_fixture.aliasName

        assert receiver_name in assignments
        assert assignments[receiver_name] == transmitter_name

    def test_system_with_unconnected_devices(
        self,
        multi_device_system_json_fixtures,
        multi_device_system_status_fixtures,
        multi_device_system_info_fixtures,
        partial_connection_matrix_fixture,
    ):
        """Verify handling of devices not connected in the matrix.

        Tests a scenario where some devices exist but are not connected
        through matrix assignments, representing standby equipment.
        """
        transmitters, receivers = build_device_collections(
            multi_device_system_json_fixtures, multi_device_system_status_fixtures, multi_device_system_info_fixtures
        )
        assignments = process_matrix_assignments(partial_connection_matrix_fixture)

        # Verify devices are created but only one is connected
        assert len(transmitters) == 1
        assert len(receivers) == 2
        assert len(assignments) == 1

        assert "TX-01" in transmitters
        assert "RX-01" in receivers
        assert "RX-02" in receivers
        assert assignments["Living Room RX"] == "Apple TV"

        # Bedroom RX should not be in assignments
        assert "Bedroom RX" not in assignments
