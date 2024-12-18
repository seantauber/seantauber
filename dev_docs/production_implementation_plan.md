# Production Pipeline Implementation Plan

## Overview
The production pipeline needs to be implemented based on the working component tests. This plan outlines the steps to create a production-ready pipeline using the latest working implementations.

## Current Working Components
Based on component tests:
1. Gmail/Newsletter Processing (test_gmail_newsletter.py)
2. Content Extraction (test_content_extraction.py)
3. README Generation (test_readme_generation.py)

## Implementation Steps

### 1. Database Setup
```bash
# Run migrations to set up database schema
python scripts/run_migrations.py
```

### 2. Environment Configuration
Create .env file with:
```env
# OpenAI
OPENAI_API_KEY=your_key

# Gmail
GMAIL_CREDENTIALS_PATH=/path/to/credentials.json
GMAIL_TOKEN_PATH=/path/to/token.json
GMAIL_LABEL=GenAI-News

# GitHub
GITHUB_TOKEN=your_token

# Database
DATABASE_PATH=/path/to/database.sqlite

# Vector Storage
VECTOR_STORE_PATH=/path/to/vector/store
```

### 3. Create Pipeline Runner
Create scripts/run_pipeline.py:

```python
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

async def main():
    """Run the production pipeline."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize database
        db = Database(os.getenv('DATABASE_PATH'))
        db.connect()
        
        try:
            # Initialize vector store
            store = EmbedchainStore(os.getenv('GMAIL_TOKEN_PATH'))
            
            # Initialize Gmail client
            gmail_client = GmailClient(
                os.getenv('GMAIL_CREDENTIALS_PATH'),
                os.getenv('GMAIL_TOKEN_PATH')
            )
            
            # Create components
            newsletter_monitor = NewsletterMonitor(gmail_client, store)
            content_extractor = ContentExtractorAgent(
                store,
                github_token=os.getenv('GITHUB_TOKEN')
            )
            readme_generator = ReadmeGenerator(db)
            
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
```

### 4. Testing Steps

1. Test Database Setup:
```bash
# Verify migrations
python scripts/run_migrations.py
```

2. Test Gmail Connection:
```bash
# Run newsletter component test
pytest tests/components/test_gmail_newsletter.py -v
```

3. Test Content Extraction:
```bash
# Run extraction component test
pytest tests/components/test_content_extraction.py -v
```

4. Test README Generation:
```bash
# Run readme component test
pytest tests/components/test_readme_generation.py -v
```

5. Test Full Pipeline:
```bash
# Run production pipeline
python scripts/run_pipeline.py
```

### 5. Monitoring Setup

1. Check Logs:
```bash
tail -f pipeline.log
```

2. Check Database:
```bash
sqlite3 path/to/database.sqlite
```

3. Verify README:
```bash
cat README.md
```

## Deployment Considerations

1. Scheduling:
   - Set up cron job or GitHub Action
   - Run daily or on specific triggers

2. Error Handling:
   - Monitor logs
   - Set up error notifications
   - Implement retry logic

3. Data Management:
   - Regular database backups
   - Vector store maintenance
   - Log rotation

## Success Criteria

1. Pipeline runs successfully end-to-end
2. All component tests pass
3. README is generated with latest content
4. Logs show proper execution
5. Error handling works as expected

## Next Steps

1. Implement pipeline runner
2. Set up monitoring
3. Create deployment documentation
4. Set up automated scheduling
5. Monitor initial runs
