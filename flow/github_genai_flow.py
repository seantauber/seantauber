"""Main flow implementation for GitHub GenAI List processing"""
from crewai.flow.flow import Flow, listen, start, router, and_
from crewai import Agent
from typing import Dict, List, Optional
import logging
from datetime import datetime
import yaml

from models.flow_state import FlowState
from models.github_repo_data import GitHubRepoData
from processing.pipeline_stage import PipelineResult
from config.logging_config import setup_logging
from config.config_manager import AppConfig
from db.database import DatabaseManager

# Set up logging
logger = setup_logging("flow")

class GitHubGenAIFlow(Flow[FlowState]):
    """Main flow for GitHub GenAI List processing"""
    
    def __init__(self, config: AppConfig):
        """Initialize the flow
        
        Args:
            config: Application configuration
        """
        super().__init__()
        self.config = config
        self.logger = logger
        
        # Initialize database manager
        self.db = DatabaseManager()
        
        # Load existing state or create new
        saved_state = self.db.load_flow_state()
        self.state = saved_state if saved_state else FlowState()
        
        # Load agent configurations
        self.agents_config = self._load_agent_configs()
        
        self.logger.info("Initialized GitHubGenAIFlow")
    
    def _load_agent_configs(self) -> Dict:
        """Load agent configurations from yaml"""
        try:
            with open('config/agents.yaml', 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Error loading agent configs: {str(e)}")
            raise
    
    def _persist_state(self) -> bool:
        """Persist current flow state to database"""
        try:
            success = self.db.persist_flow_state(self.state)
            if success:
                self.logger.info("Successfully persisted flow state")
            else:
                self.logger.error("Failed to persist flow state")
            return success
        except Exception as e:
            self.logger.error(f"Error persisting flow state: {str(e)}")
            return False
    
    def get_analyzer_agent(self) -> Agent:
        """Get analyzer agent for repo categorization"""
        return Agent(
            config=self.agents_config['analyzer'],
            verbose=True,
            tools=[self.categorize_tool]
        )
    
    def get_content_generator(self) -> Agent:
        """Get content generator agent for README generation"""
        return Agent(
            config=self.agents_config['content_generator'],
            verbose=True,
            tools=[self.get_current_date_tool]
        )
    
    @start()
    def fetch_repos(self) -> PipelineResult:
        """Start by fetching repos from GitHub"""
        self.logger.info("Starting repo fetch stage")
        
        try:
            # Initialize fetch stage
            from processing.stages.fetch_stage import FetchStage
            fetch_stage = FetchStage(
                name="fetch_repos",
                config=self.config
            )
            
            # Execute fetch
            result = fetch_stage.execute(None, self.state)
            
            if result.success:
                self.logger.info(
                    f"Successfully fetched {result.processed_count} repos"
                )
                # Persist state after successful fetch
                if not self._persist_state():
                    self.logger.warning("Failed to persist state after fetch")
            else:
                self.logger.error(f"Fetch stage failed: {result.error}")
            
            return result
            
        except Exception as e:
            self.logger.exception("Error in fetch stage")
            return PipelineResult(
                success=False,
                stage_name="fetch_repos",
                error=str(e)
            )
    
    @router(fetch_repos)
    def handle_fetch_result(self, fetch_result: PipelineResult) -> str:
        """Route based on fetch result"""
        if fetch_result.success:
            return "success"
        else:
            return "error"
    
    @listen("error")
    def handle_error(self):
        """Handle pipeline errors"""
        self.logger.error("Pipeline failed, cleaning up state")
        self.cleanup_old_states()
        return PipelineResult(
            success=False,
            stage_name="error_handler",
            error="Pipeline failed, see logs for details"
        )
    
    @listen("success")
    def process_repos(self) -> PipelineResult:
        """Process fetched repos"""
        self.logger.info("Starting repo processing stage")
        
        try:
            # Initialize processing stage
            from processing.stages.process_stage import ProcessStage
            process_stage = ProcessStage(
                name="process_repos",
                batch_size=self.config.batch_size
            )
            
            # Execute processing
            result = process_stage.execute(
                self.state.raw_repos,
                self.state
            )
            
            if result.success:
                self.logger.info(
                    f"Successfully processed {result.processed_count} repos"
                )
                # Persist state after successful processing
                if not self._persist_state():
                    self.logger.warning("Failed to persist state after processing")
            else:
                self.logger.error(f"Processing stage failed: {result.error}")
            
            return result
            
        except Exception as e:
            self.logger.exception("Error in processing stage")
            return PipelineResult(
                success=False,
                stage_name="process_repos",
                error=str(e)
            )
    
    @listen(process_repos)
    def analyze_repos(self, process_result: PipelineResult) -> PipelineResult:
        """Analyze processed repos using LLM agent"""
        self.logger.info("Starting repo analysis stage")
        
        if not process_result.success:
            self.logger.error("Skipping analysis due to processing failure")
            return process_result
        
        try:
            # Initialize analysis stage with agent
            from processing.stages.analysis_stage import AnalysisStage
            analysis_stage = AnalysisStage(
                name="analyze_repos",
                agent=self.get_analyzer_agent(),
                batch_size=10  # Small batch size for LLM context
            )
            
            # Execute analysis
            result = analysis_stage.execute(
                self.state.raw_repos,
                self.state
            )
            
            if result.success:
                self.logger.info(
                    f"Successfully analyzed {result.processed_count} repos"
                )
                # Persist state after successful analysis
                if not self._persist_state():
                    self.logger.warning("Failed to persist state after analysis")
            else:
                self.logger.error(f"Analysis stage failed: {result.error}")
            
            return result
            
        except Exception as e:
            self.logger.exception("Error in analysis stage")
            return PipelineResult(
                success=False,
                stage_name="analyze_repos",
                error=str(e)
            )
    
    @listen(and_(process_repos, analyze_repos))
    def generate_readme(self) -> PipelineResult:
        """Generate README content after both processing and analysis complete"""
        self.logger.info("Starting README generation stage")
        
        try:
            # Initialize README stage with agent
            from processing.stages.readme_stage import ReadmeStage
            readme_stage = ReadmeStage(
                name="generate_readme",
                agent=self.get_content_generator()
            )
            
            # Execute README generation
            result = readme_stage.execute(
                self.state.analyzed_repos,
                self.state
            )
            
            if result.success:
                self.logger.info("Successfully generated README content")
                # Persist state after successful README generation
                if not self._persist_state():
                    self.logger.warning("Failed to persist state after README generation")
            else:
                self.logger.error(f"README generation failed: {result.error}")
            
            return result
            
        except Exception as e:
            self.logger.exception("Error in README generation stage")
            return PipelineResult(
                success=False,
                stage_name="generate_readme",
                error=str(e)
            )
    
    def cleanup_old_states(self, keep_latest: int = 5):
        """Clean up old flow states
        
        Args:
            keep_latest: Number of latest states to keep
        """
        try:
            self.db.cleanup_flow_states(keep_latest)
            self.logger.info(f"Cleaned up old states, keeping {keep_latest} latest")
        except Exception as e:
            self.logger.error(f"Error cleaning up old states: {str(e)}")
    
    def plot(self, filename: str = "github_genai_flow"):
        """Generate a plot of the flow
        
        Args:
            filename: Name of the output file (without extension)
        """
        super().plot(filename)
        self.logger.info(f"Generated flow plot: {filename}.html")
    
    def get_progress(self) -> Dict:
        """Get current flow progress
        
        Returns:
            Dictionary with progress information
        """
        return self.state.get_progress()
