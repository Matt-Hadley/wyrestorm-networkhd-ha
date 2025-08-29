"""Constants for the WyreStorm NetworkHD 2 integration."""

from typing import Final

# Integration metadata
DOMAIN = "wyrestorm_networkhd_2"
NAME = "WyreStorm NetworkHD 2"
VERSION = "2.0.0"

# Configuration keys
CONF_HOST = "host"
CONF_PORT = "port"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_SSH_TIMEOUT = "ssh_timeout"

# Default values
DEFAULT_PORT = 10022
DEFAULT_USERNAME = "wyrestorm"
DEFAULT_PASSWORD = "networkhd"  # WARNING: Change default credentials for security
DEFAULT_UPDATE_INTERVAL = 60  # Default to 60 seconds
DEFAULT_SSH_TIMEOUT = 10  # Default SSH timeout in seconds

# SSH Security Settings
SSH_HOST_KEY_POLICY = "auto_add"  # Auto-add host keys with warning for usability

# Platforms supported by this integration
PLATFORMS: Final = ["binary_sensor", "button", "select"]

# Device classes
DEVICE_CLASS_TRANSMITTER: Final = "transmitter"
DEVICE_CLASS_RECEIVER: Final = "receiver"
DEVICE_CLASS_CONTROLLER: Final = "controller"

# Services
SERVICE_MATRIX_SET: Final = "matrix_set"
SERVICE_POWER_CONTROL: Final = "power_control"

# Service attributes
ATTR_SOURCE_DEVICE: Final = "source_device"
ATTR_TARGET_DEVICE: Final = "target_device"
ATTR_DEVICES: Final = "devices"