"""
Consensus-based categorization system implementing multiple specialized agents
that collaborate to provide accurate and validated repository categorization.
"""
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from openai import OpenAI
from pydantic import BaseModel
from models.curation_models import (
    CategoryHierarchy, 
    EnhancedCurationDetails,
    HistoricalDecision,
    RepositoryHistory
)
from models.repo_models import RepoDetails
from agents.base_agent import BaseAgent

class CategoryResponse(BaseModel):
    categories: List[CategoryHierarchy]

class CategoryAgent(BaseAgent):
    """Agent responsible for initial category generation"""
    
    def __init__(self, client: Optional[Union[OpenAI, Any]] = None):
        super().__init__("category_agent", client)
    
    def execute(self, repo: RepoDetails) -> List[CategoryHierarchy]:
        """Generate initial categories for a repository"""
        return self.categorize(repo)
    
    def categorize(self, repo: RepoDetails) -> List[CategoryHierarchy]:
        """Generate initial categories using LLM"""
        prompt = f"""
        Please categorize this GitHub repository:
        Name: {repo.name}
        Description: {repo.description}
        Topics: {', '.join(repo.topics) if repo.topics else 'None'}
        Language: {repo.language}
        Stars: {repo.stargazers_count}
        """
        
        try:
            completion = self.client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": "You are a repository categorization expert. Analyze GitHub repositories and categorize them into appropriate main categories and subcategories."},
                    {"role": "user", "content": prompt}
                ],
                response_format=CategoryResponse,
                max_tokens=500
            )
            return completion.choices[0].message.parsed.categories
        except Exception as e:
            # Fallback categorization if parsing fails
            return [CategoryHierarchy(
                main_category="Uncategorized",
                subcategory="General",
                confidence=0.5,
                reasoning="Failed to parse LLM response"
            )]

class ReviewAgent(BaseAgent):
    """Agent responsible for reviewing and refining categories"""
    
    def __init__(self, client: Optional[Union[OpenAI, Any]] = None):
        super().__init__("review_agent", client)
    
    def execute(self, repo: RepoDetails, initial_categories: List[CategoryHierarchy]) -> List[CategoryHierarchy]:
        """Review and refine the initial categories"""
        return self.review(repo, initial_categories)
    
    def review(self, repo: RepoDetails, initial_categories: List[CategoryHierarchy]) -> List[CategoryHierarchy]:
        """Review categories using LLM"""
        initial_cats_str = "\n".join([
            f"- {cat.main_category}/{cat.subcategory} (Confidence: {cat.confidence})\n  Reason: {cat.reasoning}"
            for cat in initial_categories
        ])
        
        prompt = f"""
        Please review these category assignments for the repository:
        Name: {repo.name}
        Description: {repo.description}
        Topics: {', '.join(repo.topics) if repo.topics else 'None'}
        
        Initial Categories:
        {initial_cats_str}
        """
        
        try:
            completion = self.client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": "You are a repository review expert. Validate and refine category assignments for GitHub repositories."},
                    {"role": "user", "content": prompt}
                ],
                response_format=CategoryResponse,
                max_tokens=500
            )
            return completion.choices[0].message.parsed.categories
        except Exception:
            # Return original categories if parsing fails
            return initial_categories

class ValidationAgent(BaseAgent):
    """Agent responsible for validating categories against historical decisions"""
    
    def __init__(self, client: Optional[Union[OpenAI, Any]] = None):
        super().__init__("validation_agent", client)
    
    def execute(
        self, 
        repo: RepoDetails,
        categories: List[CategoryHierarchy],
        historical_data: RepositoryHistory
    ) -> List[CategoryHierarchy]:
        """Validate categories against historical decisions"""
        return self.validate(repo, categories, historical_data)
    
    def validate(
        self, 
        repo: RepoDetails,
        categories: List[CategoryHierarchy],
        historical_data: RepositoryHistory
    ) -> List[CategoryHierarchy]:
        """Validate categories using LLM and historical data"""
        if not historical_data.decisions:
            return categories

        # Format historical decisions
        history_str = ""
        if historical_data.latest_decision:
            cats = historical_data.latest_decision.categories
            history_str = "\n".join([
                f"- {cat.main_category}/{cat.subcategory} (Confidence: {cat.confidence})"
                for cat in cats
            ])
        
        current_cats_str = "\n".join([
            f"- {cat.main_category}/{cat.subcategory} (Confidence: {cat.confidence})\n  Reason: {cat.reasoning}"
            for cat in categories
        ])
        
        prompt = f"""
        Please validate these category assignments considering historical data:
        
        Repository:
        Name: {repo.name}
        Description: {repo.description}
        
        Current Categories:
        {current_cats_str}
        
        Historical Categories:
        {history_str}
        
        Historical Stability Metrics:
        {historical_data.statistics if historical_data.statistics else 'No statistics available'}
        """
        
        try:
            completion = self.client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": "You are a repository validation expert. Validate category assignments considering historical decisions."},
                    {"role": "user", "content": prompt}
                ],
                response_format=CategoryResponse,
                max_tokens=500
            )
            return completion.choices[0].message.parsed.categories
        except Exception:
            # Return original categories if parsing fails
            return categories

