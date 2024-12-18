# Troubleshooting Guide

This guide helps diagnose and resolve common issues in the GitHub repository curation system.

## Diagnostic Tools

1. **System Health Check**
   ```bash
   python scripts/health_check.py
   ```
   Verifies:
   - API connections
   - Vector storage status
   - Agent availability
   - Pipeline state

2. **Log Analysis**
   ```bash
   python scripts/analyze_logs.py
   ```
   Shows:
   - Error patterns
   - Performance metrics
   - Pipeline statistics

## Common Issues

### 1. Pipeline Failures

#### Symptoms
- Pipeline stops mid-execution
- Incomplete README updates
- Error messages in logs

#### Possible Causes
1. **API Rate Limits**
   - Check GitHub API limits:
     ```bash
     curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/rate_limit
     ```
   - Monitor OpenAI API usage

2. **Vector Storage Issues**
   - Insufficient disk space
   - Corrupted indexes
   - Connection timeouts

3. **Agent Failures**
   - Invalid configurations
   - Resource exhaustion
   - Timeout issues

#### Solutions
1. **API Issues**
   - Implement rate limiting:
     ```python
     from time import sleep
     
     def rate_limited_call():
         try:
             return api.call()
         except RateLimitError:
             sleep(60)
             return api.call()
     ```
   - Use API key rotation
   - Monitor usage patterns

2. **Vector Storage**
   - Clean up old vectors:
     ```bash
     python scripts/cleanup_vectors.py --age 30
     ```
   - Rebuild indexes:
     ```bash
     python scripts/rebuild_indexes.py
     ```
   - Check storage health:
     ```bash
     python scripts/check_storage.py
     ```

3. **Agent Recovery**
   - Reset agent state:
     ```bash
     python scripts/reset_agents.py
     ```
   - Clear agent caches
   - Restart pipeline

### 2. Data Quality Issues

#### Symptoms
- Missing or duplicate entries
- Poor content extraction
- Incorrect repository information

#### Possible Causes
1. **Vector Similarity Issues**
   - Inappropriate thresholds
   - Poor embedding quality
   - Inconsistent chunking

2. **Content Processing Errors**
   - Invalid content format
   - Character encoding issues
   - HTML parsing errors

#### Solutions
1. **Vector Quality**
   - Adjust similarity thresholds:
     ```python
     # config/pipeline_config.yaml
     vector_store:
       similarity_threshold: 0.8
       chunk_size: 500
     ```
   - Reprocess problematic content:
     ```bash
     python scripts/reprocess_content.py --id <content_id>
     ```

2. **Content Processing**
   - Validate input format
   - Fix encoding issues:
     ```python
     content = content.encode('utf-8', errors='ignore').decode('utf-8')
     ```
   - Update parsing rules

### 3. Performance Issues

#### Symptoms
- Slow pipeline execution
- High memory usage
- Delayed updates

#### Possible Causes
1. **Resource Constraints**
   - Insufficient memory
   - CPU bottlenecks
   - Disk I/O limitations

2. **Inefficient Operations**
   - Large batch sizes
   - Unoptimized queries
   - Missing indexes

#### Solutions
1. **Resource Management**
   - Monitor resource usage:
     ```bash
     python scripts/monitor_resources.py
     ```
   - Implement batch processing:
     ```python
     async def process_batch(items, batch_size=10):
         for i in range(0, len(items), batch_size):
             batch = items[i:i + batch_size]
             await process_items(batch)
     ```
   - Clean up temporary files

2. **Optimization**
   - Adjust batch sizes
   - Optimize queries
   - Add indexes:
     ```python
     await store.create_index('metadata.url')
     ```

### 4. Integration Issues

#### Symptoms
- Failed API connections
- Authentication errors
- Webhook failures

#### Possible Causes
1. **Configuration Problems**
   - Invalid credentials
   - Expired tokens
   - Incorrect endpoints

2. **Network Issues**
   - Firewall blocks
   - DNS problems
   - Proxy configuration

#### Solutions
1. **Configuration**
   - Verify credentials:
     ```bash
     python scripts/verify_credentials.py
     ```
   - Update tokens:
     ```bash
     python scripts/refresh_tokens.py
     ```
   - Check endpoints:
     ```bash
     python scripts/check_endpoints.py
     ```

2. **Network**
   - Test connectivity:
     ```bash
     python scripts/test_connectivity.py
     ```
   - Configure proxies:
     ```python
     os.environ['HTTPS_PROXY'] = 'http://proxy:port'
     ```
   - Update DNS settings

## Monitoring and Prevention

### 1. Logging

Configure detailed logging:
```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)
```

### 2. Alerts

Set up monitoring alerts:
```python
async def check_system_health():
    if not await store.is_healthy():
        send_alert("Vector store unhealthy")
    if not await check_api_quotas():
        send_alert("API quota low")
```

### 3. Regular Maintenance

Schedule maintenance tasks:
```bash
# Add to crontab
0 0 * * * python scripts/maintenance.py
```

## Recovery Procedures

### 1. Data Recovery

Restore from backup:
```bash
python scripts/restore.py --backup latest
```

### 2. Pipeline Reset

Reset pipeline state:
```bash
python scripts/reset_pipeline.py --clean
```

### 3. Emergency Shutdown

Graceful shutdown:
```bash
python scripts/shutdown.py --graceful
```

## Getting Help

1. Check logs:
   ```bash
   tail -f logs/error.log
   ```

2. Generate diagnostic report:
   ```bash
   python scripts/generate_report.py
   ```

3. Contact support with:
   - Diagnostic report
   - Error messages
   - Steps to reproduce
   - System configuration

Remember to always check the logs first and gather relevant information before attempting any fixes.
