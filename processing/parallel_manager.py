"""
Parallel processing manager for handling batch operations on repository data.
Provides functionality for concurrent processing of repository data with status tracking.
"""

from concurrent.futures import ThreadPoolExecutor, Future
from typing import List, Callable, Any, Dict, Optional, Set, Tuple
from datetime import datetime
import time
import logging
import threading
from collections import defaultdict
from db.database import DatabaseManager

class BatchStatus:
    """Status constants for batch processing"""
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    RETRY_QUEUE = 'retry_queue'
    CLEANED_UP = 'cleaned_up'

class ParallelProcessor:
    """
    Manages parallel processing of repository data in batches.
    
    Handles concurrent execution of tasks while tracking batch status
    and managing database interactions for storing results.
    """
    
    def __init__(self, max_workers: int = 4, max_retries: int = 3):
        """
        Initialize the parallel processor.

        Args:
            max_workers (int): Maximum number of concurrent worker threads. Defaults to 4.
            max_retries (int): Maximum number of retry attempts for failed batches. Defaults to 3.
        """
        self.max_workers = max_workers
        self.max_retries = max_retries
        self.db = DatabaseManager()
        self._active_futures: Dict[int, Future] = {}  # batch_id -> Future mapping
        self._failed_batches: Dict[int, Dict] = {}  # Track failed batches with error info
        self._retry_queue: Set[int] = set()  # Queue of batch_ids to retry
        self._error_patterns: Dict[str, int] = defaultdict(int)  # Track error patterns
        self._completed_batches: Set[int] = set()  # Track completed batches
        self._processing_complete = False  # Flag to indicate when processing is done

    def process_batch(self, task_type: str, items: List[Any], 
                     process_fn: Callable, batch_size: int = 10,
                     monitor_progress: bool = True) -> Dict:
        """
        Process items in parallel batches with progress monitoring.

        Args:
            task_type (str): Type of task being processed ('fetch', 'analyze', etc.)
            items (List[Any]): List of items to process
            process_fn (Callable): Function to process each batch
            batch_size (int): Size of each batch. Defaults to 10.
            monitor_progress (bool): Whether to print progress updates. Defaults to True.

        Returns:
            Dict: Summary of processing results
        """
        batches = self._create_batches(items, batch_size)
        total_batches = len(batches)
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all batches for processing
            for batch in batches:
                batch_id = self.db.create_batch(task_type)
                future = executor.submit(self._process_single_batch,
                                      batch, process_fn, batch_id, 0)
                self._active_futures[batch_id] = future

            # Start a separate thread for progress monitoring if requested
            if monitor_progress:
                monitor_thread = threading.Thread(
                    target=self._monitor_batch_progress,
                    args=(task_type, total_batches)
                )
                monitor_thread.daemon = True
                monitor_thread.start()

            # Collect results and handle retries
            results = self._collect_results_with_retry(executor, process_fn)
            
            # Process any remaining retry queue items
            if self._retry_queue:
                retry_results = self._process_retry_queue(executor, process_fn)
                results.extend(retry_results)

            # Signal that processing is complete
            self._processing_complete = True

            # Analyze errors and cleanup failed batches
            self._analyze_errors()
            self._cleanup_failed_batches()
        
        return self._combine_results(results)

    def _process_single_batch(self, batch: List[Any], 
                            process_fn: Callable, batch_id: int,
                            retry_count: int) -> Dict:
        """
        Process a single batch and update its status.

        Args:
            batch (List[Any]): Batch of items to process
            process_fn (Callable): Function to process the batch
            batch_id (int): ID of the current batch
            retry_count (int): Number of times this batch has been retried

        Returns:
            Dict: Results from processing the batch with additional metadata
        """
        try:
            start_time = time.time()
            self.db.update_batch_status(batch_id, BatchStatus.PROCESSING)
            
            result = process_fn(batch, batch_id)
            processing_time = time.time() - start_time
            
            # Add metadata to result
            result.update({
                'batch_id': batch_id,
                'success': True,
                'processing_time': processing_time,
                'retry_count': retry_count,
                'items_processed': len(batch)
            })
            
            self.db.update_batch_status(batch_id, BatchStatus.COMPLETED)
            self._completed_batches.add(batch_id)
            return result
            
        except Exception as e:
            error_msg = f"Batch {batch_id} failed (attempt {retry_count + 1}/{self.max_retries}): {str(e)}"
            self.db.update_batch_status(batch_id, BatchStatus.FAILED, error_msg)
            
            # Track failed batch
            self._failed_batches[batch_id] = {
                'error': str(e),
                'retry_count': retry_count,
                'batch_size': len(batch),
                'timestamp': datetime.now().isoformat(),
                'batch': batch
            }
            
            # Track error pattern
            error_type = type(e).__name__
            self._error_patterns[error_type] += 1
            
            if retry_count < self.max_retries:
                self._retry_queue.add(batch_id)
                return {
                    'batch_id': batch_id,
                    'success': False,
                    'error': error_msg,
                    'retry_count': retry_count,
                    'items_processed': 0,
                    'needs_retry': True
                }
            else:
                return {
                    'batch_id': batch_id,
                    'success': False,
                    'error': error_msg,
                    'retry_count': retry_count,
                    'items_processed': 0,
                    'needs_retry': False
                }

    def _process_retry_queue(self, executor: ThreadPoolExecutor, 
                           process_fn: Callable) -> List[Dict]:
        """
        Process all batches in the retry queue.

        Args:
            executor (ThreadPoolExecutor): The executor handling the batch processing
            process_fn (Callable): The function to process batches

        Returns:
            List[Dict]: Results from retry attempts
        """
        retry_results = []
        while self._retry_queue:
            batch_id = self._retry_queue.pop()
            if batch_id in self._failed_batches:
                failed_info = self._failed_batches[batch_id]
                if failed_info['retry_count'] < self.max_retries:
                    try:
                        self.db.update_batch_status(batch_id, BatchStatus.RETRY_QUEUE)
                        result = self._process_single_batch(
                            failed_info['batch'],
                            process_fn,
                            batch_id,
                            failed_info['retry_count'] + 1
                        )
                        retry_results.append(result)
                        if result.get('success', False):
                            self._completed_batches.add(batch_id)
                    except Exception as e:
                        logging.error(f"Unhandled error during retry of batch {batch_id}: {str(e)}")
        return retry_results

    def _analyze_errors(self) -> Dict[str, Any]:
        """
        Analyze error patterns and generate error report.

        Returns:
            Dict[str, Any]: Error analysis report
        """
        error_analysis = {
            'total_failures': len(self._failed_batches),
            'error_patterns': dict(self._error_patterns),
            'retry_statistics': self._get_retry_statistics(),
            'failure_timeline': self._get_failure_timeline(),
            'recommendations': self._generate_error_recommendations()
        }
        
        # Log error analysis
        logging.info("Error Analysis Report:")
        for key, value in error_analysis.items():
            logging.info(f"{key}: {value}")
        
        return error_analysis

    def _get_retry_statistics(self) -> Dict[str, int]:
        """
        Calculate statistics about retry attempts.

        Returns:
            Dict[str, int]: Retry statistics
        """
        retry_counts = defaultdict(int)
        for batch_info in self._failed_batches.values():
            retry_counts[batch_info['retry_count']] += 1
        return dict(retry_counts)

    def _get_failure_timeline(self) -> List[Tuple[str, int]]:
        """
        Generate timeline of failures.

        Returns:
            List[Tuple[str, int]]: List of (timestamp, count) pairs
        """
        timeline = defaultdict(int)
        for batch_info in self._failed_batches.values():
            timestamp = batch_info['timestamp'][:13]  # Group by hour
            timeline[timestamp] += 1
        return sorted(timeline.items())

    def _generate_error_recommendations(self) -> List[str]:
        """
        Generate recommendations based on error patterns.

        Returns:
            List[str]: List of recommendations
        """
        recommendations = []
        if self._error_patterns:
            most_common_error = max(self._error_patterns.items(), key=lambda x: x[1])
            recommendations.append(
                f"Most common error type '{most_common_error[0]}' occurred {most_common_error[1]} times. "
                "Consider implementing specific handling for this error type."
            )
        
        retry_stats = self._get_retry_statistics()
        if retry_stats.get(self.max_retries, 0) > 0:
            recommendations.append(
                f"{retry_stats[self.max_retries]} batches failed after maximum retries. "
                "Consider increasing max_retries or investigating persistent failures."
            )
        
        return recommendations

    def _cleanup_failed_batches(self):
        """Clean up failed batches and update their status."""
        for batch_id in self._failed_batches:
            if batch_id not in self._retry_queue:
                self.db.update_batch_status(batch_id, BatchStatus.CLEANED_UP)
                
        # Clear tracking dictionaries
        self._failed_batches.clear()
        self._error_patterns.clear()

    def _collect_results_with_retry(self, executor: ThreadPoolExecutor,
                                  process_fn: Callable) -> List[Dict]:
        """
        Collect results from futures and handle retries for failed batches.

        Args:
            executor (ThreadPoolExecutor): The executor handling the batch processing
            process_fn (Callable): The function to process batches

        Returns:
            List[Dict]: Results from all batches, including retries
        """
        results = []
        while self._active_futures:
            completed_batch_ids = []
            for batch_id, future in self._active_futures.items():
                if future.done():
                    try:
                        result = future.result()
                        results.append(result)
                        if result.get('success', False):
                            self._completed_batches.add(batch_id)
                            completed_batch_ids.append(batch_id)
                        elif result.get('needs_retry', False):
                            # Submit a new attempt for the failed batch
                            failed_info = self._failed_batches[batch_id]
                            new_future = executor.submit(
                                self._process_single_batch,
                                failed_info['batch'],
                                process_fn,
                                batch_id,
                                failed_info['retry_count'] + 1
                            )
                            self._active_futures[batch_id] = new_future
                        else:
                            # Failed and no more retries
                            completed_batch_ids.append(batch_id)
                    except Exception as e:
                        # Handle any other exceptions
                        results.append({
                            'batch_id': batch_id,
                            'success': False,
                            'error': str(e),
                            'retry_count': 0,
                            'items_processed': 0
                        })
                        completed_batch_ids.append(batch_id)
            
            # Remove completed futures
            for batch_id in completed_batch_ids:
                if batch_id in self._active_futures:
                    del self._active_futures[batch_id]
            
            time.sleep(0.1)  # Prevent busy waiting
        
        return results

    def _monitor_batch_progress(self, task_type: str, total_batches: int):
        """
        Monitor and print batch processing progress.

        Args:
            task_type (str): Type of task being monitored
            total_batches (int): Total number of batches to process
        """
        last_status_time = 0
        status_interval = 5  # Status update interval in seconds

        while not self._processing_complete:
            current_time = time.time()
            if current_time - last_status_time >= status_interval:
                completed = len(self._completed_batches)
                failed = len(self._failed_batches)
                active = len(self._active_futures)
                retries = len(self._retry_queue)
                
                progress = ((completed + failed) / total_batches) * 100 if total_batches > 0 else 0
                
                print(f"\nProcessing Status for {task_type}:")
                print(f"Progress: {progress:.1f}% ({completed + failed}/{total_batches} batches)")
                print(f"Active Batches: {active}")
                print(f"Retry Queue Size: {retries}")
                
                if self._failed_batches:
                    print(f"\nFailed Batches: {failed}")
                    for batch_id, info in list(self._failed_batches.items())[-3:]:  # Show last 3 failures
                        print(f"  Batch {batch_id}: {info['error']}")
                
                last_status_time = current_time
            
            time.sleep(1)

    def _create_batches(self, items: List[Any], batch_size: int) -> List[List[Any]]:
        """Split items into batches."""
        return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]

    def _combine_results(self, results: List[Dict]) -> Dict:
        """Combine results from all batches."""
        summary = {
            'total_processed': sum(r.get('items_processed', 0) for r in results),
            'successful_batches': len(self._completed_batches),
            'failed_batches': len(self._failed_batches),
            'errors': [info['error'] for info in self._failed_batches.values()],
            'total_retries': sum(r.get('retry_count', 0) for r in results),
            'average_processing_time': 0
        }
        
        processing_times = [r.get('processing_time', 0) for r in results if r.get('success', False)]
        if processing_times:
            summary['average_processing_time'] = sum(processing_times) / len(processing_times)
        
        return summary
