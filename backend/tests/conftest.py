import sys
from unittest.mock import MagicMock

# Mock heavy haystack dependencies so unit tests don't require them installed.
# The tests mock the actual service calls (search_points_raw etc.) so these modules are never invoked at runtime during testing.
sys.modules["haystack_integrations"] = MagicMock()
sys.modules["haystack_integrations.components"] = MagicMock()
sys.modules["haystack_integrations.components.embedders"] = MagicMock()
sys.modules["haystack_integrations.components.embedders.fastembed"] = MagicMock()
sys.modules["haystack"] = MagicMock()
sys.modules["haystack.dataclasses"] = MagicMock()
