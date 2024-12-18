#!/usr/bin/env python3
"""Independent runner for README generation stage."""

import os
import logging
import click
from dotenv import load_dotenv

from processing.tasks import update_readme
from db.connection import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - README Stage - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@click.command()
@click.option('--force', is_flag=True, help='Force README update even if no new content')
def main(force):
    """Generate and update README."""
    try:
        # Load environment
        load_dotenv()
        
        # Initialize database
        db = Database(os.getenv('DATABASE_PATH'))
        db.connect()
        
        try:
            if not force:
                # Check if we have new content since last README update
                last_update = db.fetch_one("""
                    SELECT value 
                    FROM system_config 
                    WHERE key = 'last_readme_update'
                """)
                
                new_content = db.fetch_one("""
                    SELECT COUNT(*) as count
                    FROM repositories r
                    LEFT JOIN system_config sc ON sc.key = 'last_readme_update'
                    WHERE r.created_at > sc.value
                    OR sc.value IS NULL
                """)
                
                if not new_content['count']:
                    logger.info("No new content since last README update")
                    return
                    
                logger.info(f"Found {new_content['count']} new items since last update")
            else:
                logger.info("Forcing README update")
            
            # Enqueue README update task
            logger.info("Starting README update")
            task = update_readme.send(
                db_path=os.getenv('DATABASE_PATH'),
                github_token=os.getenv('GITHUB_TOKEN')
            )
            
            # Wait for completion
            result = task.get_result(block=True, timeout=None)
            
            if result:
                # Update last README update timestamp
                db.execute("""
                    INSERT OR REPLACE INTO system_config (key, value)
                    VALUES ('last_readme_update', datetime('now'))
                """)
                logger.info("README updated successfully")
            else:
                logger.warning("README update completed with warnings")
            
        finally:
            db.disconnect()
            
    except Exception as e:
        logger.error(f"README update failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
