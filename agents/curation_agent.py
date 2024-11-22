from .base_agent import BaseAgent
from models.curation_models import CurationDetails
from models.repo_models import RepoDetails
from openai import OpenAI
from pydantic import ValidationError

class CurationAgent(BaseAgent):
    """
    Curation Agent: Assigns tags and scores to repositories.
    """
    def __init__(self, client: OpenAI):
        super().__init__(name="CurationAgent")
        self.client = client
    
    def curate_repo(self, repo: RepoDetails) -> CurationDetails:
        prompt = (
            f"Based on the following repository details, assign relevant tags and calculate popularity and trending scores:\n\n"
            f"Repository Details:\n{repo.model_dump()}\n\n"
            "Tasks:\n"
            "1. Assign relevant tags based on the repository's primary purpose, description, topics, and language. Focus on the following key categories and their subcategories:\n"
            "   - **Generative AI**: Text generation, image generation, music generation, code generation, etc. Includes models like GPT, LLMs, and GANs.\n"
            "   - **Artificial Intelligence**: General-purpose AI frameworks, machine learning models, reinforcement learning, NLP, computer vision.\n"
            "       - **Machine Learning Frameworks**: Libraries designed to train, deploy, or serve ML models.\n"
            "       - **Chatbots & Assistance**: Conversational agents, automated assistants, customer support bots, etc.\n"
            "   - **Data Science**: Data analysis, visualization, statistical modeling, etc. Includes libraries like pandas, NumPy, and visualization tools.\n"
            "   - **MLOps & AI Infrastructure**: Tools for managing and deploying AI models in production, monitoring, and infrastructure.\n"
            "   - **Agentic Frameworks**: Libraries focused on multi-agent systems or agent-based development, autonomous systems, coordination frameworks.\n"
            "2. Create subcategories within the above categories if a repository fits within a niche not directly covered by the main categories.\n"
            "3. Assign a 'catch-all' tag as 'Other' only if you are unable to confidently match the repository to an existing category.\n"
            "4. Calculate a popularity score as a weighted combination of stars per year and activity level.\n"
            "5. Calculate a trending score based on the rate of recent star growth and social activity.\n"
        )

        try:
            completion = self.client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": "You are a Curation Agent. Your role is to assign relevant tags and calculate popularity and trending scores for repositories."},
                    {"role": "user", "content": prompt}
                ],
                response_format=CurationDetails,
                max_tokens=150
            )
            
            return completion.choices[0].message.parsed
            
        except ValidationError as ve:
            print(f"CurationAgent Validation Error: {str(ve)}")
            raise ve
        except Exception as e:
            print(f"CurationAgent Unexpected Error: {str(e)}")
            raise e
    
    def curate_repositories(self, repos: list) -> list:
        """
        Curate a list of repositories by assigning tags and calculating scores.
        
        Args:
            repos: List of repository objects to curate
            
        Returns:
            List of curated repository objects with tags and scores added
        """
        curated_repos = []
        for repo in repos:
            try:
                # Convert dict to RepoDetails if needed
                if isinstance(repo, dict):
                    repo = RepoDetails(**repo)
                
                curation = self.curate_repo(repo)
                repo_dict = repo.model_dump()
                repo_dict.update(curation.model_dump())
                curated_repos.append(repo_dict)
            except Exception as e:
                print(f"CurationAgent Error curating repo {repo.name if hasattr(repo, 'name') else str(repo)}: {str(e)}")
        return curated_repos
    
    def execute(self, repos: list) -> list:
        """Legacy method that calls curate_repositories"""
        return self.curate_repositories(repos)
