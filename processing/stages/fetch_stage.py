"""Pipeline stage for fetching GitHub repositories"""
from typing import Any, Dict, List, Optional
from github import Github
import math
import logging

from models.flow_state import FlowState
from models.github_repo_data import GitHubRepoData
from processing.pipeline_stage import PipelineStage, PipelineResult
from config.config_manager import AppConfig
from config.logging_config import setup_logging

# Set up logging
logger = setup_logging("pipeline.fetch")

class FetchStage(PipelineStage):
    """Pipeline stage for fetching GitHub repositories"""
    
    def __init__(self, name: str, config: AppConfig):
        """Initialize fetch stage
        
        Args:
            name: Stage name
            config: Application configuration
        """
        super().__init__(name)
        self.config = config
        self.github_client = Github(config.github.github_token)
    
    def process(self, data: Any, state: FlowState) -> PipelineResult:
        """Fetch repositories from GitHub
        
        Args:
            data: Not used for this stage
            state: Current flow state
            
        Returns:
            PipelineResult with fetched repositories
        """
        try:
            # Fetch starred repos
            username = self.config.github.github_username
            self.logger.info(f"Fetching starred repositories for user: {username}")
            
            starred_repos = list(self.github_client.get_user(username).get_starred())
            self.logger.info(f"Successfully fetched {len(starred_repos)} repositories")
            
            # Convert to GitHubRepoData objects
            repo_data_list = []
            for repo in starred_repos:
                try:
                    repo_data = GitHubRepoData(
                        full_name=repo.full_name,
                        description=repo.description,
                        html_url=repo.html_url,
                        stargazers_count=repo.stargazers_count,
                        topics=repo.get_topics(),
                        created_at=repo.created_at,
                        updated_at=repo.updated_at,
                        language=repo.language
                    )
                    repo_data_list.append(repo_data)
                    
                except Exception as e:
                    self.logger.error(f"Error converting repo {repo.full_name}: {str(e)}")
                    continue
            
            # Update flow state
            state.add_raw_repos(repo_data_list)
            
            self.logger.info(f"Successfully processed {len(repo_data_list)} repositories")
            
            # Return success result
            return self._create_success_result(
                processed_count=len(repo_data_list),
                data=repo_data_list
            )
            
        except Exception as e:
            error_msg = f"Error fetching repositories: {str(e)}"
            self.logger.exception(error_msg)
            return self._create_error_result(error_msg)
    
    def _validate_config(self) -> Optional[str]:
        """Validate required configuration
        
        Returns:
            Error message if validation fails, None if successful
        """
        if not self.config.github.github_token:
            return "GitHub token not configured"
        
        if not self.config.github.github_username:
            return "GitHub username not configured"
        
        return None
    
    def execute(self, data: Any, state: FlowState) -> PipelineResult:
        """Execute fetch stage with validation
        
        Args:
            data: Not used for this stage
            state: Current flow state
            
        Returns:
            PipelineResult with execution results
        """
        # Validate config
        error = self._validate_config()
        if error:
            return self._create_error_result(f"Configuration error: {error}")
        
        # Execute stage
        return super().execute(data, state)
