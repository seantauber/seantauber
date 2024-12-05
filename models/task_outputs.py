"""
Task output models for processing summaries.
These models standardize the return values from various processing tasks.
"""

from typing import Dict, List
from pydantic import BaseModel

class ProcessingSummary(BaseModel):
    """Base model for task processing summaries"""
    success: bool
    message: str
    processed_count: int
    batch_count: int
    completed_batches: int
    failed_batches: int
    error_count: int = 0
    errors: List[str] = []

    def __str__(self) -> str:
        """String representation of processing summary"""
        status = "Success" if self.success else "Failed"
        return (
            f"Processing {status}: {self.message}\n"
            f"Processed: {self.processed_count} items in {self.batch_count} batches\n"
            f"Completed batches: {self.completed_batches}\n"
            f"Failed batches: {self.failed_batches}\n"
            f"Errors ({self.error_count}): {', '.join(self.errors) if self.errors else 'None'}"
        )

class FetchSummary(ProcessingSummary):
    """Summary for fetch tasks"""
    source: str  # 'starred' or 'trending'
    total_repos: int
    stored_repos: int

    def __str__(self) -> str:
        """String representation of fetch summary"""
        base_summary = super().__str__()
        return (
            f"{base_summary}\n"
            f"Source: {self.source}\n"
            f"Total repositories: {self.total_repos}\n"
            f"Stored repositories: {self.stored_repos}"
        )
    
class AnalysisSummary(ProcessingSummary):
    """Summary for analysis tasks"""
    total_analyzed: int
    categories: Dict[str, int]  # Count of repos per category
    quality_stats: Dict[str, float]  # Min/max/avg quality scores

    def __str__(self) -> str:
        """String representation of analysis summary"""
        base_summary = super().__str__()
        category_breakdown = "\n".join(
            f"  - {category}: {count}" 
            for category, count in self.categories.items()
        )
        quality_breakdown = "\n".join(
            f"  - {metric}: {value:.2f}" 
            for metric, value in self.quality_stats.items()
        )
        return (
            f"{base_summary}\n"
            f"Total analyzed: {self.total_analyzed}\n"
            f"Categories:\n{category_breakdown}\n"
            f"Quality metrics:\n{quality_breakdown}"
        )
