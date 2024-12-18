"""Task definitions for parallel processing pipeline."""

import dramatiq
from dramatiq.brokers.redis import RedisBroker
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime

from processing.gmail.client import GmailClient
from processing.embedchain_store import EmbedchainStore
from agents.newsletter_monitor import NewsletterMonitor
from agents.content_extractor import ContentExtractorAgent
from db.connection import Database

# Configure Redis broker
redis_broker = RedisBroker(url="redis://localhost:6379")
dramatiq.set_broker(redis_broker)

# Configure logging
logger = logging.getLogger(__name__)

@dramatiq.actor(max_retries=3)
def process_newsletter_batch(
    newsletters: List[Dict],
    batch_id: str,
    vector_store_path: str,
    db_path: str
) -> None:
    """
    Process a batch of newsletters in parallel.
    
    Args:
        newsletters: List of newsletter data dictionaries
        batch_id: Unique identifier for this batch
        vector_store_path: Path to vector storage
        db_path: Path to SQLite database
    """
    try:
        logger.info(f"Processing batch {batch_id} with {len(newsletters)} newsletters")
        
        # Initialize components
        store = EmbedchainStore(vector_store_path)
        db = Database(db_path)
        db.connect()
        
        try:
            for i, newsletter in enumerate(newsletters, 1):
                logger.info(f"Processing newsletter {i}/{len(newsletters)} in batch {batch_id}")
                
                # Create vector embedding
                vector_id = store.newsletter_store.add(
                    newsletter['content'],
                    metadata={"email_id": newsletter['email_id']}
                )
                
                # Store in database
                processed_date = datetime.utcnow().isoformat()
                db.execute("""
                    INSERT INTO newsletters (
                        email_id, received_date, processed_date, 
                        storage_status, vector_id, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    newsletter['email_id'],
                    newsletter['received_date'],
                    processed_date,
                    'active',
                    vector_id,
                    str(newsletter.get('metadata', {}))
                ))
                
                logger.info(f"Successfully processed newsletter {newsletter['email_id']}")
                
        finally:
            db.disconnect()
            
        logger.info(f"Completed batch {batch_id}")
        
    except Exception as e:
        logger.error(f"Failed to process batch {batch_id}: {str(e)}")
        raise

@dramatiq.actor(max_retries=2)
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
        logger.info(f"Processing content batch {batch_id} with {len(vector_ids)} items")
        
        store = EmbedchainStore(vector_store_path)
        extractor = ContentExtractorAgent(store=store, github_token=github_token)
        
        # Create event loop for async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            for i, vector_id in enumerate(vector_ids, 1):
                logger.info(f"Processing content {i}/{len(vector_ids)} in batch {batch_id}")
                
                # Get content from vector store
                content = store.newsletter_store.get(vector_id)
                if not content:
                    logger.warning(f"No content found for vector ID {vector_id}")
                    continue
                    
                # Extract and process content using event loop
                loop.run_until_complete(extractor.process_content(content))
                
            logger.info(f"Completed content batch {batch_id}")
            
        finally:
            loop.close()
        
    except Exception as e:
        logger.error(f"Failed to process content batch {batch_id}: {str(e)}")
        raise

@dramatiq.actor(max_retries=1)
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
        logger.info("Starting README update")
        
        db = Database(db_path)
        db.connect()
        
        try:
            from agents.readme_generator import ReadmeGenerator
            generator = ReadmeGenerator(db=db, github_token=github_token)
            
            # Create event loop for async operations
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                success = loop.run_until_complete(generator.update_github_readme())
                
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
