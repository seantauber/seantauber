# Data Storage Implementation Plan

## Problem Statement
The current implementation faces memory limitations when:
1. Processing large amounts of repository data from GitHub API
2. Passing data between agents for analysis and categorization
3. Hitting LLM context size limits during processing
4. Sequential processing of large repository lists is inefficient

## Proposed Solution
Implement a simple SQLite database to store intermediate results between agent tasks, reducing memory usage and context size requirements. Add parallel processing capabilities for handling large lists of repositories.

## Implementation Details

### 1. Database Schema

```sql
-- Store raw repository data
CREATE TABLE raw_repositories (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL,  -- 'starred' or 'trending'
    data JSON NOT NULL,    -- serialized GitHubRepoData
    processed BOOLEAN DEFAULT FALSE,
    batch_id INTEGER,      -- For tracking parallel processing batches
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Store analyzed repository data
CREATE TABLE analyzed_repositories (
    id INTEGER PRIMARY KEY,
    raw_repo_id INTEGER,
    analysis_data JSON NOT NULL,  -- serialized AnalyzedRepoData
    batch_id INTEGER,      -- For tracking parallel processing batches
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (raw_repo_id) REFERENCES raw_repositories(id)
);

-- Store batch processing status
CREATE TABLE batch_processing (
    id INTEGER PRIMARY KEY,
    task_type TEXT NOT NULL,  -- 'fetch', 'analyze', etc.
    batch_id INTEGER NOT NULL,
    status TEXT NOT NULL,     -- 'pending', 'processing', 'completed', 'failed'
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error TEXT
);
```

### 2. Code Changes Required

#### A. Add Database Manager Class
```python
# db/database.py
import sqlite3
import json
from datetime import datetime
from typing import List, Dict
from models.github_repo_data import GitHubRepoData, AnalyzedRepoData

class DatabaseManager:
    def __init__(self, db_path: str = "db/github_repos.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        # Create tables if they don't exist
        pass
    
    def store_raw_repos(self, repos: List[GitHubRepoData], source: str, batch_id: int):
        # Store raw repository data with batch tracking
        pass
    
    def get_unprocessed_repos(self, batch_size: int = 10) -> List[GitHubRepoData]:
        # Get batch of unprocessed repositories
        pass
    
    def store_analyzed_repos(self, analyzed_repos: List[AnalyzedRepoData], batch_id: int):
        # Store analyzed repository data with batch tracking
        pass
    
    def get_analyzed_repos(self) -> List[AnalyzedRepoData]:
        # Get all analyzed repositories for README generation
        pass

    def create_batch(self, task_type: str) -> int:
        # Create new batch and return batch_id
        pass

    def update_batch_status(self, batch_id: int, status: str, error: str = None):
        # Update batch processing status
        pass

    def get_batch_status(self, task_type: str) -> Dict[int, str]:
        # Get status of all batches for a task type
        pass
```

#### B. Add Parallel Processing Manager
```python
# processing/parallel_manager.py
from concurrent.futures import ThreadPoolExecutor
from typing import List, Callable, Any
from db.database import DatabaseManager

class ParallelProcessor:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.db = DatabaseManager()

    def process_batch(self, task_type: str, items: List[Any], 
                     process_fn: Callable, batch_size: int = 10) -> Dict:
        """
        Process items in parallel batches
        Returns summary of processing results
        """
        batches = self._create_batches(items, batch_size)
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for batch in batches:
                batch_id = self.db.create_batch(task_type)
                future = executor.submit(self._process_single_batch,
                                      batch, process_fn, batch_id)
                futures.append(future)
            
            results = [f.result() for f in futures]
        
        return self._combine_results(results)

    def _process_single_batch(self, batch: List[Any], 
                            process_fn: Callable, batch_id: int) -> Dict:
        """Process a single batch and update status"""
        try:
            self.db.update_batch_status(batch_id, 'processing')
            result = process_fn(batch, batch_id)
            self.db.update_batch_status(batch_id, 'completed')
            return result
        except Exception as e:
            self.db.update_batch_status(batch_id, 'failed', str(e))
            raise
```

