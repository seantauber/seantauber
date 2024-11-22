from typing import Optional, Union, List, Any
from .base_agent import BaseAgent
from models.repo_models import RepoDetails
from openai import OpenAI
from pydantic import ValidationError
from datetime import datetime

class ProcessingAgent(BaseAgent):
    """
    Processing Agent: Cleans and enriches repository data.
    """
    def __init__(self, client: Optional[Union[OpenAI, Any]] = None):
        super().__init__(name="ProcessingAgent", client=client)
    
    def process_repo(self, repo: dict) -> RepoDetails:
        prompt = (
            "You are a Processing Agent. Your role is to clean and enrich repository data.\n\n"
            f"Given the following repository data, clean and enrich it with additional metrics.\n\n"
            f"Repository Data:\n{repo}\n\n"
            "Tasks:\n"
            "1. Remove any unnecessary fields.\n"
            "2. Calculate star growth rate (stars per year since creation).\n"
            "3. Determine activity level based on days since last update:\n"
            "   - 'High': updated within last 30 days\n"
            "   - 'Medium': updated within last 90 days\n"
            "   - 'Low': updated more than 90 days ago\n"
            "4. Set relevance based on combined metrics:\n"
            "   - 'High': high activity and growth rate > 100\n"
            "   - 'Medium': medium activity or growth rate > 50\n"
            "   - 'Low': low activity and low growth rate\n\n"
            "Note: activity_level and relevance MUST be exactly one of: 'Low', 'Medium', 'High'\n"
            "The response must match the RepoDetails schema exactly."
        )
        
        try:
            completion = self.client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[
                    {
                        "role": "system", 
                        "content": (
                            "Extract and enrich the repository information. "
                            "Ensure activity_level and relevance are exactly 'Low', 'Medium', or 'High'. "
                            "Do not use any other values or descriptions."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format=RepoDetails,
                max_tokens=500
            )
            
            processed_repo = completion.choices[0].message.parsed
            return processed_repo
            
        except ValidationError as ve:
            print(f"ProcessingAgent Validation Error: {str(ve)}")
            raise ve
        except Exception as e:
            print(f"ProcessingAgent Unexpected Error: {str(e)}")
            raise e
    
    def execute(self, repos: List[dict]) -> List[RepoDetails]:
        """
        Process a list of repositories.
        
        Args:
            repos: List of repository dictionaries from GitHub API
            
        Returns:
            List of processed RepoDetails objects
        """
        processed_repos = []
        for repo in repos:
            try:
                processed_repo = self.process_repo(repo)
                processed_repos.append(processed_repo)
            except Exception as e:
                print(f"ProcessingAgent Error processing repo {repo.get('full_name', 'unknown')}: {str(e)}")
        return processed_repos
