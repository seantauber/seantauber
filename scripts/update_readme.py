#!/usr/bin/env python3
"""Script to update the README with latest repository data."""

import asyncio
import logging
import logfire
from pathlib import Path

from agents.readme_generator import ReadmeGenerator
from db.connection import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - UpdateReadme - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('update_readme.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Update README with latest repository data."""
    try:
        logger.info("Starting README update")
        logfire.info("Starting README update", component="update_readme")

        # Connect to database
        db = Database()
        db.connect()
        logger.info("Connected to database")

        try:
            # Initialize readme generator
            generator = ReadmeGenerator(db)
            logger.info("Initialized ReadmeGenerator")

            # Generate new content
            content = await generator.generate_markdown()
            logger.info("Generated new README content")

            # Write to README.md
            readme_path = Path("README.md")
            readme_path.write_text(content)
            logger.info(f"Updated {readme_path}")
            logfire.info(
                "Successfully updated README",
                component="update_readme",
                content_length=len(content)
            )

        finally:
            # Always disconnect from database
            db.disconnect()
            logger.info("Disconnected from database")

    except Exception as e:
        logger.error(f"Failed to update README: {str(e)}")
        logfire.error(
            "Failed to update README",
            component="update_readme",
            error=str(e)
        )
        raise

if __name__ == "__main__":
    asyncio.run(main())
