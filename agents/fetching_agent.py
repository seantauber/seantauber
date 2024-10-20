from .base_agent import BaseAgent
from models.repo_models import RepoDetails
from openai import OpenAI
from pydantic import ValidationError
import requests

class FetchingAgent(BaseAgent):
    """
    Fetching Agent: Retrieves starred repositories from GitHub.
    """
    def __init__(self, client: OpenAI, github_token: str):
        super().__init__(name="FetchingAgent")
        self.client = client
        self.github_token = github_token
        self.headers = {"Authorization": f"token {self.github_token}"}
    
    def fetch_starred_repos(self, username: str) -> list:
        url = f"https://api.github.com/users/{username}/starred"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def execute(self, username: str) -> list:
        try:
            repos = self.fetch_starred_repos(username)
            return repos
        except requests.exceptions.RequestException as e:
            print(f"FetchingAgent Error fetching repos: {e}")
            raise e
