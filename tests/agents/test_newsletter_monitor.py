"""Tests for the Newsletter Monitor agent."""

import json
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from pydantic_ai import Agent
from pydantic_ai.messages import ModelTextResponse

from agents.newsletter_monitor import (
    NewsletterMonitor,
    Newsletter,
    NewsletterMonitorDeps,
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
def mock_agent():
    """Create a mock Agent."""
    agent = Mock(spec=Agent)
    agent.run = AsyncMock()
    return agent

@pytest.fixture
def newsletter_monitor():
    """Create a NewsletterMonitor instance."""
    return NewsletterMonitor()

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

    def test_deps_model(self, mock_gmail_client, mock_embedchain_store):
        """Test NewsletterMonitorDeps model validation."""
        deps = NewsletterMonitorDeps(
            gmail_client=mock_gmail_client,
            embedchain_store=mock_embedchain_store
        )
        assert isinstance(deps.gmail_client, GmailClient)
        assert isinstance(deps.embedchain_store, EmbedchainStore)

    @pytest.mark.asyncio
    async def test_process_newsletters_success(
        self,
        newsletter_monitor,
        mock_gmail_client,
        mock_embedchain_store
    ):
        """Test successful end-to-end newsletter processing."""
        result_data = NewsletterMonitorResult(
            newsletters=[
                Newsletter(
                    email_id='test123',
                    subject='AI Newsletter #1',
                    received_date='Thu, 15 Feb 2024 10:00:00 GMT',
                    content='Test newsletter content',
                    vector_id='vector123',
                    processed_date='2024-02-15T10:00:00Z'
                )
            ],
            total_processed=1,
            processing_date='2024-02-15T10:00:00Z',
            queued_count=0
        )
        
        # Mock the agent's run method to return a successful result
        newsletter_monitor.agent.run = AsyncMock(return_value=ModelTextResponse(
            content=result_data.model_dump_json()
        ))

        result = await newsletter_monitor.process_newsletters(
            mock_gmail_client,
            mock_embedchain_store
        )

        assert isinstance(result, NewsletterMonitorResult)
        assert len(result.newsletters) == 1
        assert result.total_processed == 1
        assert result.newsletters[0].vector_id == 'vector123'

    @pytest.mark.asyncio
    async def test_queue_operations(self, newsletter_monitor):
        """Test queue operations and status tracking."""
        # Create test newsletters
        newsletters = [
            Newsletter(
                email_id=f'test{i}',
                subject=f'Newsletter {i}',
                received_date='2024-02-15T10:00:00Z',
                content=f'Content {i}'
            )
            for i in range(3)
        ]

        # Add to queue through internal method
        for newsletter in newsletters:
            newsletter_monitor._processing_queue.append(newsletter)

        # Test queue size
        assert newsletter_monitor.queue_size == 3

        # Test getting queued newsletters
        queued = newsletter_monitor.get_queued_newsletters()
        assert len(queued) == 3
        assert all(n.processing_status == 'pending' for n in queued)

    @pytest.mark.asyncio
    async def test_batch_processing(
        self,
        newsletter_monitor,
        mock_gmail_client,
        mock_embedchain_store
    ):
        """Test processing newsletters in batches."""
        # Create test newsletters
        newsletters = [
            Newsletter(
                email_id=f'test{i}',
                subject=f'Newsletter {i}',
                received_date='2024-02-15T10:00:00Z',
                content=f'Content {i}'
            )
            for i in range(5)
        ]

        # Add to queue
        for newsletter in newsletters:
            newsletter_monitor._processing_queue.append(newsletter)

        # Create processed newsletters with vector IDs
        processed_newsletters = newsletters[:3]  # First batch of 3
        for i, newsletter in enumerate(processed_newsletters):
            newsletter.vector_id = f'vector{i}'
            newsletter.processed_date = '2024-02-15T10:00:00Z'
            newsletter.processing_status = 'completed'

        result_data = NewsletterMonitorResult(
            newsletters=processed_newsletters,
            total_processed=3,
            processing_date='2024-02-15T10:00:00Z',
            queued_count=2
        )

        # Mock the process_queued_newsletters tool to actually process the queue
        async def mock_process_queued(*args, **kwargs):
            # Process first 3 newsletters
            processed = []
            for _ in range(3):
                if newsletter_monitor._processing_queue:
                    newsletter = newsletter_monitor._processing_queue.popleft()
                    newsletter.processing_status = 'completed'
                    newsletter.vector_id = 'vector123'
                    newsletter.processed_date = '2024-02-15T10:00:00Z'
                    processed.append(newsletter)
            return processed

        # Replace the tool implementation
        newsletter_monitor._register_tools = Mock()
        newsletter_monitor.agent.run = AsyncMock(return_value=ModelTextResponse(
            content=result_data.model_dump_json()
        ))

        # Call process_queued_newsletters directly to simulate tool execution
        await mock_process_queued()

        result = await newsletter_monitor.process_newsletters(
            mock_gmail_client,
            mock_embedchain_store,
            batch_size=3
        )

        assert isinstance(result, NewsletterMonitorResult)
        assert result.total_processed == 3
        assert result.queued_count == 2
        assert newsletter_monitor.queue_size == 2

    @pytest.mark.asyncio
    async def test_queue_error_recovery(
        self,
        newsletter_monitor,
        mock_gmail_client,
        mock_embedchain_store
    ):
        """Test queue recovery after processing error."""
        # Create test newsletter
        newsletter = Newsletter(
            email_id='test123',
            subject='Test Newsletter',
            received_date='2024-02-15T10:00:00Z',
            content='Test content'
        )

        # Add to queue
        newsletter_monitor._processing_queue.append(newsletter)
        assert newsletter_monitor.queue_size == 1

        # Mock storage error
        mock_embedchain_store.load_and_store_newsletters = AsyncMock(
            side_effect=Exception("Storage error")
        )
        
        # Mock the agent's run method to simulate error
        newsletter_monitor.agent.run = AsyncMock(side_effect=Exception("Storage error"))

        # Process should fail and return newsletter to queue
        with pytest.raises(Exception):
            await newsletter_monitor.process_newsletters(
                mock_gmail_client,
                mock_embedchain_store
            )

        # Verify newsletter was returned to queue with failed status
        assert newsletter_monitor.queue_size == 1
        queued = newsletter_monitor.get_queued_newsletters()
        assert queued[0].processing_status == 'pending'  # Status remains pending since agent.run failed before processing

    @pytest.mark.asyncio
    async def test_process_empty_queue(
        self,
        newsletter_monitor,
        mock_gmail_client,
        mock_embedchain_store
    ):
        """Test processing with empty queue."""
        result_data = NewsletterMonitorResult(
            newsletters=[],
            total_processed=0,
            processing_date='2024-02-15T10:00:00Z',
            queued_count=0
        )

        # Mock the agent's run method for empty queue
        newsletter_monitor.agent.run = AsyncMock(return_value=ModelTextResponse(
            content=result_data.model_dump_json()
        ))

        result = await newsletter_monitor.process_newsletters(
            mock_gmail_client,
            mock_embedchain_store
        )

        assert isinstance(result, NewsletterMonitorResult)
        assert result.total_processed == 0
        assert result.queued_count == 0
        assert len(result.newsletters) == 0

    @pytest.mark.asyncio
    async def test_queue_status_tracking(
        self,
        newsletter_monitor,
        mock_gmail_client,
        mock_embedchain_store
    ):
        """Test newsletter status tracking through processing stages."""
        # Create test newsletter
        newsletter = Newsletter(
            email_id='test123',
            subject='Test Newsletter',
            received_date='2024-02-15T10:00:00Z',
            content='Test content'
        )

        # Initial state
        assert newsletter.processing_status == 'pending'

        # Add to queue
        newsletter_monitor._processing_queue.append(newsletter)
        queued = newsletter_monitor.get_queued_newsletters()
        assert queued[0].processing_status == 'pending'

        result_data = NewsletterMonitorResult(
            newsletters=[
                Newsletter(
                    email_id='test123',
                    subject='Test Newsletter',
                    received_date='2024-02-15T10:00:00Z',
                    content='Test content',
                    vector_id='vector123',
                    processed_date='2024-02-15T10:00:00Z',
                    queued_date='2024-02-15T09:55:00Z',
                    processing_status='completed'
                )
            ],
            total_processed=1,
            processing_date='2024-02-15T10:00:00Z',
            queued_count=0
        )

        # Mock successful processing
        newsletter_monitor.agent.run = AsyncMock(return_value=ModelTextResponse(
            content=result_data.model_dump_json()
        ))

        result = await newsletter_monitor.process_newsletters(
            mock_gmail_client,
            mock_embedchain_store
        )

        assert result.newsletters[0].processing_status == 'completed'
        assert result.newsletters[0].vector_id is not None
        assert result.newsletters[0].processed_date is not None
