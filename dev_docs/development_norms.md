# Development Norms and Best Practices Guide

## Code Quality Standards

### 1. Python Style Guidelines
- Follow PEP 8 style guide
- Use type hints for all function parameters and return values
- Maximum line length: 88 characters (Black formatter standard)
- Use descriptive variable and function names
- Document all public functions and classes

Example:
```python
from typing import List, Optional

def process_newsletter(
    email_id: str,
    content: str,
    metadata: Optional[dict] = None
) -> List[str]:
    """
    Process newsletter content and extract repository links.

    Args:
        email_id: Unique identifier for the newsletter email
        content: Raw content of the newsletter
        metadata: Optional metadata about the newsletter

    Returns:
        List of extracted repository URLs
    """
    # Implementation
```

### 2. Code Organization
- One class per file
- Group related functionality in modules
- Use absolute imports
- Maintain clear module hierarchy

Example directory structure:
```
agents/
├── __init__.py
├── base.py
├── newsletter_monitor.py
├── content_extractor.py
└── utils/
    ├── __init__.py
    └── parsing.py
```

### 3. Error Handling
- Use custom exceptions for domain-specific errors
- Always catch specific exceptions
- Provide meaningful error messages
- Log errors appropriately

Example:
```python
class NewsletterProcessingError(Exception):
    """Raised when newsletter processing fails."""
    pass

try:
    process_newsletter(email_id, content)
except NewsletterProcessingError as e:
    logger.error(f"Failed to process newsletter {email_id}: {str(e)}")
    raise
except Exception as e:
    logger.error(f"Unexpected error processing newsletter {email_id}: {str(e)}")
    raise NewsletterProcessingError(f"Unexpected error: {str(e)}")
```

## Testing Standards

### 1. Test Organization
- Mirror production code structure in tests
- Use descriptive test names
- Group related tests in classes
- Use appropriate fixtures

Example:
```python
class TestNewsletterProcessor:
    @pytest.fixture
    def sample_newsletter(self):
        return {
            "email_id": "test123",
            "content": "Sample content",
            "metadata": {"date": "2024-01-15"}
        }

    def test_valid_newsletter_processing(self, sample_newsletter):
        result = process_newsletter(**sample_newsletter)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_invalid_newsletter_handling(self, sample_newsletter):
        with pytest.raises(NewsletterProcessingError):
            process_newsletter(**{**sample_newsletter, "content": None})
```

### 2. Test Coverage Requirements
- Minimum 90% code coverage
- 100% coverage for critical paths
- Test edge cases and error conditions
- Include integration tests

### 3. Test Data Management
- Use fixtures for common test data
- Avoid hard-coded test values
- Clean up test data after tests
- Use appropriate mocks for external services

## Development Workflow

### 1. Git Practices
- Use feature branches
- Branch naming: `feature/`, `bugfix/`, `hotfix/`
- Commit message format:
  ```
  type(scope): description

  [optional body]
  [optional footer]
  ```
- Squash commits before merging

Example:
```bash
# Good commit messages
feat(newsletter): add Gmail integration
fix(database): handle concurrent access
test(agents): add integration tests
```

### 2. Code Review Process
- All changes require review
- Maximum 400 lines per review
- Address all comments
- Update tests and documentation
- Verify CI pipeline passes

### 3. Documentation Requirements
- Update README for new features
- Document all public APIs
- Include example usage
- Update architecture docs for significant changes

## Database Practices

### 1. Schema Changes
- Use migrations for all changes
- Version control migrations
- Test migration rollbacks
- Document schema changes

Example:
```python
# migrations/001_add_newsletter_table.py
def upgrade():
    """Create newsletter table."""
    execute("""
        CREATE TABLE newsletters (
            id INTEGER PRIMARY KEY,
            email_id TEXT NOT NULL UNIQUE,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

def downgrade():
    """Remove newsletter table."""
    execute("DROP TABLE newsletters")
```

### 2. Query Standards
- Use parameterized queries
- Optimize for performance
- Handle transactions properly
- Log slow queries

Example:
```python
def get_newsletter(email_id: str) -> Optional[Dict]:
    """Retrieve newsletter by email ID."""
    query = """
        SELECT id, email_id, content, created_at
        FROM newsletters
        WHERE email_id = ?
    """
    with db.transaction():
        return db.fetch_one(query, (email_id,))
```

## Logging and Monitoring

### 1. Logging Standards
- Use appropriate log levels
- Include context in log messages
- Structure logs for parsing
- Rotate log files

Example:
```python
logger.info("Processing newsletter", extra={
    "email_id": email_id,
    "processor": "ContentExtractor",
    "timestamp": datetime.utcnow().isoformat()
})
```

### 2. Monitoring Requirements
- Track key metrics
- Set up alerts for errors
- Monitor performance
- Regular health checks

## Security Practices

### 1. Credential Management
- Use environment variables
- Never commit secrets
- Rotate credentials regularly
- Use secure credential storage

Example:
```python
# config.py
import os
from typing import Optional

def get_api_key(key_name: str) -> Optional[str]:
    """Safely retrieve API key from environment."""
    return os.environ.get(f"APP_{key_name.upper()}_KEY")
```

### 2. Input Validation
- Validate all inputs
- Sanitize data
- Use prepared statements
- Handle sensitive data properly

Example:
```python
def validate_email_id(email_id: str) -> bool:
    """Validate email ID format and content."""
    if not isinstance(email_id, str):
        return False
    if len(email_id) > 255:
        return False
    return bool(re.match(r'^[a-zA-Z0-9._-]+$', email_id))
```

## Performance Guidelines

### 1. Code Optimization
- Profile before optimizing
- Use appropriate data structures
- Optimize database queries
- Cache when appropriate

### 2. Resource Management
- Close connections properly
- Use context managers
- Handle memory efficiently
- Clean up temporary resources

Example:
```python
class DatabaseConnection:
    def __enter__(self):
        self.conn = create_connection()
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()

with DatabaseConnection() as conn:
    process_data(conn)
```

## Deployment Practices

### 1. Release Process
- Tag releases semantically
- Update changelog
- Test in staging
- Automated deployment

### 2. Configuration Management
- Use environment variables
- Separate config from code
- Version control configs
- Document all settings

Example:
```python
# settings.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    """Application settings."""
    database_url: str
    api_key: str
    debug: bool = False
    max_retries: int = 3

    class Config:
        env_prefix = "APP_"
```

Remember: These guidelines are meant to help maintain code quality and consistency. They should be reviewed and updated regularly based on team feedback and project needs.
