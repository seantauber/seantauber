#!/usr/bin/env python
from crew import GitHubGenAICrew
from github import Github
from dotenv import load_dotenv
from db.database import DatabaseManager
from config.config_manager import AppConfig
import os
import argparse
import sys

def load_configuration():
    """Load and validate configuration using Pydantic"""
    load_dotenv()
    try:
        config = AppConfig.from_env()
        return config
    except ValueError as e:
        print(f"Configuration Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error loading configuration: {e}")
        sys.exit(1)

def main():
    """Main entry point for the GitHub GenAI List project"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='GitHub GenAI List project')
    parser.add_argument('--test', action='store_true', help='Run in test mode, output to README.test.md')
    parser.add_argument('--no-cleanup', action='store_true', help='Skip database cleanup before running')
    args = parser.parse_args()
    
    # Load and validate configuration
    config = load_configuration()

    # Initialize database with cleanup flag based on --no-cleanup argument
    print("Initializing database...")
    db_manager = DatabaseManager(cleanup=not args.no_cleanup)
    if not args.no_cleanup:
        print("Database cleanup complete.")

    # Read current README
    with open('README.md', 'r') as file:
        current_readme = file.read()
    
    crew = GitHubGenAICrew(config=config)
    
    # Update README with starred repos
    print("Updating README with starred repositories...")
    readme_crew = crew.readme_update_crew(test_mode=args.test)
    readme_crew.kickoff(inputs={"current_readme_content": current_readme})

if __name__ == "__main__":
    main()
