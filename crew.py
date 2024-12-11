#!/usr/bin/env python
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.tools import tool
from crewai_tools import GithubSearchTool
from github import Github
from models.github_repo_data import ReadmeStructure, GitHubRepoData
from models.task_outputs import ProcessingSummary, FetchSummary, AnalysisSummary
from db.database import DatabaseManager
from processing.parallel_manager import ParallelProcessor
from config.config_manager import AppConfig
from config.logging_config import setup_logging
import os
from typing import List, Dict, Any, Optional
import requests
from datetime import datetime
import yaml
from embedchain import App
from embedchain.config import AppConfig as EmbedChainConfig
import math
import logging

# Set up logging
logger = setup_logging("crew")
crewai_logger = logging.getLogger('crewai')

# Global config for tools
app_config = None

def fetch_starred_repos_fn() -> FetchSummary:
    """Fetches starred repositories for the configured GitHub user and stores them in the database"""
    logger.info("Starting fetch_starred_repos execution")
    
    if app_config is None:
        logger.error("Tool not properly initialized. Config is missing.")
        raise RuntimeError("Tool not properly initialized. Config is missing.")
    
    try:
        logger.info(f"Initializing GitHub client for user: {app_config.github.github_username}")
        github_client = Github(app_config.github.github_token)
        username = app_config.github.github_username
        
        logger.info("Fetching starred repositories from GitHub API")
        starred_repos = list(github_client.get_user(username).get_starred())
        logger.info(f"Successfully fetched {len(starred_repos)} starred repositories")
        
        # Calculate total batches needed
        batch_size = app_config.batch_size
        total_batches = math.ceil(len(starred_repos) / batch_size)
        logger.info(f"Calculated {total_batches} total batches with batch size {batch_size}")
        
        def process_repo_batch(batch: List[Any], batch_id: int) -> Dict:
            """Process a batch of repositories"""
            logger.info(f"Processing batch {batch_id} with {len(batch)} repositories")
            
            try:
                repo_data_list = []
                for repo in batch:
                    logger.debug(f"Converting repository {repo.full_name} to GitHubRepoData")
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
                
                # Store batch in database
                logger.info(f"Storing batch {batch_id} in database")
                db_manager = DatabaseManager(cleanup=False)  # Explicitly set cleanup=False
                db_manager.store_raw_repos(repo_data_list, source='starred', batch_id=batch_id)
                logger.info(f"Successfully stored batch {batch_id}")
                
                return {
                    'success': True,
                    'processed_count': len(repo_data_list),
                    'error': None
                }
            except Exception as e:
                logger.error(f"Error processing batch {batch_id}: {str(e)}")
                return {
                    'success': False,
                    'processed_count': 0,
                    'error': str(e)
                }

        # Initialize parallel processor with config
        logger.info(f"Initializing ParallelProcessor with {app_config.max_workers} workers")
        processor = ParallelProcessor(max_workers=app_config.max_workers)
        
        # Process repositories in parallel batches
        logger.info("Starting parallel batch processing")
        result = processor.process_batch(
            task_type='fetch_starred',
            items=starred_repos,
            process_fn=process_repo_batch,
            batch_size=batch_size
        )
        logger.info("Completed parallel batch processing")
        
        # Log processing results
        logger.info(f"Processing summary:")
        logger.info(f"- Total processed: {result['total_processed']}")
        logger.info(f"- Successful batches: {result['successful_batches']}")
        logger.info(f"- Failed batches: {result['failed_batches']}")
        logger.info(f"- Total errors: {len(result['errors'])}")
        
        # Create FetchSummary from results
        return FetchSummary(
            success=result['failed_batches'] == 0,
            message=f"Completed fetching starred repositories for user: {username}",
            processed_count=result['total_processed'],
            batch_count=total_batches,
            completed_batches=result['successful_batches'],
            failed_batches=result['failed_batches'],
            error_count=len(result['errors']),
            errors=result['errors'],
            source='starred',
            total_repos=len(starred_repos),
            stored_repos=result['total_processed']
        )
    except Exception as e:
        logger.error(f"Fatal error in fetch_starred_repos: {str(e)}")
        raise

