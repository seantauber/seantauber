# Test Plan

This document outlines the test-driven development (TDD) approach for the GenAI Newsletter-Driven Repository Curator project.

## Testing Philosophy

1. Write tests first, then implement code
2. Each feature must have comprehensive test coverage
3. Tests should be independent and repeatable
4. Mock external services to ensure reliable testing for unit and integration tests
5. Use live dependencies for component testing to verify real-world behavior
6. Regular test suite execution in CI/CD pipeline

## Test Categories

### 1. Unit Tests

#### Database Models
- Test model validation
- Test relationships between models
- Test data integrity constraints
- Test model methods and properties

#### Vector Storage
- Test metadata management:
  - Content type classification
  - Relationship tracking
  - Metadata validation
  - Update operations
- Test relationship mapping:
  - Newsletter -> Repository links
  - Newsletter -> Web content links
  - Repository -> Related content
  - Topic -> Content associations
- Test retention policies:
  - Content aging
  - Archival triggers
  - Summarization process
  - Permanent storage
- Test unified collection:
  - Cross-content-type queries
  - Relationship-based searches
  - Metadata filtering
  - Context preservation

#### Gmail Integration
- Test credential loading
- Test email filtering
- Test content extraction
- Test error handling
- Mock Gmail API responses

#### Firecrawl Integration
- Test API client wrapper
- Test rate limit handling
- Test caching system
- Test error recovery
- Mock Firecrawl API responses

#### Agent Components
- Test individual agent behaviors
- Test agent state management
- Test agent communication
- Test error handling
- Mock dependencies

### 2. Integration Tests

#### Agent Workflow
- Test complete agent interaction cycles
- Test data flow between agents
- Test state persistence
- Test error propagation
- Test recovery mechanisms

#### External Services
- Test Gmail API integration
- Test Firecrawl API integration
- Test GitHub API integration
- Test error handling and retries
- Test rate limit compliance

#### Database Operations
- Test complex queries
- Test data migrations
- Test concurrent operations
- Test backup/restore procedures

#### Data Lifecycle Management
- Test content aging process:
  - Transition to archive storage
  - Data summarization
  - Relationship preservation
  - Historical trend maintenance
- Test archival operations:
  - Content summarization accuracy
  - Metadata preservation
  - Relationship maintenance
  - Storage optimization
- Test permanent storage:
  - Topic evolution tracking
  - Category structure history
  - Trend analysis data
  - Historical metrics

#### Vector Storage Integration
- Test unified collection operations:
  - Cross-content-type relationships
  - Complex query patterns
  - Metadata-based filtering
  - Context preservation
- Test retention workflow:
  - Aging process integration
  - Archival process integration
  - Permanent storage management
  - Data cleanup operations

### 3. Component Tests

#### Overview
Component tests verify functionality with live external dependencies to ensure real-world compatibility and performance. These tests:
- Use actual external services (Gmail, GitHub, LLM)
- Operate on production-like data
- Verify end-to-end workflows
- Collect evidence of functionality
- Monitor performance metrics

#### Test Environment
- Separate test credentials
- Dedicated test database
- Isolated vector storage
- Production-like configuration
- Comprehensive logging

#### Component Test Areas

1. Gmail/Newsletter Component
   - Live Gmail account integration
   - Real newsletter fetching
   - Vector storage creation
   - Database persistence
   - Historical tracking
   Evidence collection:
   - Fetched newsletters in database
   - Vector embeddings
   - Processing timestamps
   - Duplicate prevention logs

2. Content Extraction Component
   - Process actual newsletters
   - Extract live GitHub links
   - Real API calls for metadata
   - Live LLM interactions
   - Production database storage
   Evidence collection:
   - Extracted links vs source
   - GitHub API responses
   - Embedding quality metrics
   - Processing step logs

3. Topic Analysis Component
   - Live LLM categorization
   - Real repository processing
   - Actual GitHub topics
   - Production data updates
   Evidence collection:
   - LLM categorization responses
   - Topic hierarchy verification
   - Consistency checks
   - Analysis decision logs

4. Repository Curation Component
   - Live repository data
   - Real GitHub API usage
   - LLM duplicate detection
   - Actual metadata updates
   Evidence collection:
   - Metadata update records
   - Duplicate detection results
   - Data consistency checks
   - Curation decision logs

5. README Generation Component
   - Live database content
   - Actual markdown generation
   - Real category organization
   - Production README updates
   Evidence collection:
   - Generated content validation
   - Category organization checks
   - Format verification
   - Generation process logs

### 4. System Tests

#### End-to-End Workflow
- Test complete system operation
- Test GitHub Actions integration
- Test scheduled execution
- Test monitoring and alerts
- Test recovery from failures

