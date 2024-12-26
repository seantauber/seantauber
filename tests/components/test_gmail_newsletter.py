"""Tests for Gmail newsletter ingestion and processing pipeline.

This test suite validates the complete Gmail newsletter ingestion pipeline, including:
1. Fetching newsletters from Gmail
2. Storing newsletter data in the database
3. Processing newsletter content into vector embeddings
4. Tracking historical newsletter data

Data Flow:
----------
Input:
- Gmail emails (fetched via GmailClient)
  - Format: Raw email data including subject, content, received date
  - Source: Gmail account configured via GMAIL_CREDENTIALS_PATH and GMAIL_TOKEN_PATH

Processing Steps:
1. Newsletter Ingestion (test_newsletter_ingestion):
   - Fetches up to 10 most recent newsletters from Gmail
   - For each newsletter:
     - Checks for existing entry in database
     - Updates existing or inserts new record with:
       * email_id: Unique Gmail message ID
       * subject: Email subject line
       * received_date: Date email was received
       * content: Raw email content
       * vector_id: Initially null
       * metadata: Additional email metadata as JSON string
       * processing_status: Initial 'pending' status
       * created_at/processed_date: Timestamps

2. Content Processing (test_content_processing):
   - Identifies unprocessed newsletters (where vector_id is NULL)
   - For each unprocessed newsletter:
     - Generates vector embedding from content
     - Updates database record with:
       * vector_id: Unique identifier for stored embedding
       * processing_status: Updated to 'completed'
       * processed_date: Timestamp of processing

3. Historical Tracking (test_historical_tracking):
   - Analyzes processed newsletters to verify:
     * Date distribution (earliest to latest)
     * Processing status counts
     * Timeline of newsletter receipts

Output/Storage:
--------------
1. Database (newsletters table):
   - Schema:
     * email_id: TEXT (primary key)
     * subject: TEXT
     * received_date: TEXT (ISO format)
     * content: TEXT
     * vector_id: TEXT (null until processed)
     * metadata: TEXT (JSON string)
     * processing_status: TEXT
     * created_at: TEXT (ISO format)
     * processed_date: TEXT (ISO format)

2. Vector Store:
   - Stores embeddings generated from newsletter content
   - Each embedding has unique vector_id referenced in database
   - Enables semantic search/similarity operations

Usage Notes:
------------
- Requires configured Gmail credentials and token
- Uses test database path from settings
- Cleans database before each test
- Limited to 10 newsletters per fetch for testing
- Processes both new and existing newsletters
- Handles duplicate prevention via email_id

Integration Points:
-----------------
- GmailClient: Fetches raw newsletter data
- NewsletterMonitor: Orchestrates ingestion and processing
- EmbedchainStore: Generates and stores vector embeddings
- Database: Persists newsletter data and processing state

For developers building additional modules:
----------------------------------------
1. Accessing newsletter data:
   - Query newsletters table for processed content
   - Join on vector_id for embedding access
   - Use processing_status to identify state

2. Processing pipeline integration:
   - Monitor 'pending' status for new content
   - Update processing_status for tracking
   - Reference vector_id for similarity searches

3. Historical analysis:
   - received_date and processed_date enable timeline analysis
   - metadata field stores additional context
   - vector_id enables semantic clustering
"""

import pytest
from agents.newsletter_monitor import NewsletterMonitor
from db.connection import Database
from db.migrations import MigrationManager
from processing.embedchain_store import EmbedchainStore
from processing.gmail.client import GmailClient
from tests.config import get_test_settings
from tests.components.conftest import print_newsletter_summary
from datetime import datetime, UTC

pytestmark = pytest.mark.asyncio

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
        
        # Clear existing data for clean test state
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
    def newsletter_monitor(self, gmail_client: GmailClient, vector_store: EmbedchainStore) -> NewsletterMonitor:
        """Initialize newsletter monitor."""
        monitor = NewsletterMonitor(gmail_client, vector_store)
        yield monitor

    async def test_newsletter_ingestion(self, newsletter_monitor: NewsletterMonitor, setup_database):
        """Test ingesting newsletters from live Gmail account."""
        print("\n=== Testing Newsletter Ingestion ===")
        
        db = setup_database
        try:
            # Fetch new newsletters (limited to 10)
            print("\nFetching newsletters from Gmail...")
            newsletters = await newsletter_monitor.fetch_newsletters(max_results=10)
            
            # Save newsletters to database
            for newsletter in newsletters:
                # Check if newsletter already exists
                existing = db.fetch_one(
                    "SELECT * FROM newsletters WHERE email_id = ?",
                    (newsletter.email_id,)
                )
                
                if existing:
                    # Update existing newsletter
                    db.execute(
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
                    # Insert new newsletter
                    db.execute(
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
            
            # Verify results
            stored_newsletters = [dict(row) for row in db.fetch_all(
                "SELECT * FROM newsletters ORDER BY received_date DESC"
            )]
            
            print("\nIngestion Results:")
            print(f"- Fetched {len(newsletters)} newsletters from Gmail")
            print(f"- Successfully stored {len(stored_newsletters)} newsletters in database")
            
            # Show sample of ingested content
            if stored_newsletters:
                print("\nSample Newsletter Content:")
                sample = stored_newsletters[0]
                print(f"Subject: {sample['subject']}")
                print(f"Received: {sample['received_date']}")
                print(f"Content Preview: {sample['content'][:200]}...")
            
            # Basic assertions
            assert len(stored_newsletters) > 0, "No newsletters were ingested"
            assert all(n['email_id'] for n in stored_newsletters), "Some newsletters missing email ID"
            
        finally:
            pass  # Database cleanup handled by fixture
            
    async def test_content_processing(self, newsletter_monitor: NewsletterMonitor, setup_database):
        """Test processing newsletter content with live data."""
        print("\n=== Testing Newsletter Content Processing ===")
        
        db = setup_database
        try:
            # Get or fetch newsletters to process
            unprocessed = [dict(row) for row in db.fetch_all(
                """
                SELECT * FROM newsletters 
                WHERE vector_id IS NULL AND content IS NOT NULL 
                ORDER BY received_date DESC
                """
            )]
            
            if not unprocessed:
                print("\nFetching new newsletters for processing...")
                newsletters = await newsletter_monitor.fetch_newsletters(max_results=10)  # Updated to 10
                
                # Save new newsletters
                for newsletter in newsletters:
                    db.execute(
                        """
                        INSERT INTO newsletters (
                            email_id, subject, received_date, content,
                            metadata, processing_status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            newsletter.email_id,
                            newsletter.subject,
                            newsletter.received_date,
                            newsletter.content,
                            str(newsletter.metadata or {}),
                            'pending',
                            datetime.now(UTC).isoformat()
                        )
                    )
                
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
                
                for newsletter in unprocessed:
                    try:
                        # Process content and create vector embedding
                        vector_id = await newsletter_monitor.process_newsletter_content(
                            newsletter['email_id'],
                            newsletter['content']
                        )
                        
                        if vector_id:
                            # Update database status
                            db.execute(
                                """
                                UPDATE newsletters 
                                SET vector_id = ?, 
                                    processing_status = 'completed',
                                    processed_date = ?
                                WHERE email_id = ?
                                """,
                                (vector_id, datetime.now(UTC).isoformat(), newsletter['email_id'])
                            )
                            processed_count += 1
                        
                    except Exception as e:
                        print(f"Error processing newsletter {newsletter['email_id']}: {str(e)}")
                        continue
                
                # Verify results
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
            
            # Get all newsletters
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
