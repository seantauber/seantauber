"""Tests for content extraction with live dependencies."""
import json
import os
from datetime import datetime
from zoneinfo import UTC

import pytest
from agents.content_extractor import ContentExtractorAgent
from db.connection import Database
from processing.embedchain_store import EmbedchainStore
from tests.config import get_test_settings, TEST_DB_PATH
from tests.components.conftest import (
    print_newsletter_summary,
    print_repository_summary,
    print_extraction_results
)

class TestContentExtractionComponent:
    """Tests for content extraction with live dependencies."""
    
    @pytest.fixture
    def content_extractor(self, vector_store: EmbedchainStore) -> ContentExtractorAgent:
        """Initialize content extractor component."""
        settings = get_test_settings()
        extractor = ContentExtractorAgent(
            vector_store,
            github_token=os.getenv('GITHUB_TOKEN', settings.GITHUB_TOKEN)
        )
        yield extractor
    
    async def test_repository_extraction(self, content_extractor: ContentExtractorAgent):
        """Test extracting repositories from live newsletter content."""
        print("\n=== Content Extraction Component Test ===")
        print("\nStarting repository extraction test...")
        
        extraction_results = []
        db = Database(TEST_DB_PATH)
        db.connect()
        try:
            # Get newsletters to process
            newsletters = db.fetch_all(
                "SELECT * FROM newsletters WHERE processing_status = 'completed' ORDER BY received_date DESC"
            )
            
            print("\nProcessing Source Newsletters:")
            print_newsletter_summary("Input Newsletters", newsletters, show_content=True)
            
            for newsletter in newsletters:
                print(f"\nAnalyzing newsletter: {newsletter['subject']}")
                print(f"Content preview: {newsletter['content'][:200]}...")
                
                try:
                    # Extract repositories
                    repos = content_extractor.extract_repository_links(newsletter['content'])
                    
                    # Record results
                    for repo_url in repos:
                        result = {
                            'newsletter_subject': newsletter['subject'],
                            'email_id': newsletter['email_id'],
                            'received_date': newsletter['received_date'],
                            'repository_url': repo_url,
                            'vector_id': None,  # Will be set if vector storage succeeds
                            'summary': None     # Will be set if summary generation succeeds
                        }
                        
                        try:
                            # Fetch metadata and README
                            metadata = await content_extractor.fetch_repository_metadata(repo_url)
                            
                            # Generate summary
                            summary = await content_extractor.generate_repository_summary(metadata)
                            result['summary'] = summary
                            
                            # Store in vector storage
                            repo_data = {
                                "github_url": repo_url,
                                "name": metadata["name"],
                                "description": metadata["description"],
                                "summary": summary,
                                "metadata": {
                                    "stars": metadata["stars"],
                                    "forks": metadata["forks"],
                                    "language": metadata["language"],
                                    "topics": metadata["topics"],
                                    "created_at": metadata["created_at"],
                                    "updated_at": metadata["updated_at"]
                                },
                                "first_seen_date": datetime.now(UTC).isoformat(),
                                "source_type": "newsletter",
                                "source_id": newsletter['email_id']
                            }
                            vector_id = await content_extractor.vector_store.store_repository(repo_data)
                            result['vector_id'] = vector_id
                            
                        except Exception as e:
                            print(f"Error processing repository {repo_url}: {str(e)}")
                            
                        extraction_results.append(result)
                        
                except Exception as e:
                    print(f"Error processing newsletter: {str(e)}")
                    continue
            
            # Print detailed results
            print_extraction_results("Repository Extraction Results", extraction_results)
            
            # Print summary details
            print("\nRepository Summaries:")
            for result in extraction_results:
                if result['summary']:
                    print(f"\nRepository: {result['repository_url']}")
                    print("Summary:")
                    print(f"- Primary Purpose: {result['summary']['primary_purpose']}")
                    print(f"- Key Technologies: {', '.join(result['summary']['key_technologies'])}")
                    print(f"- Target Users: {result['summary']['target_users']}")
                    print(f"- Main Features: {', '.join(result['summary']['main_features'])}")
                    print(f"- Technical Domain: {result['summary']['technical_domain']}")
            
            assert len(extraction_results) > 0, "No repositories were extracted"
            assert any(r['summary'] for r in extraction_results), "No summaries were generated"
            
        finally:
            db.disconnect()

    async def test_metadata_collection(self, content_extractor: ContentExtractorAgent):
        """Test collecting metadata from live GitHub repositories."""
        print("\n=== Repository Metadata Collection Test ===")
        
        db = Database(TEST_DB_PATH)
        db.connect()
        try:
            # Get repositories to process
            repos = db.fetch_all(
                "SELECT * FROM repositories ORDER BY first_seen_date DESC"
            )
            
            print("\nProcessing Repositories:")
            processed_repos = []
            
            for repo in repos:
                print(f"\nCollecting metadata for: {repo['github_url']}")
                
                try:
                    # Fetch metadata and README
                    metadata = await content_extractor.fetch_repository_metadata(repo['github_url'])
                    
                    # Generate summary
                    summary = await content_extractor.generate_repository_summary(metadata)
                    
                    # Store result for summary
                    processed_repos.append({
                        'url': repo['github_url'],
                        'description': metadata['description'],
                        'metadata': metadata,
                        'summary': summary
                    })
                    
                    print("Successfully collected data:")
                    print("\nMetadata:")
                    for key, value in metadata.items():
                        if key != 'readme_content':  # Skip long README content
                            print(f"- {key}: {value}")
                            
                    print("\nSummary:")
                    print(f"- Primary Purpose: {summary['primary_purpose']}")
                    print(f"- Key Technologies: {', '.join(summary['key_technologies'])}")
                    print(f"- Target Users: {summary['target_users']}")
                    print(f"- Main Features: {', '.join(summary['main_features'])}")
                    print(f"- Technical Domain: {summary['technical_domain']}")
                        
                except Exception as e:
                    print(f"Error collecting data: {str(e)}")
                    continue
            
            # Show processed repositories
            print_repository_summary("Processed Repositories with Metadata", processed_repos, show_metadata=True)
            
            assert len(processed_repos) > 0, "No metadata was collected"
            assert all('summary' in repo for repo in processed_repos), "Some repositories missing summaries"
            
        finally:
            db.disconnect()
            
    async def test_full_extraction_pipeline(self, content_extractor: ContentExtractorAgent):
        """Test complete extraction pipeline with live data."""
        print("\n=== Full Content Extraction Pipeline Test ===")
        
        pipeline_results = []
        db = Database(TEST_DB_PATH)
        db.connect()
        try:
            # Get newsletters to process
            newsletters = db.fetch_all(
                "SELECT * FROM newsletters WHERE processing_status = 'completed' ORDER BY received_date DESC"
            )
            
            print("\nProcessing Pipeline Input:")
            print_newsletter_summary("Source Newsletters", newsletters, show_content=True)
            
            for newsletter in newsletters:
                print(f"\nProcessing newsletter: {newsletter['subject']}")
                
                try:
                    # 1. Extract repositories
                    repos = content_extractor.extract_repository_links(newsletter['content'])
                    print(f"Found {len(repos)} repositories")
                    
                    # 2. Process each repository
                    for repo_url in repos:
                        result = {
                            'newsletter_subject': newsletter['subject'],
                            'email_id': newsletter['email_id'],
                            'received_date': newsletter['received_date'],
                            'repository_url': repo_url,
                            'metadata': None,
                            'summary': None,
                            'vector_id': None
                        }
                        
                        try:
                            print(f"\nProcessing repository: {repo_url}")
                            
                            # Fetch metadata and README
                            metadata = await content_extractor.fetch_repository_metadata(repo_url)
                            result['metadata'] = metadata
                            
                            # Generate summary
                            summary = await content_extractor.generate_repository_summary(metadata)
                            result['summary'] = summary
                            
                            # Store in vector storage
                            repo_data = {
                                "github_url": repo_url,
                                "name": metadata["name"],
                                "description": metadata["description"],
                                "summary": summary,
                                "metadata": {
                                    "stars": metadata["stars"],
                                    "forks": metadata["forks"],
                                    "language": metadata["language"],
                                    "topics": metadata["topics"],
                                    "created_at": metadata["created_at"],
                                    "updated_at": metadata["updated_at"]
                                },
                                "first_seen_date": datetime.now(UTC).isoformat(),
                                "source_type": "newsletter",
                                "source_id": newsletter['email_id']
                            }
                            vector_id = await content_extractor.vector_store.store_repository(repo_data)
                            result['vector_id'] = vector_id
                            
                            print("Successfully processed repository:")
                            print("- Metadata collected")
                            print("- Summary generated")
                            print(f"- Vector ID: {vector_id}")
                            
                            # Print summary details
                            print("\nRepository Summary:")
                            print(f"- Primary Purpose: {summary['primary_purpose']}")
                            print(f"- Key Technologies: {', '.join(summary['key_technologies'])}")
                            print(f"- Target Users: {summary['target_users']}")
                            print(f"- Main Features: {', '.join(summary['main_features'])}")
                            print(f"- Technical Domain: {summary['technical_domain']}")
                            
                        except Exception as e:
                            print(f"Error processing repository: {str(e)}")
                            
                        pipeline_results.append(result)
                            
                except Exception as e:
                    print(f"Error processing newsletter: {str(e)}")
                    continue
            
            # Print detailed pipeline results
            print_extraction_results("Pipeline Execution Results", pipeline_results)
            
            # Print summary statistics
            print("\nSummary Generation Statistics:")
            total_repos = len(pipeline_results)
            with_summaries = sum(1 for r in pipeline_results if r['summary'])
            print(f"Total Repositories: {total_repos}")
            print(f"With Summaries: {with_summaries}")
            print(f"Summary Success Rate: {(with_summaries/total_repos*100) if total_repos > 0 else 0:.1f}%")
            
            assert len(pipeline_results) > 0, "No repositories were processed"
            assert any(r['vector_id'] for r in pipeline_results), "No vector embeddings were created"
            assert any(r['summary'] for r in pipeline_results), "No summaries were generated"
            
        finally:
            db.disconnect()

    async def test_migration(self, content_extractor: ContentExtractorAgent):
        """Test migration of existing repositories to include summaries."""
        print("\n=== Repository Migration Test ===")
        
        db = Database(TEST_DB_PATH)
        db.connect()
        try:
            # Get existing repositories
            before_repos = db.fetch_all(
                "SELECT * FROM repositories ORDER BY first_seen_date DESC"
            )
            print("\nExisting Repositories Before Migration:")
            print_repository_summary("Pre-Migration State", before_repos)
            
            # Run migration
            print("\nStarting repository migration...")
            await content_extractor.migrate_existing_repositories()
            
            # Get updated repositories
            after_repos = db.fetch_all(
                "SELECT * FROM repositories ORDER BY first_seen_date DESC"
            )
            print("\nRepositories After Migration:")
            print_repository_summary("Post-Migration State", after_repos)
            
            # Verify summaries
            print("\nVerifying Repository Summaries:")
            for repo in after_repos:
                metadata = json.loads(repo['metadata']) if repo['metadata'] else {}
                if 'summary' in metadata:
                    print(f"\nRepository: {repo['github_url']}")
                    summary = metadata['summary']
                    print("Summary:")
                    print(f"- Primary Purpose: {summary['primary_purpose']}")
                    print(f"- Key Technologies: {', '.join(summary['key_technologies'])}")
                    print(f"- Target Users: {summary['target_users']}")
                    print(f"- Main Features: {', '.join(summary['main_features'])}")
                    print(f"- Technical Domain: {summary['technical_domain']}")
            
            assert len(after_repos) == len(before_repos), "Repository count changed during migration"
            assert all('summary' in json.loads(r['metadata']) for r in after_repos if r['metadata']), "Some repositories missing summaries"
            
        finally:
            db.disconnect()