#### Performance Tests
- Test processing speed
- Test memory usage
- Test API rate limit compliance
- Test concurrent operations
- Test system under load
- Test vector storage performance:
  - Query response times
  - Relationship traversal speed
  - Cross-content-type search
  - Large-scale operations
- Test retention system performance:
  - Archival process speed
  - Summarization efficiency
  - Storage optimization
  - Data access patterns

## Test Implementation Guidelines

### Test Structure
```python
# Example test structure
def test_newsletter_processing():
    # Arrange
    newsletter = create_test_newsletter()
    
    # Act
    result = process_newsletter(newsletter)
    
    # Assert
    assert result.repositories_found > 0
    assert result.categories_updated
    assert result.processing_status == 'completed'

# Vector storage test example
def test_content_relationships():
    # Arrange
    newsletter = create_test_newsletter()
    repository = create_test_repository()
    
    # Act
    storage.add_relationship(newsletter, repository, "mentions")
    
    # Assert
    assert storage.get_related_content(newsletter, "mentions") == [repository]
```

### Mocking Strategy
```python
# Example mock setup
@pytest.fixture
def mock_gmail_api():
    with patch('gmail.api.client') as mock_client:
        mock_client.get_messages.return_value = [
            create_test_message()
        ]
        yield mock_client

def test_gmail_integration(mock_gmail_api):
    result = fetch_newsletters()
    assert len(result) > 0
    mock_gmail_api.get_messages.assert_called_once()
```

### Test Data Management
- Use fixtures for common test data
- Implement data factories for complex objects
- Clean up test data after each test
- Use separate test database

## Continuous Integration

### GitHub Actions Workflow
```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: pip install -r requirements-dev.txt
      - name: Run tests
        run: pytest --cov
```

## Test Coverage Requirements

### Minimum Coverage Levels
- Unit Tests: 90% coverage
- Integration Tests: 80% coverage
- Component Tests: 70% coverage
- System Tests: 70% coverage

### Critical Areas (100% Coverage Required)
- Database models
- API integrations
- Agent state management
- Error handling
- Security-related code
- Vector storage operations
- Data retention processes

## Testing Tools

### Required Tools
- pytest for test execution
- pytest-cov for coverage reporting
- pytest-mock for mocking
- pytest-asyncio for async testing
- factory_boy for test data generation
- responses for HTTP mocking
- pytest-env for environment management
- python-dotenv for configuration
- requests for live API testing
- logging for evidence collection

### Development Tools
- black for code formatting
- flake8 for linting
- mypy for type checking
- bandit for security testing

## Test Documentation

### Test Case Template
```markdown
## Test Case: [ID] - [Name]

### Objective
[Description of what is being tested]

### Prerequisites
- [Required setup]
- [Required data]

### Steps
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Expected Results
- [Expected outcome 1]
- [Expected outcome 2]

### Actual Results
- [Actual outcome 1]
- [Actual outcome 2]

### Pass/Fail Criteria
- [Criterion 1]
- [Criterion 2]
```

## Test Execution

### Local Development
1. Run unit tests during development
2. Run integration tests before commit
3. Run component tests in isolated environment
4. Run full suite before push

### CI/CD Pipeline
1. Run all tests on push
2. Run all tests on pull request
3. Generate coverage report
4. Block merge if tests fail

## Test Maintenance

### Regular Tasks
1. Review and update tests monthly
2. Clean up test data
3. Update mock data
4. Review coverage reports
5. Update test credentials
6. Verify external service access
7. Monitor API usage and limits

### Test Debt Management
1. Track test issues in GitHub
2. Regular test refactoring
3. Update tests for new features
4. Remove obsolete tests

### Component Test Maintenance
1. Review and update test credentials monthly
2. Monitor external service health
3. Track API quotas and usage
4. Manage test data lifecycle
5. Rotate logs and evidence data
6. Update service expectations
7. Document API changes

## Security Testing

### Areas to Cover
1. API credential handling
2. Data encryption
3. Input validation
4. Error message security
5. Rate limiting

### Security Test Cases
1. Credential exposure
2. API authentication
3. Data validation
4. Error handling
5. Rate limit enforcement

## Performance Testing

### Metrics to Track
1. Processing time
2. Memory usage
3. API call frequency
4. Database operations
5. Response times

### Performance Test Cases
1. Large newsletter processing
2. Concurrent operations
3. Rate limit handling
4. Database scaling
5. Memory management

## Component Test Success Criteria

### Functionality Verification
1. All components operate with live services
2. Data flows through entire system
3. External APIs respond correctly
4. Vector operations work properly
5. Database updates succeed

### Performance Metrics
1. Response times within limits
2. API quota compliance
3. Resource usage acceptable
4. Error rates minimal
5. Processing speed adequate

### Evidence Quality
1. Logs provide clear tracking
2. All operations documented
3. Errors properly recorded
4. Metrics accurately captured
5. Results easily verified
