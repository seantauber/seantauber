#!/usr/bin/env python3
"""Independent runner for content extraction stage."""

import os
import uuid
import logging
import click
from datetime import datetime, timedelta
from dotenv import load_dotenv

from processing.tasks import extract_content_batch
from db.connection import Database

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
            
            # Wait for completion
            for task in extraction_tasks:
                task.get_result(block=True, timeout=None)
            
            logger.info("Content extraction completed successfully")
            
        finally:
            db.disconnect()
            
    except Exception as e:
        logger.error(f"Content extraction failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
