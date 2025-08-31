"""Global test configuration and fixtures."""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Ensure the custom_components directory is in the path
custom_components_path = project_root / "custom_components"
if custom_components_path.exists():
    sys.path.insert(0, str(custom_components_path.parent))

# Import all fixtures from _fixtures.py to make them available globally
from tests.custom_components.wyrestorm_networkhd._fixtures import *  # noqa: E402, F401, F403
