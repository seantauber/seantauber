# 🤖 GenAI, AI, and Data Science Resources

Welcome to my AI GENERATED list of interesting repositories in the fields of Generative AI, Artificial Intelligence, and Data Science. As a technical product manager specializing in these areas, I've compiled this list to help developers, researchers, and enthusiasts stay up-to-date with the latest advancements and tools.

## How This Landing Page Works

This GitHub landing page is **automatically updated every day by AI** to showcase my latest interests and discoveries in the fields of AI, Machine Learning, and Data Science.

Here's how it works:

1. **Automated Updates**: The repository list you see below is automatically updated daily using GitHub Actions that I've set up to run the AI pipeline.
2. **Starred Repositories**: The content is based on my GitHub starred repositories, reflecting my current interests and valuable finds in the tech world.
3. **AI-Powered Organization**: An AI model (GPT-3.5-turbo) is used to categorize and organize the repositories, ensuring that the list remains well-structured and informative.
4. **Minimal Manual Intervention**: Once set up, this page requires little to no manual updating. All I need to do is star a new repo and it will automatically be categorized and added to this document. When I remove a repo from my starred list, the AI automatically removes it from this page.

**Why use AI for this?**: The key thing that the LLM-based solution is doing is dynamically deciding what categories should exist on this and how to group my starred repos into those categories. It also reassess and changes the categories and groupings over time as the starred repos change. It does all of this without the need for me to decide in advance what categories it should consider or to pre-train the model on categories. Implementing this algorithm is extremely simple compared to implementing a solution with a more traditional ML/AI approach that doesn't have the NLP reasoning capabilities of an LLM.

## 📚 Table of Contents

- [Generative AI](#generative-ai)
  - [Large Language Models (LLMs)](#large-language-models-llms)
  - [Chat Applications](#chat-applications)
- [Artificial Intelligence](#artificial-intelligence)
  - [Machine Learning Frameworks](#machine-learning-frameworks)
  - [Autonomous Agents](#autonomous-agents)
- [Data Science](#data-science)
  - [Data Visualization](#data-visualization)
  - [Data Analysis](#data-analysis)
- [MLOps & AI Infrastructure](#mlops--ai-infrastructure)
- [AI Ethics & Responsible AI](#ai-ethics--responsible-ai)
- [Resume Tools](#resume-tools)
- [Other](#other)
- [How to Implement This Landing Page On Your Own GitHub](#how-to-implement-this-landing-page-on-your-own-github)
- [🌟 Contributing](#-contributing)
- [📄 License](#-license)

## Generative AI

### Large Language Models (LLMs)

- [AGiXT](https://github.com/AGiXT) - A dynamic AI Agent Automation Platform that seamlessly orchestrates instruction management and complex task execution across diverse AI providers.
- [open-webui](https://github.com/open-webui) - User-friendly WebUI for LLMs (Formerly Ollama WebUI).
- [GenerativeAI](https://github.com/GenerativeAI) - GenAI & LLM usecases and applications.
- [ai-toolkit](https://github.com/ai-toolkit) - Various AI scripts. Mostly Stable Diffusion stuff.
- [kotaemon](https://github.com/kotaemon) - An open-source RAG-based tool for chatting with your documents.
- [llamacoder](https://github.com/llamacoder) - Open source Claude Artifacts – built with Llama 3.1 405B.

### Chat Applications

- [ai-chat-protocol](https://github.com/ai-chat-protocol) - A library + API spec for easily streaming generative AI output to your chat applications.

## Artificial Intelligence

### Machine Learning Frameworks

- [playwright-python](https://github.com/playwright-python) - Python version of the Playwright testing and automation library.

### Autonomous Agents

- [babyagi](https://github.com/babyagi) - BabyAGI, an autonomous AI agent with task prioritization and task execution capabilities.
- [Teenage-AGI](https://github.com/Teenage-AGI) - Teenage-AGI project with advanced AI agents.
- [gptrpg](https://github.com/gptrpg) - A demo of a GPT-based agent existing in an RPG-like environment.
- [crewAI](https://github.com/crewAI) - Framework for orchestrating role-playing, autonomous AI agents.
- [AutoGPT](https://github.com/AutoGPT) - The vision of accessible AI for everyone, to use and to build on. Our mission is to provide the tools, so that you can focus on what matters.

## Data Science

### Data Visualization

- [gradio](https://github.com/gradio) - Build and share delightful machine learning apps, all in Python.

### Data Analysis

- [llama_index](https://github.com/llama_index) - LlamaIndex is a data framework for your LLM applications.
- [paper-qa](https://github.com/paper-qa) - High accuracy RAG for answering questions from scientific documents with citations.

## MLOps & AI Infrastructure

- [mactop](https://github.com/mactop) - Apple Silicon Monitor Top written in pure Golang.
- [ragapp](https://github.com/ragapp) - The easiest way to use Agentic RAG in any enterprise.

## AI Ethics & Responsible AI

- [artkit](https://github.com/artkit) - Automated prompt-based testing and evaluation of Gen AI applications.

## Resume Tools

- [resume.md](https://github.com/resume.md) - Write your resume in Markdown, style it with CSS, output to HTML and PDF.
- [markdown-resume](https://github.com/markdown-resume) - A simple, elegant, and fast workflow to write resumes and CVs in Markdown.
- [online-resume](https://github.com/online-resume) - A minimalist Jekyll theme for your resume.
- [DevResume-Theme](https://github.com/DevResume-Theme) - DevResume - Bootstrap 5 Resume/CV Theme for Software Developers.

## Other

- [llama-fs](https://github.com/llama-fs) - A self-organizing file system with llama 3.
- [jigsaw-generator](https://github.com/jigsaw-generator) - Software for creating jigsaw puzzles using LaTeX, with output similar to Tarsia's Formulator software.
- [piecemaker](https://github.com/piecemaker) - Create jigsaw puzzle pieces.
- [gpt-assistants-api-ui](https://github.com/gpt-assistants-api-ui) - OpenAI Assistants API chat UI that supports file upload/download and Streaming API.
- [whisperX](https://github.com/whisperX) - WhisperX: Automatic Speech Recognition with Word-level Timestamps (& Diarization).

## How to Implement This Landing Page On Your Own GitHub

If you'd like to create a similar landing page for your GitHub profile:

1. Fork this repository.
2. Set up the following secrets in your forked repository's settings:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `PAT`: A GitHub Personal Access Token with appropriate permissions
3. Update the `update_readme.py` script in the `.github/scripts/` directory:
   - Replace `"YourGitHubUsername"` with your actual GitHub username
4. Customize the README.md template to fit your personal brand and interests.
5. The GitHub Action will run daily, updating your README with your latest starred repositories.

Feel free to modify the script or the README structure to better suit your needs. Happy showcasing!

---

**Note**: This landing page uses OpenAI's GPT-3.5-turbo model. Make sure you comply with OpenAI's use-case policies and monitor your API usage to manage costs.

---

## 🌟 Contributing

Feel free to open a pull request if you have any suggestions for additions or improvements to this list. Let's collaborate to keep this resource up-to-date and valuable for the community!

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

---

📊 *Last edited: [September 19, 2024]*

🔗 Connect with me on [LinkedIn](https://www.linkedin.com/in/taubersean)