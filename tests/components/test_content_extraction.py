"""Tests for content extraction with live dependencies."""
import json
import asyncio
from datetime import datetime, UTC
from typing import List, Dict, Any, AsyncGenerator

import pytest
from agents.content_extractor import ContentExtractorAgent
from db.connection import Database
from processing.github_client import RateLimitedGitHubClient
from tests.config import get_test_settings

pytestmark = pytest.mark.asyncio

BATCH_SIZE = 3  # Process in smaller batches due to API limits

class TestContentExtractionComponent:
    """Tests for content extraction with live dependencies."""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Set up test database."""
        settings = get_test_settings()
        db = Database(settings.TEST_DATABASE_PATH)
        db.connect()
        
        # Clear existing data
        db.execute("DELETE FROM repositories")
        db.execute("DELETE FROM topics")
        db.execute("DELETE FROM repository_categories")
        db.execute("DELETE FROM content_cache")
        
        yield db
        db.disconnect()
    
    @pytest.fixture
    async def github_client(self) -> RateLimitedGitHubClient:
        """Initialize rate-limited GitHub client."""
        settings = get_test_settings()
        async with RateLimitedGitHubClient(settings.GITHUB_TOKEN) as client:
            yield client
    
    @pytest.fixture
    async def content_extractor(
        self,
        setup_database: Database
    ) -> ContentExtractorAgent:
        """Initialize content extractor with dependencies."""
        agent = ContentExtractorAgent(
            github_token=get_test_settings().GITHUB_TOKEN,
            db=setup_database,
            max_age_hours=0  # Always update during testing
        )
        return agent
    
    async def process_newsletter_batch(
        self,
        newsletters: List[Dict],
        extractor: ContentExtractorAgent,
        batch_id: int
    ) -> Dict[str, Any]:
        """Process a batch of newsletters in parallel.
        
        Args:
            newsletters: List of newsletters to process
            extractor: Content extractor instance
            batch_id: Unique identifier for this batch
            
        Returns:
            Dict containing processing results
        """
        results = {
            "successful": [],
            "failed": [],
            "errors": {},
            "repositories": [],
            "urls": []
        }
        
        print(f"\nProcessing batch {batch_id} with {len(newsletters)} newsletters")
        
        # Process newsletters concurrently
        tasks = []
        for newsletter in newsletters:
            tasks.append(
                extractor.process_newsletter_content(
                    newsletter['email_id'],
                    newsletter['content']
                )
            )
        
        # Wait for all processing tasks
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for newsletter, result in zip(newsletters, batch_results):
            if isinstance(result, Exception):
                print(f"Error in batch {batch_id}: {str(result)}")
                results["failed"].append(newsletter['email_id'])
                results["errors"][newsletter['email_id']] = str(result)
                continue
            
            if result:
                results["successful"].append(newsletter['email_id'])
                
                # Track repositories and URLs
                for item in result:
                    if "repositories" in item:
                        results["repositories"].extend(item["repositories"])
                    if "urls" in item:
                        results["urls"].extend(item["urls"])
                        
                print(f"Successfully processed newsletter {newsletter['email_id']} in batch {batch_id}")
        
        return results
    
    async def test_repository_extraction(
        self,
        content_extractor: ContentExtractorAgent,
        setup_database: Database
    ):
        """Test extracting repositories from live newsletter content."""
        print("\n=== Content Extraction Component Test ===")
        
        # Await the fixture to get the agent instance
        agent = await content_extractor
        async with agent as extractor:
            # Get newsletters to process
            db = setup_database
            
            newsletters = db.fetch_all(
                "SELECT * FROM newsletters WHERE processing_status = 'completed' ORDER BY received_date DESC"
            )
            
            if not newsletters:
                pytest.skip("No newsletters available for testing")
            
            print(f"\nFound {len(newsletters)} newsletters to process")
            
            # Split into batches
            batches = [
                newsletters[i:i + BATCH_SIZE]
                for i in range(0, len(newsletters), BATCH_SIZE)
            ]
            print(f"\nSplit into {len(batches)} batches of size {BATCH_SIZE}")
            
            # Process batches concurrently
            batch_results = await asyncio.gather(*[
                self.process_newsletter_batch(batch, extractor, i)
                for i, batch in enumerate(batches)
            ])
        
            # Aggregate results
            total_results = {
                "successful": [],
                "failed": [],
                "errors": {},
                "repositories": [],
                "urls": []
            }
            
            for result in batch_results:
                total_results["successful"].extend(result["successful"])
                total_results["failed"].extend(result["failed"])
                total_results["errors"].update(result["errors"])
                total_results["repositories"].extend(result["repositories"])
                total_results["urls"].extend(result["urls"])
            
            # Print summary
            print("\nExtraction Results:")
            print(f"Newsletters processed: {len(newsletters)}")
            print(f"Successfully processed: {len(total_results['successful'])}")
            print(f"Failed: {len(total_results['failed'])}")
            print(f"\nContent extracted:")
            print(f"- Repositories: {len(total_results['repositories'])}")
            print(f"- Other URLs: {len(total_results['urls'])}")
            
            if total_results["errors"]:
                print("\nErrors encountered:")
                for email_id, error in total_results["errors"].items():
                    print(f"- {email_id}: {error}")
            
            # Verify database storage
            repo_count = db.fetch_one(
                "SELECT COUNT(*) as count FROM repositories"
            )['count']
            topic_count = db.fetch_one(
                "SELECT COUNT(*) as count FROM topics"
            )['count']
            category_count = db.fetch_one(
                "SELECT COUNT(*) as count FROM repository_categories"
            )['count']
            cached_url_count = db.fetch_one(
                "SELECT COUNT(*) as count FROM content_cache"
            )['count']
            
            print("\nDatabase Storage:")
            print(f"- Repositories: {repo_count}")
            print(f"- Topics: {topic_count}")
            print(f"- Categories: {category_count}")
            print(f"- Cached URLs: {cached_url_count}")
            
            # Show sample repository
            if total_results["repositories"]:
                repo = total_results["repositories"][0]
                print("\nSample Repository:")
                print(f"URL: {repo['url']}")
                print(f"Name: {repo['metadata']['name']}")
                print(f"Description: {repo['metadata']['description']}")
                print(f"Stars: {repo['metadata']['stars']}")
                if repo['summary']['is_genai']:
                    print("\nCategories:")
                    for cat in repo['summary']['ranked_categories']:
                        print(f"- {cat['category']} (rank {cat['rank']})")
            
            # Basic assertions
            assert len(total_results["successful"]) > 0, "No newsletters were processed"
            assert repo_count > 0, "No repositories were stored"
            assert topic_count > 0, "No topics were stored"
            assert category_count > 0, "No categories were stored"
            assert cached_url_count > 0, "No URLs were cached"
            
            # Verify pipeline state
            stage_status = extractor.pipeline_state.get_stage_status("content_extraction")
            print("\nPipeline Stage Status:")
            print(f"Total Batches: {stage_status['total_batches']}")
            print(f"Completed: {stage_status['completed']}")
            print(f"Failed: {stage_status['failed']}")
            print(f"Running: {stage_status['running']}")
            print(f"Total Processed: {stage_status['total_processed']}")
            print(f"Total Failed: {stage_status['total_failed']}")
            
            if stage_status['errors']:
                print("\nStage Errors:")
                for error in stage_status['errors']:
                    print(f"- {error}")
            
            # Verify state matches results
            # Note: Repository batches are tracked as sub-batches of newsletter batches
            assert stage_status['total_batches'] == len(newsletters), (
                f"Batch count mismatch. Expected {len(newsletters)} newsletter batches, "
                f"got {stage_status['total_batches']}"
            )
            assert stage_status['completed'] + stage_status['failed'] == len(newsletters), (
                "Incomplete batches. Expected all newsletter batches to be either completed or failed."
            )
            # Verify processed counts
            # Note: total_processed tracks all processed repositories, including non-GenAI ones
            assert stage_status['total_processed'] == len(total_results['repositories']), (
                f"Processed repository count mismatch. Expected {len(total_results['repositories'])} processed repositories, "
                f"got {stage_status['total_processed']}"
            )
            
            # Verify stored repository count
            assert repo_count <= len(total_results['repositories']), (
                f"Stored repository count too high. Have {repo_count} stored repositories but only "
                f"processed {len(total_results['repositories'])} total"
            )
            
            # Verify successful newsletter processing
            assert len(total_results['successful']) == len(newsletters), (
                f"Newsletter processing mismatch. Expected {len(newsletters)} newsletters, "
                f"got {len(total_results['successful'])} successful"
            )
            
            # Verify failed counts
            assert stage_status['total_failed'] == len(total_results['failed']), (
                f"Failed count mismatch. Expected {len(total_results['failed'])} failures, "
                f"got {stage_status['total_failed']}"
            )
