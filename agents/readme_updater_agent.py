from .base_agent import BaseAgent
from models.repo_models import RepoDetails
from models.editor_models import EditorNote
from openai import OpenAI
from pydantic import ValidationError
import re
from datetime import datetime

class ReadmeUpdaterAgent(BaseAgent):
    """
    ReadmeUpdater Agent: Updates the README.md with curated repository information.
    Uses a combination of LLM and pattern matching for robust content updates.
    """
    def __init__(self, archive_agent, openai_client=None):
        super().__init__(name="ReadmeUpdaterAgent")
        self.archive_agent = archive_agent  # Instance of ArchiveAgent
        self.openai_client = openai_client  # Optional OpenAI client for LLM processing
    
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
        """
        Updates the table of contents section using pattern matching.
        """
        toc_start = "## 📚 Table of Contents"
        toc_end = "## Generative AI"
        
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
        
        # Find and replace the TOC section
        pattern = f"{toc_start}.*?{toc_end}"
        updated_content = re.sub(pattern, f"{new_toc}\n{toc_end}", readme_content, flags=re.DOTALL)
        return updated_content
    
    def slugify(self, text: str) -> str:
        """Convert text to URL-friendly slug format."""
        return re.sub(r'[\s&]+', '-', text.lower())
    
    def update_section(self, content: str, section_name: str, new_content: str) -> str:
        """
        Updates a specific section in the content using pattern matching.
        Falls back to LLM-based processing if pattern matching fails.
        """
        try:
            # First attempt: Pattern matching
            pattern = f"## {section_name}.*?(?=##|$)"
            updated = re.sub(pattern, f"## {section_name}\n\n{new_content}\n\n", content, flags=re.DOTALL)
            
            # Verify the update was successful
            if new_content not in updated:
                raise ValueError("Pattern matching failed to update content")
            
            return updated
            
        except Exception as e:
            print(f"Pattern matching failed for section {section_name}: {str(e)}")
            
            # Second attempt: LLM-based processing if available
            if self.openai_client:
                try:
                    prompt = f"""
                    Given this markdown content:
                    ---
                    {content}
                    ---
                    
                    Replace the section "{section_name}" with this new content:
                    ---
                    {new_content}
                    ---
                    
                    Return the complete updated markdown content.
                    """
                    
                    response = self.openai_client.chat.completions.create(
                        model="gpt-4",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0
                    )
                    
                    return response.choices[0].message.content
                    
                except Exception as llm_error:
                    print(f"LLM processing failed: {str(llm_error)}")
                    raise
            else:
                raise
    
    def execute(self, grouped_repos: dict, editors_note: EditorNote, readme_path: str = 'README.md'):
        """
        Executes the README update process with improved error handling and content processing.
        """
        try:
            # Read the current README
            with open(readme_path, 'r') as file:
                readme_content = file.read()
        except FileNotFoundError:
            print(f"ReadmeUpdaterAgent Error: {readme_path} not found.")
            raise
        except Exception as e:
            print(f"ReadmeUpdaterAgent Error reading {readme_path}: {e}")
            raise
        
        try:
            # Build and update repository sections
            repo_sections = self.build_repos_section(grouped_repos)
            readme_content = self.update_section(readme_content, "Generative AI", repo_sections)
            
            # Update table of contents
            categories = list(grouped_repos.keys())
            readme_content = self.update_table_of_contents(readme_content, categories)
            
            # Update editor's note
            readme_content = self.update_section(readme_content, "Editor's Note", editors_note.content)
            
            # Update last edited date
            current_date = datetime.now().strftime("%B %d, %Y")
            readme_content = re.sub(
                r'\*Last edited:.*?\*',
                f'*Last edited: {current_date}*',
                readme_content
            )
            
            # Ensure archive link is present
            if "Editor Summaries Archive" not in readme_content:
                readme_content += "\n\nFor a history of editor summaries, check the [Editor Summaries Archive](EDITOR_SUMMARIES.md).\n"
            
            # Write the updated README
            with open(readme_path, 'w') as file:
                file.write(readme_content)
            print(f"ReadmeUpdaterAgent: Successfully updated {readme_path}.")
            
            # Archive the editor's note
            self.archive_agent.execute(editors_note.content)
            print("ReadmeUpdaterAgent: Successfully archived editor's note.")
            
            return True
            
        except Exception as e:
            print(f"ReadmeUpdaterAgent Error during execution: {str(e)}")
            raise
