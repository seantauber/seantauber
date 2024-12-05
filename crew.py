#!/usr/bin/env python
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.tools import tool
from crewai_tools import GithubSearchTool, SerplyNewsSearchTool, FileWriterTool, SerperDevTool
from github import Github
from models.github_repo_data import ReadmeStructure
from models.task_outputs import ProcessingSummary, FetchSummary, AnalysisSummary
from db.database import DatabaseManager
from processing.parallel_manager import ParallelProcessor
import os
from typing import List, Dict, Any
import requests
from datetime import datetime
import yaml


@tool("Fetch Starred Repos Tool")
def fetch_starred_repos(github_username: str) -> FetchSummary:
    """Fetches starred repositories for a given GitHub username and stores them in the database"""
    github_client = Github(os.environ['GITHUB_TOKEN'])
    starred_repos = list(github_client.get_user(os.environ['GITHUB_USERNAME']).get_starred())
    
    def process_repo_batch(batch: List[Any], batch_id: int) -> Dict:
        """Process a batch of repositories"""
        repo_data_list = [
            {
                'full_name': repo.full_name,
                'description': repo.description,
                'html_url': repo.html_url,
                'stargazers_count': repo.stargazers_count,
                'topics': repo.get_topics(),
                'created_at': repo.created_at,
                'updated_at': repo.updated_at,
                'language': repo.language,
                'batch_id': batch_id
            }
            for repo in batch
        ]
        
        # Store batch in database
        db_manager = DatabaseManager()
        db_manager.store_raw_repos(repo_data_list, source='starred', batch_id=batch_id)
        
        return {
            'success': True,
            'processed_count': len(repo_data_list),
            'error': None
        }

    # Initialize parallel processor
    processor = ParallelProcessor(max_workers=4)
    
    # Process repositories in parallel batches
    result = processor.process_batch(
        task_type='fetch_starred',
        items=starred_repos,
        process_fn=process_repo_batch,
        batch_size=10
    )
    
    # Create FetchSummary from results
    return FetchSummary(
        success=result['failed_batches'] == 0,
        message="Completed fetching starred repositories",
        processed_count=result['total_processed'],
        batch_count=result['successful_batches'] + result['failed_batches'],
        completed_batches=result['successful_batches'],
        failed_batches=result['failed_batches'],
        error_count=len(result['errors']),
        errors=result['errors'],
        source='starred',
        total_repos=len(starred_repos),
        stored_repos=result['total_processed']
    )

@tool("Store Raw Repos Tool")
def store_raw_repos(repos: List[Dict], source: str) -> str:
    """Store raw repository data in the database"""
    db_manager = DatabaseManager()
    db_manager.store_raw_repos(repos, source)
    return f"Stored {len(repos)} repositories in database with source: {source}"

@tool("Get Unprocessed Repos Tool")
def get_unprocessed_repos(batch_size: int = 10) -> List[Dict]:
    """Get a batch of unprocessed repositories from the database"""
    db_manager = DatabaseManager()
    return db_manager.get_unprocessed_repos(batch_size)

@tool("Store Analyzed Repos Tool")
def store_analyzed_repos(analyzed_repos: List[Dict], batch_id: int) -> str:
    """Store analyzed repository data in the database"""
    db_manager = DatabaseManager()
    db_manager.store_analyzed_repos(analyzed_repos, batch_id)
    return f"Stored {len(analyzed_repos)} analyzed repositories in database for batch {batch_id}"

@tool("Get Analyzed Repos Tool")
def get_analyzed_repos() -> List[Dict]:
    """Get all analyzed repositories from the database"""
    db_manager = DatabaseManager()
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

    def __init__(self):
        self.fetch_starred_repos_tool = fetch_starred_repos
        self.github_search_tool = GithubSearchTool(
            gh_token=os.environ['GITHUB_TOKEN'],
            content_types=['code', 'repo']
        )
        self.get_current_date_tool = get_current_date
        self.save_file_tool = save_file
        self.store_raw_repos_tool = store_raw_repos
        self.get_unprocessed_repos_tool = get_unprocessed_repos
        self.store_analyzed_repos_tool = store_analyzed_repos
        self.get_analyzed_repos_tool = get_analyzed_repos
            
    @agent
    def github_api_agent(self) -> Agent:
        """Creates the GitHub API agent"""
        return Agent(
            config=self.agents_config['github_api_agent'],
            verbose=True,
            tools=[self.fetch_starred_repos_tool, self.github_search_tool]
        )

    @agent
    def content_processor(self) -> Agent:
        """Creates the content processor agent"""
        return Agent(
            config=self.agents_config['content_processor'],
            verbose=True
        )

    @agent
    def content_generator(self) -> Agent:
        """Creates the content generator agent"""
        return Agent(
            config=self.agents_config['content_generator'],
            verbose=True
        )

    @agent
    def analyzer(self) -> Agent:
        """Creates the analyzer agent"""
        return Agent(
            config=self.agents_config['analyzer'],
            verbose=True,
            tools=[
                self.get_unprocessed_repos_tool,
                self.store_analyzed_repos_tool
            ]
        )

    @task
    def fetch_starred(self) -> Task:
        """Creates the fetch starred repos task"""
        return Task(
            config=self.tasks_config['fetch_starred'],
            output_json=FetchSummary
        )
    
    @task
    def search_trending(self) -> Task:
        """Creates the search trending repos task"""
        return Task(
            config=self.tasks_config['search_trending'],
            output_json=FetchSummary,
            tools=[self.store_raw_repos_tool]
        )
    
    @task
    def combine_repos(self) -> Task:
        """Creates the combine repos task"""
        return Task(
            config=self.tasks_config['combine_repos'],
            output_json=ProcessingSummary,
            tools=[self.get_unprocessed_repos_tool]
        )
    
    @task
    def analyze_repos(self) -> Task:
        """Creates the analyze repos task with batch processing support"""
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
        return Task(
            config=self.tasks_config['parse_readme'],
            output_json=ReadmeStructure
        )

    @task
    def generate_content(self) -> Task:
        """Creates the generate updated content task"""
        return Task(
            config=self.tasks_config['generate_content'],
            tools=[self.get_analyzed_repos_tool]
        )
    
    @task
    def update_readme(self, test_mode: bool = False) -> Task:
        """Creates the update readme task"""
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
        return Crew(
            agents=[
                self.github_api_agent(),
                self.content_processor(),
                self.content_generator(),
                self.analyzer()  # Added analyzer agent for parallel processing
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
