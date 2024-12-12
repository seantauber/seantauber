# MVP Plan for GenAI Newsletter-Driven Repository Curator

## MVP Scope

### Core Features for MVP

1. Basic Newsletter Processing
   - Gmail integration with basic filtering
   - Simple content extraction
   - Storage of newsletter content in SQLite
   - Backlog processing capability

2. Essential Repository Management
   - GitHub repository link extraction
   - Basic repository metadata storage
   - Simple categorization system

3. Minimal Topic System
   - Basic topic identification
   - Fixed category structure (no dynamic evolution yet)
   - Simple parent/child relationships

4. README Generation
   - Basic markdown generation
   - Static category organization
   - Simple repository listing

### Features Excluded from MVP

1. Advanced Topic Analysis
   - Dynamic topic evolution
   - Complex relationship mapping
   - Historical trend analysis

2. Vector Storage Features
   - Semantic search capabilities
   - Relationship discovery
   - Content similarity analysis

3. Advanced Content Processing
   - Web content crawling
   - Deep context extraction
   - Content summarization

4. Complex Data Management
   - Content archival system
   - Tiered storage
   - Cache management

## Test-Driven Development Approach

### Testing Framework Setup (Day 1)
1. Core Test Infrastructure
   ```python
   # Example test structure
   class TestNewsletterProcessing:
       def test_gmail_connection(self):
           # Test Gmail API connection
           pass
           
       def test_newsletter_filtering(self):
           # Test newsletter identification
           pass
           
       def test_content_extraction(self):
           # Test content parsing
           pass
   ```

2. Mock Services
   ```python
   # Example mock setup
   class MockGmailService:
       def __init__(self, test_data):
           self.newsletters = test_data
           
       def get_messages(self):
           return self.newsletters
   ```

3. Test Data Fixtures
   ```python
   # Example fixtures
   @pytest.fixture
   def sample_newsletters():
       return [
           {
               "id": "msg1",
               "content": "Sample newsletter content...",
               "date": "2024-01-15"
           }
       ]
   ```

## Implementation Plan with Checkpoints

### Phase 1: Core Infrastructure (Week 1)

#### Checkpoint 1.1: Database & Tests (Days 1-2)
- Deliverable: Working database with test suite
- Demo: Run tests showing database CRUD operations
```sql
-- Essential tables only
CREATE TABLE newsletters (
    id INTEGER PRIMARY KEY,
    email_id TEXT NOT NULL UNIQUE,
    received_date TIMESTAMP NOT NULL,
    processed_date TIMESTAMP,
    content TEXT,
    metadata JSON
);

CREATE TABLE repositories (
    id INTEGER PRIMARY KEY,
    github_url TEXT NOT NULL UNIQUE,
    first_seen_date TIMESTAMP NOT NULL,
    last_mentioned_date TIMESTAMP NOT NULL,
    mention_count INTEGER DEFAULT 1,
    metadata JSON
);

CREATE TABLE topics (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    parent_topic_id INTEGER,
    FOREIGN KEY (parent_topic_id) REFERENCES topics(id)
);

CREATE TABLE repository_categories (
    id INTEGER PRIMARY KEY,
    repository_id INTEGER NOT NULL,
    topic_id INTEGER NOT NULL,
    FOREIGN KEY (repository_id) REFERENCES repositories(id),
    FOREIGN KEY (topic_id) REFERENCES topics(id)
);
```

#### Checkpoint 1.2: Gmail Integration (Days 3-4)
- Deliverable: Working Gmail API integration with tests
- Demo: Fetch and display sample newsletters
- Test Coverage: API connection, filtering, error handling

#### Checkpoint 1.3: Initial Testing (Day 5)
- Deliverable: Complete test suite for core infrastructure
- Demo: Run full test suite with coverage report
- Review: Code quality and test coverage metrics

### Phase 2: Core Agents (Week 2)

#### Checkpoint 2.1: Newsletter Processing (Days 1-2)
- Deliverable: Working newsletter processor with tests
- Demo: Process sample newsletters end-to-end
- Test Coverage: Content extraction, storage, error cases

