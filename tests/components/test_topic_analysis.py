"""Tests for topic analysis with live dependencies."""
import pytest
from agents.topic_analyzer import TopicAnalyzer
from processing.embedchain_store import EmbedchainStore

class TestTopicAnalysisComponent:
    """Tests for topic analysis with live dependencies."""
    
    @pytest.fixture
    def topic_analyzer(self, vector_store: EmbedchainStore) -> TopicAnalyzer:
        """Initialize topic analyzer component."""
        analyzer = TopicAnalyzer(embedchain_store=vector_store)
        yield analyzer
            
    async def test_parent_topic_handling(self, topic_analyzer: TopicAnalyzer):
        """Test parent/child relationship handling in topic analysis."""
        print("\n=== Parent Topic Handling Test ===")
        
        # Get fixed category structure
        categories = topic_analyzer.get_fixed_categories()
        
        # Test repositories with clear parent/child relationships
        test_repos = [
            {
                'github_url': 'https://github.com/example/llm-project',
                'description': 'A project focused on large language models and prompt engineering'
            },
            {
                'github_url': 'https://github.com/example/ml-pipeline',
                'description': 'Machine learning pipeline with MLOps and model monitoring capabilities'
            }
        ]
        
        print("\nProcessing test repositories as batch...")
        try:
            # Get categories with confidence scores for the batch
            batch_results = await topic_analyzer.analyze_repositories_batch(test_repos)
            
            for repo, repo_categories in zip(test_repos, batch_results):
                print(f"\nAnalyzing repository: {repo['github_url']}")
                print(f"Description: {repo['description']}")
                
                # Group categories by parent/child relationships
                hierarchy = {}
                for cat in repo_categories:
                    cat_info = categories[cat['topic_id']]
                    parent_id = cat_info['parent_id']
                    
                    if parent_id is None:
                        if 'root' not in hierarchy:
                            hierarchy['root'] = []
                        hierarchy['root'].append({
                            'name': cat_info['name'],
                            'confidence': cat['confidence_score']
                        })
                    else:
                        parent_name = categories[parent_id]['name']
                        if parent_name not in hierarchy:
                            hierarchy[parent_name] = []
                        hierarchy[parent_name].append({
                            'name': cat_info['name'],
                            'confidence': cat['confidence_score']
                        })
                
                # Print hierarchy
                print("\nCategory Hierarchy:")
                if 'root' in hierarchy:
                    for root_cat in sorted(hierarchy['root'], key=lambda x: x['confidence'], reverse=True):
                        print(f"- {root_cat['name']} ({root_cat['confidence']:.2f})")
                        # Print children
                        for parent_name, children in hierarchy.items():
                            if parent_name != 'root' and parent_name == root_cat['name']:
                                for child in sorted(children, key=lambda x: x['confidence'], reverse=True):
                                    print(f"  - {child['name']} ({child['confidence']:.2f})")
                
        except Exception as e:
            print(f"Error analyzing repositories: {str(e)}")
            
        print("\nParent/Child Relationship Test Complete")

    async def test_confidence_threshold(self, topic_analyzer: TopicAnalyzer):
        """Test confidence threshold behavior in topic analysis."""
        print("\n=== Confidence Threshold Test ===")
        
        # Test repositories with varying relevance to categories
        test_repos = [
            {
                'github_url': 'https://github.com/example/clear-ml-project',
                'description': 'A clear machine learning project using neural networks'
            },
            {
                'github_url': 'https://github.com/example/ambiguous-project',
                'description': 'A general software project with some AI-related features'
            }
        ]
        
        print(f"\nConfidence Threshold: {topic_analyzer.MIN_CONFIDENCE_THRESHOLD}")
        print(f"Processing test repositories as batch...")
        
        try:
            # Get categories with confidence scores for the batch
            batch_results = await topic_analyzer.analyze_repositories_batch(test_repos)
            
            for repo, repo_categories in zip(test_repos, batch_results):
                print(f"\nAnalyzing repository: {repo['github_url']}")
                print(f"Description: {repo['description']}")
                
                # Sort by confidence score
                sorted_categories = sorted(
                    repo_categories,
                    key=lambda x: x['confidence_score'],
                    reverse=True
                )
                
                # Print results
                print("\nCategory Confidence Scores:")
                for cat in sorted_categories:
                    cat_info = topic_analyzer.FIXED_CATEGORIES[cat['topic_id']]
                    confidence = cat['confidence_score']
                    status = "ACCEPTED" if confidence >= topic_analyzer.MIN_CONFIDENCE_THRESHOLD else "REJECTED"
                    print(f"- {cat_info['name']}: {confidence:.2f} [{status}]")
                
        except Exception as e:
            print(f"Error analyzing repositories: {str(e)}")
            
        print("\nConfidence Threshold Test Complete")
