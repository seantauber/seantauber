# System Issues and Resolution Plan

## Critical Issues (Immediate Priority)

### 1. Database Cleanup Issue
- ❌ Multiple database cleanups occurring due to DatabaseManager initialization:
  * DatabaseManager initialized with cleanup=True by default
  * Each agent creates its own DatabaseManager instance
  * Multiple cleanups causing data loss between tasks
- Technical details:
  * Issue occurs in the following sequence:
    1. fetch_starred_repos creates DatabaseManager and stores data
    2. analyzer agent creates new DatabaseManager
    3. New DatabaseManager cleans up database
    4. Previously stored data is lost
  * Affected components:
    ```python
    # db/database.py
    class DatabaseManager:
        def __init__(self, db_path: str = "db/github_repos.db", cleanup: bool = True):
            # cleanup=True by default causes the issue
    ```
  * Current implementation:
    ```python
    # crew.py
    # Each tool creates its own DatabaseManager instance
    def store_raw_repos(repos: List[Dict], source: str) -> str:
        db_manager = DatabaseManager()  # New instance with cleanup=True
    
    def get_unprocessed_repos(batch_size: int = 10) -> List[Dict]:
        db_manager = DatabaseManager()  # Another instance with cleanup=True
    ```

### 2. GitHub Username Configuration
- ✓ Configuration implementation is correct:
  * GITHUB_USERNAME properly set in .env
  * GitHubConfig loads and validates username
  * fetch_starred_repos uses app_config correctly
- Required changes:
  * ✓ Remove unused github_username parameter from fetch_starred_repos
  * ✓ Keep existing config usage
  * ✓ Add error logging

### 3. Database Implementation
- ✓ Schema implementation is correct:
  * Tables properly defined
  * Relationships properly set
  * Constraints in place
- ❌ Data persistence issues:
  * Multiple cleanups causing data loss
  * Need singleton pattern for DatabaseManager
  * Need to control cleanup behavior

## Resolution Plan

### Phase 1: Database Manager Refactoring

1. Implement Singleton Pattern:
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
            if cleanup:  # Only cleanup if explicitly requested
                self.cleanup_database()
            self.init_db()
```

2. Update Tool Implementations:
```python
# Update all tool implementations to use singleton instance
def store_raw_repos(repos: List[Dict], source: str) -> str:
    db_manager = DatabaseManager(cleanup=False)  # Will reuse existing instance
    
def get_unprocessed_repos(batch_size: int = 10) -> List[Dict]:
    db_manager = DatabaseManager(cleanup=False)  # Will reuse existing instance
```

3. Add Database State Verification:
```python
class DatabaseManager:
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

### Phase 2: Implementation Steps

1. Create DatabaseManager Singleton:
   - Implement singleton pattern
   - Add state verification
   - Default cleanup to False
   - Add proper initialization tracking

2. Update Tool Implementations:
   - Modify all database interactions
   - Remove cleanup flag from normal usage
   - Add state verification calls

3. Add Database Monitoring:
   - Implement state logging
   - Add transaction tracking
   - Monitor table contents
   - Track cleanup operations

4. Testing:
   - Test singleton behavior
   - Verify data persistence
   - Check cleanup control
   - Validate state tracking

### Phase 3: Validation Steps

1. Data Flow Testing:
   - Verify fetch_starred_repos storage
   - Check data persistence
   - Validate analysis flow
   - Test end-to-end process

2. Error Handling:
   - Test cleanup scenarios
   - Verify error recovery
   - Check state consistency
   - Validate logging

## Implementation Timeline

1. Database Refactoring (1 day):
   - Implement singleton pattern
   - Update tool implementations
   - Add state verification

2. Testing & Validation (1 day):
   - Test data persistence
   - Verify cleanup control
   - Validate state tracking

Total Implementation Time: 2 days

## Success Metrics

1. Data persists between tasks
2. Single DatabaseManager instance
3. Controlled cleanup behavior
4. Complete state tracking
5. Proper error handling

## Notes

- ✓ Identified root cause
- ✓ Designed singleton solution
- ✓ Planned implementation steps
- Need to implement changes
- Need to validate solution
