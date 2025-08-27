"""Command and communication utilities for WyreStorm NetworkHD integration."""
from __future__ import annotations

import logging
from typing import Any


def safe_device_command(logger: logging.Logger, device_id: str, command_name: str):
    """Decorator for safe device command execution with logging.
    
    Args:
        logger: Logger instance to use
        device_id: Device identifier for logging
        command_name: Name of the command being executed
    
    Returns:
        Decorator function
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                logger.info("Sending %s command to %s", command_name, device_id)
                result = await func(*args, **kwargs)
                logger.info("%s command sent successfully to %s", command_name, device_id)
                return result
            except Exception as err:
                logger.error("Failed to send %s command to %s: %s", command_name, device_id, err)
                raise
        return wrapper
    return decorator