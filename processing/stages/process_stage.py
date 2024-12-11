"""Pipeline stage for processing repositories in batches"""
from typing import Any, Dict, List
import logging
from datetime import datetime

from models.flow_state import FlowState
from models.github_repo_data import GitHubRepoData
from processing.pipeline_stage import BatchProcessingStage, PipelineResult
from db.database import DatabaseManager
from config.logging_config import setup_logging

# Set up logging
logger = setup_logging("pipeline.process")

class ProcessStage(BatchProcessingStage):
    """Pipeline stage for processing repositories in batches"""
    
    def __init__(self, name: str, batch_size: int = 10):
        """Initialize process stage
        
        Args:
            name: Stage name
            batch_size: Size of batches to process
        """
        super().__init__(name, batch_size)
        self.db_manager = DatabaseManager()  # Use singleton instance
    
    def process_batch(self, batch: List[GitHubRepoData], state: FlowState) -> PipelineResult:
        """Process a batch of repositories
        
        Args:
            batch: List of repositories to process
            state: Current flow state
            
        Returns:
            PipelineResult with processing results
        """
        try:
            # Create new batch
            batch_id = self.db_manager.create_batch('process')
            self.logger.info(f"Created new batch {batch_id}")
            
            try:
                # Store in database
                self.logger.info(f"Storing batch of {len(batch)} repositories")
                self.db_manager.store_raw_repos(batch, source='starred', batch_id=batch_id)
                
                # Update processing state
                state.update_processing_state(processed=len(batch))
                
                # Update batch status
                self.db_manager.update_batch_status(batch_id, 'completed')
                
                # Return success result
                return self._create_success_result(
                    processed_count=len(batch),
                    data={'batch_id': batch_id, 'repos': batch}
                )
                
            except Exception as e:
                # Update batch status on error
                error_msg = f"Error processing batch: {str(e)}"
                self.db_manager.update_batch_status(batch_id, 'failed', error=error_msg)
                raise
            
        except Exception as e:
            error_msg = f"Error processing batch: {str(e)}"
            self.logger.exception(error_msg)
            
            # Update state with error
            state.update_processing_state(failed=len(batch), error=error_msg)
            
            return self._create_error_result(error_msg)
    
    def _verify_database(self) -> bool:
        """Verify database connection and tables
        
        Returns:
            True if verification succeeds, False otherwise
        """
        try:
            # Verify database state
            db_state = self.db_manager.verify_state()
            
            # Check required tables exist
            required_tables = ['raw_repositories', 'batch_processing', 'flow_state']
            for table in required_tables:
                if not db_state['tables_exist'].get(table, False):
                    self.logger.error(f"Required table {table} does not exist")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Database verification failed: {str(e)}")
            return False
    
    def execute(self, data: List[GitHubRepoData], state: FlowState) -> PipelineResult:
        """Execute processing stage with database verification
        
        Args:
            data: List of repositories to process
            state: Current flow state
            
        Returns:
            PipelineResult with execution results
        """
        # Verify database
        if not self._verify_database():
            error_msg = "Database verification failed"
            state.update_processing_state(error=error_msg)
            return self._create_error_result(error_msg)
        
        try:
            # Execute stage
            result = super().execute(data, state)
            
            # Cleanup on success
            if result.success:
                self._cleanup_database()
            
            return result
            
        except Exception as e:
            error_msg = f"Error executing process stage: {str(e)}"
            self.logger.exception(error_msg)
            state.update_processing_state(error=error_msg)
            return self._create_error_result(error_msg)
    
    def _cleanup_database(self):
        """Clean up database after processing
        
        This ensures any unprocessed repositories are marked as processed
        and updates batch statuses appropriately.
        """
        try:
            self.logger.info("Starting database cleanup")
            
            # Get incomplete batches
            batch_status = self.db_manager.get_batch_status('process')
            incomplete_batches = [
                batch_id for batch_id, status in batch_status.items()
                if status['status'] not in ('completed', 'failed', 'cleaned_up')
            ]
            
            for batch_id in incomplete_batches:
                try:
                    # Mark batch as cleaned up
                    self.db_manager.update_batch_status(batch_id, 'cleaned_up')
                    self.logger.info(f"Marked batch {batch_id} as cleaned up")
                except Exception as e:
                    self.logger.error(f"Error cleaning up batch {batch_id}: {str(e)}")
            
            self.logger.info("Database cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during database cleanup: {str(e)}")
