from .base_agent import BaseAgent
from models.editor_models import EditorNote, ExtractedReadme, Category, Repository
from openai import OpenAI
from pydantic import ValidationError
import json

class EditorAgent(BaseAgent):
    """
    Editor Agent: Aligns new repositories with existing README structure and updates it.
    """
    def __init__(self, client: OpenAI):
        super().__init__(name="EditorAgent")
        self.client = client
        self.system_prompt = (
            "You are an Editor Agent. Your role is to align new repository data with the existing README structure, "
            "maintaining consistency and making structural improvements when necessary."
        )

    def extract_existing_repos(self, readme_content: str) -> ExtractedReadme:
        """
        Uses an LLM to extract existing repositories from the README into a structured JSON format
        and validate the structure using Pydantic models.
        """
        prompt = (
            "You are an assistant tasked with extracting structured information from a GitHub README file. The README contains a list of repositories organized under different categories. "
            "Your goal is to read the content and output the data as a JSON object with the following format:\n\n"
            "{\n"
            '  "Category Name": [\n'
            '    {"name": "Repository Name", "url": "Repository URL", "description": "Repository Description"}\n'
            "  ],\n"
            '  "Another Category": [\n'
            '    {"name": "Another Repository", "url": "Repository URL", "description": "Repository Description"}\n'
            "  ]\n"
            "}\n\n"
            "If a category contains repositories without descriptions, use 'No description available' as the description. Ensure that all category names are preserved exactly as they appear in the README.\n"
            "Here is the README content:\n\n"
            f"README:\n{readme_content}\n\n"
            "Extract the data and return it in the specified JSON format."
        )

        try:
            response = self.client.beta.chat.completions.create(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format=ExtractedReadme,
                max_tokens=1000,
                temperature=0.3
            )
            extracted_readme = completion.choices[0].message.parsed
            return extracted_readme
        except json.JSONDecodeError as jde:
            print(f"Error parsing LLM response as JSON: {jde}")
            return ExtractedReadme(categories=[])
        except ValidationError as ve:
            print(f"Validation error with Pydantic model: {ve}")
            return ExtractedReadme(categories=[])
        except Exception as e:
            print(f"Unexpected error during LLM extraction: {e}")
            return ExtractedReadme(categories=[])

    def align_repos(self, existing_repos: ExtractedReadme, new_repos: list) -> ExtractedReadme:
        """
        Aligns new repositories with existing ones, favoring existing structure but allowing improvements.
        Uses an LLM to categorize repositories more robustly.
        """
        # Convert existing repos to a dictionary for easier merging
        aligned_repos = {category.name: category.repositories for category in existing_repos.categories}

        def categorize_with_llm(repo):
            """
            Uses the LLM to determine the most appropriate category for the given repository.
            """
            prompt = (
                "You are an AI assistant tasked with categorizing repositories based on their descriptions and details. "
                "Below are the current categories:\n\n"
                "1. **Generative AI**: Repositories focusing on text generation, image generation, music generation, code generation, etc. Includes models like GPT, LLMs, and GANs.\n"
                "2. **Artificial Intelligence**: General-purpose AI frameworks, machine learning models, reinforcement learning, NLP, computer vision.\n"
                "    - **Machine Learning Frameworks**: Libraries designed to train, deploy, or serve ML models.\n"
                "    - **Chatbots & Assistance**: Conversational agents, automated assistants, customer support bots, etc.\n"
                "3. **Data Science**: Tools for data analysis, visualization, statistical modeling, etc. Includes libraries like pandas, NumPy, and visualization tools.\n"
                "4. **MLOps & AI Infrastructure**: Tools for managing and deploying AI models in production, monitoring, and infrastructure.\n"
                "5. **Agentic Frameworks**: Libraries focused on multi-agent systems or agent-based development, autonomous systems, coordination frameworks.\n"
                "6. **Other**: Repositories that do not fit into the categories above.\n\n"
                "Based on the following details, assign this repository to the most appropriate category or suggest a new subcategory if needed:\n\n"
                f"Repository Name: {repo['name']}\n"
                f"Repository Description: {repo['description']}\n"
                f"Topics: {repo.get('topics', 'N/A')}\n"
                f"Language: {repo.get('language', 'N/A')}\n\n"
                "Return only the category name or subcategory name."
            )

            try:
                response = self.client.beta.chat.completions.create(
                    model="gpt-4o-2024-08-06",
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    response_format=CategoryAssignment,
                    max_tokens=50,
                    temperature=0.2
                )
                category = completion.choices[0].message.parsed
                return category
            except Exception as e:
                print(f"Error during LLM categorization: {e}")
                return "Other"  # Default to "Other" in case of errors

        # Assign each new repository to a category using the LLM
        for repo in new_repos:
            category = categorize_with_llm(repo)
            if category not in aligned_repos:
                aligned_repos[category] = []
            aligned_repos[category].append(Repository(**repo))

        # Convert aligned_repos back to the ExtractedReadme structure
        return ExtractedReadme.from_dict(aligned_repos)

    def create_editors_note(self, existing_repos: ExtractedReadme, aligned_repos: ExtractedReadme) -> EditorNote:
        prompt = (
            f"Given the existing repositories in the README and the newly aligned repositories, generate an editor's note explaining the changes made to the repository list and structure.\n\n"
            f"Existing Repositories:\n{existing_repos.json(indent=2)}\n\n"
            f"Aligned Repositories:\n{aligned_repos.json(indent=2)}\n\n"
            "Tasks:\n"
            "1. Summarize the changes made to the repository list, including newly added, removed, or re-categorized repositories.\n"
            "2. Explain any structural modifications made to the README. Specify if any new categories or subcategories were introduced, merged, or renamed.\n"
            "3. Highlight improvements or optimizations in categorization, focusing on why certain repositories were moved or added to specific categories.\n"
            "4. Mention any repositories that remain in the 'Other' category and provide justification for why they could not be confidently categorized elsewhere.\n"
            "5. Maintain a professional and concise tone, suitable for an editorial note.\n\n"
            "Provide the output in JSON format adhering to the following schema:\n\n"
            "{\n"
            '    "content": "string"\n'
            "}"
        )
        
        try:
            completion = self.client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format=EditorNote,
                temperature=0.5,
                max_tokens=300
            )
            editors_note = completion.choices[0].message.parsed
            return editors_note
        except ValidationError as ve:
            print(f"EditorAgent Validation Error: {ve}")
            raise ve
        except Exception as e:
            print(f"EditorAgent Unexpected Error: {e}")
            raise e

    def execute(self, new_repos: list, readme_content: str) -> dict:
        existing_repos = self.extract_existing_repos(readme_content)
        aligned_repos = self.align_repos(existing_repos, new_repos)
        editors_note = self.create_editors_note(existing_repos, aligned_repos)
        return {
            "aligned_repos": aligned_repos,
            "editors_note": editors_note
        }
