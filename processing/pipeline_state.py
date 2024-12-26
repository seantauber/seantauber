"""Pipeline state tracking for parallel processing."""

import logging
from datetime import datetime, UTC
from threading import Lock
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class PipelineState:
    """Tracks state and errors for pipeline batches."""
    
    def __init__(self):
        """Initialize pipeline state tracker."""
        self.batches: Dict[str, Dict] = {}
        self.lock = Lock()
    
    def start_batch(self, batch_id: str, stage: str):
        """Start tracking a new batch.
        
        Args:
            batch_id: Unique identifier for the batch
            stage: Pipeline stage name (e.g. 'content_extraction')
        """
        with self.lock:
            self.batches[batch_id] = {
                'stage': stage,
                'status': 'running',
                'started_at': datetime.now(UTC).isoformat(),
                'completed_at': None,
                'errors': [],
                'processed_items': 0,
                'failed_items': 0
            }
            logger.info(f"Started batch {batch_id} in stage {stage}")
    
    def complete_batch(self, batch_id: str, processed_count: int = 0):
        """Mark a batch as completed.
        
        Args:
            batch_id: Batch identifier
            processed_count: Number of successfully processed items
        """
        with self.lock:
            if batch_id in self.batches:
                self.batches[batch_id].update({
                    'status': 'completed',
                    'completed_at': datetime.now(UTC).isoformat(),
                    'processed_items': processed_count
                })
                logger.info(
                    f"Completed batch {batch_id} with {processed_count} items"
                )
    
    def fail_batch(
        self,
        batch_id: str,
        error: Exception,
        failed_items: Optional[List[str]] = None
    ):
        """Record a batch failure.
        
        Args:
            batch_id: Batch identifier
            error: Exception that caused the failure
            failed_items: Optional list of failed item IDs
        """
        with self.lock:
            if batch_id in self.batches:
                self.batches[batch_id].update({
                    'status': 'failed',
                    'completed_at': datetime.now(UTC).isoformat(),
                    'failed_items': len(failed_items or [])
                })
                self.batches[batch_id]['errors'].append(str(error))
                
                if failed_items:
                    logger.error(
                        f"Batch {batch_id} failed with {len(failed_items)} items: {str(error)}"
                    )
                else:
                    logger.error(f"Batch {batch_id} failed: {str(error)}")
    
    def get_batch_status(self, batch_id: str) -> Optional[Dict]:
        """Get current status of a batch.
        
        Args:
            batch_id: Batch identifier
            
        Returns:
            Dictionary with batch status information or None if not found
        """
        with self.lock:
            return self.batches.get(batch_id)
    
    def get_stage_status(self, stage: str) -> Dict:
        """Get status summary for all batches in a stage.
        
        Args:
            stage: Pipeline stage name
            
        Returns:
            Dictionary with stage statistics
        """
        with self.lock:
            stage_batches = [
                b for b in self.batches.values()
                if b['stage'] == stage
            ]
            
            return {
                'total_batches': len(stage_batches),
                'completed': len([b for b in stage_batches if b['status'] == 'completed']),
                'failed': len([b for b in stage_batches if b['status'] == 'failed']),
                'running': len([b for b in stage_batches if b['status'] == 'running']),
                'total_processed': sum(b.get('processed_items', 0) for b in stage_batches),
                'total_failed': sum(b.get('failed_items', 0) for b in stage_batches),
                'errors': [
                    e for b in stage_batches
                    for e in b.get('errors', [])
                ]
            }
    
    def clear_stage(self, stage: str):
        """Clear all batch data for a stage.
        
        Args:
            stage: Pipeline stage name to clear
        """
        with self.lock:
            self.batches = {
                bid: data
                for bid, data in self.batches.items()
                if data['stage'] != stage
            }
            logger.info(f"Cleared state data for stage: {stage}")
