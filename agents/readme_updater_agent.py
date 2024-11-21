from .base_agent import BaseAgent
from models.repo_models import RepoDetails
from models.editor_models import EditorNote
from openai import OpenAI
from pydantic import ValidationError
import re
import json
from datetime import datetime

class ReadmeUpdaterAgent(BaseAgent):
    """
    ReadmeUpdater Agent: Updates the README.md with curated repository information.
    """
    def __init__(self, archive_agent):
        super().__init__(name="ReadmeUpdaterAgent")
        self.archive_agent = archive_agent  # Instance of ArchiveAgent
    
    def build_repos_section(self, grouped_repos: dict[str, list[RepoDetails]]) -> str:
        """
        Builds the repositories section for the README based on the grouped repositories data.
        """
        section = ""
        for category, repos in grouped_repos.items():
            section += f"## {category}\n\n"
            for repo in repos:
                # Format the repository details into the README section
                section += (
                    f"- [{repo.name}]({repo.html_url}) - {repo.description}\n"
                    f"  - ⭐ Stars: {repo.stargazers_count}, 🍴 Forks: {repo.forks_count}, "
                    f"👀 Watchers: {repo.watchers_count}, 🛠️ Issues: {repo.open_issues_count}\n"
                    f"  - 🔍 Language: {repo.language}, 🌱 Default Branch: {repo.default_branch}, "
                    f"📈 Star Growth: {repo.star_growth_rate:.2f}%, 🔥 Activity Level: {repo.activity_level}\n"
                    f"  - 📆 Created: {repo.created_at}, Updated: {repo.updated_at}\n"
                    f"  - 🎯 Relevance: {repo.relevance}, 🏷️ Topics: {', '.join(repo.topics)}\n\n"
                )
            section += "\n"
        return section

    
    def update_table_of_contents(self, readme_content: str, categories: list) -> str:
        toc_start = "## 📚 Table of Contents"
        toc_end = "## Generative AI"  # Adjust based on actual README structure
        existing_toc_pattern = re.compile(r'## 📚 Table of Contents.*?## Generative AI', re.DOTALL)
        
        new_toc = f"{toc_start}\n\n"
        for category in categories:
            toc_entry = f"- [{category}](#{self.slugify(category)})\n"
            new_toc += toc_entry
        # Add remaining sections
        new_toc += "- [How to Implement This Landing Page On Your Own GitHub](#how-to-implement-this-landing-page-on-your-own-github)\n"
        new_toc += "- [🌟 Contributing](#-contributing)\n"
        new_toc += "- [📄 License](#-license)\n"
        new_toc += "- [Explanation of the Updates](#explanation-of-the-updates)\n"
        new_toc += "- [Final Notes](#final-notes)\n"
        
        updated_content = re.sub(existing_toc_pattern, f"{new_toc}\n## Generative AI", readme_content, count=1)
        return updated_content
    
    def slugify(self, text: str) -> str:
        return re.sub(r'[\s&]+', '-', text.lower())
    
    def execute(self, grouped_repos: dict, editors_note: EditorNote, readme_path: str = 'README.md'):
        try:
            with open(readme_path, 'r') as file:
                readme_content = file.read()
        except FileNotFoundError:
            print(f"ReadmeUpdaterAgent Error: {readme_path} not found.")
            raise
        except Exception as e:
            print(f"ReadmeUpdaterAgent Error reading {readme_path}: {e}")
            raise
        
        # Update repositories sections
        repo_sections = self.build_repos_section(grouped_repos)
        
        # Insert the repo sections into the README
        # Adjust the regex based on the actual README structure
        repo_section_pattern = re.compile(r'## Generative AI\n\n(.*?)\n## ', re.DOTALL)
        updated_readme = re.sub(repo_section_pattern, f"## Generative AI\n\n{repo_sections}\n## ", readme_content, flags=re.DOTALL)
        
        # Update the Table of Contents
        categories = list(grouped_repos.keys())
        updated_readme = self.update_table_of_contents(updated_readme, categories)
        
        # Update the Editor's Note
        editors_note_pattern = re.compile(r"### Editor's Note\n\n(.*?)\n\n", re.DOTALL)
        updated_readme = re.sub(editors_note_pattern, f"### Editor's Note\n\n{editors_note.content}\n\n", updated_readme)
        
        # Update the Last edited date
        current_date = datetime.now().strftime("%B %d, %Y")
        updated_readme = re.sub(r'\*Last edited: .*?\*', f'*Last edited: {current_date}*', updated_readme)
        
        # Link the archive
        updated_readme += "\n\nFor a history of editor summaries, check the [Editor Summaries Archive](EDITOR_SUMMARIES.md).\n"
        
        # Write the updated README
        try:
            with open(readme_path, 'w') as file:
                file.write(updated_readme)
            print(f"ReadmeUpdaterAgent: Successfully updated {readme_path}.")
        except Exception as e:
            print(f"ReadmeUpdaterAgent Error writing to {readme_path}: {e}")
            raise
        
        # Archive the editor's note using the execute method
        try:
            self.archive_agent.execute(editors_note.content)
        except Exception as e:
            print(f"ReadmeUpdaterAgent Error archiving editor's note: {e}")
            raise
