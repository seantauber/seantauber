# Configuration Guide

## Environment Variables (.env)

### Required Variables

```bash
# OpenAI API
OPENAI_API_KEY=your_key

# Gmail Integration
GMAIL_CREDENTIALS_PATH=/path/to/credentials.json
GMAIL_TOKEN_PATH=/path/to/token.json
GMAIL_LABEL=GenAI-News

# GitHub Access
GITHUB_TOKEN=your_token

# Storage Paths
DATABASE_PATH=/path/to/database.sqlite
VECTOR_STORE_PATH=/path/to/vector/store

# Optional
LOG_LEVEL=INFO  # Default: INFO
```

## Pipeline Configuration (config/pipeline_config.yaml)

```yaml
# Maximum items to process
max_newsletters: 10
max_urls_per_newsletter: 20

# Error handling
max_retries: 2
```

## Logging Configuration (config/logging_config.yaml)

The logging system is configured to:
- Log to both console and file
- Rotate log files at 10MB
- Keep 3 backup files
- Use timestamp and level in messages

## Configuration Tips

1. Environment Variables
- Use absolute paths when possible
- Keep credentials secure
- Don't commit .env file

2. Pipeline Settings
- Start with default values
- Adjust based on API limits
- Monitor processing times

3. Logging
- Check log files regularly
- Rotate logs as needed
- Monitor disk usage
