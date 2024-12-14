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

   # Vector Storage
   VECTOR_STORE_PATH=path/to/vector/storage
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

6. **Initialize Vector Storage**
   ```bash
   python scripts/init_vector_store.py
   ```

7. **Run Tests**
   ```bash
   pytest tests/
   ```

## Configuration

### Vector Storage Settings

Edit `config/vector_store.json`:
```json
{
  "collections": {
    "newsletters": {
      "chunk_size": 500,
      "similarity_threshold": 0.7
    },
    "repositories": {
      "chunk_size": 500,
      "similarity_threshold": 0.8
    }
  }
}
```

### Agent Configuration

Edit `config/agents.json`:
```json
{
  "newsletter_monitor": {
    "poll_interval": 3600,
    "batch_size": 10
  },
  "content_extractor": {
    "min_confidence": 0.7
  },
  "topic_analyzer": {
    "min_topic_confidence": 0.8
  }
}
```

## Running the System

1. **Start the Pipeline**
   ```bash
   python scripts/run_pipeline.py
   ```

2. **Monitor Logs**
   ```bash
   tail -f logs/pipeline.log
   ```

3. **Check Results**
   - View updated README in GitHub repository
   - Check vector storage status:
     ```bash
     python scripts/check_vector_store.py
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

1. **Gmail Authentication**
   - Ensure credentials are correctly configured
   - Check token refresh process
   - Verify API access permissions

2. **Vector Storage**
   - Check disk space for vector storage
   - Verify file permissions
   - Monitor memory usage

3. **GitHub Integration**
   - Verify token permissions
   - Check API rate limits
   - Ensure repository access

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
