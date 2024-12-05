"""
Performance testing module for the parallel processing implementation.
Tests processing speed, memory usage, and error handling under various configurations.
"""

import time
import psutil
import random
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import logging
from datetime import datetime
from parallel_manager import ParallelProcessor, BatchStatus

logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')

class PerformanceTest:
    """
    Performance testing suite for parallel processing implementation.
    Tests different configurations and generates performance metrics.
    """
    
    def __init__(self):
        self.process = psutil.Process()
        self.results: Dict[str, Any] = {}
    
    def generate_test_data(self, size: int) -> List[Dict]:
        """
        Generate test data for performance testing.
        
        Args:
            size (int): Number of test items to generate
            
        Returns:
            List[Dict]: List of test items
        """
        return [
            {
                'id': i,
                'data': f"Test data {i}",
                'timestamp': datetime.now().isoformat(),
                'metadata': {
                    'type': random.choice(['type1', 'type2', 'type3']),
                    'priority': random.randint(1, 5)
                }
            }
            for i in range(size)
        ]

    def mock_process_fn(self, batch: List[Dict], batch_id: int) -> Dict:
        """
        Mock processing function that simulates real work.
        
        Args:
            batch (List[Dict]): Batch of items to process
            batch_id (int): ID of the current batch
            
        Returns:
            Dict: Processing results
        """
        # Simulate varying processing times
        process_time = random.uniform(0.1, 0.5)
        time.sleep(process_time)
        
        # Randomly introduce errors for testing error handling
        if random.random() < 0.1:  # 10% chance of error
            raise Exception(f"Simulated error in batch {batch_id}")
            
        return {
            'processed_count': len(batch),
            'processing_time': process_time,
            'batch_id': batch_id,
            'results': [
                {'id': item['id'], 'status': 'processed'}
                for item in batch
            ]
        }

    def measure_memory(self) -> float:
        """
        Measure current memory usage.
        
        Returns:
            float: Memory usage in MB
        """
        return self.process.memory_info().rss / 1024 / 1024  # Convert to MB

    def run_performance_test(self, 
                           data_size: int,
                           batch_sizes: List[int],
                           worker_counts: List[int]) -> Dict:
        """
        Run performance tests with different configurations.
        
        Args:
            data_size (int): Total number of items to process
            batch_sizes (List[int]): List of batch sizes to test
            worker_counts (List[int]): List of worker counts to test
            
        Returns:
            Dict: Test results and metrics
        """
        test_data = self.generate_test_data(data_size)
        results = {
            'test_parameters': {
                'data_size': data_size,
                'batch_sizes': batch_sizes,
                'worker_counts': worker_counts
            },
            'configurations': []
        }
        
        # Test each configuration
        for batch_size in batch_sizes:
            for worker_count in worker_counts:
                logging.info(f"\nTesting configuration: batch_size={batch_size}, workers={worker_count}")
                
                # Initialize processor with current configuration
                processor = ParallelProcessor(max_workers=worker_count)
                
                # Measure initial memory
                initial_memory = self.measure_memory()
                start_time = time.time()
                
                # Run processing
                processing_result = processor.process_batch(
                    task_type='performance_test',
                    items=test_data,
                    process_fn=self.mock_process_fn,
                    batch_size=batch_size,
                    monitor_progress=True
                )
                
                # Calculate metrics
                end_time = time.time()
                peak_memory = self.measure_memory()
                total_time = end_time - start_time
                items_per_second = data_size / total_time
                memory_usage = peak_memory - initial_memory
                
                # Record configuration results
                config_result = {
                    'configuration': {
                        'batch_size': batch_size,
                        'worker_count': worker_count
                    },
                    'performance_metrics': {
                        'total_time': total_time,
                        'items_per_second': items_per_second,
                        'memory_usage_mb': memory_usage,
                        'successful_batches': processing_result['successful_batches'],
                        'failed_batches': processing_result['failed_batches'],
                        'retry_attempts': processing_result['retry_attempts'],
                        'average_batch_time': processing_result['average_processing_time']
                    }
                }
                
                results['configurations'].append(config_result)
                
                logging.info(f"Configuration completed:")
                logging.info(f"  Total time: {total_time:.2f}s")
                logging.info(f"  Items/second: {items_per_second:.2f}")
                logging.info(f"  Memory usage: {memory_usage:.2f}MB")
        
        # Find optimal configuration
        optimal_config = self._find_optimal_configuration(results['configurations'])
        results['recommendations'] = self._generate_recommendations(
            results['configurations'],
            optimal_config
        )
        
        return results

    def run_sequential_comparison(self, data_size: int, batch_size: int) -> Dict:
        """
        Compare parallel vs sequential processing performance.
        
        Args:
            data_size (int): Total number of items to process
            batch_size (int): Batch size for processing
            
        Returns:
            Dict: Comparison results
        """
        test_data = self.generate_test_data(data_size)
        results = {
            'test_parameters': {
                'data_size': data_size,
                'batch_size': batch_size
            },
            'sequential': {},
            'parallel': {}
        }
        
        # Test sequential processing
        logging.info("\nTesting sequential processing...")
        start_time = time.time()
        initial_memory = self.measure_memory()
        
        batches = [test_data[i:i + batch_size] 
                  for i in range(0, len(test_data), batch_size)]
        sequential_results = []
        
        for i, batch in enumerate(batches):
            try:
                result = self.mock_process_fn(batch, i)
                sequential_results.append(result)
            except Exception as e:
                logging.error(f"Sequential processing error: {str(e)}")
        
        sequential_time = time.time() - start_time
        sequential_memory = self.measure_memory() - initial_memory
        
        # Test parallel processing
        logging.info("\nTesting parallel processing...")
        processor = ParallelProcessor(max_workers=4)
        
        start_time = time.time()
        initial_memory = self.measure_memory()
        
        parallel_result = processor.process_batch(
            task_type='performance_test',
            items=test_data,
            process_fn=self.mock_process_fn,
            batch_size=batch_size
        )
        
        parallel_time = time.time() - start_time
        parallel_memory = self.measure_memory() - initial_memory
        
        # Record results
        results['sequential'] = {
            'total_time': sequential_time,
            'memory_usage_mb': sequential_memory,
            'items_per_second': data_size / sequential_time
        }
        
        results['parallel'] = {
            'total_time': parallel_time,
            'memory_usage_mb': parallel_memory,
            'items_per_second': data_size / parallel_time,
            'worker_count': 4
        }
        
        # Calculate improvement metrics
        speedup = sequential_time / parallel_time
        memory_overhead = parallel_memory - sequential_memory
        
        results['comparison'] = {
            'speedup_factor': speedup,
            'memory_overhead_mb': memory_overhead,
            'efficiency': speedup / 4  # efficiency = speedup / number of workers
        }
        
        logging.info("\nComparison Results:")
        logging.info(f"Sequential: {sequential_time:.2f}s, {results['sequential']['items_per_second']:.2f} items/s")
        logging.info(f"Parallel: {parallel_time:.2f}s, {results['parallel']['items_per_second']:.2f} items/s")
        logging.info(f"Speedup: {speedup:.2f}x")
        logging.info(f"Memory overhead: {memory_overhead:.2f}MB")
        
        return results

    def _find_optimal_configuration(self, configurations: List[Dict]) -> Dict:
        """
        Find the optimal configuration based on performance metrics.
        
        Args:
            configurations (List[Dict]): List of test configurations and results
            
        Returns:
            Dict: Optimal configuration
        """
        # Score each configuration based on processing speed and memory usage
        scored_configs = []
        for config in configurations:
            metrics = config['performance_metrics']
            
            # Calculate score (higher is better)
            # Weight speed more heavily than memory usage
            speed_score = metrics['items_per_second'] * 0.7
            memory_score = (1 / metrics['memory_usage_mb']) * 0.3
            total_score = speed_score + memory_score
            
            scored_configs.append((total_score, config))
        
        # Return configuration with highest score
        return max(scored_configs, key=lambda x: x[0])[1]

    def _generate_recommendations(self, 
                                configurations: List[Dict],
                                optimal_config: Dict) -> Dict:
        """
        Generate performance recommendations based on test results.
        
        Args:
            configurations (List[Dict]): List of test configurations and results
            optimal_config (Dict): The optimal configuration found
            
        Returns:
            Dict: Performance recommendations
        """
        recommendations = {
            'optimal_configuration': optimal_config['configuration'],
            'expected_performance': optimal_config['performance_metrics'],
            'suggestions': []
        }
        
        # Analyze patterns in the results
        batch_size_impact = self._analyze_batch_size_impact(configurations)
        worker_count_impact = self._analyze_worker_count_impact(configurations)
        
        # Generate specific recommendations
        if batch_size_impact['trend'] == 'increasing':
            recommendations['suggestions'].append(
                "Consider using larger batch sizes for better throughput, "
                "but monitor memory usage"
            )
        elif batch_size_impact['trend'] == 'decreasing':
            recommendations['suggestions'].append(
                "Smaller batch sizes appear more efficient. Consider reducing "
                "batch size to improve performance"
            )
            
        if worker_count_impact['trend'] == 'plateaued':
            recommendations['suggestions'].append(
                f"Adding more workers beyond {worker_count_impact['optimal']} "
                "doesn't significantly improve performance. Consider limiting "
                "worker count to this value"
            )
            
        # Memory usage recommendation
        avg_memory = sum(c['performance_metrics']['memory_usage_mb'] 
                        for c in configurations) / len(configurations)
        if avg_memory > 1000:  # If average memory usage is over 1GB
            recommendations['suggestions'].append(
                "High memory usage detected. Consider implementing memory-efficient "
                "processing strategies or reducing batch sizes"
            )
            
        return recommendations

    def _analyze_batch_size_impact(self, configurations: List[Dict]) -> Dict:
        """
        Analyze the impact of batch size on performance.
        
        Args:
            configurations (List[Dict]): List of test configurations and results
            
        Returns:
            Dict: Analysis of batch size impact
        """
        # Group by batch size
        batch_sizes = {}
        for config in configurations:
            batch_size = config['configuration']['batch_size']
            if batch_size not in batch_sizes:
                batch_sizes[batch_size] = []
            batch_sizes[batch_size].append(
                config['performance_metrics']['items_per_second']
            )
        
        # Calculate average performance for each batch size
        avg_performance = {
            size: sum(perfs) / len(perfs)
            for size, perfs in batch_sizes.items()
        }
        
        # Determine trend
        sizes = sorted(avg_performance.keys())
        if len(sizes) > 1:
            if avg_performance[sizes[-1]] > avg_performance[sizes[0]]:
                trend = 'increasing'
            elif avg_performance[sizes[-1]] < avg_performance[sizes[0]]:
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
            
        return {
            'trend': trend,
            'performance_by_size': avg_performance
        }

    def _analyze_worker_count_impact(self, configurations: List[Dict]) -> Dict:
        """
        Analyze the impact of worker count on performance.
        
        Args:
            configurations (List[Dict]): List of test configurations and results
            
        Returns:
            Dict: Analysis of worker count impact
        """
        # Group by worker count
        worker_counts = {}
        for config in configurations:
            workers = config['configuration']['worker_count']
            if workers not in worker_counts:
                worker_counts[workers] = []
            worker_counts[workers].append(
                config['performance_metrics']['items_per_second']
            )
        
        # Calculate average performance for each worker count
        avg_performance = {
            workers: sum(perfs) / len(perfs)
            for workers, perfs in worker_counts.items()
        }
        
        # Find optimal worker count
        optimal_workers = max(avg_performance.items(), key=lambda x: x[1])[0]
        
        # Determine if performance has plateaued
        counts = sorted(avg_performance.keys())
        if len(counts) > 2:
            last_improvement = avg_performance[counts[-1]] - avg_performance[counts[-2]]
            prev_improvement = avg_performance[counts[-2]] - avg_performance[counts[-3]]
            
            if last_improvement < prev_improvement * 0.2:  # Less than 20% improvement
                trend = 'plateaued'
            else:
                trend = 'increasing'
        else:
            trend = 'insufficient_data'
            
        return {
            'trend': trend,
            'optimal': optimal_workers,
            'performance_by_count': avg_performance
        }

