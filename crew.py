#!/usr/bin/env python
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.tools import tool
from crewai_tools import GithubSearchTool
from github import Github
from models.github_repo_data import GitHubRepoData
import os
from typing import List, Dict, Any
import requests
from datetime import datetime


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

@CrewBase
class GitHubGenAICrew:
    """Crew for managing the GitHub GenAI List project"""

    def __init__(self):
        self.fetch_starred_repos_tool = fetch_starred_repos
        self.github_search_tool = GithubSearchTool(
            gh_token=os.environ['GITHUB_TOKEN'],
            content_types=['code', 'repo']
        )
        
    @agent
    def github_api_agent(self) -> Agent:
        """Creates the GitHub API agent"""
        return Agent(
            config=self.agents_config['github_api_agent'],
            verbose=True,
            tools=[self.fetch_starred_repos_tool]
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
    def researcher(self) -> Agent:
        """Creates the researcher agent"""
        return Agent(
            config=self.agents_config['researcher'],
            verbose=True,
            tools=[self.github_search_tool]
        )

    @agent
    def analyzer(self) -> Agent:
        """Creates the analyzer agent"""
        return Agent(
            config=self.agents_config['analyzer'],
            verbose=True,
            tools=[self.github_search_tool]
        )

    @agent
    def curator(self) -> Agent:
        """Creates the curator agent"""
        return Agent(
            config=self.agents_config['curator'],
            verbose=True
        )

    @task
    def fetch_starred_repos_task(self) -> Task:
        """Creates the fetch starred repos task"""
        return Task(
            config=self.tasks_config['fetch_starred_repos']
        )

    @task
    def read_readme_task(self) -> Task:
        """Creates the read readme task"""
        return Task(
            config=self.tasks_config['read_readme']
        )

    @task
    def generate_updated_content_task(self) -> Task:
        """Creates the generate updated content task"""
        return Task(
            config=self.tasks_config['generate_updated_content']
        )

    @task
    def write_readme_task(self, test_mode: bool = False) -> Task:
        """Creates the write readme task"""
        config = dict(self.tasks_config['write_readme'])
        if test_mode:
            config['output_file'] = 'README.test.md'
        return Task(config=config)

    @task
    def research_task(self) -> Task:
        """Creates the research task"""
        return Task(
            config=self.tasks_config['research_task']
        )

    @task
    def analyze_task(self) -> Task:
        """Creates the analyze task"""
        return Task(
            config=self.tasks_config['analyze_task']
        )

    @task
    def curate_task(self, test_mode: bool = False) -> Task:
        """Creates the curate task"""
        config = dict(self.tasks_config['curate_task'])
        if test_mode:
            config['output_file'] = 'README.test.md'
        return Task(config=config)

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
                self.fetch_starred_repos_task(),
                self.read_readme_task(),
                self.generate_updated_content_task(),
                self.write_readme_task(test_mode=test_mode)
            ],
            process=Process.sequential,
            verbose=True
        )

    @crew
    def research_crew(self, test_mode: bool = False) -> Crew:
        """Creates the research crew"""
        return Crew(
            agents=[
                self.researcher(),
                self.analyzer(),
                self.curator()
            ],
            tasks=[
                self.research_task(),
                self.analyze_task(),
                self.curate_task(test_mode=test_mode)
            ],
            process=Process.sequential,
            verbose=True
        )
