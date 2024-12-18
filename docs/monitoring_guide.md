# Monitoring Guide

## Log Monitoring

### View Recent Activity
```bash
# Follow log output
tail -f pipeline.log

# Check for errors
grep ERROR pipeline.log

# View today's logs
grep "$(date +%Y-%m-%d)" pipeline.log
```

### Common Log Messages

1. Success Patterns:
```
INFO - Starting pipeline
INFO - Processing newsletters
INFO - Extracting repositories
INFO - Generating README
INFO - Pipeline completed successfully
```

2. Error Patterns:
```
ERROR - Gmail authentication failed
ERROR - GitHub API rate limit exceeded
ERROR - Failed to extract content
ERROR - Database connection error
```

## Health Checks

### Database
```bash
# Check size
du -h data/database.sqlite

# Verify access
sqlite3 data/database.sqlite ".tables"
```

### API Status
```bash
# Check GitHub rate limit
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/rate_limit

# Verify Gmail token
python scripts/check_gmail_auth.py
```

## Troubleshooting

### Pipeline Failures

1. Check Logs
```bash
# View recent errors
tail pipeline.log

# Search for specific errors
grep "Failed to" pipeline.log
```

2. Common Issues:
- Gmail token expired
- GitHub rate limit reached
- Database locked
- Disk space full

### Recovery Steps

1. Authentication Issues
- Refresh Gmail token
- Rotate GitHub token
- Verify credentials exist

2. Rate Limits
- Wait for reset
- Check remaining calls
- Adjust batch sizes

3. Storage Issues
- Clear old logs
- Run database vacuum
- Check disk space

## Maintenance

### Regular Tasks

1. Daily
- Check log files
- Verify README updates
- Monitor disk space

2. Weekly
- Review error patterns
- Clean old logs
- Check token status

3. Monthly
- Rotate credentials
- Optimize database
- Review configurations
