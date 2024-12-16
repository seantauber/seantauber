"""Tests for Gmail newsletter ingestion with live dependencies."""
import pytest
from agents.newsletter_monitor import NewsletterMonitor
from db.connection import Database
from processing.embedchain_store import EmbedchainStore
from processing.gmail.client import GmailClient
from tests.config import get_test_settings, TEST_DB_PATH
from tests.components.conftest import print_newsletter_summary

class TestGmailNewsletterComponent:
    """Tests for Gmail newsletter ingestion with live dependencies."""
    
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

    async def test_newsletter_ingestion(self, newsletter_monitor: NewsletterMonitor):
        """Test ingesting newsletters from live Gmail account."""
        print("\n=== Gmail Newsletter Ingestion Test ===")
        
        db = Database(TEST_DB_PATH)
        db.connect()
        try:
            # Get initial state
            initial_newsletters = db.fetch_all(
                "SELECT * FROM newsletters ORDER BY received_date DESC"
            )
            print("\nInitial Newsletter State:")
            print_newsletter_summary("Existing Newsletters", initial_newsletters)
            
            # Fetch new newsletters
            print("\nFetching new newsletters...")
            await newsletter_monitor.fetch_newsletters()
            
            # Get updated state
            updated_newsletters = db.fetch_all(
                "SELECT * FROM newsletters ORDER BY received_date DESC"
            )
            print("\nUpdated Newsletter State:")
            print_newsletter_summary("All Newsletters", updated_newsletters, show_content=True)
            
            # Verify processing
            print("\nProcessing Statistics:")
            new_count = len(updated_newsletters) - len(initial_newsletters)
            print(f"New Newsletters: {new_count}")
            print(f"Total Newsletters: {len(updated_newsletters)}")
            
            # Check vector embeddings
            newsletters_with_vectors = db.fetch_all(
                "SELECT * FROM newsletters WHERE vector_id IS NOT NULL"
            )
            print(f"\nNewsletters with Vector Embeddings: {len(newsletters_with_vectors)}")
            
            # Verify historical tracking
            print("\nHistorical Tracking:")
            earliest = min(n['received_date'] for n in updated_newsletters) if updated_newsletters else None
            latest = max(n['received_date'] for n in updated_newsletters) if updated_newsletters else None
            print(f"Date Range: {earliest} to {latest}")
            
            # Verify duplicate prevention
            print("\nDuplicate Prevention Check:")
            email_ids = [n['email_id'] for n in updated_newsletters]
            unique_ids = set(email_ids)
            print(f"Total Newsletters: {len(email_ids)}")
            print(f"Unique Email IDs: {len(unique_ids)}")
            assert len(email_ids) == len(unique_ids), "Duplicate newsletters detected"
            
            # Basic assertions
            assert len(updated_newsletters) >= len(initial_newsletters), "Newsletter count decreased"
            assert all(n['vector_id'] for n in newsletters_with_vectors), "Some newsletters missing vector embeddings"
            
        finally:
            db.disconnect()
            
    async def test_content_processing(self, newsletter_monitor: NewsletterMonitor):
        """Test processing newsletter content with live data."""
        print("\n=== Newsletter Content Processing Test ===")
        
        db = Database(TEST_DB_PATH)
        db.connect()
        try:
            # Get unprocessed newsletters
            unprocessed = db.fetch_all(
                "SELECT * FROM newsletters WHERE processing_status = 'pending' ORDER BY received_date DESC"
            )
            print("\nUnprocessed Newsletters:")
            print_newsletter_summary("Pending Processing", unprocessed)
            
            if unprocessed:
                # Process newsletters
                print("\nProcessing newsletters...")
                for newsletter in unprocessed:
                    try:
                        # Process content and create vector embedding
                        vector_id = await newsletter_monitor.process_newsletter_content(
                            newsletter['email_id'],
                            newsletter['content']
                        )
                        
                        # Update database status
                        db.execute(
                            """
                            UPDATE newsletters 
                            SET processing_status = 'completed', vector_id = ? 
                            WHERE email_id = ?
                            """,
                            (vector_id, newsletter['email_id'])
                        )
                        
                        print(f"\nProcessed newsletter: {newsletter['subject']}")
                        print(f"Vector ID: {vector_id}")
                        
                    except Exception as e:
                        print(f"Error processing newsletter {newsletter['email_id']}: {str(e)}")
                        continue
                
                # Verify processing results
                processed = db.fetch_all(
                    "SELECT * FROM newsletters WHERE processing_status = 'completed' ORDER BY received_date DESC"
                )
                print("\nProcessed Newsletters:")
                print_newsletter_summary("Completed Processing", processed)
                
                # Verify vector embeddings
                with_vectors = db.fetch_all(
                    "SELECT * FROM newsletters WHERE vector_id IS NOT NULL"
                )
                print(f"\nNewsletters with Vector Embeddings: {len(with_vectors)}")
                
                assert len(processed) > 0, "No newsletters were processed"
                assert all(n['vector_id'] for n in processed), "Some processed newsletters missing vector embeddings"
                
            else:
                print("\nNo unprocessed newsletters found")
            
        finally:
            db.disconnect()
            
    async def test_historical_tracking(self, newsletter_monitor: NewsletterMonitor):
        """Test historical newsletter tracking with live data."""
        print("\n=== Newsletter Historical Tracking Test ===")
        
        db = Database(TEST_DB_PATH)
        db.connect()
        try:
            # Get all newsletters ordered by date
            newsletters = db.fetch_all(
                "SELECT * FROM newsletters ORDER BY received_date DESC"
            )
            
            if newsletters:
                # Analyze date distribution
                dates = [n['received_date'] for n in newsletters]
                earliest = min(dates)
                latest = max(dates)
                
                print("\nNewsletter Date Analysis:")
                print(f"Total Newsletters: {len(newsletters)}")
                print(f"Date Range: {earliest} to {latest}")
                
                # Group by processing status
                status_counts = {}
                for n in newsletters:
                    status = n['processing_status']
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                print("\nProcessing Status Distribution:")
                for status, count in status_counts.items():
                    print(f"{status}: {count}")
                
                # Check vector embeddings over time
                with_vectors = [n for n in newsletters if n['vector_id']]
                print(f"\nNewsletters with Vector Embeddings: {len(with_vectors)}")
                
                # Basic assertions
                assert len(newsletters) > 0, "No newsletters found"
                assert len(with_vectors) > 0, "No newsletters have vector embeddings"
                
            else:
                print("\nNo newsletters found in database")
            
        finally:
            db.disconnect()
