# Project Cleanup Plan

## Overview

The most up-to-date implementation is defined in the component tests. These tests demonstrate the working pipeline with live data and dependencies:

### Core Component Tests (Current Working Implementation)
1. tests/components/test_gmail_newsletter.py
2. tests/components/test_content_extraction.py
3. tests/components/test_readme_generation.py

### Current Working Files
1. Core Components:
   - agents/newsletter_monitor.py
   - agents/content_extractor.py
   - agents/readme_generator.py
   - agents/orchestrator.py (recently updated to remove curator)

2. Processing:
   - processing/embedchain_store.py
   - processing/core/newsletter_url_processor.py
   - processing/core/url_content_fetcher.py
   - processing/gmail/client.py

3. Database:
   - db/connection.py
   - db/migrations/*
   - config/taxonomy.yaml
   - README.template.md

Everything else in the project needs to be evaluated for cleanup, as the component tests represent the latest working implementation.

## Files to Remove

### 1. Removed Component Files
- [x] agents/repository_curator.py
- [x] tests/components/test_repository_curation.py

### 2. Outdated Tests
- [ ] tests/test_end_to_end.py (uses removed curator)
- [ ] tests/agents/test_repository_curator.py
- [ ] tests/agents/test_integration.py
- [ ] tests/components/test_topic_analysis.py
- [ ] tests/agents/test_orchestrator.py (needs review)
- [ ] tests/agents/test_readme_generator.py (needs review)

### 3. Outdated Production Scripts
- [ ] scripts/update_readme.py (replace with new pipeline runner)

## Files to Update

### 1. Configuration Files
- [ ] .env.test.template
- [ ] tests/config.py
- [ ] tests/conftest.py (remove curator references)

### 2. Documentation
- [ ] README.md
- [ ] dev_docs/setup_guide.md
- [ ] dev_docs/mvp_system_architecture.md
- [ ] dev_docs/implementation_plan.md

## Files to Create

### 1. Production Scripts
```python
# scripts/run_pipeline.py
"""Main pipeline runner script."""
import asyncio
import logging
from pathlib import Path
from agents.orchestrator import AgentOrchestrator
from processing.embedchain_store import EmbedchainStore
from agents.newsletter_monitor import NewsletterMonitor
from agents.content_extractor import ContentExtractorAgent
from agents.readme_generator import ReadmeGenerator
from db.connection import Database

async def main():
    """Run the complete pipeline."""
    # Initialize components
    db = Database()
    store = EmbedchainStore(token_path)
    
    # Create agents
    newsletter_monitor = NewsletterMonitor(gmail_client, store)
    content_extractor = ContentExtractorAgent(store, github_token)
    readme_generator = ReadmeGenerator(db)
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(
        embedchain_store=store,
        newsletter_monitor=newsletter_monitor,
        content_extractor=content_extractor,
        readme_generator=readme_generator
    )
    
    # Run pipeline
    await orchestrator.run_pipeline()

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Configuration Files
- [ ] config/pipeline_config.yaml
- [ ] .env.template (updated version)
- [ ] config/logging_config.yaml

### 3. Documentation
- [ ] docs/production_deployment.md
- [ ] docs/configuration_guide.md
- [ ] docs/monitoring_guide.md

## Implementation Order

1. Remove Outdated Files
   - Start with test files
   - Remove production scripts
   - Clean up documentation

2. Create New Files
   - Implement pipeline runner
   - Add configuration files
   - Create new documentation

3. Update Existing Files
   - Update configuration
   - Update remaining tests
   - Update documentation

4. Testing
   - Verify component tests still pass
   - Test new pipeline runner
   - Validate configurations

## Notes

- Keep backup of removed files until new implementation is verified
- Document all removed functionality in case it needs to be referenced
- Update issue tracker with cleanup progress
- Consider creating migration guide for any breaking changes
