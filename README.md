# ⭐ GitHub Starred Repositories Tracker

![GitHub Repo stars](https://img.shields.io/github/stars/seantauber/starred-repos-tracker?style=social)

## 📚 Table of Contents
- [⭐ GitHub Starred Repositories Tracker](#-github-starred-repositories-tracker)
  - [📚 Table of Contents](#-table-of-contents)
  - [Introduction](#introduction)
  - [⭐ Starred Repositories](#-starred-repositories)
  - [Generative AI](#generative-ai)
    - [Large Language Models (LLMs)](#large-language-models-llms)
  - [Artificial Intelligence](#artificial-intelligence)
    - [Machine Learning Frameworks](#machine-learning-frameworks)
    - [Chatbots \& Assistance](#chatbots--assistance)
  - [Data Science](#data-science)
    - [Data Analysis](#data-analysis)
  - [MLOps \& AI Infrastructure](#mlops--ai-infrastructure)
  - [Agentic Frameworks](#agentic-frameworks)
  - [Other](#other)
  - [🔧 Implementation Details](#-implementation-details)
    - [Architecture Overview](#architecture-overview)
    - [Multi-Agent System](#multi-agent-system)
  - [Setup and Installation](#setup-and-installation)
    - [Prerequisites](#prerequisites)
    - [Installation Steps](#installation-steps)
    - [Usage](#usage)
    - [Customization](#customization)
    - [📂 Developer Guide](#-developer-guide)
    - [🌟 Contributing](#-contributing)
    - [📄 License](#-license)

## Introduction

Welcome to the **GitHub Starred Repositories Tracker**! This project automates the process of updating your GitHub `README.md` with your latest starred repositories. By leveraging OpenAI's advanced language models and a structured multi-agent system, this tool ensures your repository list remains current, well-organized, and insightful.

This tracker serves as a practical example of implementing generative AI solutions to streamline and enhance personal projects, demonstrating effective use of automation and AI-driven data processing.

## ⭐ Starred Repositories

Here is the curated list of my starred repositories:

<!-- Starred Repositories Section Start -->
## Generative AI

### Large Language Models (LLMs)

- [create-llama](https://github.com/run-llama/create-llama) - The easiest way to get started with LlamaIndex.
- [User-Centric-RAG-Using-Llamaindex-Multi-Agent-System-and-Qdrant](https://github.com/pavannagula/User-Centric-RAG-Using-Llamaindex-Multi-Agent-System-and-Qdrant) - Customize the RAG application with user preferences over LLMs, Embeddings, Search types, and Reranking Models.
- [llama-stack](https://github.com/meta-llama/llama-stack) - Model components of the Llama Stack APIs.
- [LLMs-from-scratch](https://github.com/rasbt/LLMs-from-scratch) - Implementing a ChatGPT-like LLM in PyTorch from scratch, step by step.
- [dynamic-few-shot-llamaindex-workflow](https://github.com/rsrohan99/dynamic-few-shot-llamaindex-workflow) - None.
- [finetune-Qwen2-VL](https://github.com/zhangfaen/finetune-Qwen2-VL) - None.

## Artificial Intelligence

### Machine Learning Frameworks

- [LitServe](https://github.com/Lightning-AI/LitServe) - Lightning-fast serving engine for any AI model of any size. Flexible. Easy. Enterprise-scale.

### Chatbots & Assistance

- [LibreChat](https://github.com/danny-avila/LibreChat) - Enhanced ChatGPT Clone with multiple model integrations and security features.
- [danswer](https://github.com/danswer-ai/danswer) - Gen-AI Chat for Teams, designed to leverage unique team knowledge.
- [llm-answer-engine](https://github.com/developersdigest/llm-answer-engine) - Build a Perplexity-Inspired Answer Engine using various modern technologies.

## Data Science

### Data Analysis

- [pandas-ai](https://github.com/Sinaptik-AI/pandas-ai) - Chat with your database (SQL, CSV, pandas, polars, mongodb, noSQL, etc). PandasAI makes data analysis conversational using LLMs (GPT 3.5 / 4, Anthropic, VertexAI) and RAG.

## MLOps & AI Infrastructure

- [MLOps-Basics](https://github.com/graviraja/MLOps-Basics) - None.

## Agentic Frameworks

- [Agent-S](https://github.com/simular-ai/Agent-S) - Agent S: an open agentic framework that uses computers like a human.
- [TapeAgents](https://github.com/ServiceNow/TapeAgents) - A framework facilitating all stages of the LLM Agent development lifecycle.
- [example-agents](https://github.com/hivenetwork-ai/example-agents) - Examples of AI Agents that can be built on SwarmZero.
- [autogen](https://github.com/microsoft/autogen) - A programming framework for agentic AI 🤖.
- [GENAI-CareerAssistant-Multiagent](https://github.com/amanv1906/GENAI-CareerAssistant-Multiagent) - GenAI career assistant.

## Other

- [openai/swarm](https://github.com/openai/swarm) - Educational framework exploring ergonomic, lightweight multi-agent orchestration.
- [Auto_Jobs_Applier_AIHawk](https://github.com/feder-cr/Auto_Jobs_Applier_AIHawk) - Auto_Jobs_Applier_AIHawk is a tool that automates the jobs application process.
- [insanely-fast-whisper](https://github.com/Vaibhavs10/insanely-fast-whisper) - None.
- [crawl4ai](https://github.com/unclecode/crawl4ai) - Open-source LLM Friendly Web Crawler & Scrapper.
- [qa-mdt](https://github.com/ivcylc/qa-mdt) - SOTA Text-to-music (TTM) Generation (OpenMusic).
- [Pyramid-Flow](https://github.com/jy0205/Pyramid-Flow) - Code of Pyramidal Flow Matching for Efficient Video Generative Modeling.
- [UltimateTab](https://github.com/BenoitBellegarde/UltimateTab) - Enhanced, ads-free and fast responsive interface to browse guitar tabs scraped from Ultimate Guitar.
- [fabric](https://github.com/danielmiessler/fabric) - An open-source framework for augmenting humans using AI.
- [niledatabase/niledatabase](https://github.com/niledatabase/niledatabase) - PostgreSQL reengineered for multi-tenant apps.
- [openai_realtime_client](https://github.com/run-llama/openai_realtime_client) - A simple client and utils for interacting with OpenAI's Realtime API in Python.
- [Prompt_Engineering](https://github.com/NirDiamant/Prompt_Engineering) - A collection of tutorials and implementations for Prompt Engineering techniques.
- [weave](https://github.com/wandb/weave) - Weave is a toolkit for developing AI-powered applications.

<!-- Starred Repositories Section End -->

---

📊 *Last edited: October 20, 2024*

🔗 Connect with me on [LinkedIn](https://www.linkedin.com/in/taubersean)


## 🔧 Implementation Details

### Architecture Overview

The **GitHub Starred Repositories Tracker** employs a **multi-agent system** powered by OpenAI's GPT-4 model with **Structured Outputs**. This architecture ensures that each component of the workflow operates efficiently and reliably, maintaining the integrity and organization of your `README.md`.

### Multi-Agent System

The system is composed of the following specialized agents:

1. **Triaging Agent**
   - **Role:** Acts as the coordinator, assessing tasks and delegating them to appropriate agents.
   - **Responsibilities:**
     - Evaluate incoming tasks or update triggers.
     - Delegate tasks to specialized agents based on the nature of the update.

2. **Fetching Agent**
   - **Role:** Retrieves your starred repositories from the GitHub API.
   - **Responsibilities:**
     - Fetch the latest list of starred repositories.
     - Ensure data integrity and handle API interactions.

3. **Processing Agent**
   - **Role:** Cleans and enriches the fetched repository data.
   - **Responsibilities:**
     - Remove duplicates and handle missing values.
     - Calculate metrics such as star growth rate and activity level.

4. **Curation Agent**
   - **Role:** Assigns tags and scores to repositories.
   - **Responsibilities:**
     - Categorize repositories based on relevance and topics.
     - Calculate popularity and trending scores to prioritize listings.

5. **Editor Agent**
   - **Role:** Aligns new repositories with the existing README structure.
   - **Responsibilities:**
     - Merge new curated data with existing entries.
     - Maintain consistency in categorization and tagging.
     - Generate editor's notes explaining changes and decisions.

6. **ReadmeUpdater Agent**
   - **Role:** Updates the `README.md` with the latest repository information.
   - **Responsibilities:**
     - Insert or update repository sections in the README.
     - Update the table of contents to reflect new categories.
     - Append links to archived editor notes.

7. **Archive Agent**
   - **Role:** Maintains a historical log of editor summaries.
   - **Responsibilities:**
     - Archive each editor's note with timestamps.
     - Provide a historical reference for changes made over time.

## Setup and Installation

### Prerequisites

- **Python 3.8+**
- **GitHub Personal Access Token (PAT):** Required to access the GitHub API.
- **OpenAI API Key:** Needed to utilize OpenAI's GPT-4 model.

### Installation Steps

1. **Clone the Repository**

```bash
git clone https://github.com/seantauber/starred-repos-tracker.git
cd starred-repos-tracker
```

2. **Create a Virtual Environment**

```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Install Dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure Environment Variables**

Create a `.env` file in the project root with the following content:

```env
GITHUB_TOKEN=your_github_personal_access_token
OPENAI_API_KEY=your_openai_api_key
```

Security Note: Ensure that the `.env` file is added to `.gitignore` to prevent accidental commits of sensitive information.

5. **Initialize the Agents**

The agents are modular and can be extended with additional capabilities as needed. By default, they come with predefined functionalities tailored to this project.

### Usage
To update your `README.md` with the latest starred repositories, execute the main script:

```bash
python update_readme.py`
```

This script orchestrates the multi-agent workflow:

1. Triaging Agent assesses the update task.
2. Fetching Agent retrieves your starred repositories.
3. Processing Agent cleans and enriches the data.
4. Curation Agent categorizes and scores the repositories.
5. Editor Agent aligns new data with the existing README.
6. ReadmeUpdater Agent updates the README.md.
7. Archive Agent logs the editor's notes for historical reference.

### Customization

The system is designed for extensibility. You can initialize agents with additional capabilities or modify existing ones to suit your specific needs. Refer to the [Developer Guide](docs/developer_guide.md) for detailed instructions on extending and customizing the agents.

### 📂 Developer Guide

For an in-depth understanding of the project's architecture, agent implementations, and customization options, please refer to the [Developer Guide](docs/developer_guide.md).

### 🌟 Contributing

Contributions are welcome! If you have suggestions or improvements, feel free to open an issue or submit a pull request.

### 📄 License

This project is licensed under the MIT License.

Explanation of the Updates
This project utilizes a structured multi-agent system powered by OpenAI's GPT-4 to automate the updating of your GitHub README.md. By fetching, processing, curating, and aligning your starred repositories, the system ensures your repository list remains current and well-organized. Detailed explanations of each agent's role and the workflow are provided above.

Final Notes
The GitHub Starred Repositories Tracker serves as both a practical tool for maintaining an updated list of repositories and a demonstration of effective generative AI solutions. By leveraging structured outputs and a modular multi-agent architecture, this project showcases the potential of AI-driven automation in personal and professional settings.

For any questions or support, please feel free to reach *out*

For a comprehensive developer-oriented documentation, please visit the [Developer Guide](docs/developer_guide.md).
