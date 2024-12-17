"""Component tests for verifying functionality with live external dependencies.

Note: This module has been refactored into smaller files under tests/components/.
It now re-exports the test classes for backwards compatibility.

Components:
1. Gmail/Newsletter - Tests newsletter ingestion from Gmail, including fetching,
   storage, vector embeddings, and historical tracking
2. Content Extraction - Tests repository extraction from newsletters, metadata
   collection, and summary generation
3. Topic Analysis - Tests semantic categorization of repositories using fixed
   categories and confidence thresholds
4. Repository Curation - Tests repository metadata management and semantic
   duplicate detection
"""

from tests.components.test_gmail_newsletter import TestGmailNewsletterComponent
from tests.components.test_content_extraction import TestContentExtractionComponent
from tests.components.test_topic_analysis import TestTopicAnalysisComponent
from tests.components.test_repository_curation import TestRepositoryCurationComponent

__all__ = [
    'TestGmailNewsletterComponent',
    'TestContentExtractionComponent',
    'TestTopicAnalysisComponent',
    'TestRepositoryCurationComponent'
]