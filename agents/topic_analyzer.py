"""Topic Analyzer agent for semantic categorization of repositories."""

import logging
from typing import Dict, List, Optional, Tuple
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

    # Minimum confidence threshold for category assignment
    MIN_CONFIDENCE_THRESHOLD = 0.6
    
    # Process repositories in batches for efficiency
    BATCH_SIZE = 5

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

    async def _calculate_batch_similarities(
        self,
        repositories: List[Dict],
        category: str
    ) -> List[float]:
        """
        Calculate semantic similarity between multiple repositories and a category.
        
        This method uses embedchain's semantic search capabilities to determine how
        closely each repository aligns with a given category. The similarity calculation
        involves:
        1. Creating a category-specific query that includes key characteristics
        2. Using vector similarity to compare against repository descriptions
        3. Normalizing scores to account for varying description lengths
        4. Applying category-specific adjustments based on hierarchy

        Args:
            repositories: List of repository dictionaries with descriptions
            category: Category name to compare against

        Returns:
            List of similarity scores between 0 and 1
        """
        try:
            # Construct category-specific query to capture key characteristics
            category_query = f"""
            Determine if this repository is related to {category}. 
            Consider:
            - Core functionality and features
            - Primary use cases and applications
            - Technical requirements and dependencies
            - Target users and developers
            """

            # Get semantic search results for the batch
            results = await self.store.query_repositories(
                query=category_query,
                limit=len(repositories)
            )

            # Calculate normalized similarity scores
            scores = []
            for repo, result in zip(repositories, results):
                # Skip if no results returned
                if not result:
                    scores.append(0.0)
                    continue

                # Calculate base similarity score using semantic search result
                # The score is derived from how prominently the repository appears
                # in the search results for the category query
                base_score = 0.0
                
                # Parse the semantic search results to extract relevance indicators
                relevant_terms = 0
                total_terms = 0
                
                # Look for category-specific keywords and patterns in the results
                result_text = ' '.join(result).lower()
                repo_desc = repo['description'].lower()
                
                # Core category terms
                if any(term in result_text for term in category.lower().split()):
                    relevant_terms += 2
                
                # Related technology mentions
                tech_terms = self._get_technology_terms(category)
                relevant_terms += sum(1 for term in tech_terms if term in result_text)
                
                # Application domain matches
                domain_terms = self._get_domain_terms(category)
                relevant_terms += sum(1 for term in domain_terms if term in result_text)
                
                total_terms = 4 + len(tech_terms) + len(domain_terms)
                
                # Calculate normalized score
                if total_terms > 0:
                    base_score = min(relevant_terms / total_terms, 1.0)
                
                # Apply category-specific adjustments
                adjusted_score = self._adjust_category_score(
                    base_score,
                    category,
                    repo_desc
                )
                
                scores.append(adjusted_score)

            return scores

        except Exception as e:
            logger.error(f"Error calculating batch similarities: {str(e)}")
            return [0.0] * len(repositories)

    def _get_technology_terms(self, category: str) -> List[str]:
        """Get relevant technology terms for a category."""
        # Technology term mapping for different categories
        tech_terms = {
            "Machine Learning": ["tensorflow", "pytorch", "scikit-learn", "ml", "neural networks"],
            "Natural Language Processing": ["nlp", "tokenization", "bert", "gpt", "transformers"],
            "Computer Vision": ["opencv", "image processing", "cnn", "detection", "recognition"],
            "Deep Learning": ["neural networks", "cnn", "rnn", "lstm", "transformer"],
            "Reinforcement Learning": ["rl", "q-learning", "policy", "reward", "agent"],
            "MLOps": ["deployment", "monitoring", "pipeline", "ci/cd", "kubernetes"],
            "Model Deployment": ["serving", "containerization", "api", "production", "scaling"],
            "Model Monitoring": ["metrics", "drift", "performance", "logging", "alerting"],
            "Data Engineering": ["etl", "pipeline", "processing", "warehouse", "lake"],
            "Data Processing": ["etl", "transformation", "cleaning", "validation", "pipeline"],
            "Data Visualization": ["dashboard", "plotting", "charts", "bi", "reporting"],
            "Large Language Models": ["llm", "gpt", "bert", "transformer", "embedding"],
            "Prompt Engineering": ["prompt", "template", "instruction", "completion", "generation"],
            "Model Fine-tuning": ["training", "transfer learning", "adaptation", "optimization"],
            "AI Agents": ["autonomous", "agent", "decision", "planning", "reasoning"],
            "Multi-agent Systems": ["coordination", "communication", "collaboration", "swarm"],
            "Agent Frameworks": ["framework", "sdk", "toolkit", "library", "platform"],
            "AI Tools": ["automation", "productivity", "assistant", "utility"],
            "Development Tools": ["ide", "debugging", "testing", "development", "coding"],
            "Productivity Tools": ["automation", "workflow", "efficiency", "integration"]
        }
        return tech_terms.get(category, [])

    def _get_domain_terms(self, category: str) -> List[str]:
        """Get relevant domain/application terms for a category."""
        # Domain term mapping for different categories
        domain_terms = {
            "Machine Learning": ["prediction", "classification", "regression", "clustering"],
            "Natural Language Processing": ["text", "language", "translation", "sentiment"],
            "Computer Vision": ["image", "video", "object", "scene", "visual"],
            "Deep Learning": ["feature learning", "representation", "deep neural"],
            "Reinforcement Learning": ["game", "robotics", "control", "optimization"],
            "MLOps": ["production", "deployment", "operations", "infrastructure"],
            "Model Deployment": ["production", "service", "endpoint", "hosting"],
            "Model Monitoring": ["production", "observability", "maintenance"],
            "Data Engineering": ["data infrastructure", "data platform", "data pipeline"],
            "Data Processing": ["data preparation", "data cleaning", "data transformation"],
            "Data Visualization": ["analytics", "business intelligence", "reporting"],
            "Large Language Models": ["text generation", "conversation", "completion"],
            "Prompt Engineering": ["instruction design", "prompt optimization"],
            "Model Fine-tuning": ["domain adaptation", "specialization", "customization"],
            "AI Agents": ["automation", "decision making", "task execution"],
            "Multi-agent Systems": ["distributed ai", "agent cooperation"],
            "Agent Frameworks": ["agent development", "agent platform"],
            "AI Tools": ["developer tools", "productivity", "automation"],
            "Development Tools": ["software development", "programming", "coding"],
            "Productivity Tools": ["workflow", "automation", "efficiency"]
        }
        return domain_terms.get(category, [])

    def _adjust_category_score(
        self,
        base_score: float,
        category: str,
        description: str
    ) -> float:
        """
        Apply category-specific adjustments to the base similarity score.
        
        This method refines the base similarity score by considering:
        1. Category hierarchy and relationships
        2. Explicit vs implicit relevance
        3. Confidence modifiers based on description clarity
        
        Args:
            base_score: Initial similarity score
            category: Category being evaluated
            description: Repository description
            
        Returns:
            Adjusted similarity score between 0 and 1
        """
        # Start with the base score
        score = base_score
        
        # Adjust based on explicit mentions
        if category.lower() in description.lower():
            score = min(score + 0.2, 1.0)
        
        # Adjust for description clarity
        if len(description.split()) < 10:  # Short descriptions are less reliable
            score *= 0.8
        
        # Category-specific adjustments
        if category == "Large Language Models":
            # Boost score for LLM-specific indicators
            llm_indicators = ["gpt", "llm", "language model", "transformer"]
            if any(indicator in description.lower() for indicator in llm_indicators):
                score = min(score + 0.15, 1.0)
        
        elif category == "MLOps":
            # Boost score for deployment/operations focus
            mlops_indicators = ["deployment", "monitoring", "production", "pipeline"]
            if any(indicator in description.lower() for indicator in mlops_indicators):
                score = min(score + 0.15, 1.0)
        
        # Ensure score stays within valid range
        return max(0.0, min(score, 1.0))

    async def analyze_repositories_batch(
        self,
        repositories: List[Dict]
    ) -> List[List[Dict[str, float]]]:
        """
        Analyze multiple repositories in a batch and determine relevant topics.
        
        This method performs semantic analysis to categorize repositories by:
        1. Calculating similarity scores for each category
        2. Applying confidence thresholds
        3. Handling parent/child relationships
        4. Removing duplicate or redundant categories
        
        Args:
            repositories: List of repository data including descriptions

        Returns:
            List of topic lists with confidence scores for each repository

        Raises:
            ValueError: If repository data is invalid
        """
        if not repositories:
            return []

        for repo in repositories:
            if not repo.get('description'):
                raise ValueError("All repositories must have a description")

        try:
            # Initialize results for each repository
            all_results = [[] for _ in repositories]

            # Calculate similarity with each category for the batch
            for topic_id, category in self.FIXED_CATEGORIES.items():
                similarities = await self._calculate_batch_similarities(
                    repositories,
                    category['name']
                )
                
                # Process results for each repository
                for i, similarity in enumerate(similarities):
                    if similarity >= self.MIN_CONFIDENCE_THRESHOLD:
                        all_results[i].append({
                            'topic_id': topic_id,
                            'confidence_score': similarity
                        })
                        
                        # Handle parent topics with confidence propagation
                        parent_topics = await self.get_parent_topics(topic_id)
                        for parent_id in parent_topics:
                            # Calculate parent confidence based on:
                            # 1. Child confidence
                            # 2. Number of relevant children
                            # 3. Hierarchy level
                            child_confidences = [
                                c['confidence_score'] for c in all_results[i]
                                if c['topic_id'] in self.FIXED_CATEGORIES and
                                self.FIXED_CATEGORIES[c['topic_id']]['parent_id'] == parent_id
                            ]
                            
                            if child_confidences:
                                # Parent confidence increases with more relevant children
                                parent_confidence = min(
                                    similarity * (1.0 + 0.1 * len(child_confidences)),
                                    1.0
                                )
                                
                                # Add parent topic if it meets threshold
                                if parent_confidence >= self.MIN_CONFIDENCE_THRESHOLD:
                                    all_results[i].append({
                                        'topic_id': parent_id,
                                        'confidence_score': parent_confidence
                                    })

            # Post-process results for each repository
            unique_results = []
            for repo_results in all_results:
                # Sort by confidence score
                sorted_results = sorted(
                    repo_results,
                    key=lambda x: x['confidence_score'],
                    reverse=True
                )
                
                # Remove duplicates while keeping highest confidence score
                seen_topics = set()
                unique_topics = []
                for topic in sorted_results:
                    if topic['topic_id'] not in seen_topics:
                        seen_topics.add(topic['topic_id'])
                        unique_topics.append(topic)
                
                unique_results.append(unique_topics)

            logger.info(
                f"Analyzed topics for {len(repositories)} repositories in batch"
            )
            return unique_results

        except Exception as e:
            logger.error(f"Error analyzing topics batch: {str(e)}")
            raise

    async def analyze_repository_topics(
        self,
        repository: Dict
    ) -> List[Dict[str, float]]:
        """
        Analyze a single repository and determine relevant topics.
        Uses batch processing internally for efficiency.

        Args:
            repository: Repository data including description

        Returns:
            List of topics with confidence scores

        Raises:
            ValueError: If repository data is invalid
        """
        results = await self.analyze_repositories_batch([repository])
        return results[0] if results else []
