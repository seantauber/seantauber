# GenAI Newsletter-Driven Repository Curator

## Overview
A system that automatically updates a GitHub README with curated AI/ML repositories sourced from Gmail newsletters, using AI to maintain an organized and evolving category structure.

## Core Requirements

### 1. Data Source Integration
- Connect to Gmail API using provided credentials in .credentials folder
- Filter and retrieve emails with "GenAI News" label
- Use Embedchain for:
  - Gmail interaction and content retrieval
  - Vector storage of newsletter content
  - Vector storage of followed links and repository content
  - Semantic search capabilities across all stored content
- Enable efficient historical analysis through vector search

### 2. Content Analysis & Organization
- Use LLMs through agent system to:
  - Analyze newsletter content for key topics
  - Identify and track topic evolution
  - Make flexible decisions about topic categorization
- Maintain dynamic topic structure through:
  - Daily topic analysis of newsletters
  - Historical topic tracking
  - Organic topic evolution
  - Relationship mapping between topics
- Consider repository importance based on:
  - Mention frequency
  - Recency
  - Context of mentions
  - Repository quality metrics

### 3. Web Content Retrieval
- Use Firecrawl API to:
  - Fetch repository information
  - Extract relevant metadata
  - Handle rate limits appropriately
- Follow links from newsletters to gather additional context
- Store retrieved content in vector database for:
  - Enhanced context during analysis
  - Historical reference
  - Relationship discovery
- Cache API responses to minimize usage

### 4. Storage Requirements
- Primary Database: SQLite
  - Chosen for simplicity and no separate server requirement
  - Store system state and operational data
  - Track agent operations and decisions
  - Maintain configuration and settings

- Vector Storage (via Embedchain):
  - Single unified collection with rich metadata
  - Content types tracked via metadata:
    - Newsletters
    - Repository information
    - Web content
  - Relationship tracking:
    - Newsletter -> Repository links
    - Newsletter -> Web content links
    - Repository -> Related content
    - Topic -> Content associations
  - Semantic search and analysis capabilities
  - Contextual querying across all content types

- Retention Policy:
  - Active Storage (0-6 months):
    - Full content of newsletters
    - Complete repository information
    - All web content
    - Detailed relationship data
  - Archive Storage (6-24 months):
    - Summarized newsletter content
    - Key repository metadata
    - Topic relationship data
    - Trend information
  - Permanent Storage:
    - Topic evolution history
    - Category structure changes
    - Repository importance metrics
    - Historical trends

- Cache System:
  - API response caching
  - Temporary computation results
  - Frequently accessed data

### 5. Agent Workflow
- Implement using Pydantic Agents framework
- Key agents needed:
  1. Newsletter Monitor: Checks for new newsletters
  2. Content Extractor: Processes newsletters and extracts repos
  3. Topic Analyzer: Identifies and tracks topics over time
  4. Repository Curator: Selects repos for inclusion
  5. README Generator: Creates the final markdown
- Agents should follow guidelines detailed in agent_guidelines.md

### 6. Testing Requirements
- Unit tests for each component
- Integration tests for agent workflows
- Mock external services (Gmail, Firecrawl)
- Test topic evolution scenarios
- Validate README generation
- Test vector storage operations
- Validate semantic search functionality

## Technical Stack

### Core Technologies
- Python 3.8+
- Gmail API
- Embedchain (with vector storage)
- Pydantic Agents
- Firecrawl API
- SQLite

### Key Libraries
- embedchain[gmail] for Gmail integration and vector storage
- pydantic-ai for agent framework
- firecrawl-py for web scraping
- sqlite3 for database operations
- pytest for testing

## Non-Functional Requirements

### Performance
- Complete daily updates within reasonable timeframe
- Efficient use of API rate limits
- Optimize vector storage operations
- Minimize unnecessary API calls through caching

### Reliability
- Handle API failures gracefully
- Maintain data consistency
- Provide detailed logging
- Ensure vector storage backup

### Maintainability
- Clear code structure
- Comprehensive documentation
- Easy configuration management
- Simple deployment (no separate services required)

### Security
- Secure handling of API credentials
- Safe storage of cached content
- Proper error handling to prevent data leaks
- Protected vector storage access

## Operational Requirements

### Daily Update Process
- Scheduled to run once per day via GitHub Actions
- Process:
  1. Fetch new newsletters
  2. Update vector storage
  3. Analyze topics and trends
  4. Update README
  5. Archive old content as needed

### Data Management
- Automatic archival process for content > 6 months old
- Summarization of archived content
- Regular database optimization
- Vector storage maintenance
- Cache cleanup

### Monitoring
- Track storage usage
- Monitor processing times
- Alert on failures
- Report on data retention status

## Future Considerations
- Support for additional newsletter sources
- Enhanced trend analysis using vector similarity
- API for external access to curated content
- Advanced repository scoring algorithms
- Topic visualization tools
- Enhanced relationship mapping
