"""Tests for the Newsletter Monitor component."""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, UTC

from agents.newsletter_monitor import (
    NewsletterMonitor,
    Newsletter,
    NewsletterMonitorResult
)
from processing.gmail.client import GmailClient
from processing.embedchain_store import EmbedchainStore
from processing.gmail.exceptions import FetchError

class MockGmailClient(GmailClient):
    """Mock Gmail client that inherits from the real class."""
    def __init__(self):
        pass

    def get_newsletters(self, max_results=10):
        return [
            {
                'email_id': 'test123',
                'subject': 'AI Newsletter #1',
                'received_date': 'Thu, 15 Feb 2024 10:00:00 GMT',
                'content': 'Test newsletter content',
                'metadata': {
                    'thread_id': 'thread123',
                    'label_ids': ['Label_123']
                }
            }
        ]

class MockEmbedchainStore(EmbedchainStore):
    """Mock Embedchain store that inherits from the real class."""
    def __init__(self):
        pass

    async def load_and_store_newsletters(self, max_results=10):
        return ['vector123']

@pytest.fixture
def mock_gmail_client():
    """Create a mock Gmail client."""
    return MockGmailClient()

@pytest.fixture
def mock_embedchain_store():
    """Create a mock Embedchain store."""
    return MockEmbedchainStore()

@pytest.fixture
def newsletter_monitor(mock_gmail_client, mock_embedchain_store):
    """Create a NewsletterMonitor instance."""
    return NewsletterMonitor(mock_gmail_client, mock_embedchain_store)

class TestNewsletterMonitor:
    """Test suite for NewsletterMonitor."""

    def test_newsletter_model(self):
        """Test Newsletter model validation."""
        newsletter = Newsletter(
            email_id='test123',
            subject='Test Newsletter',
            received_date='2024-02-15T10:00:00Z',
            content='Test content'
        )
        assert newsletter.email_id == 'test123'
        assert newsletter.vector_id is None
        assert newsletter.processed_date is None

    @pytest.mark.asyncio
    async def test_fetch_newsletters_success(self, newsletter_monitor):
        """Test successful newsletter fetching."""
        newsletters = await newsletter_monitor.fetch_newsletters(max_results=1)
        
        assert len(newsletters) == 1
        assert newsletters[0].email_id == 'test123'
        assert newsletters[0].subject == 'AI Newsletter #1'
        assert newsletter_monitor.queue_size == 1

    @pytest.mark.asyncio
    async def test_fetch_newsletters_error(self, newsletter_monitor, mock_gmail_client):
        """Test error handling during newsletter fetching."""
        # Mock fetch error
        mock_gmail_client.get_newsletters = Mock(side_effect=FetchError("API error"))
        
        with pytest.raises(FetchError):
            await newsletter_monitor.fetch_newsletters()
        
        assert newsletter_monitor.error_count == 1
        assert newsletter_monitor.queue_size == 0

    @pytest.mark.asyncio
    async def test_process_newsletters_success(self, newsletter_monitor):
        """Test successful newsletter processing."""
        # First fetch newsletters
        await newsletter_monitor.fetch_newsletters(max_results=1)
        assert newsletter_monitor.queue_size == 1
        
        # Then process them
        processed = await newsletter_monitor.process_newsletters(batch_size=1)
        
        assert len(processed) == 1
        assert processed[0].vector_id == 'vector123'
        assert processed[0].processing_status == 'completed'
        assert newsletter_monitor.processed_count == 1
        assert newsletter_monitor.queue_size == 0

    @pytest.mark.asyncio
    async def test_process_newsletters_error(self, newsletter_monitor, mock_embedchain_store):
        """Test error handling during newsletter processing."""
        # First fetch newsletters
        await newsletter_monitor.fetch_newsletters(max_results=1)
        assert newsletter_monitor.queue_size == 1
        
        # Mock storage error
        mock_embedchain_store.load_and_store_newsletters = AsyncMock(
            side_effect=Exception("Storage error")
        )
        
        with pytest.raises(Exception):
            await newsletter_monitor.process_newsletters()
        
        # Verify newsletter was returned to queue
        assert newsletter_monitor.error_count == 1
        assert newsletter_monitor.queue_size == 1
        queued = newsletter_monitor.get_queued_newsletters()
        assert queued[0].processing_status == 'failed'

    @pytest.mark.asyncio
    async def test_run_complete_pipeline(self, newsletter_monitor):
        """Test running the complete pipeline."""
        result = await newsletter_monitor.run(max_results=1, batch_size=1)
        
        assert isinstance(result, NewsletterMonitorResult)
        assert len(result.newsletters) == 1
        assert result.total_processed == 1
        assert result.queued_count == 0
        assert newsletter_monitor.processed_count == 1
        assert newsletter_monitor.error_count == 0

    @pytest.mark.asyncio
    async def test_run_pipeline_no_newsletters(self, newsletter_monitor, mock_gmail_client):
        """Test pipeline behavior with no newsletters."""
        # Mock empty response
        mock_gmail_client.get_newsletters = Mock(return_value=[])
        
        result = await newsletter_monitor.run()
        
        assert isinstance(result, NewsletterMonitorResult)
        assert len(result.newsletters) == 0
        assert result.total_processed == 0
        assert result.queued_count == 0

    @pytest.mark.asyncio
    async def test_run_pipeline_error(self, newsletter_monitor, mock_gmail_client):
        """Test pipeline error handling."""
        # Mock fetch error
        mock_gmail_client.get_newsletters = Mock(side_effect=FetchError("API error"))
        
        with pytest.raises(Exception):
            await newsletter_monitor.run()
        
        assert newsletter_monitor.error_count == 1
        assert newsletter_monitor.queue_size == 0

    def test_stats_tracking(self, newsletter_monitor):
        """Test statistics tracking."""
        # Simulate some processing
        newsletter_monitor.processed_count = 5
        newsletter_monitor.error_count = 2
        
        stats = newsletter_monitor.get_stats()
        
        assert stats['processed_count'] == 5
        assert stats['error_count'] == 2
        assert stats['queue_size'] == 0

    @pytest.mark.asyncio
    async def test_batch_processing(self, newsletter_monitor, mock_gmail_client):
        """Test processing newsletters in batches."""
        # Mock multiple newsletters
        mock_gmail_client.get_newsletters = Mock(return_value=[
            {
                'email_id': f'test{i}',
                'subject': f'Newsletter {i}',
                'received_date': 'Thu, 15 Feb 2024 10:00:00 GMT',
                'content': f'Content {i}',
                'metadata': {'thread_id': f'thread{i}'}
            }
            for i in range(3)
        ])
        
        # Fetch all newsletters
        await newsletter_monitor.fetch_newsletters(max_results=3)
        assert newsletter_monitor.queue_size == 3
        
        # Process in batches of 2
        batch1 = await newsletter_monitor.process_newsletters(batch_size=2)
        assert len(batch1) == 2
        assert newsletter_monitor.queue_size == 1
        
        batch2 = await newsletter_monitor.process_newsletters(batch_size=2)
        assert len(batch2) == 1
        assert newsletter_monitor.queue_size == 0
        
        assert newsletter_monitor.processed_count == 3
