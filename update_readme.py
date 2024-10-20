import os
from dotenv import load_dotenv
from agents.triaging_agent import TriagingAgent
from agents.fetching_agent import FetchingAgent
from agents.processing_agent import ProcessingAgent
from agents.curation_agent import CurationAgent
from agents.editor_agent import EditorAgent
from agents.readme_updater_agent import ReadmeUpdaterAgent
from agents.archive_agent import ArchiveAgent
from openai import OpenAI

def main():
    # Load environment variables from .env
    if not os.getenv("GITHUB_ACTIONS"):
        load_dotenv()
    
    # Initialize OpenAI client
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Initialize Archive Agent first as it's needed by ReadmeUpdaterAgent
    archive_agent = ArchiveAgent()
    
    # Initialize other agents
    triaging_agent = TriagingAgent(client=openai_client)
    fetching_agent = FetchingAgent(client=openai_client, github_token=os.getenv("GITHUB_TOKEN"))
    processing_agent = ProcessingAgent(client=openai_client)
    curation_agent = CurationAgent(client=openai_client)
    editor_agent = EditorAgent(client=openai_client)
    readme_updater_agent = ReadmeUpdaterAgent(archive_agent=archive_agent)
    
    # Define the GitHub username
    github_username = os.getenv("GITHUB_USERNAME")  # Replace with your GitHub username
    
    # User query trigger (could be from schedule or manual trigger)
    user_query = "Update my README with the latest starred repositories and provide an editor's note summarizing the changes."
    
    # Step 1: Triaging Agent assesses and delegates tasks
    triage_response = triaging_agent.execute(user_query)
    if not triage_response:
        print("Triaging failed. Exiting.")
        return
    
    agents = triage_response.agents
    query = triage_response.query
    
    # Step 2: Execute Fetching Agent if included
    if "FetchingAgent" in agents:
        try:
            fetched_repos = fetching_agent.execute(github_username)
            print(f"Fetched {len(fetched_repos)} starred repositories.")
        except Exception as e:
            print(f"Error in FetchingAgent: {e}")
            return
    else:
        fetched_repos = []
    
    # Step 3: Execute Processing Agent if included
    if "ProcessingAgent" in agents:
        try:
            processed_repos = processing_agent.execute(fetched_repos)
            print(f"Processed {len(processed_repos)} repositories.")
        except Exception as e:
            print(f"Error in ProcessingAgent: {e}")
            return
    else:
        processed_repos = []
    
    # Step 4: Execute Curation Agent if included
    if "CurationAgent" in agents:
        try:
            curated_repos = curation_agent.execute(processed_repos)
            print(f"Curated {len(curated_repos)} repositories.")
        except Exception as e:
            print(f"Error in CurationAgent: {e}")
            return
    else:
        curated_repos = []
    
    # Step 5: Execute Editor Agent if included
    if "EditorAgent" in agents:
        try:
            with open('README.md', 'r') as file:
                existing_readme = file.read()
            editor_output = editor_agent.execute(curated_repos, existing_readme)
            aligned_repos = editor_output.get("aligned_repos", {})
            editors_note = editor_output.get("editors_note", None)
            if not editors_note:
                print("EditorAgent failed to generate an editor's note.")
                return
        except Exception as e:
            print(f"Error in EditorAgent: {e}")
            return
    else:
        aligned_repos = {}
        editors_note = None
    
    # Step 6: Execute ReadmeUpdater Agent if included
    if "ReadmeUpdaterAgent" in agents and aligned_repos and editors_note:
        try:
            readme_updater_agent.execute(aligned_repos, editors_note, readme_path='README.md')
        except Exception as e:
            print(f"Error in ReadmeUpdaterAgent: {e}")
            return
    else:
        print("ReadmeUpdaterAgent not included or missing required data.")
    
    print("README update process completed successfully.")

if __name__ == "__main__":
    main()
