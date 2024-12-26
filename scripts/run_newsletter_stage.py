#!/usr/bin/env python3
"""Independent runner for newsletter processing stage."""

import os
import uuid
import logging
import click
import time
from datetime import datetime
from email.utils import parsedate_to_datetime
from dramatiq.results import ResultTimeout
from dramatiq.brokers.redis import RedisBroker
from dramatiq.results import Results
from dramatiq.results.backends import RedisBackend
from dotenv import load_dotenv

from processing.gmail.client import GmailClient
from processing.tasks import process_newsletter_batch
from db.connection import Database
from scripts.utils import ensure_redis_running

# Configure Redis broker and results backend
redis_broker = RedisBroker(url="redis://localhost:6379")
result_backend = RedisBackend(url="redis://localhost:6379")
redis_broker.add_middleware(Results(backend=result_backend))

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
        
        # Ensure Redis is running
        if not ensure_redis_running():
            logger.error("Failed to start Redis server")
            return
        
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
                    after_date = parsedate_to_datetime(last_processed['received_date'])
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
                
                try:
                    # Test Redis connection before sending
                    redis_client = redis_broker.client
                    redis_client.ping()
                    logger.info("Redis connection confirmed")
                    
                    # Send task through broker
                    task = process_newsletter_batch.send(
                        newsletters=batch,
                        batch_id=batch_id,
                        vector_store_path=os.getenv('VECTOR_STORE_PATH'),
                        db_path=os.getenv('DATABASE_PATH'),
                        gmail_token_path=os.getenv('GMAIL_TOKEN_PATH')
                    )
                    processing_tasks.append(task)
                    logger.info(f"Successfully enqueued batch {i} with ID {batch_id}")
                except Exception as e:
                    logger.error(f"Failed to enqueue batch {i}: {str(e)}")
                    raise
            
            logger.info(f"Enqueued {len(processing_tasks)} processing tasks")
            
            # Wait for completion with timeout
            logger.info("Waiting for processing tasks to complete...")
            start_time = time.time()
            completed = 0
            failed = 0
            
            for i, task in enumerate(processing_tasks, 1):
                try:
                    batch_start = time.time()
                    logger.info(f"Waiting for batch {i}/{len(processing_tasks)}")
                    
                    # 35 second timeout (slightly longer than the task's 30 second timeout)
                    result = task.get_result(block=True, timeout=35000)
                    
                    batch_time = time.time() - batch_start
                    logger.info(f"[BATCH {i}] Completed in {batch_time:.2f}s")
                    
                    if result.get('status') == 'completed':
                        completed += 1
                        logger.info(
                            f"[BATCH {i}] Succeeded - "
                            f"Processed: {result['total_processed']}, "
                            f"Failed: {result['total_failed']}, "
                            f"Time: {result.get('processing_time', 0):.2f}s"
                        )
                        if result['total_failed'] > 0:
                            logger.error(f"[BATCH {i}] Failed newsletters in successful batch:")
                            for email_id in result['failed_ids']:
                                logger.error(
                                    f"[BATCH {i}] Newsletter {email_id} failed: "
                                    f"{result['errors'].get(email_id, 'Unknown error')}"
                                )
                    else:
                        failed += 1
                        logger.error(
                            f"[BATCH {i}] Failed - Error: {result.get('error', 'Unknown error')}"
                        )
                        if result.get('results'):
                            if result['results'].get('failed'):
                                logger.error(f"[BATCH {i}] Individual newsletter failures:")
                                for email_id in result['results']['failed']:
                                    logger.error(
                                        f"[BATCH {i}] Newsletter {email_id} failed: "
                                        f"{result['results']['errors'].get(email_id, 'Unknown error')}"
                                    )
                        
                except ResultTimeout:
                    logger.error(f"[BATCH {i}] Timed out after 35 seconds")
                    failed += 1
                except Exception as e:
                    logger.error(f"Batch {i} failed with exception: {str(e)}")
                    failed += 1
            
            total_time = time.time() - start_time
            logger.info(
                f"Newsletter processing completed in {total_time:.2f}s - "
                f"Successful batches: {completed}, Failed batches: {failed}"
            )
            
        finally:
            db.disconnect()
            
    except Exception as e:
        logger.error(f"Newsletter processing failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
