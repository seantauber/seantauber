"""Tests for repository curation with live dependencies."""
import pytest
from agents.repository_curator import RepositoryCurator
from processing.embedchain_store import EmbedchainStore

class TestRepositoryCurationComponent:
    """Tests for repository curation with live dependencies."""
    
    @pytest.fixture
    def repository_curator(self, vector_store: EmbedchainStore) -> RepositoryCurator:
        """Initialize repository curator component."""
        curator = RepositoryCurator(embedchain_store=vector_store)
        yield curator
