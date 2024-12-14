"""Repository Curator agent for managing and organizing repositories."""

import logging
from datetime import datetime, UTC
from typing import Dict, Optional
from processing.embedchain_store import EmbedchainStore

logger = logging.getLogger(__name__)

class RepositoryCurator:
    """Agent for curating repositories with semantic analysis and duplicate detection."""

    # Threshold for considering repositories as duplicates
    DUPLICATE_THRESHOLD = 0.90

    def __init__(self, embedchain_store: EmbedchainStore):
        """
        Initialize Repository Curator.

        Args:
            embedchain_store: Vector storage instance for semantic operations
        """
        self.store = embedchain_store
        logger.info("Initialized Repository Curator agent")

    async def process_repository(self, repository: Dict) -> Dict:
        """
        Process a repository, enrich its metadata, and store in vector storage.

        Args:
            repository: Repository data including URL and description

        Returns:
            Processed repository with enriched metadata and vector ID

        Raises:
            ValueError: If repository data is invalid
        """
        if not repository.get('github_url'):
            raise ValueError("Repository must have a valid GitHub URL")

        try:
            logger.debug(f"Processing repository: {repository['github_url']}")

            # Check for duplicates before processing
            is_duplicate = await self.detect_duplicate(repository)
            logger.debug(f"Duplicate check result: {is_duplicate}")

            if is_duplicate:
                logger.info(
                    f"Repository {repository['github_url']} detected as duplicate, "
                    "skipping processing"
                )
                return repository

            # Enrich metadata
            enriched_repo = await self.enrich_metadata(repository)
            logger.debug(f"Enriched repository data: {enriched_repo}")

            # Store in vector storage using store_repository method
            vector_id = await self.store.store_repository({
                'description': repository.get('description', ''),
                'github_url': repository['github_url'],
                'first_seen_date': repository.get('metadata', {}).get('first_seen_date', datetime.now(UTC).isoformat())
            })
            logger.debug(f"Vector storage ID: {vector_id}")

            # Create final result with vector ID
            result = {
                'github_url': enriched_repo['github_url'],
                'description': enriched_repo['description'],
                'metadata': enriched_repo['metadata'],
                'vector_id': vector_id
            }
            logger.debug(f"Final result: {result}")

            logger.info(
                f"Successfully processed repository {repository['github_url']}"
            )
            return result

        except Exception as e:
            logger.error(
                f"Error processing repository {repository['github_url']}: {str(e)}"
            )
            raise

    async def detect_duplicate(self, repository: Dict) -> bool:
        """
        Detect if a repository is semantically similar to existing ones.

        Args:
            repository: Repository data to check for duplicates

        Returns:
            True if a duplicate is found, False otherwise
        """
        try:
            logger.debug(f"Checking duplicates for: {repository['github_url']}")

            # Query vector storage for similar repositories
            similar_repos = await self.store.query_repositories(
                query=repository.get('description', ''),
                limit=5  # Check top 5 similar repositories
            )
            logger.debug(f"Similar repositories found: {similar_repos}")

            # Check each similar repository
            for similar in similar_repos:
                # If exact URL match, it's definitely a duplicate
                if similar.get('metadata', {}).get('github_url') == repository['github_url']:
                    logger.debug("Found exact URL match")
                    return True

                # Check semantic similarity
                similarity_score = similar.get('score', 0)
                logger.debug(f"Similarity score: {similarity_score}")
                if similarity_score >= self.DUPLICATE_THRESHOLD:
                    logger.info(
                        f"Repository {repository['github_url']} is semantically similar to "
                        f"{similar.get('metadata', {}).get('github_url')} "
                        f"(score: {similarity_score})"
                    )
                    return True

            logger.debug("No duplicates found")
            return False

        except Exception as e:
            logger.error(
                f"Error detecting duplicates for {repository['github_url']}: {str(e)}"
            )
            return False

    async def enrich_metadata(self, repository: Dict) -> Dict:
        """
        Enrich repository metadata with additional information.

        Args:
            repository: Repository data to enrich

        Returns:
            Repository with enriched metadata
        """
        try:
            logger.debug(f"Enriching metadata for: {repository['github_url']}")

            # Start with existing metadata or empty dict
            metadata = repository.get('metadata', {}).copy()

            # Add processing timestamp using timezone-aware datetime
            metadata['last_processed'] = datetime.now(UTC).isoformat()

            # Initialize or increment mention count
            metadata['mention_count'] = metadata.get('mention_count', 1)

            # Create enriched repository object
            enriched_repo = {
                'github_url': repository['github_url'],
                'description': repository.get('description', ''),
                'metadata': metadata
            }

            logger.debug(f"Enriched repository data: {enriched_repo}")
            logger.info(
                f"Enriched metadata for repository {repository['github_url']}"
            )
            return enriched_repo

        except Exception as e:
            logger.error(
                f"Error enriching metadata for {repository['github_url']}: {str(e)}"
            )
            raise