def store_raw_repos_fn(repos: List[Dict], source: str) -> str:
    """Store raw repository data in the database"""
    logger.info(f"Storing {len(repos)} repositories from source: {source}")
    db_manager = DatabaseManager(cleanup=False)  # Explicitly set cleanup=False
    db_manager.store_raw_repos(repos, source)
    return f"Stored {len(repos)} repositories in database with source: {source}"

def get_unprocessed_repos_fn(batch_size: int = 10) -> List[Dict]:
    """Get a batch of unprocessed repositories from the database"""
    logger.info(f"Retrieving {batch_size} unprocessed repositories")
    db_manager = DatabaseManager(cleanup=False)  # Explicitly set cleanup=False
    return db_manager.get_unprocessed_repos(batch_size)

def store_analyzed_repos_fn(analyzed_repos: List[Dict], batch_id: int) -> str:
    """Store analyzed repository data in the database"""
    logger.info(f"Storing {len(analyzed_repos)} analyzed repositories for batch {batch_id}")
    db_manager = DatabaseManager(cleanup=False)  # Explicitly set cleanup=False
    db_manager.store_analyzed_repos(analyzed_repos, batch_id)
    return f"Stored {len(analyzed_repos)} analyzed repositories in database for batch {batch_id}"

def get_analyzed_repos_fn() -> List[Dict]:
    """Get all analyzed repositories from the database"""
    logger.info("Retrieving all analyzed repositories")
    db_manager = DatabaseManager(cleanup=False)  # Explicitly set cleanup=False
    return db_manager.get_analyzed_repos()

def get_current_date_fn(date_format: str = "%m-%d-%Y %H:%M") -> str:
    """
    Tool that returns the current date and time
    date_format should be a valid date format string for the python datetime.strftime() method
    date_format defaults to "%m-%d-%Y %H:%M"
    Remember the output of this tool and don't call it again in the same task
    """
    return f"Current Date: {datetime.now().strftime(date_format)}\nDate Format: {date_format}"

def save_file_fn(file_name: str, file_extension: str, content: str) -> str:
    """
    Tool that saves the content to a file with the given file name
    file_name should be succint and descriptive of the file contents
    file_name should have the format: "{file_name} - {current_date}"
    file_name should not include the file extension
    file_extension should be the correct file extension for the file type (e.g. '.md' for markdown)
    """
    file_path = str(f".crew_storage/{file_name}")
    with open(file_path, 'w') as file:
        file.write(content)
    return f"File saved to {file_path}"

# Create tool decorators for the functions
fetch_starred_repos = tool("Fetch Starred Repos Tool")(fetch_starred_repos_fn)
store_raw_repos = tool("Store Raw Repos Tool")(store_raw_repos_fn)
get_unprocessed_repos = tool("Get Unprocessed Repos Tool")(get_unprocessed_repos_fn)
store_analyzed_repos = tool("Store Analyzed Repos Tool")(store_analyzed_repos_fn)
get_analyzed_repos = tool("Get Analyzed Repos Tool")(get_analyzed_repos_fn)
get_current_date = tool("Current Date Tool")(get_current_date_fn)
save_file = tool("Save File Tool")(save_file_fn)

