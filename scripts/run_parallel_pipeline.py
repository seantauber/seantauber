#!/usr/bin/env python3
"""Parallel pipeline runner using Dramatiq workers."""

import os
import uuid
import logging
from datetime import datetime, UTC
from typing import List, Dict
from dotenv import load_dotenv

from processing.gmail.client import GmailClient
from processing.tasks import (
    process_newsletter_batch,
    extract_content_batch,
    update_readme
)
from db.connection import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - Pipeline - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def validate_environment():
    """Validate required environment variables."""
    required = [
        "OPENAI_API_KEY",
        "GMAIL_CREDENTIALS_PATH",
        "GMAIL_TOKEN_PATH",
        "GMAIL_LABEL",
        "GITHUB_TOKEN",
        "DATABASE_PATH",
        "VECTOR_STORE_PATH",
        "REDIS_URL"  # New requirement for Dramatiq broker
    ]
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Split a list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def main():
    """Run the parallel processing pipeline."""
    try:
        # Load and validate environment
        load_dotenv()
        validate_environment()
        
        # Initialize components
        gmail_client = GmailClient(
            os.getenv('GMAIL_CREDENTIALS_PATH'),
            os.getenv('GMAIL_TOKEN_PATH')
        )
        db = Database(os.getenv('DATABASE_PATH'))
        db.connect()
        
        try:
            # 1. Get date of last processed newsletter
            last_processed = db.fetch_one("""
                SELECT received_date 
                FROM newsletters 
                ORDER BY received_date DESC 
                LIMIT 1
            """)
            after_date = None
            if last_processed:
                after_date = datetime.fromisoformat(last_processed['received_date'])
                logger.info(f"Last processed newsletter date: {after_date.isoformat()}")
            else:
                logger.info("No previously processed newsletters found")

            # 2. Fetch new newsletters
            newsletters = gmail_client.get_newsletters(
                max_results=50,  # Increased for parallel processing
                after_date=after_date
            )
            
            if not newsletters:
                logger.info("No new newsletters to process")
                return
                
            logger.info(f"Found {len(newsletters)} newsletters to process")
            
            # 3. Process newsletters in parallel batches
            batch_size = 5  # Process 5 newsletters per worker
            newsletter_batches = chunk_list(newsletters, batch_size)
            
            # Enqueue newsletter processing tasks
            processing_tasks = []
            for i, batch in enumerate(newsletter_batches, 1):
                batch_id = f"newsletters-{uuid.uuid4()}"
                logger.info(f"Enqueueing newsletter batch {i}/{len(newsletter_batches)} (ID: {batch_id})")
                
                task = process_newsletter_batch.send(
                    newsletters=batch,
                    batch_id=batch_id,
                    vector_store_path=os.getenv('VECTOR_STORE_PATH'),
                    db_path=os.getenv('DATABASE_PATH')
                )
                processing_tasks.append(task)
            
            logger.info(f"Enqueued {len(processing_tasks)} newsletter processing tasks")
            
            # 4. Wait for newsletter processing to complete
            for task in processing_tasks:
                task.get_result(block=True, timeout=None)
            
            # 5. Get all processed vector IDs for content extraction
            vector_ids = [n.get('vector_id') for n in newsletters if n.get('vector_id')]
            if not vector_ids:
                logger.warning("No vector IDs found for content extraction")
                return
                
            # 6. Process content in parallel batches
            content_batch_size = 3  # Process 3 content items per worker
            content_batches = chunk_list(vector_ids, content_batch_size)
            
            # Enqueue content extraction tasks
            extraction_tasks = []
            for i, batch in enumerate(content_batches, 1):
                batch_id = f"content-{uuid.uuid4()}"
                logger.info(f"Enqueueing content batch {i}/{len(content_batches)} (ID: {batch_id})")
                
                task = extract_content_batch.send(
                    vector_ids=batch,
                    batch_id=batch_id,
                    vector_store_path=os.getenv('VECTOR_STORE_PATH'),
                    github_token=os.getenv('GITHUB_TOKEN')
                )
                extraction_tasks.append(task)
            
            logger.info(f"Enqueued {len(extraction_tasks)} content extraction tasks")
            
            # 7. Wait for content extraction to complete
            for task in extraction_tasks:
                task.get_result(block=True, timeout=None)
            
            # 8. Update README
            logger.info("Enqueueing README update task")
            readme_task = update_readme.send(
                db_path=os.getenv('DATABASE_PATH'),
                github_token=os.getenv('GITHUB_TOKEN')
            )
            
            # Wait for README update to complete
            readme_task.get_result(block=True, timeout=None)
            
            logger.info("Pipeline completed successfully")
            
        finally:
            db.disconnect()
            
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
