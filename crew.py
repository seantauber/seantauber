#!/usr/bin/env python
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.tools import tool
from crewai_tools import GithubSearchTool, SerplyNewsSearchTool, FileWriterTool, SerperDevTool
from github import Github
from models.github_repo_data import (
    GitHubRepoData,
    StarredReposOutput,
    TrendingReposOutput,
    CombinedReposOutput,
    AnalyzedReposOutput,
    ReadmeStructure
)
import os
from typing import List, Dict, Any
import requests
from datetime import datetime
import yaml


@tool("Fetch Starred Repos Tool")
def fetch_starred_repos(github_username: str) -> List[GitHubRepoData]:
    """Fetches starred repositories for a given GitHub username"""
    github_client = Github(os.environ['GITHUB_TOKEN'])
    starred_repos = github_client.get_user(os.environ['GITHUB_USERNAME']).get_starred()
    return [
        GitHubRepoData(
            full_name=repo.full_name,
            description=repo.description,
            html_url=repo.html_url,
            stargazers_count=repo.stargazers_count,
            topics=repo.get_topics(),
            created_at=repo.created_at,
            updated_at=repo.updated_at,
            language=repo.language
        ) 
        for repo in starred_repos
    ]

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
            verbose=True
        )

    @task
    def fetch_starred(self) -> Task:
        """Creates the fetch starred repos task"""
        return Task(
            config=self.tasks_config['fetch_starred'],
            output_json=StarredReposOutput
        )
    
    @task
    def search_trending(self) -> Task:
        """Creates the search trending repos task"""
        return Task(
            config=self.tasks_config['search_trending'],
            output_json=TrendingReposOutput
        )
    
    @task
    def combine_repos(self) -> Task:
        """Creates the combine repos task"""
        return Task(
            config=self.tasks_config['combine_repos'],
            output_json=CombinedReposOutput
        )
    
    @task
    def analyze_repos(self) -> Task:
        """Creates the analyze repos task"""
        return Task(
            config=self.tasks_config['analyze_repos'],
            output_json=AnalyzedReposOutput
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
            config=self.tasks_config['generate_content']
        )
    
    @task
    def update_readme(self, test_mode: bool = False) -> Task:
        """Creates the update readme task"""
        if test_mode:
            return Task(
                config=self.tasks_config['update_readme'],
                output_file="README.test.md"
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
                self.content_generator()
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