@CrewBase
class GitHubGenAICrew:
    """Crew for managing the GitHub GenAI List project"""
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self, config: AppConfig):
        """Initialize the crew with configuration"""
        global app_config
        app_config = config
        logger.info("Initializing GitHubGenAICrew")
        
        # Log initialization
        crewai_logger.info("Initializing CrewAI components")
        
        # Initialize tools
        self.fetch_starred_repos_tool = fetch_starred_repos
        
        # Initialize embedchain app with minimal config
        app = App()
        
        # Initialize GithubSearchTool with config
        logger.info("Initializing GithubSearchTool")
        self.github_search_tool = GithubSearchTool(
            gh_token=config.github.github_token,
            content_types=['code', 'repo']
        )
        
        # Store both the tool decorators and the actual functions
        self.get_current_date_tool = get_current_date
        self.save_file_tool = save_file
        self.store_raw_repos_tool = store_raw_repos
        self.get_unprocessed_repos_tool = get_unprocessed_repos
        self.store_analyzed_repos_tool = store_analyzed_repos
        self.get_analyzed_repos_tool = get_analyzed_repos
        
        # Store the actual functions for direct use
        self.get_current_date_fn = get_current_date_fn
        self.save_file_fn = save_file_fn
        self.store_raw_repos_fn = store_raw_repos_fn
        self.get_unprocessed_repos_fn = get_unprocessed_repos_fn
        self.store_analyzed_repos_fn = store_analyzed_repos_fn
        self.get_analyzed_repos_fn = get_analyzed_repos_fn
        
        logger.info("GitHubGenAICrew initialization complete")
            
    @agent
    def analyzer(self) -> Agent:
        """Creates the analyzer agent"""
        crewai_logger.info("Creating analyzer agent")
        return Agent(
            config=self.agents_config['analyzer'],
            verbose=True
        )

    @agent
    def readme_generator(self) -> Agent:
        """Creates the README generator agent"""
        crewai_logger.info("Creating README generator agent")
        return Agent(
            config=self.agents_config['readme_generator'],
            verbose=True,
            tools=[
                self.get_current_date_tool,
                self.save_file_tool
            ]
        )

    @task
    def analyze_repo_batch(self) -> Task:
        """Creates the analyze repo batch task"""
        crewai_logger.info("Creating analyze repo batch task")
        task_config = self.tasks_config['analyze_repo_batch'].copy()
        
        # Get unprocessed repos and convert to list format expected by CrewAI
        repos = self.get_unprocessed_repos_fn()
        task_config['context'] = [{"repo": repo} for repo in repos]
        
        return Task(
            description=task_config['description'],
            expected_output=task_config['expected_output'],
            agent=self.analyzer(),
            output_json=AnalysisSummary,
            context=task_config['context']
        )

    @task
    def generate_readme_content(self, analyze_task: Optional[Task] = None) -> Task:
        """Creates the generate readme content task"""
        crewai_logger.info("Creating generate readme content task")
        task_config = self.tasks_config['generate_readme_content'].copy()
        
        # Get analyzed repos and convert to list format expected by CrewAI
        analyzed_repos = self.get_analyzed_repos_fn()
        task_config['context'] = [{"analyzed_repo": repo} for repo in analyzed_repos]
        
        return Task(
            description=task_config['description'],
            expected_output=task_config['expected_output'],
            agent=self.readme_generator(),
            context=task_config['context'],
            dependencies=[analyze_task] if analyze_task else None
        )

    @task
    def validate_readme(self, generate_task: Optional[Task] = None) -> Task:
        """Creates the validate readme task"""
        crewai_logger.info("Creating validate readme task")
        task_config = self.tasks_config['validate_readme'].copy()
        
        return Task(
            description=task_config['description'],
            expected_output=task_config['expected_output'],
            agent=self.readme_generator(),
            dependencies=[generate_task] if generate_task else None
        )

    @crew
    def readme_update_crew(self, test_mode: bool = False) -> Crew:
        """Creates the README update crew"""
        crewai_logger.info("Creating README update crew")
        
        # Create tasks with dependencies
        analyze_task = self.analyze_repo_batch()
        generate_task = self.generate_readme_content(analyze_task)
        validate_task = self.validate_readme(generate_task)
        
        crew = Crew(
            agents=[
                self.analyzer(),
                self.readme_generator()
            ],
            tasks=[
                analyze_task,
                generate_task,
                validate_task
            ],
            process=Process.sequential,
            verbose=True
        )
        
        # Log crew configuration
        crewai_logger.info(f"Crew configured with {len(crew.agents)} agents and {len(crew.tasks)} tasks")
        crewai_logger.debug("Agents: " + ", ".join([type(agent).__name__ for agent in crew.agents]))
        crewai_logger.debug("Tasks: " + ", ".join([type(task).__name__ for task in crew.tasks]))
        
        return crew