def run_comprehensive_test():
    """Run a comprehensive performance test suite."""
    test = PerformanceTest()
    
    # Test parameters
    data_sizes = [1000, 5000, 10000]
    batch_sizes = [10, 50, 100, 200]
    worker_counts = [2, 4, 8]
    
    all_results = {
        'timestamp': datetime.now().isoformat(),
        'test_runs': []
    }
    
    # Run tests for different data sizes
    for data_size in data_sizes:
        logging.info(f"\nTesting with data size: {data_size}")
        
        # Run parallel processing tests
        parallel_results = test.run_performance_test(
            data_size=data_size,
            batch_sizes=batch_sizes,
            worker_counts=worker_counts
        )
        
        # Run sequential comparison
        comparison_results = test.run_sequential_comparison(
            data_size=data_size,
            batch_size=100  # Use middle-range batch size for comparison
        )
        
        all_results['test_runs'].append({
            'data_size': data_size,
            'parallel_results': parallel_results,
            'sequential_comparison': comparison_results
        })
    
    return all_results

if __name__ == '__main__':
    # Run comprehensive test suite
    results = run_comprehensive_test()
    
    # Log overall results
    logging.info("\nOverall Test Results:")
    for test_run in results['test_runs']:
        data_size = test_run['data_size']
        parallel = test_run['parallel_results']
        comparison = test_run['sequential_comparison']
        
        logging.info(f"\nData Size: {data_size}")
        logging.info("Optimal Configuration:")
        logging.info(f"  Batch Size: {parallel['recommendations']['optimal_configuration']['batch_size']}")
        logging.info(f"  Worker Count: {parallel['recommendations']['optimal_configuration']['worker_count']}")
        logging.info(f"Speedup vs Sequential: {comparison['comparison']['speedup_factor']:.2f}x")
        
        logging.info("Recommendations:")
        for suggestion in parallel['recommendations']['suggestions']:
            logging.info(f"  - {suggestion}")
