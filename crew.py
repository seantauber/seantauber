#!/usr/bin/env python
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.tools import tool
from crewai_tools import GithubSearchTool, SerplyNewsSearchTool, FileWriterTool, SerperDevTool
from github import Github
from models.github_repo_data import ReadmeStructure, GitHubRepoData
from models.task_outputs import ProcessingSummary, FetchSummary, AnalysisSummary
from db.database import DatabaseManager
from processing.parallel_manager import ParallelProcessor
from config.config_manager import AppConfig
from config.logging_config import setup_logging
import os
from typing import List, Dict, Any
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

@tool("Fetch Starred Repos Tool")
def fetch_starred_repos() -> FetchSummary:
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

@tool("Store Raw Repos Tool")
def store_raw_repos(repos: List[Dict], source: str) -> str:
    """Store raw repository data in the database"""
    logger.info(f"Storing {len(repos)} repositories from source: {source}")
    db_manager = DatabaseManager(cleanup=False)  # Explicitly set cleanup=False
    db_manager.store_raw_repos(repos, source)
    return f"Stored {len(repos)} repositories in database with source: {source}"

@tool("Get Unprocessed Repos Tool")
def get_unprocessed_repos(batch_size: int = 10) -> List[Dict]:
    """Get a batch of unprocessed repositories from the database"""
    logger.info(f"Retrieving {batch_size} unprocessed repositories")
    db_manager = DatabaseManager(cleanup=False)  # Explicitly set cleanup=False
    return db_manager.get_unprocessed_repos(batch_size)

@tool("Store Analyzed Repos Tool")
def store_analyzed_repos(analyzed_repos: List[Dict], batch_id: int) -> str:
    """Store analyzed repository data in the database"""
    logger.info(f"Storing {len(analyzed_repos)} analyzed repositories for batch {batch_id}")
    db_manager = DatabaseManager(cleanup=False)  # Explicitly set cleanup=False
    db_manager.store_analyzed_repos(analyzed_repos, batch_id)
    return f"Stored {len(analyzed_repos)} analyzed repositories in database for batch {batch_id}"

@tool("Get Analyzed Repos Tool")
def get_analyzed_repos() -> List[Dict]:
    """Get all analyzed repositories from the database"""
    logger.info("Retrieving all analyzed repositories")
    db_manager = DatabaseManager(cleanup=False)  # Explicitly set cleanup=False
    return db_manager.get_analyzed_repos()

@tool("Current Date Tool")
def get_current_date(date_format: str = "%m-%d-%Y %H:%M") -> str:
    """
    Tool that returns the current date and time
    date_format should be a valid date format string for the python datetime.strftime() method
    date_format defaults to "%m-%d-%Y %H:%M"
    Remember the output of this tool and don't call it again in the same task
    """
    return f"Current Date: {datetime.now().strftime(date_format)}\nDate Format: {date_format}"

