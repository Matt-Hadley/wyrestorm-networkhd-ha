"""Test binary sensor platform for WyreStorm NetworkHD integration.

This module consolidates all binary sensor tests through imports.
Individual test components are organized in separate files:
- test_binary_sensor_setup.py: Platform setup tests
- test_binary_sensor_online.py: Online status sensor tests
- test_binary_sensor_video.py: Video input/output sensor tests
"""

# Import all test classes to make them discoverable by pytest
from tests.custom_components.wyrestorm_networkhd.test_binary_sensor_online import *  # noqa: F401,F403
from tests.custom_components.wyrestorm_networkhd.test_binary_sensor_setup import *  # noqa: F401,F403
from tests.custom_components.wyrestorm_networkhd.test_binary_sensor_video import *  # noqa: F401,F403
