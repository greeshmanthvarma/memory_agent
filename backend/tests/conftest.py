import sys
import os
from unittest.mock import MagicMock

# Set dummy env vars before any app modules are imported.
# Module-level code in database.py and qdrant_service.py calls
# create_async_engine(DATABASE_URL) and QdrantClient(url=QDRANT_URL)
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/testdb")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("QDRANT_API_KEY", "test-key")

# Mock heavy dependencies not needed for unit tests.
sys.modules["haystack_integrations"] = MagicMock()
sys.modules["haystack_integrations.components"] = MagicMock()
sys.modules["haystack_integrations.components.embedders"] = MagicMock()
sys.modules["haystack_integrations.components.embedders.fastembed"] = MagicMock()
sys.modules["haystack"] = MagicMock()
sys.modules["haystack.dataclasses"] = MagicMock()
