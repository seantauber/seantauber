# GitHub GenAI Repository Curation Pipeline

## System Overview

This system implements an automated pipeline for discovering, analyzing, and curating GitHub repositories related to Generative AI and Large Language Models. The pipeline processes AI/ML-focused newsletters to identify and categorize relevant repositories, maintaining a dynamic, curated list with rich metadata and categorization.

## Pipeline Architecture

The system consists of three stages, with the first two stages currently implemented:

### Stage 1: Newsletter Ingestion
Implemented in `tests/components/test_gmail_newsletter.py`
- Fetches AI/ML newsletters from Gmail
- Processes and stores raw content
- Generates vector embeddings for semantic analysis
- Maintains historical tracking

### Stage 2: Content Extraction
Implemented in `tests/components/test_content_extraction.py`
- Extracts GitHub repositories from newsletter content
- Analyzes repositories for GenAI relevance
- Categorizes repositories using taxonomy
- Maintains repository database

### Stage 3: README Generation
(Not yet implemented)
- Will generate dynamic README content
- Will organize repositories by category
- Will update repository listing

## Core Components

### Newsletter Processing
1. NewsletterMonitor
   - Core orchestrator for newsletter operations
   - Manages parallel processing with configurable batch sizes
   - Handles state tracking and error recovery
   - Maintains processing queue and statistics

2. GmailClient
   - Authenticates with Gmail API
   - Fetches newsletters using configured filters
   - Extracts email metadata
   - Handles rate limiting and quotas

3. EmbedchainStore
   - Generates vector embeddings from content
   - Manages persistent storage of embeddings
   - Enables semantic search capabilities
   - Links embeddings to newsletter records

### Content Analysis
1. ContentExtractorAgent
   - Orchestrates repository discovery
   - Manages GitHub API interactions
   - Implements categorization logic
   - Maintains processing state

2. RateLimitedGitHubClient
   - Handles GitHub API authentication
   - Manages API rate limits
   - Fetches repository metadata
   - Implements backoff strategies

3. NewsletterUrlProcessor
   - Extracts URLs from content
   - Validates and normalizes URLs
   - Handles content fetching and caching
   - Discovers embedded references

## Database Schema

### Core Tables

#### newsletters
```sql
CREATE TABLE newsletters (
    id INTEGER PRIMARY KEY,
    email_id TEXT NOT NULL UNIQUE,
    received_date TIMESTAMP NOT NULL,
    processed_date TIMESTAMP,
    storage_status TEXT NOT NULL,
    vector_id TEXT,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### repositories
```sql
CREATE TABLE repositories (
    id INTEGER PRIMARY KEY,
    github_url TEXT NOT NULL UNIQUE,
    first_seen_date TIMESTAMP NOT NULL,
    last_mentioned_date TIMESTAMP NOT NULL,
    metadata JSON
);
```

### Classification Tables

#### topics
```sql
CREATE TABLE topics (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    first_seen_date TIMESTAMP NOT NULL,
    last_seen_date TIMESTAMP NOT NULL,
    mention_count INTEGER
);
```

#### repository_categories
```sql
CREATE TABLE repository_categories (
    repository_id INTEGER,
    topic_id INTEGER,
    confidence_score FLOAT,
    PRIMARY KEY (repository_id, topic_id)
);
```

### Support Tables

#### content_cache
```sql
CREATE TABLE content_cache (
    id INTEGER PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    content_type TEXT NOT NULL,
    content BLOB NOT NULL,
    last_accessed TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL
);
```

## Implementation Details

### Parallel Processing
- Configurable batch sizes (BATCH_SIZE constant)
- Concurrent processing of newsletters and repositories
- Safe database transaction management
- API rate limit handling

### Error Handling
- Graceful failure recovery
- Partial progress maintenance
- Detailed error logging
- Process resumption capability

### State Management
- Processing status tracking
- Interrupted operation handling
- Process monitoring
- Audit trail maintenance

## Integration Points

### External Services
1. Gmail API
   - Requires configured credentials
   - Uses OAuth authentication
   - Implements newsletter filtering

2. GitHub API
   - Requires API token
   - Implements rate limiting
   - Fetches repository data

### Internal Components
1. Vector Store
   - Stores newsletter embeddings
   - Enables semantic search
   - Links to newsletter records

2. Database
   - Maintains relationships
   - Stores processing state
   - Enables efficient querying

## Developer Guide

### Setting Up
1. Configure Credentials
   ```bash
   # Gmail API setup
   cp .env.template .env
   # Edit .env with credentials
   
   # GitHub token
   export GITHUB_TOKEN=your_token_here
   ```

2. Initialize Database
   ```python
   from db.migrations import MigrationManager
   from db.connection import Database
   
   db = Database()
   migration_manager = MigrationManager(db)
   migration_manager.apply_migrations()
   ```

### Running the Pipeline
1. Stage 1: Newsletter Ingestion
   ```python
   from agents.newsletter_monitor import NewsletterMonitor
   
   monitor = NewsletterMonitor(gmail_client, store, db)
   results = await monitor.run(max_results=10)
   ```

2. Stage 2: Content Extraction
   ```python
   from agents.content_extractor import ContentExtractorAgent
   
   extractor = ContentExtractorAgent(github_token, db)
   results = await extractor.process_newsletter_content(email_id, content)
   ```

### Monitoring
1. Pipeline State
   ```python
   # Check processing status
   stage_status = extractor.pipeline_state.get_stage_status("content_extraction")
   print(f"Completed: {stage_status['completed']}")
   print(f"Failed: {stage_status['failed']}")
   ```

2. Error Handling
   ```python
   try:
       await monitor.process_newsletters()
   except Exception as e:
       logger.error(f"Pipeline failed: {str(e)}")
       # Implement recovery logic
   ```

## Production Considerations

### Performance
- Optimize batch sizes
- Monitor memory usage
- Balance parallelism
- Implement caching

### Reliability
- Implement retries
- Store partial progress
- Log detailed errors
- Regular backups

### Monitoring
- Track success rates
- Monitor API quotas
- Measure processing times
- Alert on failures

## Future Enhancements

1. Stage 3 Implementation
   - README generation
   - Category organization
   - Dynamic updates

2. Additional Features
   - Enhanced categorization
   - More metadata extraction
   - Advanced search capabilities

3. System Improvements
   - Additional error recovery
   - Performance optimization
   - Extended monitoring
