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
- [Other](#other)
- [How to Implement This Landing Page On Your Own GitHub](#how-to-implement-this-landing-page-on-your-own-github)
- [🌟 Contributing](#-contributing)
- [📄 License](#-license)

## Generative AI

### Large Language Models (LLMs)

- [rsrohan99/dynamic-few-shot-llamaindex-workflow](https://github.com/rsrohan99/dynamic-few-shot-llamaindex-workflow) - None.
- [rasbt/LLMs-from-scratch](https://github.com/rasbt/LLMs-from-scratch) - Implementing a ChatGPT-like LLM in PyTorch from scratch, step by step.

## Artificial Intelligence

### Machine Learning Frameworks

- [microsoft/BitNet](https://github.com/microsoft/BitNet) - Official inference framework for 1-bit LLMs.

## MLOps & AI Infrastructure

- [wandb/weave](https://github.com/wandb/weave) - Weave is a toolkit for developing AI-powered applications, built by Weights & Biases.
- [phidatahq/phidata](https://github.com/phidatahq/phidata) - Build AI Agents with memory, knowledge, tools and reasoning. Chat with them using a beautiful Agent UI.
- [ollama/ollama](https://github.com/ollama/ollama) - Get up and running with Llama 3.2, Mistral, Gemma 2, and other large language models.

## Agentic Frameworks

- [simular-ai/Agent-S](https://github.com/simular-ai/Agent-S) - Agent S: an open agentic framework that uses computers like a human.
- [ServiceNow/TapeAgents](https://github.com/ServiceNow/TapeAgents) - TapeAgents is a framework that facilitates all stages of the LLM Agent development lifecycle.
- [amanv1906/GENAI-CareerAssistant-Multiagent](https://github.com/amanv1906/GENAI-CareerAssistant-Multiagent) - GenAI career assistant.
- [neural-maze/agentic_patterns](https://github.com/neural-maze/agentic_patterns) - Implementing the 4 agentic patterns from scratch.

## Other

- [docker/genai-stack](https://github.com/docker/genai-stack) - Langchain + Docker + Neo4j + Ollama.
- [jaywcjlove/awesome-mac](https://github.com/jaywcjlove/awesome-mac) - Collect premium software in various categories.
- [trimstray/the-book-of-secret-knowledge](https://github.com/trimstray/the-book-of-secret-knowledge) - A collection of inspiring lists.
- [vinta/awesome-python](https://github.com/vinta/awesome-python) - An opinionated list of awesome Python frameworks, libraries, and resources.
- [norvig/pytudes](https://github.com/norvig/pytudes) - Python programs to perfect particular skills.
- [TheAlgorithms/Python](https://github.com/TheAlgorithms/Python) - All Algorithms implemented in Python.
- [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp) - A feature-rich command-line audio/video downloader.
- [microsoft/playwright-python](https://github.com/microsoft/playwright-python) - Python version of the Playwright testing and automation library.
- [fishaudio/fish-diffusion](https://github.com/fishaudio/fish-diffusion) - An easy-to-understand TTS/SVS/SVC framework.
- [fishaudio/fish-speech](https://github.com/fishaudio/fish-speech) - Brand new TTS solution.
- [mem0ai/mem0](https://github.com/mem0ai/mem0) - The Memory layer for your AI apps.
- [kestra-io/kestra](https://github.com/kestra-io/kestra) - Workflow Automation Platform.
- [maybe-finance/maybe](https://github.com/maybe-finance/maybe) - The OS for your personal finances.
- [NirDiamant/Prompt_Engineering](https://github.com/NirDiamant/Prompt_Engineering) - Tutorials and implementations for Prompt Engineering.
- [adarshb3/Virtual-Try-On-Application-using-Flask-Twilio-and-Gradio](https://github.com/adarshb3/Virtual-Try-On-Application-using-Flask-Twilio-and-Gradio) - Virtual try-on application built using Flask, Twilio's WhatsApp API, and Gradio's virtual try-on model.
- [niledatabase/niledatabase](https://github.com/niledatabase/niledatabase) - PostgreSQL reengineered for multi-tenant apps.
- [run-llama/openai_realtime_client](https://github.com/run-llama/openai_realtime_client) - A simple client and utils for interacting with OpenAI's Realtime API in Python.
- [jy0205/Pyramid-Flow](https://github.com/jy0205/Pyramid-Flow) - Code of Pyramidal Flow Matching for Efficient Video Generative Modeling.
- [openai/swarm](https://github.com/openai/swarm) - Educational framework exploring ergonomic, lightweight multi-agent orchestration.
- [feder-cr/Auto_Jobs_Applier_AIHawk](https://github.com/feder-cr/Auto_Jobs_Applier_AIHawk) - Automates the jobs application process using AI.

## How to Implement This Landing Page On Your Own GitHub

This project automatically updates the README with your GitHub starred repositories using a Python script and GitHub Actions.

``` python
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

📊 *Last edited: October 23, 2024*

🔗 Connect with me on [LinkedIn](https://www.linkedin.com/in/taubersean)