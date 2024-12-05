#!/usr/bin/env python
from crew import GitHubGenAICrew
from github import Github
from dotenv import load_dotenv
import os
import argparse

def load_environment():
    """Load environment variables from .env file"""
    load_dotenv()
    required_vars = ['GITHUB_TOKEN', 'OPENAI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

def main():
    """Main entry point for the GitHub GenAI List project"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='GitHub GenAI List project')
    parser.add_argument('--test', action='store_true', help='Run in test mode, output to README.test.md')
    args = parser.parse_args()
    
    # Load environment variables
    load_environment()

    # Read current README
    with open('README.md', 'r') as file:
        current_readme = file.read()
    
    crew = GitHubGenAICrew()
    
    # Update README with starred repos
    print("Updating README with starred repositories...")
    readme_crew = crew.readme_update_crew(test_mode=args.test)
    readme_crew.kickoff(inputs={"current_readme_content": current_readme})

if __name__ == "__main__":
    main()