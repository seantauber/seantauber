"""Stage 1: Newsletter Ingestion and Processing Pipeline

This module implements the first stage of a three-stage pipeline for dynamically generating and updating 
a curated list of GenAI-related GitHub repositories. While structured as a test file, it contains the 
core production functionality for newsletter ingestion and processing.

System Architecture:
------------------
The newsletter ingestion stage is responsible for:
1. Fetching AI/ML-focused newsletters from a configured Gmail account
2. Processing and storing the raw newsletter content
3. Generating vector embeddings for semantic analysis
4. Managing the historical record of processed newsletters

Key Components:
-------------
1. NewsletterMonitor:
   - Core orchestrator for newsletter operations
   - Manages parallel processing of newsletters
   - Handles state tracking and error recovery
   
2. GmailClient:
   - Authenticates with Gmail API
   - Fetches newsletters using configured filters
   - Extracts relevant email metadata
   
3. EmbedchainStore:
   - Generates vector embeddings from newsletter content
   - Manages persistent storage of embeddings
   - Enables semantic search capabilities
   
4. Database:
   - Stores newsletter metadata and processing state
   - Manages relationships between newsletters and embeddings
   - Tracks historical processing records

Data Flow:
---------
1. Newsletter Ingestion (test_newsletter_ingestion):
   Input: Raw Gmail emails
   Process:
   - Fetches newsletters in configurable batches
   - Processes multiple newsletters in parallel
   - Handles deduplication and updates
   Output: Stored newsletter records with metadata
   
2. Content Processing (test_content_processing):
   Input: Raw newsletter content
   Process:
   - Generates vector embeddings for semantic analysis
   - Updates processing status and metadata
   - Manages embedding storage
   Output: Vector embeddings linked to newsletters
   
3. Historical Tracking (test_historical_tracking):
   Input: Processed newsletter records
   Process:
   - Analyzes temporal distribution
   - Tracks processing status
   - Maintains audit trail
   Output: Historical analytics and verification

Database Schema:
--------------
newsletters table:
- email_id: TEXT (primary key) - Unique Gmail message ID
- subject: TEXT - Email subject line
- received_date: TEXT (ISO) - Receipt timestamp
- content: TEXT - Raw newsletter content
- vector_id: TEXT (nullable) - Link to embedding
- metadata: TEXT (JSON) - Additional context
- processing_status: TEXT - Current state
- created_at: TEXT (ISO) - Record creation time
- processed_date: TEXT (ISO) - Processing completion time

Implementation Details:
---------------------
1. Parallel Processing:
   - Uses batched processing (BATCH_SIZE constant)
   - Implements concurrent newsletter processing
   - Manages database transactions safely
   
2. Error Handling:
   - Graceful failure recovery
   - Maintains partial progress
   - Detailed error logging
   
3. State Management:
   - Tracks processing status
   - Handles interrupted operations
   - Enables process resumption

Integration Points:
-----------------
1. Input:
   - Gmail API (via credentials)
   - Configuration settings
   - Database connection
   
2. Output:
   - Processed newsletter records
   - Vector embeddings
   - Processing statistics

Dependencies:
------------
- Gmail API credentials (GMAIL_CREDENTIALS_PATH)
- Gmail OAuth token (GMAIL_TOKEN_PATH)
- SQLite database
- Vector storage system

For Developers:
-------------
1. Configuration:
   - Update settings in config files
   - Configure Gmail credentials
   - Set processing parameters

2. Extension:
   - Add new processing steps in process_newsletter_batch
   - Extend metadata capture in store_newsletter
   - Modify batch processing logic

3. Integration:
   - Use newsletter_monitor.fetch_newsletters() for raw data
   - Query processed content via vector_id
   - Monitor processing_status for pipeline state

Note: This module is designed to run continuously in production,
with the test framework providing structure and validation.
"""

