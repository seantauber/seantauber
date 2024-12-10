# Implementation Prompt: DatabaseManager Singleton Pattern

## Context
The current implementation of DatabaseManager creates multiple instances across different tools and agents, each initializing with cleanup=True by default. This causes data loss as each new instance cleans up the database tables. We need to implement a singleton pattern to ensure a single DatabaseManager instance is shared across the application, with controlled cleanup behavior.

## Current Issue
```python
# Current implementation in db/database.py
class DatabaseManager:
    def __init__(self, db_path: str = "db/github_repos.db", cleanup: bool = True):
        self.db_path = db_path
        self.init_db()
        if cleanup:
            self.cleanup_database()
```

Each tool creates its own instance:
```python
def store_raw_repos(repos: List[Dict], source: str) -> str:
    db_manager = DatabaseManager()  # New instance with cleanup=True

def get_unprocessed_repos(batch_size: int = 10) -> List[Dict]:
    db_manager = DatabaseManager()  # Another instance with cleanup=True
```

## Required Changes

1. Modify DatabaseManager to implement singleton pattern:
   - Add class-level instance tracking
   - Implement __new__ for singleton behavior
   - Add initialization tracking
   - Default cleanup to False
   - Add state verification

2. Update all database interactions in tools:
   - Remove cleanup flag from normal usage
   - Use singleton instance consistently
   - Add state verification calls

3. Add database state monitoring:
   - Implement state logging
   - Add transaction tracking
   - Monitor table contents

## Implementation Requirements

1. DatabaseManager Singleton:
   - Must ensure only one instance exists
   - Must track initialization state
   - Must control cleanup behavior
   - Must provide state verification
   - Must maintain existing functionality

2. Tool Updates:
   - Must update all database interactions
   - Must remove cleanup flag from normal usage
   - Must add state verification
   - Must maintain existing error handling

3. Monitoring:
   - Must implement comprehensive logging
   - Must track database state
   - Must monitor cleanup operations
   - Must verify data persistence

## Files to Modify

1. db/database.py:
   - Implement singleton pattern
   - Add state verification
   - Update initialization logic
   - Enhance logging

2. crew.py:
   - Update tool implementations
   - Add state verification calls
   - Remove cleanup flags

## Testing Requirements

1. Singleton Behavior:
   - Verify single instance
   - Test initialization tracking
   - Validate cleanup control

2. Data Persistence:
   - Test data storage
   - Verify between tasks
   - Check cleanup scenarios

3. Error Handling:
   - Test error scenarios
   - Verify recovery
   - Validate logging

## Success Criteria

1. Single DatabaseManager instance maintained across application
2. Data persists between tasks without unintended cleanup
3. Cleanup only occurs when explicitly requested
4. Complete state tracking and verification
5. Comprehensive error handling and logging

## Implementation Guidelines

1. Follow existing code style and patterns
2. Maintain comprehensive logging
3. Add clear documentation
4. Include type hints
5. Follow SOLID principles
6. Ensure backward compatibility
7. Add proper error handling
8. Include state verification

## Example Implementation Structure

```python
class DatabaseManager:
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, db_path: str = "db/github_repos.db", cleanup: bool = False):
        if not self._initialized:
            self._initialized = True
            self.db_path = db_path
            self.init_db()
            if cleanup:  # Only cleanup if explicitly requested
                self.cleanup_database()
    
    def verify_state(self):
        """Verify database state and table contents."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM raw_repositories")
            raw_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM analyzed_repositories")
            analyzed_count = cursor.fetchone()[0]
            logger.info(f"Database state - Raw repos: {raw_count}, Analyzed: {analyzed_count}")
```

## Testing Steps

1. Singleton Pattern:
```python
# Test singleton behavior
db1 = DatabaseManager()
db2 = DatabaseManager()
assert db1 is db2  # Should be same instance

# Test cleanup control
db = DatabaseManager(cleanup=False)
# Add test data
db_new = DatabaseManager(cleanup=False)  # Should not clean up
# Verify data persists
```

2. Data Persistence:
```python
# Test data storage
db = DatabaseManager(cleanup=False)
# Store test data
# Create new instance
db_new = DatabaseManager(cleanup=False)
# Verify data exists
```

3. State Verification:
```python
# Test state tracking
db = DatabaseManager(cleanup=False)
# Add test data
db.verify_state()  # Should show correct counts
```

## Notes

- Ensure backward compatibility
- Maintain existing functionality
- Add comprehensive logging
- Include proper error handling
- Add state verification
- Test thoroughly
- Document changes

## Implementation Timeline

1. Day 1:
   - Implement singleton pattern
   - Update tool implementations
   - Add state verification

2. Day 2:
   - Test implementation
   - Verify data persistence
   - Document changes

## Deliverables

1. Updated DatabaseManager implementation
2. Modified tool implementations
3. Test cases and results
4. Documentation updates
5. Implementation report

Remember to maintain the existing functionality while implementing these changes. The goal is to fix the cleanup issue without breaking any other features.
