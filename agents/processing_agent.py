from .base_agent import BaseAgent
from models.repo_models import RepoDetails
from openai import OpenAI
from pydantic import ValidationError
import json
from datetime import datetime

class ProcessingAgent(BaseAgent):
    """
    Processing Agent: Cleans and enriches repository data.
    """
    def __init__(self, client: OpenAI):
        super().__init__(name="ProcessingAgent")
        self.client = client
        self.system_prompt = (
            "You are a Processing Agent. Your role is to clean and enrich repository data."
        )
    
    def process_repo(self, repo: dict) -> RepoDetails:
        prompt = (
            f"Given the following repository data, clean and enrich it with additional metrics.\n\n"
            f"Repository Data:\n{json.dumps(repo, indent=2)}\n\n"
            "Tasks:\n"
            "- Remove any unnecessary fields.\n"
            "- Calculate star growth rate (stars per year since creation).\n"
            "- Determine activity level based on the number of days since the last update (High, Medium, Low).\n"
            "- Provide a relevance summary combining star growth rate and activity level.\n\n"
            "Provide the output in JSON format adhering to the following schema:\n\n"
            "{\n"
            '    "name": "string",\n'
            '    "full_name": "string",\n'
            '    "description": "string",\n'
            '    "html_url": "string",\n'
            '    "stargazers_count": integer,\n'
            '    "forks_count": integer,\n'
            '    "open_issues_count": integer,\n'
            '    "watchers_count": integer,\n'
            '    "language": "string",\n'
            '    "updated_at": "string",\n'
            '    "created_at": "string",\n'
            '    "topics": ["string"],\n'
            '    "default_branch": "string",\n'
            '    "star_growth_rate": number,\n'
            '    "activity_level": "string",\n'
            '    "relevance": "string"\n'
            "}"
        )
        
        try:
            completion = self.client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format=RepoDetails,
                max_tokens=300
            )
            processed_repo = completion.choices[0].message.parsed
            return processed_repo
        except ValidationError as ve:
            print(f"ProcessingAgent Validation Error: {ve}")
            raise ve
        except Exception as e:
            print(f"ProcessingAgent Unexpected Error: {e}")
            raise e
    
    def execute(self, repos: list) -> list:
        processed_repos = []
        for repo in repos:
            try:
                processed_repo = self.process_repo(repo)
                processed_repos.append(processed_repo)
            except Exception as e:
                print(f"ProcessingAgent Error processing repo {repo.get('full_name')}: {e}")
        return processed_repos
