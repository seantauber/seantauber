"""Newsletter Monitor agent for processing and storing newsletters."""

import json
import logging
from typing import List, Dict, Optional, Deque
from datetime import datetime
from collections import deque

from pydantic import BaseModel, ConfigDict
from pydantic_ai import Agent, RunContext, ModelRetry

from processing.gmail.client import GmailClient
from processing.embedchain_store import EmbedchainStore
from processing.gmail.exceptions import FetchError

# Configure logging
logger = logging.getLogger(__name__)

class Newsletter(BaseModel):
    """Newsletter data model."""
    email_id: str
    subject: str
    received_date: str
    content: str
    vector_id: Optional[str] = None
    processed_date: Optional[str] = None
    metadata: Optional[Dict] = None
    queued_date: Optional[str] = None
    processing_status: str = "pending"  # pending, processing, completed, failed

class NewsletterMonitorDeps(BaseModel):
    """Dependencies for the Newsletter Monitor agent."""
    gmail_client: GmailClient
    embedchain_store: EmbedchainStore

    model_config = ConfigDict(arbitrary_types_allowed=True)

class NewsletterMonitorResult(BaseModel):
    """Result from processing newsletters."""
    newsletters: List[Newsletter]
    total_processed: int
    processing_date: str
    queued_count: int

class NewsletterMonitor:
    """Agent responsible for monitoring and processing newsletters."""

    def __init__(self):
        """Initialize the Newsletter Monitor agent."""
        self.agent = Agent(
            'openai:gpt-4',
            deps_type=NewsletterMonitorDeps,
            result_type=NewsletterMonitorResult,
            system_prompt=(
                "You are a newsletter monitoring agent responsible for fetching and processing "
                "AI/ML newsletters. Your tasks include:\n"
                "1. Fetching newsletters from Gmail using the provided client\n"
                "2. Queuing newsletters for processing\n"
                "3. Processing queued newsletters and storing in vector storage\n"
                "4. Tracking processing status and results\n"
                "Use the available tools to accomplish these tasks efficiently."
            )
        )

        # Initialize processing queue
        self._processing_queue: Deque[Newsletter] = deque()
        
        # Register tools
        self._register_tools()

    def _register_tools(self):
        """Register tools with the agent."""
        
        @self.agent.tool(retries=2)
        async def fetch_newsletters(
            ctx: RunContext[NewsletterMonitorDeps],
            max_results: int = 10
        ) -> List[Newsletter]:
            """
            Fetch newsletters from Gmail.

            Args:
                max_results: Maximum number of newsletters to fetch

            Returns:
                List of fetched newsletters
            """
            try:
                raw_newsletters = ctx.deps.gmail_client.get_newsletters(max_results=max_results)
                newsletters = []
                for n in raw_newsletters:
                    newsletter = Newsletter(
                        email_id=n['email_id'],
                        subject=n['subject'],
                        received_date=n['received_date'],
                        content=n['content'],
                        metadata=n.get('metadata'),
                        queued_date=datetime.utcnow().isoformat()
                    )
                    self._processing_queue.append(newsletter)
                    newsletters.append(newsletter)
                
                logger.info(f"Queued {len(newsletters)} newsletters for processing")
                return newsletters
            except FetchError as e:
                logger.error(f"Failed to fetch newsletters: {str(e)}")
                raise ModelRetry(f"Failed to fetch newsletters: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error fetching newsletters: {str(e)}")
                raise ModelRetry(f"Unexpected error: {str(e)}")

        @self.agent.tool(retries=2)
        async def process_queued_newsletters(
            ctx: RunContext[NewsletterMonitorDeps],
            batch_size: int = 5
        ) -> List[Newsletter]:
            """
            Process a batch of queued newsletters.

            Args:
                batch_size: Number of newsletters to process in this batch

            Returns:
                List of processed newsletters
            """
            try:
                if not self._processing_queue:
                    logger.info("No newsletters in queue")
                    return []

                # Get batch of newsletters to process
                to_process = []
                while len(to_process) < batch_size and self._processing_queue:
                    newsletter = self._processing_queue.popleft()
                    newsletter.processing_status = "processing"
                    to_process.append(newsletter)

                if not to_process:
                    return []

                # Store in vector storage
                vector_ids = await ctx.deps.embedchain_store.load_and_store_newsletters(
                    max_results=len(to_process)
                )
                
                # Update newsletters with vector IDs and processing status
                processed_date = datetime.utcnow().isoformat()
                for newsletter, vector_id in zip(to_process, vector_ids):
                    newsletter.vector_id = vector_id
                    newsletter.processed_date = processed_date
                    newsletter.processing_status = "completed"
                
                logger.info(f"Processed {len(to_process)} newsletters")
                return to_process
            except Exception as e:
                # Return newsletters to queue on failure
                for newsletter in to_process:
                    newsletter.processing_status = "failed"
                    self._processing_queue.appendleft(newsletter)
                
                logger.error(f"Failed to process newsletters: {str(e)}")
                raise ModelRetry(f"Failed to process newsletters: {str(e)}")

    async def process_newsletters(
        self,
        gmail_client: GmailClient,
        embedchain_store: EmbedchainStore,
        max_results: int = 10,
        batch_size: int = 5
    ) -> NewsletterMonitorResult:
        """
        Process new newsletters end-to-end.

        Args:
            gmail_client: Instance of GmailClient
            embedchain_store: Instance of EmbedchainStore
            max_results: Maximum number of newsletters to fetch
            batch_size: Number of newsletters to process in each batch

        Returns:
            Result containing processed newsletters
        """
        deps = NewsletterMonitorDeps(
            gmail_client=gmail_client,
            embedchain_store=embedchain_store
        )

        result = await self.agent.run(
            f"Process up to {max_results} newsletters in batches of {batch_size}",
            deps=deps
        )
        
        # Parse the JSON content into NewsletterMonitorResult
        result_data = json.loads(result.content)
        return NewsletterMonitorResult(**result_data)

    @property
    def queue_size(self) -> int:
        """Get the current size of the processing queue."""
        return len(self._processing_queue)

    def get_queued_newsletters(self) -> List[Newsletter]:
        """Get list of currently queued newsletters."""
        return list(self._processing_queue)