@tool("Save File Tool")
def save_file(file_name: str, file_extension: str, content: str) -> str:
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
        
        self.get_current_date_tool = get_current_date
        self.save_file_tool = save_file
        self.store_raw_repos_tool = store_raw_repos
        self.get_unprocessed_repos_tool = get_unprocessed_repos
        self.store_analyzed_repos_tool = store_analyzed_repos
        self.get_analyzed_repos_tool = get_analyzed_repos
        logger.info("GitHubGenAICrew initialization complete")
            
    @agent
    def github_api_agent(self) -> Agent:
        """Creates the GitHub API agent"""
        crewai_logger.info("Creating GitHub API agent")
        return Agent(
            config=self.agents_config['github_api_agent'],
            verbose=True,
            tools=[self.fetch_starred_repos_tool, self.github_search_tool],
            allow_delegation=True
        )

    @agent
    def content_processor(self) -> Agent:
        """Creates the content processor agent"""
        crewai_logger.info("Creating content processor agent")
        return Agent(
            config=self.agents_config['content_processor'],
            verbose=True,
            allow_delegation=True
        )

    @agent
    def content_generator(self) -> Agent:
        """Creates the content generator agent"""
        crewai_logger.info("Creating content generator agent")
        return Agent(
            config=self.agents_config['content_generator'],
            verbose=True,
            allow_delegation=True
        )

    @agent
    def analyzer(self) -> Agent:
        """Creates the analyzer agent"""
        crewai_logger.info("Creating analyzer agent")
        return Agent(
            config=self.agents_config['analyzer'],
            verbose=True,
            allow_delegation=True,
            tools=[
                self.get_unprocessed_repos_tool,
                self.store_analyzed_repos_tool
            ]
        )

    @task
    def fetch_starred(self) -> Task:
        """Creates the fetch starred repos task"""
        crewai_logger.info("Creating fetch starred repos task")
        return Task(
            config=self.tasks_config['fetch_starred'],
            output_json=FetchSummary
        )
    
    @task
    def search_trending(self) -> Task:
        """Creates the search trending repos task"""
        crewai_logger.info("Creating search trending repos task")
        return Task(
            config=self.tasks_config['search_trending'],
            output_json=FetchSummary,
            tools=[self.store_raw_repos_tool]
        )
    
    @task
    def combine_repos(self) -> Task:
        """Creates the combine repos task"""
        crewai_logger.info("Creating combine repos task")
        return Task(
            config=self.tasks_config['combine_repos'],
            output_json=ProcessingSummary,
            tools=[self.get_unprocessed_repos_tool]
        )
    
    @task
    def analyze_repos(self) -> Task:
        """Creates the analyze repos task with batch processing support"""
        crewai_logger.info("Creating analyze repos task")
        task_config = self.tasks_config['analyze_repos']
        task_config['description'] = """
        Analyze repositories in parallel batches for optimal performance:
        
        1. Initialize the ParallelProcessor with appropriate batch size
        2. For each batch:
           - Fetch unprocessed repos using get_unprocessed_repos_tool
           - Analyze repos in the batch for categorization and quality metrics
           - Store results using store_analyzed_repos_tool with batch tracking
        3. Continue processing until all repos are analyzed
        4. Return AnalysisSummary with processing statistics
        
        Ensure proper error handling and batch status tracking throughout the process.
        Use batch size of 10 repositories to optimize for LLM context limits.
        """
        
        return Task(
            config=task_config,
            output_json=AnalysisSummary,
            tools=[
                self.get_unprocessed_repos_tool,
                self.store_analyzed_repos_tool
            ]
        )

    @task
    def parse_readme(self) -> Task:
        """Creates the read readme task"""
        crewai_logger.info("Creating parse readme task")
        return Task(
            config=self.tasks_config['parse_readme'],
            output_json=ReadmeStructure
        )

    @task
    def generate_content(self) -> Task:
        """Creates the generate updated content task"""
        crewai_logger.info("Creating generate content task")
        return Task(
            config=self.tasks_config['generate_content'],
            tools=[self.get_analyzed_repos_tool]
        )
    
    @task
    def update_readme(self, test_mode: bool = False) -> Task:
        """Creates the update readme task"""
        crewai_logger.info("Creating update readme task")
        if test_mode:
            return Task(
                config=self.tasks_config['update_readme'],
                output_file="README.test.md",
                tools=[self.get_current_date_tool]
            )
        return Task(
            config=self.tasks_config['update_readme']
        )

    @crew
    def readme_update_crew(self, test_mode: bool = False) -> Crew:
        """Creates the README update crew"""
        crewai_logger.info("Creating README update crew")
        crew = Crew(
            agents=[
                self.github_api_agent(),
                self.content_processor(),
                self.content_generator(),
                self.analyzer()
            ],
            tasks=[
                self.fetch_starred(),
                self.search_trending(),
                self.combine_repos(),
                self.analyze_repos(),
                self.parse_readme(),
                self.generate_content(),
                self.update_readme(test_mode=test_mode)
            ],
            process=Process.sequential,
            verbose=True
        )
        
        # Log crew configuration
        crewai_logger.info(f"Crew configured with {len(crew.agents)} agents and {len(crew.tasks)} tasks")
        crewai_logger.debug("Agents: " + ", ".join([type(agent).__name__ for agent in crew.agents]))
        crewai_logger.debug("Tasks: " + ", ".join([type(task).__name__ for task in crew.tasks]))
        
        return crew
