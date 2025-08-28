"""Test select platform for WyreStorm NetworkHD integration.

This module consolidates all select tests through imports.
Individual test components are organized in separate files:
- test_select_setup.py: Platform setup tests
- test_select_source.py: Source selection entity tests
"""

# Import all test classes to make them discoverable by pytest
from tests.custom_components.wyrestorm_networkhd.test_select_setup import *  # noqa: F401,F403
from tests.custom_components.wyrestorm_networkhd.test_select_source import *  # noqa: F401,F403
