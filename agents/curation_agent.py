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
            "1. Assign relevant tags based on the repository's primary purpose, description, topics, and language. Focus on the following key categories and their subcategories:\n"
            "   - **Generative AI**: Text generation, image generation, music generation, code generation, etc. Includes models like GPT, LLMs, and GANs.\n"
            "   - **Artificial Intelligence**: General-purpose AI frameworks, machine learning models, reinforcement learning, NLP, computer vision.\n"
            "       - **Machine Learning Frameworks**: Libraries designed to train, deploy, or serve ML models.\n"
            "       - **Chatbots & Assistance**: Conversational agents, automated assistants, customer support bots, etc.\n"
            "   - **Data Science**: Data analysis, visualization, statistical modeling, etc. Includes libraries like pandas, NumPy, and visualization tools.\n"
            "   - **MLOps & AI Infrastructure**: Tools for managing and deploying AI models in production, monitoring, and infrastructure.\n"
            "   - **Agentic Frameworks**: Libraries focused on multi-agent systems or agent-based development, autonomous systems, coordination frameworks.\n"
            "2. Create subcategories within the above categories if a repository fits within a niche not directly covered by the main categories. Examples of subcategories include 'Text-to-Music Generation' or 'Multi-Tenant Databases'.\n"
            "3. Assign a 'catch-all' tag as 'Other' only if you are unable to confidently match the repository to an existing category.\n"
            "4. Calculate a popularity score as a weighted combination of stars per year and activity level (recent commits, releases, issues).\n"
            "5. Calculate a trending score based on the rate of recent star growth and social activity.\n\n"
            "Provide the output in JSON format adhering to the following schema:\n\n"
            "{\n"
            '    "tags": ["string"],\n'
            '    "popularity_score": number,\n'
            '    "trending_score": number\n'
            "}"
        )

        
        try:
            completion = self.client.beta.chat.completions.parse(
                model="o1-mini",
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
