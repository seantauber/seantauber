"""Integration tests for the complete GitHub Starred Repositories system"""
import os
import pytest
import shutil
import re
from datetime import datetime
from openai import OpenAI
from agents.fetching_agent import FetchingAgent
from agents.processing_agent import ProcessingAgent
from agents.consensus_agents import ConsensusManager
from agents.curation_agent import CurationAgent
from agents.editor_agent import EditorAgent
from agents.readme_updater_agent import ReadmeUpdaterAgent
from agents.archive_agent import ArchiveAgent
from models.repo_models import RepoDetails
from models.editor_models import EditorNote

TEST_README_PATH = "tests/output/test_readme_output.md"
TEST_ARCHIVE_PATH = "tests/output/test_editor_summaries.md"
os.makedirs("tests/output", exist_ok=True)

# Store test data between tests
test_data = {
    'fetched_repos': None,
    'processed_repos': None,
    'curated_repos': None
}

@pytest.fixture
def github_token():
    """Get GitHub token from environment"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        pytest.skip("GITHUB_TOKEN not set")
    return token

@pytest.fixture
def openai_key():
    """Get OpenAI API key from environment"""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        pytest.skip("OPENAI_API_KEY not set")
    return key

@pytest.fixture
def openai_client(openai_key):
    """Create OpenAI client"""
    return OpenAI(api_key=openai_key)

def test_fetch_real_repos(github_token, openai_client):
    """Test fetching actual starred repositories from GitHub"""
    print("\n[test_fetch_real_repos] Starting...")
    
    agent = FetchingAgent(openai_client, github_token)
    print("[test_fetch_real_repos] Created FetchingAgent")
    
    repos = agent.execute("seantauber")
    print(f"[test_fetch_real_repos] Fetched {len(repos)} repositories")
    
    assert len(repos) > 0
    assert all(isinstance(repo, dict) for repo in repos)
    
    # Validate required fields
    for repo in repos:
        assert repo.get('name'), "Repository must have a name"
        assert repo.get('full_name'), "Repository must have a full_name"
        assert repo.get('html_url'), "Repository must have a html_url"
    
    # Log minimal stats
    if repos:
        sample_repo = repos[0]
        print(f"[test_fetch_real_repos] Sample repo name: {sample_repo.get('name', 'N/A')}")
        print(f"[test_fetch_real_repos] Sample repo owner: {sample_repo.get('owner', {}).get('login', 'N/A')}")
    
    # Store repos for next test
    test_data['fetched_repos'] = repos
    print("[test_fetch_real_repos] Completed successfully")

def test_process_real_repos(github_token, openai_key, openai_client):
    """Test processing real repositories through the agent system"""
    print("\n[test_process_real_repos] Starting...")
    
    # Use stored repos from previous test
    repos = test_data['fetched_repos']
    if not repos:
        print("[test_process_real_repos] No stored repos found, fetching new ones...")
        fetching_agent = FetchingAgent(openai_client, github_token)
        repos = fetching_agent.execute("seantauber")
    
    print(f"[test_process_real_repos] Processing {len(repos)} repositories")
    
    # Process repos
    processing_agent = ProcessingAgent(openai_client)
    print("[test_process_real_repos] Created ProcessingAgent")
    
    # Process only first 2 repos for testing to speed things up
    test_repos = repos[:2]
    print(f"[test_process_real_repos] Selected {len(test_repos)} repos for testing")
    
    processed_repos = []
    for i, repo in enumerate(test_repos, 1):
        print(f"[test_process_real_repos] Processing repo {i}/{len(test_repos)}: {repo.get('name', 'N/A')}")
        try:
            processed_repo = processing_agent.process_repo(repo)
            # Validate processed repo
            if isinstance(processed_repo, RepoDetails) and processed_repo.is_complete():
                processed_repos.append(processed_repo)
                print(f"[test_process_real_repos] Successfully processed {repo.get('name', 'N/A')}")
            else:
                print(f"[test_process_real_repos] Skipping incomplete repo {repo.get('name', 'N/A')}")
        except Exception as e:
            print(f"[test_process_real_repos] Error processing {repo.get('name', 'N/A')}: {str(e)}")
    
    print(f"[test_process_real_repos] Processed {len(processed_repos)} repositories")
    
    # Get consensus categorization
    print("[test_process_real_repos] Starting consensus categorization...")
    consensus_manager = ConsensusManager(openai_client)
    categorized_repos = []
    
    for i, repo in enumerate(processed_repos, 1):
        print(f"[test_process_real_repos] Getting consensus for repo {i}/{len(processed_repos)}: {repo.name}")
        try:
            result = consensus_manager.get_consensus(repo)
            if isinstance(result, RepoDetails) and result.is_complete():
                categorized_repos.append(result)
                print(f"[test_process_real_repos] Successfully categorized {repo.name}")
            else:
                print(f"[test_process_real_repos] Skipping incompletely categorized repo {repo.name}")
        except Exception as e:
            print(f"[test_process_real_repos] Error categorizing {repo.name}: {str(e)}")
    
    print(f"[test_process_real_repos] Categorized {len(categorized_repos)} repositories")
    
    # Curate repos
    print("[test_process_real_repos] Starting curation...")
    curation_agent = CurationAgent(openai_client)
    curated_repos = curation_agent.curate_repositories(categorized_repos)
    print(f"[test_process_real_repos] Curated down to {len(curated_repos)} repositories")
    
    assert len(curated_repos) > 0
    assert all(isinstance(repo, RepoDetails) and repo.is_complete() for repo in curated_repos)
    
    # Store curated repos for next test
    test_data['curated_repos'] = curated_repos
    print("[test_process_real_repos] Completed successfully")

def test_readme_generation(github_token, openai_key, openai_client):
    """Test generating README content with real repository data"""
    print("\n[test_readme_generation] Starting...")
    
    # Use stored curated repos from previous test
    curated_repos = test_data['curated_repos']
    if not curated_repos:
        print("[test_readme_generation] No stored curated repos found, processing new ones...")
        test_process_real_repos(github_token, openai_key, openai_client)
        curated_repos = test_data['curated_repos']
    
    print(f"[test_readme_generation] Working with {len(curated_repos)} curated repositories")
    
    # Generate new content
    editor_agent = EditorAgent(openai_client)
    print("[test_readme_generation] Created EditorAgent")
    
    edited_content = editor_agent.generate_content(curated_repos)
    print("[test_readme_generation] Generated README content")
    
    # Validate content structure using regex patterns
    assert edited_content, "Generated content should not be empty"
    assert re.search(r'##\s+⭐\s+Starred\s+Repositories', edited_content, re.IGNORECASE), "Missing Starred Repositories section"
    
    # Copy main README as template for test
    shutil.copy('README.md', TEST_README_PATH)
    print("[test_readme_generation] Copied main README as template")
    
    # Create archive agent and readme updater agent with OpenAI client
    archive_agent = ArchiveAgent(archive_file=TEST_ARCHIVE_PATH)
    updater_agent = ReadmeUpdaterAgent(archive_agent, openai_client=openai_client)
    print("[test_readme_generation] Created ReadmeUpdaterAgent")
    
    # Group repositories by their actual categories from consensus
    grouped_repos = {}
    for repo in curated_repos:
        if not isinstance(repo, RepoDetails) or not repo.is_complete():
            print(f"[test_readme_generation] Skipping incomplete repo: {getattr(repo, 'name', 'Unknown')}")
            continue
            
        category = repo.topics[0] if repo.topics else "Other"
        if category not in grouped_repos:
            grouped_repos[category] = []
        grouped_repos[category].append(repo)
    
    # Create an EditorNote
    editors_note = EditorNote(content="Test editor's note for integration test")
    
    # Execute the readme update
    updater_agent.execute(grouped_repos, editors_note, readme_path=TEST_README_PATH)
    print("[test_readme_generation] Executed README update")
    
    assert os.path.exists(TEST_README_PATH), "README file should exist"
    assert os.path.exists(TEST_ARCHIVE_PATH), "Archive file should exist"
    
    # Verify content structure
    with open(TEST_README_PATH, 'r') as f:
        content = f.read()
        # Use regex patterns for more flexible matching
        assert re.search(r'##.*Repositories', content), "Missing repositories section"
        assert re.search(r"Editor['']s\s+Note", content), "Missing editor's note section"
        # Verify basic structure
        assert re.search(r'##.*\n.*\[.*\]\(.*\)', content), "Missing repository links"
    
    print("[test_readme_generation] README verification complete")
    
    # Log completion time
    with open(TEST_README_PATH, 'a') as f:
        f.write(f"\n\n---\nIntegration Test Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("[test_readme_generation] Completed successfully")

def test_end_to_end_flow(github_token, openai_key, openai_client):
    """Test the complete end-to-end flow with real APIs"""
    print("\n[test_end_to_end_flow] Starting...")
    
    # Run all tests in sequence
    test_fetch_real_repos(github_token, openai_client)
    test_process_real_repos(github_token, openai_key, openai_client)
    test_readme_generation(github_token, openai_key, openai_client)
    
    # Verify final output exists and has content
    assert os.path.exists(TEST_README_PATH), "README file should exist"
    assert os.path.exists(TEST_ARCHIVE_PATH), "Archive file should exist"
    
    # Verify file contents
    with open(TEST_README_PATH, 'r') as f:
        readme_content = f.read()
        assert len(readme_content) > 0, "README should not be empty"
        assert re.search(r'##.*Repositories', readme_content), "README should contain repositories section"
    
    with open(TEST_ARCHIVE_PATH, 'r') as f:
        archive_content = f.read()
        assert len(archive_content) > 0, "Archive should not be empty"
    
    print("[test_end_to_end_flow] End-to-end test completed successfully")
    print(f"[test_end_to_end_flow] Output written to: {TEST_README_PATH}")
