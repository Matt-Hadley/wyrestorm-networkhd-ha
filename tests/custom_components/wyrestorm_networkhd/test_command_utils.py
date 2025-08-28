"""Test command utilities for WyreStorm NetworkHD integration."""

import logging
from unittest.mock import Mock

import pytest

from custom_components.wyrestorm_networkhd._command_utils import safe_device_command


class TestSafeDeviceCommand:
    """Test safe_device_command decorator."""

    @pytest.mark.asyncio
    async def test_successful_command(self):
        """Test successful command execution with logging."""
        logger = Mock(spec=logging.Logger)
        device_id = "test_device"
        command_name = "test_command"

        @safe_device_command(logger, device_id, command_name)
        async def test_func():
            return "success"

        result = await test_func()

        assert result == "success"
        logger.info.assert_any_call("Sending %s command to %s", command_name, device_id)
        logger.info.assert_any_call("%s command sent successfully to %s", command_name, device_id)
        logger.error.assert_not_called()

    @pytest.mark.asyncio
    async def test_failed_command(self):
        """Test failed command execution with error logging."""
        logger = Mock(spec=logging.Logger)
        device_id = "test_device"
        command_name = "test_command"
        test_error = Exception("Test error")

        @safe_device_command(logger, device_id, command_name)
        async def test_func():
            raise test_error

        with pytest.raises(Exception) as exc_info:
            await test_func()

        assert exc_info.value == test_error
        logger.info.assert_called_once_with("Sending %s command to %s", command_name, device_id)
        logger.error.assert_called_once_with("Failed to send %s command to %s: %s", command_name, device_id, test_error)

    @pytest.mark.asyncio
    async def test_command_with_args_and_kwargs(self):
        """Test command execution with arguments and keyword arguments."""
        logger = Mock(spec=logging.Logger)
        device_id = "test_device"
        command_name = "power_control"

        @safe_device_command(logger, device_id, command_name)
        async def test_func(power_state, device=None):
            return f"Set {device} to {power_state}"

        result = await test_func("on", device="decoder1")

        assert result == "Set decoder1 to on"
        logger.info.assert_any_call("Sending %s command to %s", command_name, device_id)
        logger.info.assert_any_call("%s command sent successfully to %s", command_name, device_id)

    @pytest.mark.asyncio
    async def test_specific_error_types(self):
        """Test handling of specific error types."""
        logger = Mock(spec=logging.Logger)
        device_id = "test_device"
        command_name = "matrix_set"

        # Test with NetworkHDError
        from wyrestorm_networkhd.exceptions import NetworkHDError

        network_error = NetworkHDError("Connection failed")

        @safe_device_command(logger, device_id, command_name)
        async def test_network_error():
            raise network_error

        with pytest.raises(NetworkHDError):
            await test_network_error()

        logger.error.assert_called_with(
            "Failed to send %s command to %s: %s",
            command_name,
            device_id,
            network_error,
        )

    @pytest.mark.asyncio
    async def test_command_return_none(self):
        """Test command that returns None."""
        logger = Mock(spec=logging.Logger)
        device_id = "controller"
        command_name = "reboot"

        @safe_device_command(logger, device_id, command_name)
        async def test_func():
            # Simulate a command that doesn't return anything
            pass

        result = await test_func()

        assert result is None
        logger.info.assert_any_call("Sending %s command to %s", command_name, device_id)
        logger.info.assert_any_call("%s command sent successfully to %s", command_name, device_id)

    @pytest.mark.asyncio
    async def test_nested_decorator_usage(self):
        """Test using the decorator in a more realistic scenario."""
        logger = Mock(spec=logging.Logger)

        class MockAPI:
            async def set_power(self, device, state):
                if device == "invalid":
                    raise ValueError("Invalid device")
                return f"Power {state} for {device}"

        class MockButton:
            def __init__(self, device_id):
                self.device_id = device_id
                self.api = MockAPI()

            async def async_press(self):
                @safe_device_command(logger, self.device_id, "power on")
                async def _send_command():
                    return await self.api.set_power(self.device_id, "on")

                return await _send_command()

        # Test successful case
        button = MockButton("decoder1")
        result = await button.async_press()

        assert result == "Power on for decoder1"
        assert logger.info.call_count == 2

        # Test error case
        button_error = MockButton("invalid")
        logger.reset_mock()

        with pytest.raises(ValueError):
            await button_error.async_press()

        logger.error.assert_called_once()
        # Check that the correct parameters were passed to the logger
        call_args = logger.error.call_args
        assert call_args[0][0] == "Failed to send %s command to %s: %s"
        assert call_args[0][1] == "power on"
        assert call_args[0][2] == "invalid"
