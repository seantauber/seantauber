# Library Implementation Details

## Embedchain Integration

### Gmail Setup
```python
# Required installation
pip install --upgrade embedchain[gmail]
```

### Configuration Steps
1. Setup Google Cloud Project and enable Gmail API
2. Create OAuth consent screen
3. Enable Gmail API
4. Create credentials (OAuth Client ID)
5. Add redirect URI for http://localhost:8080/
6. Save credentials.json in project directory

### Usage Pattern
```python
from embedchain import App

app = App()

# Gmail filter query syntax
gmail_filter = "to: me label:inbox"
app.add(gmail_filter, data_type="gmail")
```

### Vector Storage Configuration
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

## Pydantic Agent System

### Core Components
1. System Prompts
   - Static prompts defined at construction
   - Dynamic prompts generated at runtime
   - Multiple prompts can be combined

2. Function Tools
   - Tools that need context: `@agent.tool`
   - Context-free tools: `@agent.tool_plain`
   - Tool registration via constructor: `tools=[tool1, tool2]`

3. Type Safety
   - Runtime validation through Pydantic models
   - Static type checking support
   - Generic typing for dependencies and results

### Agent Execution Patterns
```python
# Three execution modes:
1. await agent.run()       # Coroutine
2. agent.run_sync()        # Synchronous
3. await agent.run_stream() # Streaming response
```

### Error Handling
- ModelRetry for validation failures
- UnexpectedModelBehavior for model errors
- Access to message history via agent.last_run_messages

## Firecrawl Integration

### Core Features
1. Scraping Capabilities
   - Clean markdown output
   - Structured data extraction
   - PDF parsing support
   - Dynamic content handling

2. Crawling Configuration
   - URL pattern filtering
   - Depth control
   - Rate limiting compliance
   - External link handling

### API Usage Pattern
```python
from firecrawl import FirecrawlApp

app = FirecrawlApp(api_key="YOUR_API_KEY")

# Single page scraping
result = app.scrape_url(url, params={
    'formats': ['markdown', 'html'],
    'onlyMainContent': True
})

# Multi-page crawling
crawl_status = app.crawl_url(url, params={
    'limit': 100,
    'maxDepth': 2,
    'excludePaths': ['admin/*'],
    'scrapeOptions': {
        'formats': ['markdown']
    }
})
```

### Rate Limits
- Scrape: 10-1000 requests/min (plan dependent)
- Crawl: 1-50 requests/min (plan dependent)
- Status checks: 150 requests/min

### Error Handling
- Retry mechanisms for transient failures
- Timeout handling
- Rate limit compliance
- Status monitoring for long-running crawls

## Integration Architecture

### Data Flow
1. Gmail Integration
   - Newsletter retrieval via Embedchain
   - Content embedding into vector storage
   - Metadata extraction and storage

2. Web Content Processing
   - URL extraction from newsletters
   - Content retrieval via Firecrawl
   - Clean content storage in vector database

3. Agent Operations
   - Type-safe data handling via Pydantic
   - Structured decision making
   - Content analysis and categorization

### Storage Integration
1. Vector Storage (Embedchain)
   - Newsletter content embeddings
   - Repository content embeddings
   - Relationship mappings

2. Traditional Storage (SQLite)
   - System state
   - Operation logs
   - Configuration data
   - Cache management

3. Cross-Storage Relationships
   - Vector IDs in SQLite records
   - SQLite IDs in vector metadata
   - Bidirectional relationship tracking
