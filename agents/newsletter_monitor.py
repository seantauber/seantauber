"""Newsletter Monitor for processing and storing newsletters."""

import logging
from typing import List, Dict, Optional, Deque
from datetime import datetime, UTC
from collections import deque

from pydantic import BaseModel, ConfigDict

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

class NewsletterMonitorResult(BaseModel):
    """Result from processing newsletters."""
    newsletters: List[Newsletter]
    total_processed: int
    processing_date: str
    queued_count: int

class NewsletterMonitor:
    """Component responsible for monitoring and processing newsletters."""

    def __init__(self, gmail_client: GmailClient, embedchain_store: EmbedchainStore):
        """
        Initialize the Newsletter Monitor.
        
        Args:
            gmail_client: Instance of GmailClient for fetching newsletters
            embedchain_store: Instance of EmbedchainStore for storing newsletters
        """
        self.gmail_client = gmail_client
        self.embedchain_store = embedchain_store
        
        # Initialize processing queue
        self._processing_queue: Deque[Newsletter] = deque()
        
        # Initialize stats
        self.processed_count = 0
        self.error_count = 0

    async def fetch_newsletters(self, max_results: int = 10) -> List[Newsletter]:
        """
        Fetch newsletters from Gmail and queue for processing.

        Args:
            max_results: Maximum number of newsletters to fetch

        Returns:
            List of fetched newsletters

        Raises:
            FetchError: If fetching newsletters fails
        """
        try:
            raw_newsletters = self.gmail_client.get_newsletters(max_results=max_results)
            newsletters = []
            
            for n in raw_newsletters:
                newsletter = Newsletter(
                    email_id=n['email_id'],
                    subject=n['subject'],
                    received_date=n['received_date'],
                    content=n['content'],
                    metadata=n.get('metadata', {}),  # Default to empty dict if None
                    queued_date=datetime.now(UTC).isoformat()
                )
                self._processing_queue.append(newsletter)
                newsletters.append(newsletter)
            
            logger.info(f"Queued {len(newsletters)} newsletters for processing")
            return newsletters
            
        except FetchError as e:
            self.error_count += 1
            logger.error(f"Failed to fetch newsletters: {str(e)}")
            raise
        except Exception as e:
            self.error_count += 1
            logger.error(f"Unexpected error fetching newsletters: {str(e)}")
            raise FetchError(f"Unexpected error: {str(e)}")

    async def process_newsletter_content(self, email_id: str, content: str) -> str:
        """
        Process individual newsletter content and create vector embedding.
        
        Args:
            email_id: ID of the email to process
            content: Content of the newsletter
            
        Returns:
            Vector ID for the processed content
            
        Raises:
            Exception: If processing fails
        """
        try:
            # Store content in vector storage
            vector_id = self.embedchain_store.newsletter_store.add(
                content,
                metadata={"email_id": email_id}
            )
            
            if not vector_id:
                raise ValueError("Failed to generate vector embedding")
                
            logger.info(f"Created vector embedding for newsletter {email_id}")
            return vector_id
            
        except Exception as e:
            logger.error(f"Failed to process newsletter {email_id}: {str(e)}")
            raise

    async def process_newsletters(self, batch_size: int = 5) -> List[Newsletter]:
        """
        Process queued newsletters in batches.

        Args:
            batch_size: Number of newsletters to process in each batch

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

            processed_newsletters = []
            processed_date = datetime.now(UTC).isoformat()
            
            # Process each newsletter individually
            for newsletter in to_process:
                try:
                    vector_id = await self.process_newsletter_content(
                        newsletter.email_id,
                        newsletter.content
                    )
                    newsletter.vector_id = vector_id
                    newsletter.processed_date = processed_date
                    newsletter.processing_status = "completed"
                    processed_newsletters.append(newsletter)
                    self.processed_count += 1
                except Exception as e:
                    logger.error(f"Failed to process newsletter {newsletter.email_id}: {str(e)}")
                    newsletter.processing_status = "failed"
                    self._processing_queue.appendleft(newsletter)
            
            logger.info(f"Processed {len(processed_newsletters)} newsletters")
            return processed_newsletters
            
        except Exception as e:
            self.error_count += 1
            # Return newsletters to queue on failure
            for newsletter in to_process:
                if newsletter.processing_status != "completed":
                    newsletter.processing_status = "failed"
                    self._processing_queue.appendleft(newsletter)
            
            logger.error(f"Failed to process newsletters: {str(e)}")
            raise

    async def run(self, max_results: int = 10, batch_size: int = 5) -> NewsletterMonitorResult:
        """
        Run the complete newsletter processing pipeline.

        Args:
            max_results: Maximum number of newsletters to fetch
            batch_size: Number of newsletters to process in each batch

        Returns:
            Result containing processed newsletters and stats
        """
        try:
            # Reset stats
            self.processed_count = 0
            self.error_count = 0
            
            # Fetch newsletters
            newsletters = await self.fetch_newsletters(max_results)
            if not newsletters:
                logger.info("No newsletters to process")
                return NewsletterMonitorResult(
                    newsletters=[],
                    total_processed=0,
                    processing_date=datetime.now(UTC).isoformat(),
                    queued_count=0
                )
            
            # Process newsletters in batches
            processed_newsletters = []
            while self._processing_queue:
                batch = await self.process_newsletters(batch_size)
                processed_newsletters.extend(batch)
            
            return NewsletterMonitorResult(
                newsletters=processed_newsletters,
                total_processed=self.processed_count,
                processing_date=datetime.now(UTC).isoformat(),
                queued_count=len(self._processing_queue)
            )
            
        except Exception as e:
            logger.error(f"Newsletter processing pipeline failed: {str(e)}")
            raise

    @property
    def queue_size(self) -> int:
        """Get the current size of the processing queue."""
        return len(self._processing_queue)

    def get_queued_newsletters(self) -> List[Newsletter]:
        """Get list of currently queued newsletters."""
        return list(self._processing_queue)

    def get_stats(self) -> Dict:
        """Get current processing statistics."""
        return {
            'processed_count': self.processed_count,
            'error_count': self.error_count,
            'queue_size': self.queue_size
        }
