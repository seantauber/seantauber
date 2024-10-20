from .base_agent import BaseAgent
from models.editor_models import EditorNote
from openai import OpenAI
from pydantic import ValidationError
import json
import re

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
    
    def extract_existing_repos(self, readme_content: str) -> list:
        """
        Extracts existing repositories from the README based on a known section or pattern.
        Assumes repositories are listed under specific headings.
        """
        # Example pattern: assuming repositories are under headings like ## Category Name
        repo_pattern = re.compile(r"## (\w+)\n\n((?:- \[.*?\]\(.*?\) - .*\n)+)", re.DOTALL)
        matches = repo_pattern.findall(readme_content)
        existing_repos = {}
        for category, repo_list in matches:
            repos = re.findall(r"- \[(.*?)\]\((.*?)\) - (.*)", repo_list)
            existing_repos[category] = [{"name": name, "url": url, "description": desc} for name, url, desc in repos]
        return existing_repos
    
    def align_repos(self, existing_repos: dict, new_repos: list) -> dict:
        """
        Aligns new repositories with existing ones, favoring existing structure but allowing improvements.
        """
        # This function can be expanded to perform more sophisticated alignment logic
        # For simplicity, we'll categorize new repos independently
        return new_repos  # Placeholder
    
    def create_editors_note(self, existing_repos: dict, aligned_repos: dict) -> EditorNote:
        prompt = (
            f"Given the existing repositories in the README and the newly aligned repositories, generate an editor's note explaining the changes made.\n\n"
            f"Existing Repositories:\n{json.dumps(existing_repos, indent=2)}\n\n"
            f"Aligned Repositories:\n{json.dumps(aligned_repos, indent=2)}\n\n"
            "Tasks:\n"
            "1. Summarize the changes made to the repository list.\n"
            "2. Explain any structural modifications to the README.\n"
            "3. Highlight improvements or optimizations in categorization.\n\n"
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
