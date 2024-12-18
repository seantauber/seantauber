# Production Deployment Guide

## Setup

1. Install Dependencies
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

2. Configure Environment
```bash
# Copy template and edit with actual values
cp .env.template .env
```

Required environment variables:
- OPENAI_API_KEY: For content analysis
- GMAIL_CREDENTIALS_PATH: Path to Google credentials
- GMAIL_TOKEN_PATH: Path to Gmail token
- GMAIL_LABEL: Label to monitor
- GITHUB_TOKEN: GitHub access token
- DATABASE_PATH: Path to SQLite database
- VECTOR_STORE_PATH: Path to vector storage

3. Initialize Database
```bash
python scripts/run_migrations.py
```

## Running the Pipeline

### Manual Run
```bash
python scripts/run_pipeline.py
```

### Automated Run (Linux/Mac)
```bash
# Add to crontab for daily run at 2 AM
0 2 * * * cd /path/to/github-genai-list && ./venv/bin/python scripts/run_pipeline.py
```

## Monitoring

### Logs
- Main log file: pipeline.log
- Log format: timestamp - component - level - message

### Basic Checks
```bash
# View recent logs
tail -f pipeline.log

# Check for errors
grep ERROR pipeline.log

# Verify README updates
git diff README.md
```

## Troubleshooting

### Common Issues

1. Gmail Authentication
- Check token expiration
- Verify credentials file exists
- Confirm label exists

2. GitHub Rate Limits
- Check remaining API calls
- Wait for reset if limited

3. Database Issues
- Verify file permissions
- Check disk space
- Run migrations

## Maintenance

1. Regular Tasks
- Monitor log file size
- Check disk space
- Verify backups

2. Database
```bash
# Optimize monthly
sqlite3 data/database.sqlite "VACUUM;"
```

3. Credentials
- Rotate GitHub token periodically
- Update Gmail token if expired
