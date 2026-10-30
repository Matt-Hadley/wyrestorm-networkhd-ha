"""Constants for the WyreStorm NetworkHD integration."""

from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "wyrestorm_networkhd"

CONF_UPDATE_INTERVAL: Final = "update_interval"  # Polling frequency in seconds (entry option)
CONF_HOST_KEY_FINGERPRINT: Final = "host_key_fingerprint"  # Pinned SSH host key fingerprint(s), list in entry data

# Default connection values
DEFAULT_PORT: Final = 10022  # WyreStorm standard SSH port
DEFAULT_USERNAME: Final = "wyrestorm"  # Factory default SSH username
DEFAULT_PASSWORD: Final = "networkhd"  # Factory default SSH password  # nosec B105
DEFAULT_UPDATE_INTERVAL: Final = 60  # Fallback poll; changes are pushed by controller notifications

# SSH Security Settings
SSH_HOST_KEY_POLICY: Final = "auto_add"  # Accept unknown host keys unless a fingerprint is pinned

PLATFORMS: Final = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.SELECT]

# Services
SERVICE_MATRIX_SET: Final = "matrix_set"  # Route video from source to receivers
SERVICE_POWER_CONTROL: Final = "power_control"  # Control display power via CEC/RS232/IR

# Service fields
ATTR_CONFIG_ENTRY_ID: Final = "config_entry_id"  # Controller to act on (optional)
ATTR_SOURCE_DEVICE: Final = "source_device"  # Transmitter alias or true name; omitted = disconnect
ATTR_TARGET_DEVICE: Final = "target_device"  # Receiver alias(es) or true name(s)
ATTR_DEVICES: Final = "devices"  # Receiver alias(es) or true name(s)
ATTR_POWER_STATE: Final = "power_state"
