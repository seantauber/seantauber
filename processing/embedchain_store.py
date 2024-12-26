"""Embedchain integration for vector storage."""

import logging
import re
from typing import Dict, Optional, List, Any
from embedchain import App
from embedchain.config import AppConfig

logger = logging.getLogger(__name__)

class EmbedchainStore:
    """Vector storage implementation using Embedchain."""

    def __init__(self, vector_store_path: str):
        """
        Initialize Embedchain store.

        Args:
            vector_store_path: Path to vector storage directory
        """
        # Configure Embedchain apps with vector store path
        newsletter_config = AppConfig()
        newsletter_config.name = "newsletters"
        newsletter_config.collection_name = "newsletters"
        newsletter_config.chromadb_settings = {
            "directory": vector_store_path
        }
        
        repository_config = AppConfig()
        repository_config.name = "repositories"
        repository_config.collection_name = "repositories"
        repository_config.chromadb_settings = {
            "directory": vector_store_path
        }
        
        # Initialize Embedchain apps for different collections
        self.newsletter_store = App(config=newsletter_config)
        self.repository_store = App(config=repository_config)
        
        # Cache for repository data
        self._repository_cache: Dict[str, Dict[str, Any]] = {}


    async def store_repository(self, repository: Dict[str, Any]) -> str:
        """
        Store repository data in vector storage.

        Args:
            repository: Repository data including metadata and summary

        Returns:
            Vector storage ID

        Raises:
            Exception: If storing fails
        """
        try:
            # Create searchable text representation
            search_text = (
                f"Repository: {repository['name']} ({repository['github_url']})\n"
                f"Description: {repository['description']}\n"
                f"Language: {repository['metadata']['language']}\n"
                f"Topics: {', '.join(repository['metadata']['topics'])}\n"
                f"Primary Purpose: {repository['summary']['primary_purpose']}\n"
                f"Technical Domain: {repository['summary']['technical_domain']}"
            )
            
            # Store with minimal metadata for search
            vector_id = self.repository_store.add(
                search_text,
                metadata={
                    'github_url': repository['github_url'],
                    'name': repository['name']
                }
            )
            
            # Cache complete repository data
            self._repository_cache[repository['github_url']] = repository
            
            logger.info(f"Stored repository {repository['github_url']} in vector storage")
            return vector_id
        except Exception as e:
            logger.error(f"Failed to store repository in vector storage: {str(e)}")
            raise

    async def query_newsletters(
        self,
        query: str,
        limit: int = 5
    ) -> list:
        """
        Search through stored newsletters.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of relevant newsletter content
        """
        try:
            results = self.newsletter_store.query(
                query,
                top_k=limit
            )
            return results
        except Exception as e:
            logger.error(f"Failed to query newsletters: {str(e)}")
            raise

    async def query_repositories(
        self,
        query: str,
        limit: int = 5
    ) -> list:
        """
        Search through stored repositories.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of relevant repository content
        """
        try:
            # Get search results
            results = self.repository_store.query(
                query,
                top_k=limit
            )
            
            # Extract stored data from cache
            processed_results = []
            for result in results:
                try:
                    # Handle string response format
                    if isinstance(result, str):
                        # Try to extract github_url from the text
                        import re
                        url_match = re.search(r'https://github\.com/[a-zA-Z0-9-]+/[a-zA-Z0-9-_.]+', result)
                        if url_match:
                            github_url = url_match.group(0)
                            if github_url in self._repository_cache:
                                processed_results.append(self._repository_cache[github_url])
                            else:
                                logger.warning(f"Repository not found in cache: {github_url}")
                        else:
                            logger.warning(f"Could not extract GitHub URL from result: {result}")
                    else:
                        processed_results.append(result)
                except Exception as e:
                    logger.warning(f"Error processing result: {str(e)}")
                    continue
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Failed to query repositories: {str(e)}")
            raise

    async def get_embedding(self, vector_id: str) -> Optional[List[float]]:
        """
        Get the embedding vector for a stored item.
        
        Args:
            vector_id: Vector storage ID
            
        Returns:
            Embedding vector if found, None otherwise
        """
        try:
            # Try both stores since we don't know which one contains the ID
            try:
                embedding = self.newsletter_store.get(vector_id)
                return embedding
            except:
                embedding = self.repository_store.get(vector_id)
                return embedding
        except Exception as e:
            logger.error(f"Failed to get embedding for vector ID {vector_id}: {str(e)}")
            return None
