"""Pipeline stage for generating README content using LLM agent"""
from typing import Any, Dict, List
import logging
from datetime import datetime
from crewai import Agent

from models.flow_state import FlowState, RepoAnalysis, ReadmeState
from processing.pipeline_stage import PipelineStage, PipelineResult
from db.database import DatabaseManager
from config.logging_config import setup_logging

# Set up logging
logger = setup_logging("pipeline.readme")

class ReadmeStage(PipelineStage):
    """Pipeline stage for generating README content"""
    
    def __init__(self, name: str, agent: Agent):
        """Initialize README stage
        
        Args:
            name: Stage name
            agent: CrewAI agent for content generation
        """
        super().__init__(name)
        self.agent = agent
        self.db_manager = DatabaseManager()  # Use singleton instance
    
    def process(self, data: List[RepoAnalysis], state: FlowState) -> PipelineResult:
        """Generate README content using analyzed repositories
        
        Args:
            data: List of analyzed repositories
            state: Current flow state
            
        Returns:
            PipelineResult with generated content
        """
        try:
            # Create new batch
            batch_id = self.db_manager.create_batch('readme')
            self.logger.info(f"Created new README generation batch {batch_id}")
            
            try:
                # Update batch status
                self.db_manager.update_batch_status(batch_id, 'processing')
                
                # Organize repositories by category
                categories = self._organize_categories(data)
                
                # Generate content using agent
                self.logger.info("Generating README content")
                agent_result = self.agent.execute({
                    'task': 'generate_readme',
                    'categories': categories,
                    'repo_count': len(data),
                    'prompt': self._prepare_agent_prompt(categories, len(data))
                })
                
                # Extract content and TOC
                content = agent_result['content']
                toc_items = agent_result.get('toc_items', [])
                
                # Validate generated content
                if not self._validate_content(content):
                    raise ValueError("Generated content validation failed")
                
                # Update state
                state.update_readme_state(categories, content)
                state.readme.toc_items = toc_items
                state.readme.last_updated = datetime.now()
                
                # Write content to file
                self._write_readme(content)
                
                # Update batch status
                self.db_manager.update_batch_status(batch_id, 'completed')
                
                # Return success result
                return self._create_success_result(
                    processed_count=1,
                    data={
                        'batch_id': batch_id,
                        'content': content,
                        'toc_items': toc_items,
                        'categories': len(categories)
                    }
                )
                
            except Exception as e:
                # Update batch status on error
                error_msg = f"Error generating README: {str(e)}"
                self.db_manager.update_batch_status(batch_id, 'failed', error=error_msg)
                raise
            
        except Exception as e:
            error_msg = f"Error in README generation: {str(e)}"
            self.logger.exception(error_msg)
            return self._create_error_result(error_msg)
    
    def _validate_content(self, content: str) -> bool:
        """Validate generated README content
        
        Args:
            content: Generated content to validate
            
        Returns:
            True if content is valid, False otherwise
        """
        if not content:
            self.logger.error("Generated content is empty")
            return False
        
        required_sections = [
            "# GitHub GenAI List",
            "## Table of Contents",
            "## Introduction",
        ]
        
        for section in required_sections:
            if section not in content:
                self.logger.error(f"Missing required section: {section}")
                return False
        
        return True
    
    def _organize_categories(self, analyses: List[RepoAnalysis]) -> Dict:
        """Organize repositories by category and subcategory
        
        Args:
            analyses: List of repository analyses
            
        Returns:
            Dictionary of categorized repositories
        """
        categories = {}
        
        for analysis in analyses:
            category = analysis.categorization.category
            subcategory = analysis.categorization.subcategory
            
            # Initialize category if needed
            if category not in categories:
                categories[category] = {}
            
            # Initialize subcategory if needed
            if subcategory:
                if subcategory not in categories[category]:
                    categories[category][subcategory] = []
                categories[category][subcategory].append(analysis.repo_data)
            else:
                # Use 'General' subcategory for repos without subcategory
                if 'General' not in categories[category]:
                    categories[category]['General'] = []
                categories[category]['General'].append(analysis.repo_data)
        
        return categories
    
    def _prepare_agent_prompt(self, categories: Dict, repo_count: int) -> str:
        """Prepare prompt for README generation
        
        Args:
            categories: Dictionary of categorized repositories
            repo_count: Total number of repositories
            
        Returns:
            Formatted prompt for agent
        """
        prompt = (
            f"Generate a README.md file for a curated list of {repo_count} "
            "GitHub repositories related to AI, ML, and Data Science.\n\n"
            
            "The README should include:\n"
            "1. An introduction explaining the purpose\n"
            "2. A table of contents\n"
            "3. Organized sections for each category\n"
            "4. Proper markdown formatting\n"
            "5. Links to repositories\n"
            "6. Brief descriptions\n\n"
            
            "Categories and repositories:\n"
        )
        
        for category, subcategories in categories.items():
            prompt += f"\n{category}:\n"
            for subcategory, repos in subcategories.items():
                if subcategory != 'General':
                    prompt += f"  {subcategory}:\n"
                for repo in repos:
                    prompt += (
                        f"    - {repo.full_name}\n"
                        f"      {repo.description}\n"
                        f"      Topics: {', '.join(repo.topics)}\n"
                    )
        
        return prompt
    
    def _write_readme(self, content: str):
        """Write content to README file
        
        Args:
            content: README content to write
        """
        try:
            self.logger.info("Writing README content to file")
            with open('README.md', 'w') as f:
                f.write(content)
            self.logger.info("Successfully wrote README content")
            
        except Exception as e:
            self.logger.error(f"Error writing README: {str(e)}")
            raise
    
    def execute(self, data: List[RepoAnalysis], state: FlowState) -> PipelineResult:
        """Execute README stage with validation
        
        Args:
            data: List of analyzed repositories
            state: Current flow state
            
        Returns:
            PipelineResult with execution results
        """
        # Validate input
        if not data:
            error_msg = "No analyzed repositories provided"
            state.update_processing_state(error=error_msg)
            return self._create_error_result(error_msg)
        
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
            error_msg = f"Error executing README stage: {str(e)}"
            self.logger.exception(error_msg)
            state.update_processing_state(error=error_msg)
            return self._create_error_result(error_msg)
    
    def _cleanup_incomplete_batches(self):
        """Clean up any incomplete README generation batches"""
        try:
            self.logger.info("Cleaning up incomplete README batches")
            
            # Get incomplete batches
            batch_status = self.db_manager.get_batch_status('readme')
            incomplete_batches = [
                batch_id for batch_id, status in batch_status.items()
                if status['status'] not in ('completed', 'failed', 'cleaned_up')
            ]
            
            for batch_id in incomplete_batches:
                try:
                    # Mark batch as cleaned up
                    self.db_manager.update_batch_status(batch_id, 'cleaned_up')
                    self.logger.info(f"Marked README batch {batch_id} as cleaned up")
                except Exception as e:
                    self.logger.error(f"Error cleaning up README batch {batch_id}: {str(e)}")
            
            self.logger.info("README batch cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during README batch cleanup: {str(e)}")