#### Checkpoint 2.2: Repository Extraction (Days 3-4)
- Deliverable: Working repository extractor with tests
- Demo: Extract and categorize repositories from newsletters
- Test Coverage: URL extraction, metadata collection

#### Checkpoint 2.3: Integration Testing (Day 5)
- Deliverable: Integrated workflow with tests
- Demo: End-to-end processing of test newsletters
- Review: System integration and error handling

### Phase 3: Backlog Processing & Refinement (Week 3)

#### Checkpoint 3.1: Backlog Handler (Days 1-2)
- Deliverable: Newsletter backlog processor
- Demo: Process subset of historical newsletters
- Features:
  - Batch processing capability
  - Progress tracking
  - Error recovery
  - Rate limiting for API calls
  - Resumable processing

#### Checkpoint 3.2: README Generation (Days 3-4)
- Deliverable: README generator with tests
- Demo: Generate README from processed data
- Test Coverage: Markdown generation, category organization

#### Checkpoint 3.3: Final Integration (Day 5)
- Deliverable: Complete MVP with all tests
- Demo: Full system operation including backlog processing
- Review: System stability and performance metrics

## Backlog Processing Strategy

### Phase 1: Initial Setup
1. Create backlog processing module
   ```python
   class BacklogProcessor:
       def __init__(self, batch_size=10):
           self.batch_size = batch_size
           self.progress_tracker = ProgressTracker()
           
       def process_batch(self, newsletters):
           # Process newsletters in small batches
           pass
           
       def resume_from_checkpoint(self):
           # Resume from last successful point
           pass
   ```

### Phase 2: Batch Processing
1. Process in batches of 10 newsletters
2. Store progress checkpoints
3. Implement rate limiting
4. Track processing statistics

### Phase 3: Validation
1. Verify processed data integrity
2. Generate processing reports
3. Handle error cases and retries

## Success Criteria

### Technical Requirements
1. Test Coverage
   - Core functionality: > 90% coverage
   - Integration tests: > 80% coverage
   - End-to-end tests: Key workflows covered

2. Performance
   - Newsletter processing: < 30 seconds per newsletter
   - Backlog processing: < 8 hours for full backlog
   - Daily updates: < 15 minutes

3. Reliability
   - Zero data loss
   - Graceful error handling
   - Resumable operations

### Functional Requirements
1. Newsletter Processing
   - 100% successful Gmail connection
   - Accurate newsletter filtering
   - Complete content extraction

2. Repository Management
   - 95% accurate URL extraction
   - Correct metadata collection
   - Proper categorization

3. README Generation
   - Consistent formatting
   - Accurate categorization
   - Daily updates

## Development Guidelines

### Testing Practices
1. Write tests before implementation
2. Maintain test fixtures and mocks
3. Regular test coverage reviews
4. Integration test scenarios

### Code Quality
1. Type hints and docstrings
2. Clear module structure
3. Comprehensive documentation
4. Regular code reviews

### Deployment
1. Simple setup process
2. Clear configuration
3. Basic monitoring
4. Error logging

## Timeline with Deliverables

### Week 1: Infrastructure
- Day 1: Database tests & implementation
- Day 2: Database integration tests
- Day 3: Gmail API tests
- Day 4: Gmail integration
- Day 5: Infrastructure test suite
- Deliverable: Tested core infrastructure

### Week 2: Core Functionality
- Day 1: Newsletter processor tests
- Day 2: Newsletter processor implementation
- Day 3: Repository extractor tests
- Day 4: Repository extractor implementation
- Day 5: Integration tests
- Deliverable: Working core system with tests

### Week 3: Backlog & Integration
- Day 1: Backlog processor tests
- Day 2: Backlog processor implementation
- Day 3: README generator tests
- Day 4: README generator implementation
- Day 5: Final integration & testing
- Deliverable: Complete MVP with backlog processing

## Success Metrics

### Testing Metrics
- Test coverage targets met
- All test suites passing
- Integration tests successful
- Performance tests within bounds

### Processing Metrics
- Newsletter processing success rate
- Repository extraction accuracy
- Categorization correctness
- Backlog processing completion

### System Metrics
- Error rate < 5%
- Processing time within limits
- Resource usage within bounds
- Zero data loss incidents
