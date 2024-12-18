# Troubleshooting Guide

This guide covers common issues and their solutions when running the pipeline.

## Pipeline Issues

### 1. Pipeline Hangs or Seems Stuck

**Symptoms:**
- Pipeline appears to be running but no progress
- No new log entries
- Process doesn't complete

**Solutions:**
1. Check worker status:
```bash
ps aux | grep dramatiq
```

2. Verify Redis connection:
```bash
redis-cli ping
```

3. Check queue status:
```bash
redis-cli
> LLEN queue:newsletters
> LLEN queue:content
> LLEN queue:readme
```

4. Restart workers if needed:
```bash
pkill -f dramatiq
dramatiq processing.tasks -p 3 --queues newsletters &
dramatiq processing.tasks -p 2 --queues content &
dramatiq processing.tasks -p 1 --queues readme &
```

### 2. Worker Memory Usage

**Symptoms:**
- Workers consuming excessive memory
- System slowdown
- Worker crashes

**Solutions:**
1. Adjust batch sizes:
```bash
# Smaller batches for newsletter processing
python scripts/run_newsletter_stage.py --batch-size 3

# Reduce content extraction batch size
python scripts/run_extraction_stage.py --batch-size 2
```

2. Monitor memory usage:
```bash
watch -n 1 "ps aux | grep dramatiq"
```

3. Configure worker memory limits in dramatiq settings:
```python
# In processing/tasks.py
@dramatiq.actor(max_memory=512)  # Memory limit in MB
```

## Database Issues

### 1. Migration Failures

**Symptoms:**
- Migration script errors
- Database locked errors
- Incomplete migrations

**Solutions:**
1. Check database state:
```bash
sqlite3 your_database.sqlite
> SELECT version FROM schema_version;
```

2. Backup before retrying:
```bash
cp your_database.sqlite your_database.backup.sqlite
```

3. Force single connection:
```bash
# Stop all pipeline processes
pkill -f dramatiq
pkill -f run_parallel_pipeline

# Run migration with exclusive access
python scripts/run_migrations.py
```

### 2. Database Locks

**Symptoms:**
- "database is locked" errors
- Concurrent access issues
- Hanging queries

**Solutions:**
1. Check active connections:
```bash
sqlite3 your_database.sqlite
> SELECT * FROM sqlite_master WHERE type='table';
```

2. Use pragmas for better concurrency:
```sql
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=5000;
```

3. Reduce concurrent database access:
```bash
# Run stages sequentially instead of parallel
python scripts/run_newsletter_stage.py
python scripts/run_extraction_stage.py
python scripts/run_readme_stage.py
```

## Vector Store Issues

### 1. Embedding Creation Failures

**Symptoms:**
- Vector ID generation fails
- OpenAI API errors
- Missing embeddings

**Solutions:**
1. Verify OpenAI API:
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

2. Check vector store integrity:
```python
from processing.embedchain_store import EmbedchainStore
store = EmbedchainStore("path/to/store")
store.newsletter_store.health_check()
```

3. Reprocess failed items:
```bash
python scripts/run_extraction_stage.py --reprocess
```

## Gmail Integration Issues

### 1. Authentication Failures

**Symptoms:**
- Token refresh errors
- Permission denied
- API quota exceeded

**Solutions:**
1. Refresh credentials:
```bash
rm token.json
python scripts/setup_gmail.py
```

2. Check API quotas in Google Cloud Console

3. Verify label exists:
```python
from processing.gmail.client import GmailClient
client = GmailClient("credentials.json", "token.json")
labels = client.service.users().labels().list(userId='me').execute()
```

### 2. Newsletter Processing Issues

**Symptoms:**
- Duplicate processing
- Missing newsletters
- Content truncation

**Solutions:**
1. Check processing status:
```sql
SELECT * FROM newsletters 
WHERE processed_date IS NOT NULL 
ORDER BY processed_date DESC LIMIT 5;
```

2. Verify email IDs:
```sql
SELECT COUNT(*), COUNT(DISTINCT email_id) 
FROM newsletters;
```

3. Monitor content length:
```sql
SELECT AVG(LENGTH(content)) as avg_length 
FROM newsletters;
```

## Redis Issues

### 1. Connection Problems

**Symptoms:**
- Redis connection refused
- Queue operations fail
- Worker startup errors

**Solutions:**
1. Check Redis service:
```bash
sudo systemctl status redis
# or
brew services list | grep redis
```

2. Verify connection settings:
```bash
redis-cli -u $REDIS_URL ping
```

3. Clear stuck queues:
```bash
redis-cli
> FLUSHALL
```

### 2. Queue Management

**Symptoms:**
- Tasks stuck in queue
- Uneven worker distribution
- Memory pressure

**Solutions:**
1. Monitor queue sizes:
```bash
watch -n 1 'redis-cli info | grep list'
```

2. Check task distribution:
```bash
redis-cli
> LLEN queue:newsletters
> LLEN queue:content
> LLEN queue:readme
```

3. Adjust worker counts:
```bash
# More newsletter workers for backlog
dramatiq processing.tasks -p 5 --queues newsletters
```

## General Debugging

### 1. Logging

Enable debug logging in config/logging_config.yaml:
```yaml
root:
  level: DEBUG
  handlers: [console, file]
```

### 2. Process Monitoring

Monitor all components:
```bash
# Watch logs
tail -f pipeline.log

# Monitor workers
watch -n 1 "ps aux | grep dramatiq"

# Watch Redis
redis-cli monitor

# Database queries
sqlite3 your_database.sqlite
> .timeout 5000
> PRAGMA busy_timeout = 5000;
```

### 3. Performance Tuning

1. Adjust batch sizes based on system resources
2. Scale worker counts based on queue sizes
3. Monitor memory usage and adjust as needed
4. Use appropriate timeouts for operations

Remember to check the logs (pipeline.log) for detailed error messages and stack traces when troubleshooting issues.
