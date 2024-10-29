# 🤖 GenAI, AI, and Data Science Resources

Welcome to my AI GENERATED list of interesting repositories in the fields of Generative AI, Artificial Intelligence, and Data Science. As an AI Engineer & Product Development Specialist in these areas, I've compiled this list to help developers, researchers, and enthusiasts stay up-to-date with the latest advancements and tools.

## How This Landing Page Works

This GitHub landing page is **automatically updated every day by AI** to showcase my latest interests and discoveries in the fields of AI, Machine Learning, and Data Science.

Here's how it works:

1. **Automated Updates**: The repository list you see below is automatically updated daily using GitHub Actions that I've set up to run the AI pipeline.
2. **Starred Repositories**: The content is based on my GitHub starred repositories, reflecting my current interests and valuable finds in the tech world.
3. **AI-Powered Organization**: An AI model (GPT-4o) is used to categorize and organize the repositories, ensuring that the list remains well-structured and informative.
4. **Minimal Manual Intervention**: Once set up, this page requires little to no manual updating. All I need to do is star a new repo and it will automatically be categorized and added to this document. When I remove a repo from my starred list, the AI automatically removes it from this page.

**Why use AI for this?**: The key thing that the LLM-based solution is doing is dynamically deciding what categories should exist on this and how to group my starred repos into those categories. It also reassesses and changes the categories and groupings over time as the starred repos change. It does all of this without the need for me to decide in advance what categories it should consider or to pre-train the model on categories. Implementing this algorithm is extremely simple compared to implementing a solution with a more traditional ML/AI approach that doesn't have the NLP reasoning capabilities of an LLM.

## 📚 Table of Contents