import pytest
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
from agents.newsletter_monitor import NewsletterMonitor, Newsletter
from db.connection import Database
from db.migrations import MigrationManager
from processing.embedchain_store import EmbedchainStore
from processing.gmail.client import GmailClient
from tests.config import get_test_settings
from tests.components.conftest import print_newsletter_summary
from datetime import datetime, UTC

pytestmark = pytest.mark.asyncio

BATCH_SIZE = 5  # Process newsletters in batches of 5

class TestGmailNewsletterComponent:
    """Tests for Gmail newsletter ingestion with live dependencies."""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Set up test database and apply migrations."""
        settings = get_test_settings()
        db = Database(settings.TEST_DATABASE_PATH)
        db.connect()
        
        # Apply migrations
        migration_manager = MigrationManager(db)
        migration_manager.apply_migrations()
        
        # Clear existing data for clean test state (write operation - queued)
        db.execute("DELETE FROM newsletters")
        
        yield db
        
        # Cleanup
        db.disconnect()
    
    @pytest.fixture
    def gmail_client(self) -> GmailClient:
        """Initialize Gmail client."""
        settings = get_test_settings()
        client = GmailClient(
            credentials_path=settings.GMAIL_CREDENTIALS_PATH,
            token_path=settings.GMAIL_TOKEN_PATH
        )
        yield client
        
    @pytest.fixture
    def newsletter_monitor(
        self,
        gmail_client: GmailClient,
        vector_store: EmbedchainStore,
        setup_database: Database
    ) -> NewsletterMonitor:
        """Initialize newsletter monitor."""
        monitor = NewsletterMonitor(gmail_client, vector_store, setup_database)
        yield monitor

    async def process_newsletter_batch(
        self,
        newsletters: List[Newsletter],
        db: Database,
        batch_id: int
    ) -> Dict[str, Any]:
        """Process a batch of newsletters in parallel.
        
        Args:
            newsletters: List of newsletters to process
            db: Database connection
            batch_id: Unique identifier for this batch
            
        Returns:
            Dict containing processing results
        """
        results = {
            "successful": [],
            "failed": [],
            "errors": {}
        }
        
        print(f"\nProcessing batch {batch_id} with {len(newsletters)} newsletters")
        
        for newsletter in newsletters:
            try:
                # Check if newsletter exists (read operation - direct)
                existing = db.fetch_one(
                    "SELECT * FROM newsletters WHERE email_id = ?",
                    (newsletter.email_id,)
                )
                
                if existing:
                    # Update existing newsletter (write operation - queued)
                    result = db.execute(
                        """
                        UPDATE newsletters 
                        SET received_date = ?,
                            vector_id = ?,
                            metadata = ?,
                            processing_status = ?,
                            processed_date = ?
                        WHERE email_id = ?
                        """,
                        (
                            newsletter.received_date,
                            newsletter.vector_id,
                            str(newsletter.metadata or {}),
                            newsletter.processing_status,
                            datetime.now(UTC).isoformat(),
                            newsletter.email_id
                        )
                    )
                else:
                    # Insert new newsletter (write operation - queued)
                    result = db.execute(
                        """
                        INSERT INTO newsletters (
                            email_id, subject, received_date, content,
                            vector_id, metadata, processing_status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            newsletter.email_id,
                            newsletter.subject,
                            newsletter.received_date,
                            newsletter.content,
                            newsletter.vector_id,
                            str(newsletter.metadata or {}),
                            newsletter.processing_status,
                            datetime.now(UTC).isoformat()
                        )
                    )
                
                results["successful"].append(newsletter.email_id)
                print(f"Successfully processed newsletter {newsletter.email_id} in batch {batch_id}")
                
            except Exception as e:
                error_msg = f"Failed to process newsletter: {str(e)}"
                print(f"Error in batch {batch_id}: {error_msg}")
                results["failed"].append(newsletter.email_id)
                results["errors"][newsletter.email_id] = error_msg
        
        return results

    async def test_newsletter_ingestion(self, newsletter_monitor: NewsletterMonitor, setup_database):
        """Test ingesting newsletters from live Gmail account with parallel processing."""
        print("\n=== Testing Parallel Newsletter Ingestion ===")
        
        db = setup_database
        try:
            # Fetch new newsletters
            print("\nFetching newsletters from Gmail...")
            newsletters = await newsletter_monitor.fetch_newsletters(max_results=20)  # Increased for parallel testing
            
            if not newsletters:
                pytest.skip("No newsletters available for testing")
            
            # Split newsletters into batches
            batches = [
                newsletters[i:i + BATCH_SIZE] 
                for i in range(0, len(newsletters), BATCH_SIZE)
            ]
            print(f"\nSplit {len(newsletters)} newsletters into {len(batches)} batches")
            
            # Process batches concurrently
            batch_results = await asyncio.gather(*[
                self.process_newsletter_batch(batch, db, i)
                for i, batch in enumerate(batches)
            ])
            
            # Aggregate results
            total_results = {
                "successful": [],
                "failed": [],
                "errors": {}
            }
            
            for result in batch_results:
                total_results["successful"].extend(result["successful"])
                total_results["failed"].extend(result["failed"])
                total_results["errors"].update(result["errors"])
            
            # Verify results (read operation - direct)
            stored_newsletters = [dict(row) for row in db.fetch_all(
                "SELECT * FROM newsletters ORDER BY received_date DESC"
            )]
            
            print("\nParallel Ingestion Results:")
            print(f"- Total newsletters processed: {len(newsletters)}")
            print(f"- Successfully stored: {len(total_results['successful'])}")
            print(f"- Failed: {len(total_results['failed'])}")
            
            if total_results["errors"]:
                print("\nErrors encountered:")
                for email_id, error in total_results["errors"].items():
                    print(f"- {email_id}: {error}")
            
            # Show sample of ingested content
            if stored_newsletters:
                print("\nSample Newsletter Content:")
                sample = stored_newsletters[0]
                print(f"Subject: {sample['subject']}")
                print(f"Received: {sample['received_date']}")
                print(f"Content Preview: {sample['content'][:200]}...")
            
            # Basic assertions
            assert len(stored_newsletters) > 0, "No newsletters were ingested"
            assert len(total_results["successful"]) > 0, "No newsletters were successfully processed"
            assert all(n['email_id'] for n in stored_newsletters), "Some newsletters missing email ID"
            
        finally:
            pass  # Database cleanup handled by fixture
            
    async def test_content_processing(self, newsletter_monitor: NewsletterMonitor, setup_database):
        """Test processing newsletter content with live data."""
        print("\n=== Testing Newsletter Content Processing ===")
        
        db = setup_database
        try:
            # Get or fetch newsletters to process (read operation - direct)
            unprocessed = [dict(row) for row in db.fetch_all(
                """
                SELECT * FROM newsletters 
                WHERE vector_id IS NULL AND content IS NOT NULL 
                ORDER BY received_date DESC
                """
            )]
            
            if not unprocessed:
                print("\nFetching new newsletters for processing...")
                newsletters = await newsletter_monitor.fetch_newsletters(max_results=10)
                
                # Split into batches for parallel processing
                batches = [
                    newsletters[i:i + BATCH_SIZE]
                    for i in range(0, len(newsletters), BATCH_SIZE)
                ]
                
                # Process batches concurrently
                batch_results = await asyncio.gather(*[
                    self.process_newsletter_batch(batch, db, i)
                    for i, batch in enumerate(batches)
                ])
                
                # Refresh unprocessed list (read operation - direct)
                unprocessed = [dict(row) for row in db.fetch_all(
                    """
                    SELECT * FROM newsletters 
                    WHERE vector_id IS NULL AND content IS NOT NULL 
                    ORDER BY received_date DESC
                    """
                )]
            
            if unprocessed:
                print(f"\nProcessing {len(unprocessed)} newsletters...")
                processed_count = 0
                
                # Split unprocessed newsletters into batches
                batches = [
                    unprocessed[i:i + BATCH_SIZE]
                    for i in range(0, len(unprocessed), BATCH_SIZE)
                ]
                
                async def process_batch(batch: List[Dict], batch_id: int) -> int:
                    """Process a batch of newsletters and return count of successful operations."""
                    batch_count = 0
                    for newsletter in batch:
                        try:
                            # Process content and create vector embedding
                            vector_id = await newsletter_monitor.process_newsletter_content(
                                newsletter['email_id'],
                                newsletter['content']
                            )
                            
                            if vector_id:
                                # Update database status (write operation - queued)
                                result = db.execute(
                                    """
                                    UPDATE newsletters 
                                    SET vector_id = ?, 
                                        processing_status = 'completed',
                                        processed_date = ?
                                    WHERE email_id = ?
                                    """,
                                    (vector_id, datetime.now(UTC).isoformat(), newsletter['email_id'])
                                )
                                batch_count += 1
                            
                        except Exception as e:
                            print(f"Error processing newsletter {newsletter['email_id']} in batch {batch_id}: {str(e)}")
                            continue
                    
                    return batch_count
                
                # Process batches concurrently
                batch_counts = await asyncio.gather(*[
                    process_batch(batch, i)
                    for i, batch in enumerate(batches)
                ])
                
                processed_count = sum(batch_counts)
                
                # Verify results (read operation - direct)
                processed = [dict(row) for row in db.fetch_all(
                    "SELECT * FROM newsletters WHERE vector_id IS NOT NULL ORDER BY received_date DESC"
                )]
                
                print("\nProcessing Results:")
                print(f"- Successfully processed {processed_count} newsletters")
                print(f"- Generated vector embeddings for {len(processed)} newsletters")
                
                # Show sample of processed content
                if processed:
                    print("\nSample Processed Newsletter:")
                    sample = processed[0]
                    print(f"Subject: {sample['subject']}")
                    print(f"Vector ID: {sample['vector_id']}")
                    print(f"Processing Status: {sample['processing_status']}")
                
                assert processed_count > 0, "No newsletters were processed"
                assert all(n['vector_id'] for n in processed), "Some processed newsletters missing vector embeddings"
                
            else:
                print("\nNo newsletters available for processing")
                pytest.skip("No newsletters available for testing")
            
        finally:
            pass  # Database cleanup handled by fixture
            
    async def test_historical_tracking(self, newsletter_monitor: NewsletterMonitor, setup_database):
        """Test historical newsletter tracking with live data."""
        print("\n=== Testing Newsletter Historical Tracking ===")
        
        db = setup_database
        try:
            # Ensure we have processed newsletters
            await self.test_content_processing(newsletter_monitor, setup_database)
            
            # Get all newsletters (read operation - direct)
            newsletters = [dict(row) for row in db.fetch_all(
                "SELECT * FROM newsletters ORDER BY received_date DESC"
            )]
            
            if newsletters:
                # Analyze date distribution
                dates = [n['received_date'] for n in newsletters]
                earliest = min(dates)
                latest = max(dates)
                
                # Count by processing status
                status_counts = {}
                for n in newsletters:
                    status = 'processed' if n.get('vector_id') else 'pending'
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                print("\nNewsletter History Summary:")
                print(f"- Total Newsletters: {len(newsletters)}")
                print(f"- Date Range: {earliest} to {latest}")
                print("\nProcessing Status:")
                for status, count in status_counts.items():
                    print(f"- {status.title()}: {count}")
                
                # Show sample timeline
                print("\nSample Timeline:")
                for i, n in enumerate(newsletters[:3]):  # Show first 3
                    print(f"{i+1}. {n['received_date']} - {n['subject']}")
                
                # Basic assertions
                assert len(newsletters) > 0, "No newsletters found"
                assert len([n for n in newsletters if n.get('vector_id')]) > 0, "No newsletters have vector embeddings"
                
            else:
                print("\nNo newsletters found in database")
                pytest.skip("No newsletters available for testing")
            
        finally:
            pass  # Database cleanup handled by fixture
