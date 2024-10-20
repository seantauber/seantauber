from .base_agent import BaseAgent
from models.curation_models import CurationDetails
from models.repo_models import RepoDetails
from openai import OpenAI
from pydantic import ValidationError
import json

class CurationAgent(BaseAgent):
    """
    Curation Agent: Assigns tags and scores to repositories.
    """
    def __init__(self, client: OpenAI):
        super().__init__(name="CurationAgent")
        self.client = client
        self.system_prompt = (
            "You are a Curation Agent. Your role is to assign relevant tags and calculate popularity and trending scores for repositories."
        )
    
    def curate_repo(self, repo: RepoDetails) -> CurationDetails:
        prompt = (
            f"Based on the following repository details, assign relevant tags and calculate popularity and trending scores:\n\n"
            f"Repository Details:\n{repo.json()}\n\n"
            "Tasks:\n"
            "1. Assign relevant tags based on description, topics, and language.\n"
            "2. Calculate a popularity score (weighted combination of stars per year and activity level).\n"
            "3. Calculate a trending score (based on star growth rate).\n\n"
            "Provide the output in JSON format adhering to the following schema:\n\n"
            "{\n"
            '    "tags": ["string"],\n'
            '    "popularity_score": number,\n'
            '    "trending_score": number\n'
            "}"
        )
        
        try:
            completion = self.client.beta.chat.completions.parse(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format=CurationDetails,
                max_tokens=150
            )
            curation = completion.choices[0].message.parsed
            return curation
        except ValidationError as ve:
            print(f"CurationAgent Validation Error: {ve}")
            raise ve
        except Exception as e:
            print(f"CurationAgent Unexpected Error: {e}")
            raise e
    
    def execute(self, repos: list) -> list:
        curated_repos = []
        for repo in repos:
            try:
                curation = self.curate_repo(repo)
                repo_dict = repo.dict()
                repo_dict.update(curation.dict())
                curated_repos.append(repo_dict)
            except Exception as e:
                print(f"CurationAgent Error curating repo {repo.full_name}: {e}")
        return curated_repos
