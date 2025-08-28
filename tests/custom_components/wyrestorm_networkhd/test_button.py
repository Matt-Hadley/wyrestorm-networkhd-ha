"""Test button platform for WyreStorm NetworkHD integration.

This module consolidates all button-related tests through imports.
Individual test components are organized in separate files:
- test_button_setup.py: Platform setup tests
- test_button_reboot.py: Reboot button tests
- test_button_sink_power.py: Sink power button tests
"""

# Import all test classes to make them discoverable by pytest
from tests.custom_components.wyrestorm_networkhd.test_button_reboot import *  # noqa: F401,F403
from tests.custom_components.wyrestorm_networkhd.test_button_setup import *  # noqa: F401,F403
from tests.custom_components.wyrestorm_networkhd.test_button_sink_power import *  # noqa: F401,F403
