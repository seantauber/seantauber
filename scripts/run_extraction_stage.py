#!/usr/bin/env python3
"""Independent runner for content extraction stage."""

import os
import uuid
import logging
import click
import time
import dramatiq
from datetime import datetime, timedelta
from dotenv import load_dotenv

from processing.tasks import extract_content_batch
from db.connection import Database
from scripts.utils import ensure_redis_running

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - Extraction Stage - %(levelname)s - %(message)s',
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
@click.option('--batch-size', default=3, help='Number of items per batch')
@click.option('--days-back', default=7, help='Process content from last N days')
@click.option('--reprocess', is_flag=True, help='Reprocess already extracted content')
def main(batch_size, days_back, reprocess):
    """Process content extraction in parallel batches."""
    try:
        # Load environment
        load_dotenv()
        
        # Ensure Redis is running
        if not ensure_redis_running():
            logger.error("Failed to start Redis server")
            return
        
        # Initialize database
        db = Database(os.getenv('DATABASE_PATH'))
        db.connect()
        
        try:
            # Build query based on options
            query = """
                SELECT DISTINCT vector_id 
                FROM newsletters 
                WHERE vector_id IS NOT NULL
                AND received_date >= datetime('now', ?)
            """
            
            if not reprocess:
                # Only get unprocessed content
                query += " AND vector_id NOT IN (SELECT vector_id FROM content_extraction_status WHERE status = 'completed')"
            
            # Get vector IDs to process
            days_param = f'-{days_back} days'
            vector_ids = [row['vector_id'] for row in db.fetch_all(query, (days_param,))]
            
            if not vector_ids:
                logger.info("No content to process")
                return
                
            logger.info(f"Found {len(vector_ids)} items to process")
            
            # Process in parallel batches
            content_batches = chunk_list(vector_ids, batch_size)
            
            # Enqueue extraction tasks
            extraction_tasks = []
            for i, batch in enumerate(content_batches, 1):
                batch_id = f"content-{uuid.uuid4()}"
                logger.info(f"Enqueueing batch {i}/{len(content_batches)} (ID: {batch_id})")
                
                task = extract_content_batch.send(
                    vector_ids=batch,
                    batch_id=batch_id,
                    vector_store_path=os.getenv('VECTOR_STORE_PATH'),
                    github_token=os.getenv('GITHUB_TOKEN')
                )
                extraction_tasks.append(task)
            
            logger.info(f"Enqueued {len(extraction_tasks)} extraction tasks")
            
            # Wait for completion with timeout
            logger.info("Waiting for extraction tasks to complete...")
            start_time = time.time()
            completed = 0
            failed = 0
            
            for i, task in enumerate(extraction_tasks, 1):
                try:
                    batch_start = time.time()
                    logger.info(f"Waiting for batch {i}/{len(extraction_tasks)}")
                    
                    # 6 minute timeout (slightly longer than the task's 5 minute timeout)
                    result = task.get_result(block=True, timeout=360000)
                    
                    batch_time = time.time() - batch_start
                    logger.info(f"Batch {i} completed in {batch_time:.2f}s")
                    completed += 1
                        
                except dramatiq.results.ResultTimeout:
                    logger.error(f"Batch {i} timed out after 6 minutes")
                    failed += 1
                except Exception as e:
                    logger.error(f"Batch {i} failed: {str(e)}")
                    failed += 1
            
            total_time = time.time() - start_time
            logger.info(
                f"Content extraction completed in {total_time:.2f}s - "
                f"Successful: {completed}, Failed: {failed}"
            )
            
        finally:
            db.disconnect()
            
    except Exception as e:
        logger.error(f"Content extraction failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
