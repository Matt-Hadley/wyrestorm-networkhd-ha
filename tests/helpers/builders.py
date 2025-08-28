"""Test data builders and setup utilities."""

import random
from typing import Any
from unittest.mock import AsyncMock, Mock


class TestDataBuilder:
    """Builder for creating test data structures."""

    @staticmethod
    def create_device_data(
        device_id: str | None = None,
        device_type: str = "encoder",
        model: str | None = None,
        online: bool = True,
        ip_address: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Create device data dictionary for testing."""
        if device_id is None:
            device_id = f"test_{device_type}_{random.randint(1, 999)}"

        if model is None:
            model_map = {"encoder": "NHD-TX", "decoder": "NHD-RX", "controller": "NHD-CONTROLLER"}
            model = model_map.get(device_type, "NHD-DEVICE")

        if ip_address is None:
            ip_address = f"192.168.1.{random.randint(10, 250)}"

        base_data = {
            "device_id": device_id,
            "type": device_type,
            "model": model,
            "online": online,
            "ip_address": ip_address,
            "firmware_version": f"2.{random.randint(0, 9)}.{random.randint(0, 9)}",
            "mac_address": (
                f"00:11:22:{random.randint(10, 99):02x}:{random.randint(10, 99):02x}:{random.randint(10, 99):02x}"
            ),
        }

        # Add device-specific defaults
        if device_type == "encoder":
            base_data.update(
                {
                    "video_inputs": kwargs.get("video_inputs", 1),
                    "video_outputs": kwargs.get("video_outputs", 0),
                    "audio_inputs": kwargs.get("audio_inputs", 1),
                    "audio_outputs": kwargs.get("audio_outputs", 0),
                    "hdmi_in_active": kwargs.get("hdmi_in_active", True),
                }
            )
        elif device_type == "decoder":
            base_data.update(
                {
                    "video_inputs": kwargs.get("video_inputs", 0),
                    "video_outputs": kwargs.get("video_outputs", 1),
                    "audio_inputs": kwargs.get("audio_inputs", 0),
                    "audio_outputs": kwargs.get("audio_outputs", 1),
                    "hdmi_out_active": kwargs.get("hdmi_out_active", True),
                    "current_source": kwargs.get("current_source"),
                }
            )
        elif device_type == "controller":
            base_data.update(
                {
                    "total_devices": kwargs.get("total_devices", 10),
                    "online_devices": kwargs.get("online_devices", 8),
                }
            )

        # Merge any additional kwargs
        base_data.update({k: v for k, v in kwargs.items() if k not in base_data})

        return base_data

    @staticmethod
    def create_coordinator_data(
        num_encoders: int = 2, num_decoders: int = 2, num_controllers: int = 1, **kwargs
    ) -> dict[str, Any]:
        """Create realistic coordinator data with multiple devices."""
        devices = {}

        # Add encoders
        for i in range(num_encoders):
            device_id = f"encoder{i + 1}"
            devices[device_id] = TestDataBuilder.create_device_data(
                device_id=device_id, device_type="encoder", **kwargs
            )

        # Add decoders
        for i in range(num_decoders):
            device_id = f"decoder{i + 1}"
            devices[device_id] = TestDataBuilder.create_device_data(
                device_id=device_id, device_type="decoder", **kwargs
            )

        # Add controllers
        for i in range(num_controllers):
            device_id = f"controller{i + 1}"
            devices[device_id] = TestDataBuilder.create_device_data(
                device_id=device_id, device_type="controller", **kwargs
            )

        return {
            "devices": devices,
            "system_info": {
                "firmware_version": f"2.{random.randint(0, 9)}.{random.randint(0, 9)}",
                "uptime": random.randint(1000, 86400),
                "total_devices": len(devices),
                "online_devices": sum(1 for d in devices.values() if d.get("online", False)),
            },
            **kwargs,
        }

    @staticmethod
    def create_error_scenarios() -> list[dict[str, Any]]:
        """Create various error scenarios for testing."""
        return [
            {"network_timeout": True, "description": "Network timeout error"},
            {"connection_refused": True, "description": "Connection refused error"},
            {
                "authentication_failed": True,
                "description": "Authentication failed error",
            },
            {"device_not_found": True, "description": "Device not found error"},
            {"invalid_command": True, "description": "Invalid command error"},
            {"partial_data": True, "description": "Partial data received error"},
            {"malformed_response": True, "description": "Malformed response error"},
        ]


class MockSetup:
    """Common mock setup utilities for tests."""

    @staticmethod
    def create_mock_hass() -> Mock:
        """Create a mock Home Assistant instance."""
        hass = Mock()
        hass.data = {}
        return hass

    @staticmethod
    def create_mock_config_entry(
        entry_id: str = "test_entry",
        host: str = "192.168.1.10",
        port: int = 10022,
        username: str = "wyrestorm",
        password: str = "networkhd",
    ) -> Mock:
        """Create a mock config entry."""
        config_entry = Mock()
        config_entry.entry_id = entry_id
        config_entry.data = {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
        }
        config_entry.options = {}
        return config_entry

    @staticmethod
    def create_mock_device_registry() -> Mock:
        """Create a mock device registry."""
        mock_device_reg = Mock()
        mock_device_reg.async_get_or_create.return_value = Mock(id="controller_device")
        return mock_device_reg

    @staticmethod
    def create_mock_network_client() -> Mock:
        """Create a mock network client."""
        mock_client = Mock()
        mock_client.connect = AsyncMock()
        return mock_client

    @staticmethod
    def create_mock_api() -> Mock:
        """Create a mock API instance."""
        mock_api = Mock()
        mock_api.api_query = Mock()
        mock_api.api_query.config_get_version = AsyncMock(return_value="1.2.3")
        return mock_api

    @staticmethod
    def create_mock_coordinator(
        host: str = "192.168.1.10",
        ready: bool = True,
        errors: bool = False,
        data: dict[str, Any] | None = None,
    ) -> Mock:
        """Create a mock coordinator with consistent interface."""
        if data is None:
            data = TestDataBuilder.create_coordinator_data()

        coordinator = Mock()
        coordinator.host = host
        coordinator.is_ready.return_value = ready
        coordinator.has_errors.return_value = errors
        coordinator.data = data
        coordinator.async_setup = AsyncMock()
        coordinator.async_shutdown = AsyncMock()
        coordinator.wait_for_data = AsyncMock(return_value=True)
        return coordinator
