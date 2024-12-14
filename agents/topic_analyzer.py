"""Topic Analyzer agent for semantic categorization of repositories."""

import logging
from typing import Dict, List, Optional
from processing.embedchain_store import EmbedchainStore

logger = logging.getLogger(__name__)

class TopicAnalyzer:
    """Agent for analyzing and categorizing repository topics using semantic analysis."""

    # Fixed category structure with parent/child relationships
    FIXED_CATEGORIES = {
        1: {"name": "Machine Learning", "parent_id": None},
        2: {"name": "Natural Language Processing", "parent_id": 1},
        3: {"name": "Computer Vision", "parent_id": 1},
        4: {"name": "Deep Learning", "parent_id": 1},
        5: {"name": "Reinforcement Learning", "parent_id": 1},
        6: {"name": "MLOps", "parent_id": None},
        7: {"name": "Model Deployment", "parent_id": 6},
        8: {"name": "Model Monitoring", "parent_id": 6},
        9: {"name": "Data Engineering", "parent_id": None},
        10: {"name": "Data Processing", "parent_id": 9},
        11: {"name": "Data Visualization", "parent_id": 9},
        12: {"name": "Large Language Models", "parent_id": 2},
        13: {"name": "Prompt Engineering", "parent_id": 12},
        14: {"name": "Model Fine-tuning", "parent_id": 12},
        15: {"name": "AI Agents", "parent_id": None},
        16: {"name": "Multi-agent Systems", "parent_id": 15},
        17: {"name": "Agent Frameworks", "parent_id": 15},
        18: {"name": "AI Tools", "parent_id": None},
        19: {"name": "Development Tools", "parent_id": 18},
        20: {"name": "Productivity Tools", "parent_id": 18}
    }

    MIN_CONFIDENCE_THRESHOLD = 0.6

    def __init__(self, embedchain_store: EmbedchainStore):
        """
        Initialize Topic Analyzer.

        Args:
            embedchain_store: Vector storage instance for semantic operations
        """
        self.store = embedchain_store
        logger.info("Initialized Topic Analyzer agent")

    def get_fixed_categories(self) -> Dict:
        """
        Get the fixed category structure.

        Returns:
            Dictionary of categories with their relationships
        """
        return self.FIXED_CATEGORIES

    async def get_parent_topics(self, topic_id: int) -> List[int]:
        """
        Get all parent topics for a given topic ID.

        Args:
            topic_id: ID of the topic to get parents for

        Returns:
            List of parent topic IDs
        """
        parents = []
        current = self.FIXED_CATEGORIES.get(topic_id)
        
        while current and current['parent_id']:
            parent_id = current['parent_id']
            parents.append(parent_id)
            current = self.FIXED_CATEGORIES.get(parent_id)
        
        return parents

    async def _calculate_similarity(self, text: str, category: str) -> float:
        """
        Calculate semantic similarity between text and category.

        Args:
            text: Repository description or content
            category: Category name to compare against

        Returns:
            Similarity score between 0 and 1
        """
        try:
            # Use embedchain's query to get similarity score
            results = await self.store.query_repositories(
                query=category,
                limit=1
            )
            
            # Extract similarity score from results
            # Note: This is a simplified version, in practice you might want
            # to use more sophisticated similarity calculations
            if results and len(results) > 0:
                # Normalize score to 0-1 range
                score = min(1.0, max(0.0, results[0].get('score', 0.0)))
                return score
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            return 0.0

    async def analyze_repository_topics(
        self,
        repository: Dict
    ) -> List[Dict[str, float]]:
        """
        Analyze repository content and determine relevant topics.

        Args:
            repository: Repository data including description and metadata

        Returns:
            List of topics with confidence scores

        Raises:
            ValueError: If repository data is invalid
        """
        if not repository.get('description'):
            raise ValueError("Repository must have a description")

        description = repository['description']
        relevant_topics = []

        try:
            # Calculate similarity with each category
            for topic_id, category in self.FIXED_CATEGORIES.items():
                similarity = await self._calculate_similarity(
                    description,
                    category['name']
                )
                
                if similarity >= self.MIN_CONFIDENCE_THRESHOLD:
                    relevant_topics.append({
                        'topic_id': topic_id,
                        'confidence_score': similarity
                    })
                    
                    # Add parent topics with slightly reduced confidence
                    parent_topics = await self.get_parent_topics(topic_id)
                    for parent_id in parent_topics:
                        # Reduce confidence for each level up the hierarchy
                        parent_similarity = similarity * 0.9  # 10% reduction per level
                        if parent_similarity >= self.MIN_CONFIDENCE_THRESHOLD:
                            relevant_topics.append({
                                'topic_id': parent_id,
                                'confidence_score': parent_similarity
                            })

            # Sort by confidence score and remove duplicates
            seen_topics = set()
            unique_topics = []
            for topic in sorted(
                relevant_topics,
                key=lambda x: x['confidence_score'],
                reverse=True
            ):
                if topic['topic_id'] not in seen_topics:
                    seen_topics.add(topic['topic_id'])
                    unique_topics.append(topic)

            logger.info(
                f"Analyzed topics for repository {repository['github_url']}: "
                f"found {len(unique_topics)} relevant topics"
            )
            return unique_topics

        except Exception as e:
            logger.error(
                f"Error analyzing topics for repository {repository['github_url']}: {str(e)}"
            )
            raise