#### C. New Task Return Models
```python
# models/task_outputs.py

class ProcessingSummary(BaseModel):
    """Base model for task processing summaries"""
    success: bool
    message: str
    processed_count: int
    batch_count: int
    completed_batches: int
    failed_batches: int
    error_count: int = 0
    errors: List[str] = []

class FetchSummary(ProcessingSummary):
    """Summary for fetch tasks"""
    source: str  # 'starred' or 'trending'
    total_repos: int
    stored_repos: int
    
class AnalysisSummary(ProcessingSummary):
    """Summary for analysis tasks"""
    total_analyzed: int
    categories: Dict[str, int]  # Count of repos per category
    quality_stats: Dict[str, float]  # Min/max/avg quality scores
```

#### D. Modify Task Return Values in tasks.yaml

1. Fetch Tasks:
```yaml
fetch_starred:
  expected_output: A FetchSummary object containing processing stats for starred repos
  
search_trending:
  expected_output: A FetchSummary object containing processing stats for trending repos
```

2. Analysis Task:
```yaml
analyze_repos:
  expected_output: An AnalysisSummary object containing analysis stats and category distribution
```

### 3. Task Flow Modifications

1. **Fetching Phase**
   - Split repository lists into parallel batches
   - Process batches concurrently with status tracking
   - Store results directly in database
   - Return FetchSummary with batch processing stats
   - Next task gets data from database instead of context

2. **Analysis Phase**
   - Process repositories in parallel batches from database
   - Track batch progress and handle failures
   - Store analysis results back to database
   - Return AnalysisSummary with batch processing stats
   - Content generation gets data from database

3. **Content Generation Phase**
   - Retrieve analyzed repos from database
   - Generate README content in sections if needed

### 4. Parallel Processing Flow

1. **Batch Creation**
   - Split large lists into manageable batches
   - Assign unique batch_id to each batch
   - Track batch status in database

2. **Concurrent Processing**
   - Process multiple batches simultaneously
   - Each batch runs in its own thread
   - Monitor and handle batch failures

3. **Status Tracking**
   - Track progress of each batch
   - Handle failed batches gracefully
   - Provide real-time processing status

4. **Result Aggregation**
   - Combine results from all batches
   - Generate comprehensive processing summary
   - Handle partial successes/failures

## Benefits

1. **Improved Performance**
   - Parallel processing of repository batches
   - Reduced overall processing time
   - Better resource utilization

2. **Reduced Memory Usage**
   - Data stored in SQLite instead of memory
   - Batch processing of repositories
   - Tasks return summaries instead of full data

3. **Better Error Handling**
   - Granular batch-level error tracking
   - Failed batches don't affect others
   - Ability to retry failed batches

4. **Improved Reliability**
   - Data persistence between runs
   - Recovery from failures possible
   - Clear processing status tracking

5. **Future Extensibility**
   - Easy to add new data fields
   - Support for data versioning
   - Ability to track changes over time

## Implementation Steps

1. ✅ Create implementation plan
2. ✅ Create database module
3. ✅ Add database initialization to startup
4. ✅ Modify fetch tasks to store data
5. ✅ Update analysis task for batch processing
6. ✅ Adjust content generation for database retrieval
7. ✅ Add batch processing tables to database
8. Implement ParallelProcessor class
9. Add new task output models for processing summaries
10. Update task return values in tasks.yaml
11. Modify task implementations to use parallel processing
12. Update crew.py task definitions with new output types
13. Add batch status tracking and monitoring
14. Implement error handling for failed batches
15. Test parallel processing performance
16. Verify memory usage improvements

## Notes

- SQLite chosen for simplicity and zero-config setup
- Batch size can be tuned based on LLM context limits
- JSON storage allows flexible schema evolution
- No need for complex ORM for this simple use case
- Task summaries provide quick status overview
- Database queries replace context passing
- Parallel processing improves throughput
- Batch tracking ensures reliability
