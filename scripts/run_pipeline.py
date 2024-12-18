#!/usr/bin/env python3
"""Production pipeline runner."""

import asyncio
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

from agents.orchestrator import AgentOrchestrator
from processing.embedchain_store import EmbedchainStore
from processing.gmail.client import GmailClient
from agents.newsletter_monitor import NewsletterMonitor
from agents.content_extractor import ContentExtractorAgent
from agents.readme_generator import ReadmeGenerator
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
        "VECTOR_STORE_PATH"
    ]
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

async def main():
    """Run the production pipeline."""
    try:
        # Load and validate environment
        load_dotenv()
        validate_environment()
        
        # Initialize database
        db = Database(os.getenv('DATABASE_PATH'))
        db.connect()
        
        try:
            # Initialize components
            store = EmbedchainStore(os.getenv('VECTOR_STORE_PATH'))
            gmail_client = GmailClient(
                os.getenv('GMAIL_CREDENTIALS_PATH'),
                os.getenv('GMAIL_TOKEN_PATH')
            )
            
            # Create agents
            newsletter_monitor = NewsletterMonitor(
                gmail_client=gmail_client,
                store=store,
                label=os.getenv('GMAIL_LABEL')
            )
            content_extractor = ContentExtractorAgent(
                store=store,
                github_token=os.getenv('GITHUB_TOKEN')
            )
            readme_generator = ReadmeGenerator(db=db)
            
            # Create orchestrator
            orchestrator = AgentOrchestrator(
                embedchain_store=store,
                newsletter_monitor=newsletter_monitor,
                content_extractor=content_extractor,
                readme_generator=readme_generator
            )
            
            # Run pipeline
            logger.info("Starting pipeline")
            success = await orchestrator.run_pipeline()
            
            if success:
                logger.info("Pipeline completed successfully")
            else:
                logger.error("Pipeline completed with errors")
                
        finally:
            # Always disconnect from database
            db.disconnect()
            logger.info("Disconnected from database")
            
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