class SynthesisResponse(BaseModel):
    tags: List[str]
    popularity_score: float
    trending_score: float
    synthesis_confidence: float

class SynthesisAgent(BaseAgent):
    """Agent responsible for synthesizing final categorization results"""
    
    def __init__(self, client: Optional[Union[OpenAI, Any]] = None):
        super().__init__("synthesis_agent", client)
    
    def execute(
        self,
        repo: RepoDetails,
        categories: List[CategoryHierarchy],
        agent_decisions: Dict[str, Any]
    ) -> EnhancedCurationDetails:
        """Synthesize final categorization results"""
        return self.synthesize(repo, categories, agent_decisions)
    
    def synthesize(
        self,
        repo: RepoDetails,
        categories: List[CategoryHierarchy],
        agent_decisions: Dict[str, Any]
    ) -> EnhancedCurationDetails:
        """Synthesize results using LLM"""
        cats_str = "\n".join([
            f"- {cat.main_category}/{cat.subcategory} (Confidence: {cat.confidence})\n  Reason: {cat.reasoning}"
            for cat in categories
        ])
        
        prompt = f"""
        Please synthesize the final categorization result:
        
        Repository Metrics:
        - Stars: {repo.stargazers_count}
        - Forks: {repo.forks_count}
        - Activity Level: {repo.activity_level}
        - Star Growth Rate: {repo.star_growth_rate}
        
        Categories:
        {cats_str}
        
        Agent Decisions:
        {agent_decisions}
        """
        
        try:
            completion = self.client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": "You are a synthesis expert. Analyze multiple agent decisions and create a final enhanced curation result."},
                    {"role": "user", "content": prompt}
                ],
                response_format=SynthesisResponse,
                max_tokens=500
            )
            result = completion.choices[0].message.parsed
            return EnhancedCurationDetails(
                tags=result.tags,
                popularity_score=result.popularity_score,
                trending_score=result.trending_score,
                categories=categories,
                consensus_data={
                    "agent_decisions": agent_decisions,
                    "synthesis_confidence": result.synthesis_confidence
                }
            )
        except Exception:
            # Fallback synthesis if parsing fails
            return EnhancedCurationDetails(
                tags=[cat.main_category.lower() for cat in categories],
                popularity_score=0.5,
                trending_score=0.5,
                categories=categories,
                consensus_data={
                    "agent_decisions": agent_decisions,
                    "synthesis_confidence": 0.5
                }
            )

class ConsensusManager:
    """Manages the multi-agent consensus process for repository categorization"""
    
    def __init__(self, client: Optional[Union[OpenAI, Any]] = None):
        self.client = client
        self.category_agent = CategoryAgent(client)
        self.review_agent = ReviewAgent(client)
        self.validation_agent = ValidationAgent(client)
        self.synthesis_agent = SynthesisAgent(client)
        self.historical_data: Dict[str, RepositoryHistory] = {}
    
    def get_consensus(self, repo: RepoDetails) -> EnhancedCurationDetails:
        """
        Orchestrate the consensus process to categorize a repository
        
        Args:
            repo: Repository details to categorize
            
        Returns:
            EnhancedCurationDetails with consensus-based categorization
        """
        # Get or create repository history
        repo_history = self.historical_data.get(repo.id)
        if not repo_history:
            repo_history = RepositoryHistory(repository_id=repo.id)
            self.historical_data[repo.id] = repo_history
        
        # Step 1: Initial categorization
        initial_categories = self.category_agent.execute(repo)
        
        # Step 2: Review and refinement
        reviewed_categories = self.review_agent.execute(repo, initial_categories)
        
        # Step 3: Historical validation
        validated_categories = self.validation_agent.execute(
            repo,
            reviewed_categories,
            repo_history
        )
        
        # Step 4: Final synthesis
        agent_decisions = {
            "category_agent": {
                "categories": [c.model_dump() for c in initial_categories],
                "confidence": sum(c.confidence for c in initial_categories) / len(initial_categories)
            },
            "review_agent": {
                "categories": [c.model_dump() for c in reviewed_categories],
                "confidence": sum(c.confidence for c in reviewed_categories) / len(reviewed_categories)
            },
            "validation_agent": {
                "categories": [c.model_dump() for c in validated_categories],
                "confidence": sum(c.confidence for c in validated_categories) / len(validated_categories)
            }
        }
        
        result = self.synthesis_agent.execute(repo, validated_categories, agent_decisions)
        
        # Record the decision in history
        historical_decision = HistoricalDecision(
            categories=validated_categories,
            agent_decisions=agent_decisions,
            version=result.version,
            metadata={
                "repo_updated_at": repo.updated_at,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count
            }
        )
        repo_history.add_decision(historical_decision)
        
        return result
