"""Task definitions for parallel processing pipeline."""

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.results import Results
from dramatiq.results.backends import RedisBackend
import asyncio
import logging
import os
import time
import psutil
from typing import Dict, List, Optional
from datetime import datetime, UTC
import signal
from functools import partial
from tenacity import retry, stop_after_attempt, wait_exponential
from processing.embedchain_store import EmbedchainStore
from processing.gmail.client import GmailClient
from agents.newsletter_monitor import NewsletterMonitor, Newsletter
from agents.content_extractor import ContentExtractorAgent
from db.connection import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(process)d - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Configure Redis broker and results backend
redis_broker = RedisBroker(url="redis://localhost:6379")
result_backend = RedisBackend(url="redis://localhost:6379")
redis_broker.add_middleware(Results(backend=result_backend))
dramatiq.set_broker(redis_broker)

# Configure logging
logger = logging.getLogger(__name__)

class TimeoutError(Exception):
    """Raised when an operation times out."""
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def with_timeout(seconds, func, *args, **kwargs):
    """Run a function with a timeout and retry logic."""
    # Set the signal handler and a alarm
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        result = func(*args, **kwargs)
    finally:
        signal.alarm(0)  # Disable the alarm
    return result

def log_memory_usage():
    """Log current memory usage."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    logger.info(f"Memory usage - RSS: {mem_info.rss / 1024 / 1024:.2f}MB, VMS: {mem_info.vms / 1024 / 1024:.2f}MB")

@dramatiq.actor(queue_name="newsletters", max_retries=3, store_results=True, time_limit=35000)  # 35 second timeout
def process_newsletter_batch(
    newsletters: List[Dict],
    batch_id: str,
    vector_store_path: str,
    db_path: str,
    gmail_token_path: str
) -> Dict:
    """
    Process a batch of newsletters in parallel using NewsletterMonitor.
    
    Args:
        newsletters: List of newsletter data dictionaries
        batch_id: Unique identifier for this batch
        vector_store_path: Path to vector storage
        db_path: Path to SQLite database
        gmail_token_path: Path to Gmail token
        
    Returns:
        Dict containing processing results
    """
    try:
        start_time = time.time()
        logger.info(f"[BATCH {batch_id}] Starting with {len(newsletters)} newsletters")
        log_memory_usage()
        
        # Track individual newsletter results
        results = {
            "successful": [],
            "failed": [],
            "errors": {}
        }
        
        # Initialize components
        try:
            component_start = time.time()
            
            # Ensure vector store directory exists
            os.makedirs(vector_store_path, exist_ok=True)
            logger.info(f"[BATCH {batch_id}] Ensured vector store directory exists at {vector_store_path}")
            
            store = EmbedchainStore(vector_store_path)
            db = Database(db_path)
            db.connect()
            gmail_client = GmailClient(
                os.getenv('GMAIL_CREDENTIALS_PATH'),
                gmail_token_path
            )
            monitor = NewsletterMonitor(gmail_client, store, db)
            logger.info(
                f"[BATCH {batch_id}] Component initialization took "
                f"{time.time() - component_start:.2f}s"
            )
        except Exception as e:
            error_msg = f"Failed to initialize components: {str(e)}"
            logger.error(f"[BATCH {batch_id}] {error_msg}")
            return {
                "batch_id": batch_id,
                "status": "failed",
                "error": error_msg,
                "results": results
            }
        
        try:
            # Create event loop for async operations
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Convert and log each newsletter
                newsletter_objects = []
                for n in newsletters:
                    try:
                        logger.info(
                            f"[BATCH {batch_id}] Processing newsletter: "
                            f"ID={n['email_id']}, "
                            f"Subject='{n.get('subject', 'No Subject')}', "
                            f"Content Length={len(n['content'])}"
                        )
                        
                        newsletter_objects.append(
                            Newsletter(
                                email_id=n['email_id'],
                                subject=n.get('subject', 'No Subject'),
                                received_date=n['received_date'],
                                content=n['content'],
                                metadata=n.get('metadata', {}),
                                queued_date=datetime.now(UTC).isoformat()
                            )
                        )
                    except Exception as e:
                        error_msg = f"Failed to create Newsletter object: {str(e)}"
                        logger.error(
                            f"[BATCH {batch_id}] {error_msg} for newsletter {n.get('email_id', 'unknown')}"
                        )
                        results["failed"].append(n.get('email_id', 'unknown'))
                        results["errors"][n.get('email_id', 'unknown')] = error_msg
                
                if not newsletter_objects:
                    raise ValueError("No valid newsletters to process")
                
                # Process newsletters using monitor's logic
                process_start = time.time()
                
                # Track timing for each newsletter
                for n in newsletter_objects:
                    try:
                        newsletter_start = time.time()
                        logger.info(
                            f"[BATCH {batch_id}] Starting vector embedding for newsletter {n.email_id}"
                        )
                        
                        # Log memory before vector embedding
                        logger.info(
                            f"[BATCH {batch_id}] Memory before vector embedding for newsletter {n.email_id}:"
                        )
                        log_memory_usage()
                        
                        # Time the vector embedding
                        embed_start = time.time()
                        vector_id = store.newsletter_store.add(
                            n.content,
                            metadata={"email_id": n.email_id}
                        )
                        embed_time = time.time() - embed_start
                        logger.info(
                            f"[BATCH {batch_id}] Vector embedding took {embed_time:.2f}s "
                            f"for newsletter {n.email_id} (content length: {len(n.content)})"
                        )
                        
                        # Log memory after vector embedding
                        logger.info(
                            f"[BATCH {batch_id}] Memory after vector embedding for newsletter {n.email_id}:"
                        )
                        log_memory_usage()
                        
                        # Log memory before database operation
                        logger.info(
                            f"[BATCH {batch_id}] Memory before database operation for newsletter {n.email_id}:"
                        )
                        log_memory_usage()
                        
                        # Check if newsletter already exists
                        db_start = time.time()
                        n.vector_id = vector_id
                        n.processed_date = datetime.now(UTC).isoformat()
                        
                        existing = db.fetch_one(
                            "SELECT id FROM newsletters WHERE email_id = ?",
                            (n.email_id,)
                        )
                        
                        if existing:
                            # Update existing record
                            sql = """
                                UPDATE newsletters 
                                SET processed_date = ?,
                                    vector_id = ?,
                                    metadata = ?
                                WHERE email_id = ?
                            """
                            params = (
                                n.processed_date,
                                n.vector_id,
                                str(n.metadata),
                                n.email_id
                            )
                        else:
                            # Insert new record
                            sql = """
                                INSERT INTO newsletters (
                                    email_id, received_date, processed_date, 
                                    storage_status, vector_id, metadata
                                ) VALUES (?, ?, ?, ?, ?, ?)
                            """
                            params = (
                                n.email_id,
                                n.received_date,
                                n.processed_date,
                                'active',
                                n.vector_id,
                                str(n.metadata)
                            )
                        
                        db.execute(sql, params)
                        
                        db_time = time.time() - db_start
                        logger.info(
                            f"[BATCH {batch_id}] Database operation took {db_time:.2f}s "
                            f"for newsletter {n.email_id}"
                        )
                        
                        # Log memory after database operation
                        logger.info(
                            f"[BATCH {batch_id}] Memory after database operation for newsletter {n.email_id}:"
                        )
                        log_memory_usage()
                        
                        total_time = time.time() - newsletter_start
                        logger.info(
                            f"[BATCH {batch_id}] Successfully processed newsletter {n.email_id} "
                            f"in {total_time:.2f}s (embed: {embed_time:.2f}s, db: {db_time:.2f}s)"
                        )
                        
                        results["successful"].append(n.email_id)
                        
                    except Exception as e:
                        error_msg = f"Failed to process newsletter: {str(e)}"
                        logger.error(
                            f"[BATCH {batch_id}] {error_msg} for newsletter {n.email_id}"
                        )
                        results["failed"].append(n.email_id)
                        results["errors"][n.email_id] = error_msg
                
                process_time = time.time() - process_start
                logger.info(
                    f"[BATCH {batch_id}] Newsletter processing took {process_time:.2f}s - "
                    f"Successful: {len(results['successful'])}, "
                    f"Failed: {len(results['failed'])}"
                )
                
                result = {
                    "batch_id": batch_id,
                    "total_processed": len(results["successful"]),
                    "total_failed": len(results["failed"]),
                    "processed_ids": results["successful"],
                    "failed_ids": results["failed"],
                    "errors": results["errors"],
                    "status": "completed",
                    "processing_time": process_time
                }
                
            finally:
                loop.close()
                
            logger.info(f"[BATCH {batch_id}] Completed: {result}")
            return result
            
        finally:
            db.disconnect()
            
    except Exception as e:
        error_msg = f"Failed to process batch: {str(e)}"
        logger.error(f"[BATCH {batch_id}] {error_msg}")
        return {
            "batch_id": batch_id,
            "status": "failed",
            "error": error_msg,
            "results": results
        }

@dramatiq.actor(max_retries=2, time_limit=300000)  # 5 minute timeout
def extract_content_batch(
    vector_ids: List[str],
    batch_id: str,
    vector_store_path: str,
    github_token: str
) -> None:
    """
    Extract and process content from a batch of vector embeddings.
    
    Args:
        vector_ids: List of vector IDs to process
        batch_id: Unique identifier for this batch
        vector_store_path: Path to vector storage
        github_token: GitHub API token
    """
    try:
        start_time = time.time()
        logger.info(f"[TIMING] Starting content batch {batch_id} with {len(vector_ids)} items")
        log_memory_usage()
        
        init_start = time.time()
        
        # Ensure vector store directory exists
        os.makedirs(vector_store_path, exist_ok=True)
        logger.info(f"[TIMING] Ensured vector store directory exists at {vector_store_path}")
        
        store = EmbedchainStore(vector_store_path)
        extractor = ContentExtractorAgent(store=store, github_token=github_token)
        logger.info(f"[TIMING] Component initialization took {time.time() - init_start:.2f}s")
        
        # Create event loop for async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            for i, vector_id in enumerate(vector_ids, 1):
                item_start = time.time()
                logger.info(f"[TIMING] Starting content {i}/{len(vector_ids)} in batch {batch_id}")
                log_memory_usage()
                
                # Get content from vector store with timeout and retry
                fetch_start = time.time()
                try:
                    content = with_timeout(
                        60,  # 1 minute timeout for content retrieval
                        store.newsletter_store.get,
                        vector_id
                    )
                    logger.info(f"[TIMING] Content fetch took {time.time() - fetch_start:.2f}s")
                except TimeoutError:
                    logger.error(f"Content fetch timed out for vector ID {vector_id}")
                    raise
                except Exception as e:
                    logger.error(f"Content fetch failed for vector ID {vector_id}: {str(e)}")
                    raise
                
                if not content:
                    logger.warning(f"No content found for vector ID {vector_id}")
                    continue
                    
                # Extract and process content using event loop
                process_start = time.time()
                loop.run_until_complete(extractor.process_content(content))
                logger.info(f"[TIMING] Content processing took {time.time() - process_start:.2f}s")
                logger.info(f"[TIMING] Total time for content {i}: {time.time() - item_start:.2f}s")
                
            logger.info(f"Completed content batch {batch_id}")
            
        finally:
            loop.close()
        
    except Exception as e:
        logger.error(f"Failed to process content batch {batch_id}: {str(e)}")
        raise

@dramatiq.actor(max_retries=1, time_limit=300000)  # 5 minute timeout
def update_readme(
    db_path: str,
    github_token: str
) -> None:
    """
    Generate and update the README with latest content.
    
    Args:
        db_path: Path to SQLite database
        github_token: GitHub API token
    """
    try:
        start_time = time.time()
        logger.info("[TIMING] Starting README update")
        log_memory_usage()
        
        db = Database(db_path)
        db.connect()
        
        try:
            from agents.readme_generator import ReadmeGenerator
            init_start = time.time()
            generator = ReadmeGenerator(db=db, github_token=github_token)
            logger.info(f"[TIMING] Generator initialization took {time.time() - init_start:.2f}s")
            
            # Create event loop for async operations
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                update_start = time.time()
                success = loop.run_until_complete(generator.update_github_readme())
                logger.info(f"[TIMING] README update took {time.time() - update_start:.2f}s")
                
                if success:
                    logger.info("README updated successfully")
                else:
                    logger.warning("README update completed with warnings")
            finally:
                loop.close()
                
        finally:
            db.disconnect()
            
    except Exception as e:
        logger.error(f"Failed to update README: {str(e)}")
        raise
