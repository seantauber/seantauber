#!/usr/bin/env python3
"""Independent runner for newsletter processing stage."""

import os
import uuid
import logging
import click
from datetime import datetime
from dotenv import load_dotenv

from processing.gmail.client import GmailClient
from processing.tasks import process_newsletter_batch
from db.connection import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - Newsletter Stage - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def chunk_list(lst, chunk_size):
    """Split a list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

@click.command()
@click.option('--max-results', default=50, help='Maximum number of newsletters to fetch')
@click.option('--batch-size', default=5, help='Number of newsletters per batch')
@click.option('--start-date', help='Start date for fetching (YYYY-MM-DD). If not provided, uses last processed date.')
def main(max_results, batch_size, start_date):
    """Process newsletters in parallel batches."""
    try:
        # Load environment
        load_dotenv()
        
        # Initialize components
        gmail_client = GmailClient(
            os.getenv('GMAIL_CREDENTIALS_PATH'),
            os.getenv('GMAIL_TOKEN_PATH')
        )
        db = Database(os.getenv('DATABASE_PATH'))
        db.connect()
        
        try:
            # Determine start date
            after_date = None
            if start_date:
                after_date = datetime.strptime(start_date, "%Y-%m-%d")
                logger.info(f"Using provided start date: {start_date}")
            else:
                last_processed = db.fetch_one("""
                    SELECT received_date 
                    FROM newsletters 
                    ORDER BY received_date DESC 
                    LIMIT 1
                """)
                if last_processed:
                    after_date = datetime.fromisoformat(last_processed['received_date'])
                    logger.info(f"Using last processed date: {after_date.isoformat()}")
                else:
                    logger.info("No previous processing date found")

            # Fetch newsletters
            newsletters = gmail_client.get_newsletters(
                max_results=max_results,
                after_date=after_date
            )
            
            if not newsletters:
                logger.info("No new newsletters to process")
                return
                
            logger.info(f"Found {len(newsletters)} newsletters to process")
            
            # Process in parallel batches
            newsletter_batches = chunk_list(newsletters, batch_size)
            
            # Enqueue processing tasks
            processing_tasks = []
            for i, batch in enumerate(newsletter_batches, 1):
                batch_id = f"newsletters-{uuid.uuid4()}"
                logger.info(f"Enqueueing batch {i}/{len(newsletter_batches)} (ID: {batch_id})")
                
                task = process_newsletter_batch.send(
                    newsletters=batch,
                    batch_id=batch_id,
                    vector_store_path=os.getenv('VECTOR_STORE_PATH'),
                    db_path=os.getenv('DATABASE_PATH')
                )
                processing_tasks.append(task)
            
            logger.info(f"Enqueued {len(processing_tasks)} processing tasks")
            
            # Wait for completion
            for task in processing_tasks:
                task.get_result(block=True, timeout=None)
            
            logger.info("Newsletter processing completed successfully")
            
        finally:
            db.disconnect()
            
    except Exception as e:
        logger.error(f"Newsletter processing failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
