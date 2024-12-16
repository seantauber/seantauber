# Component Testing Guide

This guide explains how to run and maintain the component tests that verify functionality with live external dependencies.

## Overview

The component tests validate each system component's functionality using real external services:
- Gmail API for newsletter fetching
- GitHub API for repository data
- LLM services for analysis
- Vector storage for embeddings
- SQLite database for persistence

## Prerequisites

Before running the tests, ensure you have:

1. Gmail API credentials configured
2. GitHub API token set up
3. LLM API key configured
4. Test database initialized
5. Vector storage properly configured

## Configuration

Create a `.env.test` file in the project root with the following:

```bash
# Gmail API
GMAIL_CREDENTIALS_PATH=/path/to/credentials.json
GMAIL_TOKEN_PATH=/path/to/token.json

# GitHub API
GITHUB_TOKEN=your_github_token

# LLM Configuration
OPENAI_API_KEY=your_openai_key

# Vector Storage
VECTOR_STORAGE_PATH=/path/to/vector/storage

# Database
TEST_DATABASE_PATH=/path/to/test.db
```

## Running Tests

### Full Component Test Suite

Run all component tests:

```bash
pytest tests/component_tests.py -v
```

### Individual Component Tests

Test specific components:

```bash
# Gmail/Newsletter tests
pytest tests/component_tests.py::TestGmailNewsletterComponent -v

# Content Extraction tests
pytest tests/component_tests.py::TestContentExtractionComponent -v

# Topic Analysis tests
pytest tests/component_tests.py::TestTopicAnalysisComponent -v

# Repository Curation tests
pytest tests/component_tests.py::TestRepositoryCurationComponent -v

# README Generation tests
pytest tests/component_tests.py::TestReadmeGenerationComponent -v

# End-to-end flow test
pytest tests/component_tests.py::test_end_to_end_flow -v
```

## Test Evidence Collection

The tests automatically collect evidence through logging. Logs include:
- Timestamps for operations
- Success/failure status
- Key metrics and counts
- Processing details
- Error information

Logs are written to `component_tests.log` with the format:
```
YYYY-MM-DD HH:MM:SS - ComponentName - Level - Message
```

## Maintenance

### Adding New Tests

1. Identify the appropriate component test class
2. Add new test method with clear name and docstring
3. Include proper logging statements
4. Verify external dependencies
5. Update documentation

Example:
```python
def test_new_feature(self, component):
    """Test description of new feature."""
    logger.info("Starting new feature test")
    
    # Test implementation
    result = component.new_feature()
    
    # Verification
    assert result is not None
    
    # Logging
    logger.info(f"New feature test completed: {result}")
```

### Updating Tests

When updating existing tests:
1. Maintain backwards compatibility
2. Update documentation
3. Verify external dependencies
4. Test with production credentials
5. Update logging as needed

## Troubleshooting

### Common Issues

1. API Authentication
   - Verify credentials are properly configured
   - Check token expiration
   - Confirm API permissions

2. Rate Limiting
   - Monitor API usage
   - Implement proper delays
   - Use test account quotas

3. Data Consistency
   - Verify database state
   - Check vector storage integrity
   - Validate test data

### Error Recovery

1. API Errors
   - Check error messages
   - Verify credentials
   - Confirm service status

2. Database Errors
   - Verify connection
   - Check schema version
   - Validate data integrity

3. Vector Storage Errors
   - Check storage path
   - Verify permissions
   - Confirm space availability

## Best Practices

1. Test Independence
   - Each test should be self-contained
   - Clean up test data
   - Don't rely on other tests

2. Resource Management
   - Close connections properly
   - Clean up temporary files
   - Manage API quotas

3. Error Handling
   - Log all errors
   - Provide context
   - Include recovery steps

4. Documentation
   - Keep docs updated
   - Include examples
   - Document dependencies

## Monitoring

Monitor test execution:
1. Check logs regularly
2. Review error patterns
3. Track API usage
4. Monitor performance
5. Verify data integrity

## Success Criteria

Tests should verify:
1. Component functionality
2. External integration
3. Data consistency
4. Error handling
5. Performance metrics

## Reporting

Generate test reports:
1. Test results summary
2. Error logs
3. Performance metrics
4. Coverage data
5. Integration status

Remember to regularly review and update this documentation as the system evolves.
