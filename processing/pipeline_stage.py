"""Base class and utilities for pipeline stages"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging
from models.flow_state import FlowState
from config.logging_config import setup_logging

# Set up logging
logger = setup_logging("pipeline")

class PipelineResult:
    """Result object for pipeline stage execution"""
    def __init__(
        self,
        success: bool,
        stage_name: str,
        processed_count: int = 0,
        error: Optional[str] = None,
        data: Any = None
    ):
        self.success = success
        self.stage_name = stage_name
        self.processed_count = processed_count
        self.error = error
        self.data = data
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert result to dictionary"""
        return {
            'success': self.success,
            'stage_name': self.stage_name,
            'processed_count': self.processed_count,
            'error': self.error,
            'data': self.data,
            'timestamp': self.timestamp.isoformat()
        }

class PipelineStage(ABC):
    """Base class for pipeline stages"""
    
    def __init__(self, name: str):
        """Initialize pipeline stage
        
        Args:
            name: Name of the pipeline stage
        """
        self.name = name
        self.logger = logging.getLogger(f"pipeline.{name}")
    
    @abstractmethod
    def process(self, data: Any, state: FlowState) -> PipelineResult:
        """Process data and update flow state
        
        Args:
            data: Input data for the stage
            state: Current flow state
            
        Returns:
            PipelineResult with processing results
        """
        pass
    
    def execute(self, data: Any, state: FlowState) -> PipelineResult:
        """Execute the pipeline stage with error handling
        
        Args:
            data: Input data for the stage
            state: Current flow state
            
        Returns:
            PipelineResult with execution results
        """
        self.logger.info(f"Starting pipeline stage: {self.name}")
        try:
            # Execute stage processing
            result = self.process(data, state)
            
            # Log result
            if result.success:
                self.logger.info(
                    f"Successfully completed stage {self.name} - "
                    f"Processed: {result.processed_count}"
                )
            else:
                self.logger.error(
                    f"Stage {self.name} failed - Error: {result.error}"
                )
            
            return result
            
        except Exception as e:
            error_msg = f"Error in pipeline stage {self.name}: {str(e)}"
            self.logger.exception(error_msg)
            return PipelineResult(
                success=False,
                stage_name=self.name,
                error=error_msg
            )
    
    def _create_success_result(
        self,
        processed_count: int,
        data: Any = None
    ) -> PipelineResult:
        """Create a success result
        
        Args:
            processed_count: Number of items processed
            data: Optional data to include in result
            
        Returns:
            PipelineResult indicating success
        """
        return PipelineResult(
            success=True,
            stage_name=self.name,
            processed_count=processed_count,
            data=data
        )
    
    def _create_error_result(
        self,
        error: str,
        processed_count: int = 0,
        data: Any = None
    ) -> PipelineResult:
        """Create an error result
        
        Args:
            error: Error message
            processed_count: Number of items processed before error
            data: Optional data to include in result
            
        Returns:
            PipelineResult indicating error
        """
        return PipelineResult(
            success=False,
            stage_name=self.name,
            processed_count=processed_count,
            error=error,
            data=data
        )

class BatchProcessingStage(PipelineStage):
    """Base class for stages that process data in batches"""
    
    def __init__(self, name: str, batch_size: int = 10):
        """Initialize batch processing stage
        
        Args:
            name: Name of the pipeline stage
            batch_size: Size of batches to process
        """
        super().__init__(name)
        self.batch_size = batch_size
    
    def process_batch(self, batch: List[Any], state: FlowState) -> PipelineResult:
        """Process a single batch of data
        
        Args:
            batch: Batch of data to process
            state: Current flow state
            
        Returns:
            PipelineResult with batch processing results
        """
        pass
    
    def process(self, data: List[Any], state: FlowState) -> PipelineResult:
        """Process all data in batches
        
        Args:
            data: List of data to process in batches
            state: Current flow state
            
        Returns:
            PipelineResult with overall processing results
        """
        total_processed = 0
        total_errors = []
        
        # Process in batches
        for i in range(0, len(data), self.batch_size):
            batch = data[i:i + self.batch_size]
            self.logger.info(f"Processing batch {i//self.batch_size + 1}")
            
            # Process batch
            result = self.process_batch(batch, state)
            
            # Track results
            total_processed += result.processed_count
            if not result.success:
                total_errors.append(result.error)
        
        # Return overall result
        if not total_errors:
            return self._create_success_result(total_processed)
        else:
            return self._create_error_result(
                error=f"Batch processing errors: {'; '.join(total_errors)}",
                processed_count=total_processed
            )
