# Database Schema Documentation

## 1. SQLite Table Structures

### System Configuration
```sql
CREATE TABLE system_config (
    id INTEGER PRIMARY KEY,
    key TEXT NOT NULL UNIQUE,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Agent Operations
```sql
CREATE TABLE agent_operations (
    id INTEGER PRIMARY KEY,
    agent_type TEXT NOT NULL,
    operation_type TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    error_message TEXT,
    metadata JSON
);
```

### Newsletters
```sql
CREATE TABLE newsletters (
    id INTEGER PRIMARY KEY,
    email_id TEXT NOT NULL UNIQUE,
    received_date TIMESTAMP NOT NULL,
    processed_date TIMESTAMP,
    storage_status TEXT NOT NULL, -- 'active', 'archived', 'summarized'
    vector_id TEXT,              -- Reference to vector storage
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Repositories
```sql
CREATE TABLE repositories (
    id INTEGER PRIMARY KEY,
    github_url TEXT NOT NULL UNIQUE,
    first_seen_date TIMESTAMP NOT NULL,
    last_mentioned_date TIMESTAMP NOT NULL,
    mention_count INTEGER DEFAULT 1,
    vector_id TEXT,              -- Reference to vector storage
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Topics
```sql
CREATE TABLE topics (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    first_seen_date TIMESTAMP NOT NULL,
    last_seen_date TIMESTAMP NOT NULL,
    mention_count INTEGER DEFAULT 1,
    parent_topic_id INTEGER,
    vector_id TEXT,              -- Reference to vector storage
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_topic_id) REFERENCES topics(id)
);
```

### Topic Relationships
```sql
CREATE TABLE topic_relationships (
    id INTEGER PRIMARY KEY,
    source_topic_id INTEGER NOT NULL,
    target_topic_id INTEGER NOT NULL,
    relationship_type TEXT NOT NULL, -- 'sibling', 'evolution', etc.
    strength FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_topic_id) REFERENCES topics(id),
    FOREIGN KEY (target_topic_id) REFERENCES topics(id)
);
```

### Repository Categories
```sql
CREATE TABLE repository_categories (
    id INTEGER PRIMARY KEY,
    repository_id INTEGER NOT NULL,
    topic_id INTEGER NOT NULL,
    confidence_score FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (repository_id) REFERENCES repositories(id),
    FOREIGN KEY (topic_id) REFERENCES topics(id)
);
```

### Content Cache
```sql
CREATE TABLE content_cache (
    id INTEGER PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    content_type TEXT NOT NULL,
    content BLOB,
    last_accessed TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 2. Vector Storage Metadata Schema

### Collection Structure
```json
{
    "id": "unique_vector_id",
    "content_type": "newsletter|repository|web_content",
    "embedding": "[float_array]",
    "metadata": {
        "source_id": "reference_to_sqlite_id",
        "source_type": "newsletter|repository|topic",
        "creation_date": "timestamp",
        "last_updated": "timestamp",
        "storage_status": "active|archived|summarized",
        "relationships": [
            {
                "related_vector_id": "vector_id",
                "relationship_type": "mentions|similar|references",
                "strength": 0.95
            }
        ],
        "retention": {
            "category": "active|archive|permanent",
            "archive_date": "timestamp",
            "summary_vector_id": "summarized_version_vector_id"
        }
    }
}
```

## 3. Traditional and Vector Storage Relationships

### Direct References
- SQLite tables maintain `vector_id` columns linking to vector storage
- Vector storage metadata includes `source_id` referencing SQLite records

### Relationship Types
1. Newsletter Content
   - SQLite: Basic metadata and processing status
   - Vector: Full content embedding and semantic relationships

2. Repository Information
   - SQLite: GitHub metadata and mention statistics
   - Vector: README content, documentation embeddings

3. Topic Representations
   - SQLite: Hierarchical relationships and statistics
   - Vector: Semantic meaning and contextual relationships

## 4. Archival/Retention Implementation

### Storage Tiers
1. Active Storage (0-6 months)
```sql
CREATE TABLE active_storage_rules (
    id INTEGER PRIMARY KEY,
    content_type TEXT NOT NULL,
    retention_period_days INTEGER NOT NULL,
    archival_policy TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

2. Archive Storage (6-24 months)
```sql
CREATE TABLE archive_storage_rules (
    id INTEGER PRIMARY KEY,
    content_type TEXT NOT NULL,
    retention_period_days INTEGER NOT NULL,
    summarization_policy TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

3. Permanent Storage
```sql
CREATE TABLE permanent_storage_rules (
    id INTEGER PRIMARY KEY,
    content_type TEXT NOT NULL,
    criteria JSON NOT NULL,
    storage_policy TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Archival Process
```sql
CREATE TABLE archival_jobs (
    id INTEGER PRIMARY KEY,
    content_type TEXT NOT NULL,
    source_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    summary_vector_id TEXT,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Retention Triggers
```sql
CREATE TABLE retention_triggers (
    id INTEGER PRIMARY KEY,
    trigger_type TEXT NOT NULL,
    content_type TEXT NOT NULL,
    condition_sql TEXT NOT NULL,
    action_type TEXT NOT NULL,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Content Summarization
```sql
CREATE TABLE content_summaries (
    id INTEGER PRIMARY KEY,
    original_content_id INTEGER NOT NULL,
    content_type TEXT NOT NULL,
    summary_type TEXT NOT NULL,
    vector_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON
);
