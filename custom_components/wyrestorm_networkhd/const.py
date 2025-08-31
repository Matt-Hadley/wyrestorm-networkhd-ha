"""Constants for the WyreStorm NetworkHD integration."""

from typing import Final

# Integration metadata
DOMAIN = "wyrestorm_networkhd"  # Home Assistant domain identifier
NAME = "WyreStorm NetworkHD"  # Display name in Home Assistant UI
VERSION = "2.0.0"  # Integration version

# Configuration keys (used in config flow and data storage)
CONF_HOST = "host"  # IP address or hostname of NetworkHD controller
CONF_PORT = "port"  # SSH port number (typically 10022 for WyreStorm)
CONF_USERNAME = "username"  # SSH username for device authentication
CONF_PASSWORD = "password"  # SSH password for device authentication  # nosec B105
CONF_UPDATE_INTERVAL = "update_interval"  # Polling frequency in seconds

# Default connection values
DEFAULT_PORT = 10022  # WyreStorm standard SSH port
DEFAULT_USERNAME = "wyrestorm"  # Factory default SSH username
DEFAULT_PASSWORD = "networkhd"  # Factory default SSH password (SECURITY: Change in production!)  # nosec B105
DEFAULT_UPDATE_INTERVAL = 60  # Poll device every 60 seconds for status updates

# SSH Security Settings
SSH_HOST_KEY_POLICY = "auto_add"  # Accept unknown host keys (convenience over strict security)

# Platforms supported by this integration (entity types that will be created)
PLATFORMS: Final = ["binary_sensor", "button", "select"]

# Device classes (used for Home Assistant device categorization)
DEVICE_CLASS_TRANSMITTER: Final = "transmitter"  # Video source devices (encoders)
DEVICE_CLASS_RECEIVER: Final = "receiver"  # Video destination devices (decoders)
DEVICE_CLASS_CONTROLLER: Final = "controller"  # Matrix switching controller unit

# Service identifiers (custom services exposed to Home Assistant)
SERVICE_MATRIX_SET: Final = "matrix_set"  # Route video from source to destination
SERVICE_POWER_CONTROL: Final = "power_control"  # Control display power via CEC/RS232/IR

# Service attribute names (parameters for custom services)
ATTR_SOURCE_DEVICE: Final = "source_device"  # Source device alias for matrix routing
ATTR_TARGET_DEVICE: Final = "target_device"  # Target device alias for matrix routing
ATTR_DEVICES: Final = "devices"  # List of devices for bulk operations