- [Generative AI](#generative-ai)
  - [Large Language Models (LLMs)](#large-language-models-llms)
- [Artificial Intelligence](#artificial-intelligence)
  - [Machine Learning Frameworks](#machine-learning-frameworks)
- [MLOps & AI Infrastructure](#mlops--ai-infrastructure)
- [Agentic Frameworks](#agentic-frameworks)
- [Documentation](#documentation)
- [TTS & Speech](#tts--speech)
- [Other](#other)
- [How to Implement This Landing Page On Your Own GitHub](#how-to-implement-this-landing-page-on-your-own-github)
- [🌟 Contributing](#-contributing)
- [📄 License](#-license)

## Generative AI

### Large Language Models (LLMs)

- [facebookresearch/lingua](https://github.com/facebookresearch/lingua) - Meta Lingua: a lean, efficient, and easy-to-hack codebase to research LLMs.
- [cpacker/MemGPT](https://github.com/cpacker/MemGPT) - Letta (fka MemGPT) is a framework for creating stateful LLM services.
- [microsoft/semantic-kernel](https://github.com/microsoft/semantic-kernel) - Integrate cutting-edge LLM technology quickly and easily into your apps.
- [oobabooga/text-generation-webui](https://github.com/oobabooga/text-generation-webui) - A Gradio web UI for Large Language Models.
- [huggingface/chat-ui](https://github.com/huggingface/chat-ui) - Open source codebase powering the HuggingChat app.

## Artificial Intelligence

### Machine Learning Frameworks

- [kenshiro-o/nagato-ai](https://github.com/kenshiro-o/nagato-ai) - Simple cross-LLM AI Agent library.
- [run-llama/multi-agent-concierge](https://github.com/run-llama/multi-agent-concierge) - An example of multi-agent orchestration with llama-index.

## MLOps & AI Infrastructure

- [langflow-ai/langflow](https://github.com/langflow-ai/langflow) - Langflow is a low-code app builder for RAG and multi-agent AI applications.
- [Marker-Inc-Korea/AutoRAG](https://github.com/Marker-Inc-Korea/AutoRAG) - AutoML tool for RAG.

## Agentic Frameworks

- [neural-maze/agentic_patterns](https://github.com/neural-maze/agentic_patterns) - Implementing the 4 agentic patterns from scratch.

## Documentation

- [mkdocs/mkdocs](https://github.com/mkdocs/mkdocs) - Project documentation with Markdown.

## TTS & Speech

- [fishaudio/fish-diffusion](https://github.com/fishaudio/fish-diffusion) - An easy to understand TTS / SVS / SVC framework.
- [fishaudio/fish-speech](https://github.com/fishaudio/fish-speech) - Brand new TTS solution.

## Other

- [enricoros/big-AGI](https://github.com/enricoros/big-AGI) - Generative AI suite powered by state-of-the-art models and providing advanced AI/AGI functions.
- [eosphoros-ai/Awesome-Text2SQL](https://github.com/eosphoros-ai/Awesome-Text2SQL) - Curated tutorials and resources for Large Language Models, Text2SQL, and more.
- [zou-group/textgrad](https://github.com/zou-group/textgrad) - TextGrad: Automatic 'Differentiation' via Text.
- [SylphAI-Inc/AdalFlow](https://github.com/SylphAI-Inc/AdalFlow) - AdalFlow: The library to build & auto-optimize LLM applications.
- [xitanggg/open-resume](https://github.com/xitanggg/open-resume) - OpenResume is a powerful open-source resume builder and resume parser.
- [srbhr/Resume-Matcher](https://github.com/srbhr/Resume-Matcher) - Resume Matcher is an open-source, free tool to improve your resume.
- [lobehub/lobe-chat](https://github.com/lobehub/lobe-chat) - Lobe Chat - an open-source, modern-design AI chat framework.
- [ScrapeGraphAI/Scrapegraph-ai](https://github.com/ScrapeGraphAI/Scrapegraph-ai) - Python scraper based on AI.
- [Shubhamsaboo/awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps) - Collection of awesome LLM apps with RAG.
- [microsoft/OmniParser](https://github.com/microsoft/OmniParser) - A simple screen parsing tool towards pure vision based GUI agent.
- [mem0ai/mem0](https://github.com/mem0ai/mem0) - The Memory layer for your AI apps.
- [kestra-io/kestra](https://github.com/kestra-io/kestra) - Workflow Automation Platform.
- [maybe-finance/maybe](https://github.com/maybe-finance/maybe) - The OS for your personal finances.
- [docker/genai-stack](https://github.com/docker/genai-stack) - Langchain + Docker + Neo4j + Ollama.
- [jaywcjlove/awesome-mac](https://github.com/jaywcjlove/awesome-mac) - Collect premium software in various categories.
- [ollama/ollama](https://github.com/ollama/ollama) - Get up and running with Llama 3.2, Mistral, Gemma 2, and other large language models.
- [dipanjanS/improving-RAG-systems-dhs2024](https://github.com/dipanjanS/improving-RAG-systems-dhs2024) - Improving Real-world Retrieval Augmented Generation Systems at DataHack Summit 2024.

## How to Implement This Landing Page On Your Own GitHub

This project automatically updates the README with your GitHub starred repositories using a Python script and GitHub Actions.

```python
# 1. Clone the repository:
git clone https://github.com/your-username/github-genai-list.git
cd github-genai-list

# 2. Set up your environment:
# Ensure you have Python 3.x installed. You can check your version with:
python --version

# 3. Install dependencies:
# First, make sure pip is up-to-date:
python -m pip install --upgrade pip
# Then install the required dependencies:
pip install -r requirements.txt

# 4. Set up GitHub secrets:
# Go to your GitHub repository settings, and under Secrets and variables > Actions, create the following secrets:
# GITHUB_TOKEN: Your personal access token for GitHub API.
# OPENAI_API_KEY: Your API key for OpenAI (if applicable for LLM updates).
# PAT: A GitHub Personal Access Token with appropriate permissions

# 5. Update the script:
# In the update_readme.py script located in the scripts/ directory, replace "YourGitHubUsername" with your actual GitHub username.

# 6. Configure the GitHub Action:
# The workflow is already set up in .github/workflows/update-readme.yml.
# It runs daily at midnight (UTC) or can be triggered manually via the GitHub Actions tab.

# 7. Running locally (optional):
# You can also run the script manually to test it locally:
python scripts/update_readme.py

# 8. Commit and push changes:
git add .
git commit -m "Updated project structure"
git push origin main

# 9. Customize the README:
# You can modify the README.md template to fit your personal brand and interests.
# The GitHub Action will automatically update it with your latest starred repositories daily.
```

**Note**: This landing page uses OpenAI's GPT-4o model. Make sure you comply with OpenAI's use-case policies and monitor your API usage to manage costs.

---

## 🌟 Contributing

Feel free to open a pull request if you have any suggestions for additions or improvements to this list. Let's collaborate to keep this resource up-to-date and valuable for the community!

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

---

📊 *Last edited: October 29, 2024*

🔗 Connect with me on [LinkedIn](https://www.linkedin.com/in/taubersean)