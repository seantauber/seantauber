# 🤖 GitHub GenAI List

An AI-powered, automatically updating list of notable repositories in Generative AI, AI, and Data Science. This project uses GPT-4 to dynamically discover, categorize, and organize GitHub repositories from AI newsletters, providing an up-to-date resource for developers and researchers.

## 🌟 Features

- **AI Newsletter Monitoring**: Automatically discovers new repositories by monitoring AI/ML newsletters in your Gmail
- **Intelligent Curation**: Uses GPT-4 to:
  - Extract and validate GitHub repository links from newsletters
  - Analyze repository content and purpose
  - Categorize repositories based on their focus areas
  - Generate descriptive summaries
- **Quality Focus**: Only includes repositories with 1000+ stars
- **Daily Updates**: Refreshes content every 24 hours
- **Smart Categorization**: Dynamically adjusts categories based on the current state of the field
- **Minimal Maintenance**: Self-maintaining through GitHub Actions

## 🔄 How It Works

1. **Newsletter Monitoring**
   - Connects to your Gmail account via OAuth
   - Monitors specified AI/ML newsletter subscriptions
   - Extracts GitHub repository links from newsletter content

2. **Repository Analysis**
   - Fetches repository metadata using GitHub's API
   - Analyzes repository content, README, and descriptions
   - Filters repositories based on quality criteria (stars, activity)

3. **AI-Powered Categorization**
   - Uses GPT-4 to understand repository purpose and features
   - Dynamically creates and updates category structure
   - Places repositories in relevant categories
   - Generates concise, informative descriptions

4. **Automated Updates**
   - GitHub Actions pipeline runs daily to:
     - Check for new newsletter content
     - Update repository metadata
     - Regenerate categories and descriptions
     - Update the README

## 📚 Repository List

{AI_GENERATED_CONTENT}

## 🛠️ Setup Your Own Instance

1. **Clone the Repository**
```bash
git clone https://github.com/yourusername/github-genai-list.git
cd github-genai-list
```

2. **Install Dependencies**
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

3. **Configure Environment**
- Copy `.env.template` to `.env`
- Add your API keys:
  - GitHub Personal Access Token
  - OpenAI API Key

4. **Set Up Gmail OAuth**
- Create a Google Cloud Project
- Enable Gmail API
- Configure OAuth 2.0 credentials
- Add credentials to `.env`:
  - `GMAIL_CLIENT_ID`
  - `GMAIL_CLIENT_SECRET`
  - `GMAIL_REFRESH_TOKEN`

5. **Configure Newsletter Sources**
- Edit `config/newsletters.yaml` to specify:
  - Newsletter sender addresses
  - Subject line patterns
  - Content extraction rules

6. **Set Up GitHub Actions**
- Go to your repository's Settings > Secrets
- Add the following secrets:
  - `GITHUB_TOKEN`
  - `OPENAI_API_KEY`
  - `GMAIL_REFRESH_TOKEN`

7. **Run Locally**
```bash
# Run database migrations
python scripts/run_migrations.py

# Update readme
python scripts/update_readme.py
```

## 🧪 Testing

Run the test suite to verify functionality:
```bash
uv run pytest tests/ -v
```

## 📝 Project Structure

```
github-genai-list/
├── agents/              # AI agents for different tasks
│   ├── newsletter_monitor.py    # Gmail monitoring
│   ├── content_extractor.py    # Link extraction
│   ├── repository_curator.py   # Repo analysis
│   └── readme_generator.py     # README generation
├── config/             # Configuration files
├── db/                 # Database operations
├── processing/         # Data processing modules
├── scripts/           # Utility scripts
└── tests/             # Test suite
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

Please ensure your PR:
- Follows the existing code style
- Includes appropriate tests
- Updates documentation as needed

## 📄 License

This project is licensed under the MIT License - see [LICENSE.md](LICENSE.md) for details.

## 📊 Stats

- Last Updated: {LAST_UPDATED_DATE}
- Total Repositories: {TOTAL_REPOS}
- Categories: {CATEGORY_COUNT}
- Monitored Newsletters: Various AI/ML focused newsletters

## 📫 Contact

- Create an issue for bug reports or feature requests
- Submit a pull request to contribute
- Connect on [LinkedIn](https://www.linkedin.com/in/taubersean) for discussions

---

*This README is automatically updated daily by AI 🤖*
