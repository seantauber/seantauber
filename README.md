# 🤖 GenAI, AI, and Data Science Resources

Welcome to my AI GENERATED list of interesting repositories in the fields of Generative AI, Artificial Intelligence, and Data Science. As an AI Engineer & Product Development Specialist in these areas, I've compiled this list to help developers, researchers, and enthusiasts stay up-to-date with the latest advancements and tools.

## How This Landing Page Works

This GitHub landing page is **automatically updated every day by AI** to showcase my latest interests and discoveries in the fields of AI, Machine Learning, and Data Science.

Here's how it works:

1. **Automated Updates**: The repository list you see below is automatically updated daily using GitHub Actions that I've set up to run the AI pipeline.
2. **Starred Repositories**: The content is based on my GitHub starred repositories, reflecting my current interests and valuable finds in the tech world.
3. **AI-Powered Organization**: An AI model (GPT-4o) is used to categorize and organize the repositories, ensuring that the list remains well-structured and informative.
4. **Minimal Manual Intervention**: Once set up, this page requires little to no manual updating. All I need to do is star a new repo and it will automatically be categorized and added to this document. When I remove a repo from my starred list, the AI automatically removes it from this page.

**Why use AI for this?**: The key thing that the LLM-based solution is doing is dynamically deciding what categories should exist on this page and how to group my starred repos into those categories. It also reassesses and changes the categories and groupings over time as the starred repos change. It does all of this without the need for me to decide in advance what categories it should consider or to pre-train the model on categories. Implementing this algorithm is extremely simple compared to implementing a solution with a more traditional ML/AI approach that doesn't have the NLP reasoning capabilities of an LLM.

## 📚 Table of Contents

- [Generative AI](#generative-ai)
- [Artificial Intelligence](#artificial-intelligence)
- [MLOps & AI Infrastructure](#mlops--ai-infrastructure)
- [AI Agents](#ai-agents)
- [Model Context Protocol (MCP)](#model-context-protocol-mcp)
- [Other](#other)
- [How to Implement This Landing Page On Your Own GitHub](#how-to-implement-this-landing-page-on-your-own-github)
- [🌟 Contributing](#-contributing)
- [📄 License](#-license)

## Generative AI

- [HKUDS/LightRAG](https://github.com/HKUDS/LightRAG) - "LightRAG: Simple and Fast Retrieval-Augmented Generation".

## Artificial Intelligence

- [elevenlabs/elevenlabs-examples](https://github.com/elevenlabs/elevenlabs-examples) - Various use cases and examples for ElevenLabs' tools and APIs.

## MLOps & AI Infrastructure

- [ZubeidHendricks/youtube-mcp-server](https://github.com/ZubeidHendricks/youtube-mcp-server) - MCP Server for YouTube API, enabling video management, Shorts creation, and advanced analytics.
- [varunneal/spotify-mcp](https://github.com/varunneal/spotify-mcp) - MCP to connect Claude with Spotify.
- [GeLi2001/shopify-mcp](https://github.com/GeLi2001/shopify-mcp) - MCP server for Shopify api, usable on mcp clients such as Anthropic's Claude and Cursor IDE.
- [makeplane/plane](https://github.com/makeplane/plane) - Open Source JIRA, Linear, Monday, and Asana Alternative.

## AI Agents

- [wjayesh/mahilo](https://github.com/wjayesh/mahilo) - mahilo: Multi-Agent Human-in-the-Loop Framework is a flexible framework for creating multi-agent systems that can each interact with humans while sharing relevant context internally.
- [jezweb/roo-commander](https://github.com/jezweb/roo-commander) - Think of it like having a virtual, specialized software development team right inside your editor, orchestrated by the 👑 Roo Commander, powered by Roo Code on VS Code.
- [GreatScottyMac/RooFlow](https://github.com/GreatScottyMac/RooFlow) - RooFlow - Enhanced Memory Bank System with ☢️Footgun Power☢️ Next-gen Memory Bank system with five integrated modes and system-level customization. Uses Roo Code's experimental "Footgun" feature for deep AI assistant customization while maintaining efficient token usage!

## Model Context Protocol (MCP)

- [ibraheem4/linear-mcp](https://github.com/ibraheem4/linear-mcp) - Enables AI agents to manage issues, projects, and teams on the Linear platform programmatically.
- [dvcrn/mcp-server-siri-shortcuts](https://github.com/dvcrn/mcp-server-siri-shortcuts) - MCP for calling Siri Shorcuts from LLMs.
- [jerhadf/linear-mcp-server](https://github.com/jerhadf/linear-mcp-server) - A server that integrates Linear's project management system with the Model Context Protocol (MCP) to allow LLMs to interact with Linear.
- [ferrislucas/iterm-mcp](https://github.com/ferrislucas/iterm-mcp) - A Model Context Protocol server that executes commands in the current iTerm session - useful for REPL and CLI assistance.
- [sooperset/mcp-atlassian](https://github.com/sooperset/mcp-atlassian) - MCP server for Atlassian tools (Confluence, Jira).
- [evalstate/mcp-hfspace](https://github.com/evalstate/mcp-hfspace) - MCP Server to Use HuggingFace spaces, easy configuration and Claude Desktop mode.
- [tegonhq/tegon](https://github.com/tegonhq/tegon) - Tegon is an open-source, dev-first alternative to Jira, Linear.

## Other

- [google/A2A](https://github.com/google/A2A) - An open protocol enabling communication and interoperability between opaque agentic applications.
- [Michaelzag/RooCode-Tips-Tricks](https://github.com/Michaelzag/RooCode-Tips-Tricks)

## How to Implement This Landing Page On Your Own GitHub

This project automatically updates the README with your GitHub starred repositories using a Python script and GitHub Actions.

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

**Note**: This landing page uses OpenAI's GPT-4o model. Make sure you comply with OpenAI's use-case policies and monitor your API usage to manage costs.

---

## 🌟 Contributing

Feel free to open a pull request if you have any suggestions for additions or improvements to this list. Let's collaborate to keep this resource up-to-date and valuable for the community!

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

---

📊 *Last edited: 2025-04-14*

🔗 Connect with me on [LinkedIn](https://www.linkedin.com/in/taubersean)