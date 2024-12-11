"""Pipeline stage for analyzing repositories using LLM agent"""
from typing import Any, Dict, List
import logging
from datetime import datetime
from crewai import Agent

from models.flow_state import FlowState, RepoAnalysis, RepoCategorization
from models.github_repo_data import GitHubRepoData
from processing.pipeline_stage import BatchProcessingStage, PipelineResult
from db.database import DatabaseManager
from config.logging_config import setup_logging

# Set up logging
logger = setup_logging("pipeline.analysis")

class AnalysisStage(BatchProcessingStage):
    """Pipeline stage for analyzing repositories using LLM agent"""
    
    def __init__(self, name: str, agent: Agent, batch_size: int = 10):
        """Initialize analysis stage
        
        Args:
            name: Stage name
            agent: CrewAI agent for analysis
            batch_size: Size of batches to process
        """
        super().__init__(name, batch_size)
        self.agent = agent
        self.db_manager = DatabaseManager()  # Use singleton instance
    
    def process_batch(self, batch: List[GitHubRepoData], state: FlowState) -> PipelineResult:
        """Process a batch of repositories using LLM agent
        
        Args:
            batch: List of repositories to analyze
            state: Current flow state
            
        Returns:
            PipelineResult with analysis results
        """
        try:
            # Create new batch
            batch_id = self.db_manager.create_batch('analyze')
            self.logger.info(f"Created new analysis batch {batch_id}")
            
            try:
                # Prepare batch for agent
                repo_data = []
                for repo in batch:
                    repo_data.append({
                        'name': repo.full_name,
                        'description': repo.description,
                        'topics': repo.topics,
                        'language': repo.language,
                        'stars': repo.stargazers_count
                    })
                
                # Update batch status
                self.db_manager.update_batch_status(batch_id, 'processing')
                
                # Call agent for analysis
                self.logger.info(f"Analyzing batch of {len(repo_data)} repositories")
                agent_result = self.agent.execute({
                    'task': 'analyze_repos',
                    'repos': repo_data,
                    'prompt': self._prepare_agent_prompt(repo_data)
                })
                
                # Process agent results
                analyzed_repos = []
                failed_repos = []
                
                for repo, analysis in zip(batch, agent_result['analyses']):
                    try:
                        # Create categorization
                        categorization = RepoCategorization(
                            category=analysis['category'],
                            subcategory=analysis.get('subcategory'),
                            confidence=analysis['confidence'],
                            reasoning=analysis['reasoning']
                        )
                        
                        # Create repo analysis
                        repo_analysis = RepoAnalysis(
                            repo_data=repo,
                            categorization=categorization,
                            quality_score=analysis['quality_score'],
                            relevance_score=analysis['relevance_score']
                        )
                        
                        analyzed_repos.append(repo_analysis)
                        
                    except Exception as e:
                        self.logger.error(f"Error processing analysis for {repo.full_name}: {str(e)}")
                        failed_repos.append(repo.full_name)
                        continue
                
                # Store in database
                if analyzed_repos:
                    self._store_analyses(analyzed_repos, batch_id)
                
                # Update state
                state.update_processing_state(
                    analyzed=len(analyzed_repos),
                    failed=len(failed_repos)
                )
                
                for analysis in analyzed_repos:
                    state.add_analyzed_repo(analysis)
                
                # Update batch status
                if failed_repos:
                    error_msg = f"Failed to analyze repos: {', '.join(failed_repos)}"
                    self.db_manager.update_batch_status(batch_id, 'completed', error=error_msg)
                else:
                    self.db_manager.update_batch_status(batch_id, 'completed')
                
                # Return success result
                return self._create_success_result(
                    processed_count=len(analyzed_repos),
                    data={
                        'batch_id': batch_id,
                        'analyzed': analyzed_repos,
                        'failed': failed_repos
                    }
                )
                
            except Exception as e:
                # Update batch status on error
                error_msg = f"Error analyzing batch: {str(e)}"
                self.db_manager.update_batch_status(batch_id, 'failed', error=error_msg)
                raise
            
        except Exception as e:
            error_msg = f"Error in analysis batch: {str(e)}"
            self.logger.exception(error_msg)
            
            # Update state with error
            state.update_processing_state(
                failed=len(batch),
                error=error_msg
            )
            
            return self._create_error_result(error_msg)
    
    def _store_analyses(self, analyses: List[RepoAnalysis], batch_id: int):
        """Store analyses in database
        
        Args:
            analyses: List of repository analyses to store
            batch_id: ID of the current batch
        """
        try:
            # Convert to database format
            db_analyses = []
            for analysis in analyses:
                db_analyses.append({
                    'raw_repo_id': analysis.repo_data.id,
                    'analysis_data': {
                        'category': analysis.categorization.category,
                        'subcategory': analysis.categorization.subcategory,
                        'confidence': analysis.categorization.confidence,
                        'reasoning': analysis.categorization.reasoning,
                        'quality_score': analysis.quality_score,
                        'relevance_score': analysis.relevance_score,
                        'include': True,  # Default to including in results
                        'justification': analysis.categorization.reasoning
                    }
                })
            
            # Store in database
            self.logger.info(f"Storing {len(db_analyses)} analyses for batch {batch_id}")
            self.db_manager.store_analyzed_repos(db_analyses, batch_id)
            
        except Exception as e:
            self.logger.error(f"Error storing analyses: {str(e)}")
            raise
    
    def _prepare_agent_prompt(self, repos: List[Dict]) -> str:
        """Prepare prompt for agent analysis
        
        Args:
            repos: List of repository data
            
        Returns:
            Formatted prompt for agent
        """
        prompt = (
            "Analyze the following repositories and categorize them based on their purpose, "
            "technology, and relevance to AI/ML/Data Science:\n\n"
        )
        
        for repo in repos:
            prompt += (
                f"Repository: {repo['name']}\n"
                f"Description: {repo['description']}\n"
                f"Topics: {', '.join(repo['topics'])}\n"
                f"Language: {repo['language']}\n"
                f"Stars: {repo['stars']}\n\n"
            )
        
        prompt += (
            "For each repository, provide:\n"
            "1. Main category (e.g., 'Machine Learning', 'Data Science', 'MLOps')\n"
            "2. Subcategory if applicable\n"
            "3. Confidence score (0-1)\n"
            "4. Brief reasoning for categorization\n"
            "5. Quality score (0-1) based on documentation, stars, activity\n"
            "6. Relevance score (0-1) for AI/ML/Data Science field\n"
        )
        
        return prompt
    
    def execute(self, data: List[GitHubRepoData], state: FlowState) -> PipelineResult:
        """Execute analysis stage with agent verification
        
        Args:
            data: List of repositories to analyze
            state: Current flow state
            
        Returns:
            PipelineResult with execution results
        """
        # Verify agent
        if not self.agent:
            error_msg = "Agent not configured"
            state.update_processing_state(error=error_msg)
            return self._create_error_result(error_msg)
        
        try:
            # Execute stage
            result = super().execute(data, state)
            
            # Cleanup on success
            if result.success:
                self._cleanup_incomplete_batches()
            
            return result
            
        except Exception as e:
            error_msg = f"Error executing analysis stage: {str(e)}"
            self.logger.exception(error_msg)
            state.update_processing_state(error=error_msg)
            return self._create_error_result(error_msg)
    
    def _cleanup_incomplete_batches(self):
        """Clean up any incomplete analysis batches"""
        try:
            self.logger.info("Cleaning up incomplete analysis batches")
            
            # Get incomplete batches
            batch_status = self.db_manager.get_batch_status('analyze')
            incomplete_batches = [
                batch_id for batch_id, status in batch_status.items()
                if status['status'] not in ('completed', 'failed', 'cleaned_up')
            ]
            
            for batch_id in incomplete_batches:
                try:
                    # Mark batch as cleaned up
                    self.db_manager.update_batch_status(batch_id, 'cleaned_up')
                    self.logger.info(f"Marked analysis batch {batch_id} as cleaned up")
                except Exception as e:
                    self.logger.error(f"Error cleaning up analysis batch {batch_id}: {str(e)}")
            
            self.logger.info("Analysis batch cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during analysis batch cleanup: {str(e)}")
