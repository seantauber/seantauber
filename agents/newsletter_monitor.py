"""Newsletter Monitor for processing and storing newsletters."""

import logging
import asyncio
from typing import List, Dict, Optional, Deque, Tuple
from datetime import datetime, UTC
from collections import deque

from pydantic import BaseModel

from processing.gmail.client import GmailClient
from processing.embedchain_store import EmbedchainStore
from processing.gmail.exceptions import FetchError
from db.connection import Database

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
    start_date: Optional[str] = None  # Added to track fetch period
    batch_results: Optional[List[Dict]] = None  # Added to track batch processing results

class BatchResult(BaseModel):
    """Result from processing a batch of newsletters."""
    batch_id: str
    successful: List[str]  # List of successful email IDs
    failed: List[str]  # List of failed email IDs
    errors: Dict[str, str]  # Map of email ID to error message
    processing_time: float

class NewsletterMonitor:
    """Component responsible for monitoring and processing newsletters."""

    def __init__(self, gmail_client: GmailClient, store: EmbedchainStore, db: Database):
        """
        Initialize the Newsletter Monitor.
        
        Args:
            gmail_client: Instance of GmailClient for fetching newsletters
            store: Instance of EmbedchainStore for storing newsletters
            db: Database connection for tracking processed newsletters
        """
        self.gmail_client = gmail_client
        self.embedchain_store = store
        self.db = db
        
        # Initialize processing queue
        self._processing_queue: Deque[Newsletter] = deque()
        
        # Initialize stats
        self.processed_count = 0
        self.error_count = 0
        
        # Batch tracking
        self._active_batches: Dict[str, BatchResult] = {}

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
            # Get date of most recent processed newsletter (read operation - direct)
            last_processed = self.db.fetch_one("""
                SELECT received_date 
                FROM newsletters 
                ORDER BY received_date DESC 
                LIMIT 1
            """)
            
            # If no newsletters processed yet, use None to fetch all
            after_date = None
            if last_processed:
                after_date = datetime.fromisoformat(last_processed['received_date'])
                logger.info(f"Last processed newsletter date: {after_date.isoformat()}")
            else:
                logger.info("No previously processed newsletters found - will fetch all")

            # Fetch newsletters after the last processed date
            raw_newsletters = self.gmail_client.get_newsletters(
                max_results=max_results,
                after_date=after_date
            )

            # Handle any duplicates during processing
            newsletters = []
            processed_ids = set()
            
            for n in raw_newsletters:
                # Skip if we somehow got a duplicate
                if n['email_id'] in processed_ids:
                    logger.warning(f"Skipping duplicate newsletter {n['email_id']}")
                    continue
                
                newsletter = Newsletter(
                    email_id=n['email_id'],
                    subject=n['subject'],
                    received_date=n['received_date'],
                    content=n['content'],
                    metadata=n.get('metadata', {}),
                    queued_date=datetime.now(UTC).isoformat()
                )
                
                self._processing_queue.append(newsletter)
                newsletters.append(newsletter)
                processed_ids.add(n['email_id'])
            
            logger.info(f"Queued {len(newsletters)} new newsletters for processing")
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

    async def process_newsletter_batch(
        self,
        batch: List[Newsletter],
        batch_id: str
    ) -> BatchResult:
        """
        Process a batch of newsletters in parallel.
        
        Args:
            batch: List of newsletters to process
            batch_id: Unique identifier for this batch
            
        Returns:
            BatchResult containing processing results
        """
        start_time = datetime.now(UTC)
        result = BatchResult(
            batch_id=batch_id,
            successful=[],
            failed=[],
            errors={},
            processing_time=0
        )
        
        try:
            # Process newsletters in parallel
            async def process_single(newsletter: Newsletter) -> Tuple[bool, Optional[str]]:
                try:
                    # Process content and create vector embedding
                    vector_id = await self.process_newsletter_content(
                        newsletter.email_id,
                        newsletter.content
                    )
                    
                    if vector_id:
                        newsletter.vector_id = vector_id
                        newsletter.processed_date = datetime.now(UTC).isoformat()
                        newsletter.processing_status = "completed"
                        
                        # Store in database (write operation - queued)
                        db_result = self.db.execute(
                            """
                            INSERT INTO newsletters (
                                email_id, received_date, processed_date, 
                                storage_status, vector_id, metadata
                            ) VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (
                                newsletter.email_id,
                                newsletter.received_date,
                                newsletter.processed_date,
                                'active',
                                newsletter.vector_id,
                                str(newsletter.metadata)
                            )
                        )
                        
                        return True, None
                    return False, "Failed to generate vector ID"
                    
                except Exception as e:
                    return False, str(e)
            
            # Process all newsletters in batch concurrently
            tasks = [process_single(n) for n in batch]
            results = await asyncio.gather(*tasks)
            
            # Collect results
            for newsletter, (success, error) in zip(batch, results):
                if success:
                    result.successful.append(newsletter.email_id)
                    self.processed_count += 1
                else:
                    result.failed.append(newsletter.email_id)
                    result.errors[newsletter.email_id] = error or "Unknown error"
                    self.error_count += 1
            
        except Exception as e:
            logger.error(f"Batch {batch_id} failed: {str(e)}")
            # Mark all remaining as failed
            for newsletter in batch:
                if newsletter.email_id not in result.successful:
                    result.failed.append(newsletter.email_id)
                    result.errors[newsletter.email_id] = str(e)
        
        result.processing_time = (datetime.now(UTC) - start_time).total_seconds()
        return result

    async def process_newsletters(self, batch_size: int = 5) -> List[BatchResult]:
        """
        Process queued newsletters in parallel batches.

        Args:
            batch_size: Number of newsletters to process in each batch

        Returns:
            List of batch results
        """
        try:
            if not self._processing_queue:
                logger.info("No newsletters in queue")
                return []

            # Split queue into batches
            batches = []
            current_batch = []
            
            while self._processing_queue and len(batches) * batch_size < len(self._processing_queue):
                if len(current_batch) < batch_size:
                    newsletter = self._processing_queue.popleft()
                    newsletter.processing_status = "processing"
                    current_batch.append(newsletter)
                else:
                    batches.append(current_batch)
                    current_batch = []
            
            if current_batch:
                batches.append(current_batch)

            if not batches:
                return []

            logger.info(f"Processing {len(batches)} batches of newsletters")
            
            # Process batches in parallel
            batch_results = []
            for i, batch in enumerate(batches):
                batch_id = f"batch_{datetime.now(UTC).timestamp()}_{i}"
                result = await self.process_newsletter_batch(batch, batch_id)
                batch_results.append(result)
                
                # Log batch results
                logger.info(
                    f"Batch {batch_id} completed: "
                    f"{len(result.successful)} successful, "
                    f"{len(result.failed)} failed, "
                    f"took {result.processing_time:.2f}s"
                )
            
            return batch_results
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Failed to process newsletter batches: {str(e)}")
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
            
            logger.info(f"Starting newsletter processing (max_results={max_results}, batch_size={batch_size})")
            
            # Fetch newsletters
            start_time = datetime.now(UTC)
            newsletters = await self.fetch_newsletters(max_results)
            
            if not newsletters:
                logger.info("No new newsletters to process")
                return NewsletterMonitorResult(
                    newsletters=[],
                    total_processed=0,
                    processing_date=start_time.isoformat(),
                    queued_count=0,
                    batch_results=[]
                )
            
            # Process newsletters in batches
            batch_results = await self.process_newsletters(batch_size)
            
            # Collect processed newsletters
            processed_newsletters = []
            for newsletter in newsletters:
                if any(newsletter.email_id in result.successful for result in batch_results):
                    processed_newsletters.append(newsletter)
            
            end_time = datetime.now(UTC)
            processing_duration = (end_time - start_time).total_seconds()
            
            logger.info(
                f"Newsletter processing completed in {processing_duration:.2f} seconds. "
                f"Processed {self.processed_count} newsletters with {self.error_count} errors."
            )
            
            return NewsletterMonitorResult(
                newsletters=processed_newsletters,
                total_processed=self.processed_count,
                processing_date=end_time.isoformat(),
                queued_count=len(self._processing_queue),
                start_date=start_time.isoformat(),
                batch_results=[result.dict() for result in batch_results]
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
