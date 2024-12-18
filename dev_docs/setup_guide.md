# Setup Guide

This guide walks through the setup process for the GitHub repository curation system.

## Prerequisites

1. **Python Environment**
   - Python 3.9 or higher
   - pip or uv package manager
   - Virtual environment tool (e.g., venv, conda)

2. **API Keys**
   - OpenAI API key for GPT-4
   - Gmail API credentials
   - GitHub Personal Access Token

3. **Infrastructure**
   - Redis server (for message queuing)
   - SQLite (for data storage)

## Installation Steps

1. **Clone Repository**
   ```bash
   git clone https://github.com/yourusername/github-genai-list.git
   cd github-genai-list
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   # Using pip
   pip install -r requirements.txt

   # Using uv (recommended)
   uv pip install -r requirements.txt

   # Install Redis (macOS)
   brew install redis

   # Install Redis (Ubuntu)
   sudo apt-get install redis-server
   ```

4. **Configure Environment Variables**
   Create a `.env` file in the project root:
   ```env
   # OpenAI API
   OPENAI_API_KEY=your_openai_key

   # Gmail API
   GMAIL_CREDENTIALS_PATH=path/to/credentials.json
   GMAIL_TOKEN_PATH=path/to/token.json
   GMAIL_LABEL=GenAI-News

   # GitHub API
   GITHUB_TOKEN=your_github_token
   GITHUB_REPO=yourusername/github-genai-list

   # Storage
   DATABASE_PATH=path/to/database.sqlite
   VECTOR_STORE_PATH=path/to/vector/storage

   # Redis
   REDIS_URL=redis://localhost:6379
   ```

5. **Set Up Gmail API**
   1. Go to [Google Cloud Console](https://console.cloud.google.com/)
   2. Create a new project
   3. Enable Gmail API
   4. Create OAuth 2.0 credentials
   5. Download credentials as `credentials.json`
   6. Run setup script:
      ```bash
      python scripts/setup_gmail.py
      ```

6. **Initialize Database**
   ```bash
   python scripts/run_migrations.py
   ```

7. **Initialize Vector Storage**
   ```bash
   python scripts/init_vector_store.py
   ```

## Running the System

### 1. Start Required Services

```bash
# Start Redis server
redis-server

# Start Dramatiq workers (in separate terminals)
# Newsletter processing workers
dramatiq processing.tasks -p 3 --queues newsletters

# Content extraction workers
dramatiq processing.tasks -p 2 --queues content

# README update worker
dramatiq processing.tasks -p 1 --queues readme
```

### 2. Run Pipeline

You can run the pipeline in three ways:

#### A. Full Pipeline
Runs all stages in parallel with proper coordination:
```bash
python scripts/run_parallel_pipeline.py
```

#### B. Individual Stages
Run specific stages independently:

1. Newsletter Processing:
```bash
# Basic usage
python scripts/run_newsletter_stage.py

# With options
python scripts/run_newsletter_stage.py \
  --max-results 100 \
  --batch-size 10 \
  --start-date 2024-01-01
```

2. Content Extraction:
```bash
# Basic usage
python scripts/run_extraction_stage.py

# With options
python scripts/run_extraction_stage.py \
  --batch-size 5 \
  --days-back 14 \
  --reprocess
```

3. README Generation:
```bash
# Basic usage
python scripts/run_readme_stage.py

# Force update
python scripts/run_readme_stage.py --force
```

### 3. Monitor Progress

```bash
# View pipeline logs
tail -f pipeline.log

# Monitor Redis queue
redis-cli monitor
```

## Development Setup

1. **Install Development Dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

2. **Set Up Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

3. **Configure IDE**
   - VSCode settings in `.vscode/settings.json`
   - PyCharm configuration in `.idea/`

4. **Run Development Tools**
   ```bash
   # Format code
   black .
   
   # Run linter
   flake8
   
   # Run type checker
   mypy .
   ```

## Common Issues

1. **Redis Connection**
   - Ensure Redis server is running
   - Check REDIS_URL in .env
   - Verify Redis port availability

2. **Worker Management**
   - Each stage has its own worker pool
   - Workers can be scaled independently
   - Monitor worker logs for issues

3. **Database Migrations**
   - Run migrations after schema changes
   - Back up database before migrations
   - Check migration logs for errors

4. **Gmail Integration**
   - Verify credentials and token
   - Check label configuration
   - Monitor API quota usage

## Next Steps

1. Review the [Vector Storage Documentation](vector_storage.md)
2. Check the [Troubleshooting Guide](troubleshooting.md)
3. Read the [Development Norms](development_norms.md)

## Support

For issues and questions:
1. Check the troubleshooting guide
2. Review existing GitHub issues
3. Create a new issue with:
   - System information
   - Error messages
   - Steps to reproduce
