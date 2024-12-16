# LLM-Based Repository Categorization

This document describes the implementation approach for LLM-based repository categorization, which involves two main components: repository summarization and category prototype generation.

## Repository Summarization

### Overview
The Content Extractor will generate structured summaries of repositories using LLM, incorporating both repository metadata and README content. This provides richer context for categorization than metadata alone.

### Summary Structure
```json
{
    "primary_purpose": "Main goal or function",
    "key_technologies": ["tech1", "tech2"],
    "target_users": "Primary audience",
    "main_features": ["feature1", "feature2"],
    "technical_domain": "Specific technical area"
}
```

### Implementation Details
- README content is fetched and included in summary generation
- Summaries are vectorized and stored alongside existing embeddings
- Processing is batched to manage API rate limits
- Each summary captures repository essence beyond metadata
- Migration handles existing repositories without disruption

## Category Prototype Generation

### Overview
The Topic Analyzer generates prototypical repository variants for each category using LLM. The number and nature of variants are dynamically determined based on category complexity.

### Prototype Generation Prompt
```
Analyze the AI/ML category: [category_name]

1. First, identify the distinct major use cases, implementation patterns, or approaches that repositories in this category commonly represent. Consider:
- Different technical approaches or frameworks
- Various application domains
- Different scales of implementation
- Common architectural patterns

2. For each identified variant, create a prototypical repository summary that represents that specific use case or pattern.

Format your response as a JSON array of variant summaries, where each summary has:
- variant_name: A descriptive name for this variant
- rationale: Why this is a distinct variant worth considering
- summary: {
    primary_purpose: Main goal or function
    key_technologies: Array of core technologies
    target_users: Primary audience
    main_features: Array of key capabilities
    technical_domain: Specific technical area
  }
```

### Implementation Details
- LLM determines appropriate number of variants per category
- Each variant gets its own vector embedding
- Variants capture different implementation patterns and use cases
- Prototype generation is a one-time operation unless categories change
- Prototypes are versioned for tracking changes

## Categorization Process

1. Repository Processing:
   - Extract metadata and README
   - Generate structured summary
   - Create summary embedding

2. Category Matching:
   - Compare repository summary embedding to category prototype embeddings
   - Calculate similarity scores
   - Apply confidence thresholds
   - Consider parent/child relationships

3. Confidence Scoring:
   - Based on similarity to category prototypes
   - Influenced by parent/child relationships
   - Adjusted by category-specific factors

## Data Migration

### Repository Migration
1. Fetch README content for existing repositories
2. Generate structured summaries
3. Create new embeddings
4. Maintain existing metadata
5. Update database schema

### Category Migration
1. Generate category prototypes
2. Create prototype embeddings
3. Recategorize existing repositories
4. Validate new categorizations
5. Version control for prototypes

### Database Updates
1. Add columns for structured summaries
2. Add prototype version tracking
3. Backup existing data
4. Implement rollback capability

## Testing Strategy

1. Repository Summarization:
   - Verify summary quality and completeness
   - Validate embedding generation
   - Test batch processing
   - Check migration success

2. Category Prototypes:
   - Validate prototype generation
   - Test versioning system
   - Verify variant coverage
   - Check embedding quality

3. Categorization:
   - Test similarity matching
   - Verify confidence scoring
   - Validate parent/child handling
   - Check migration results

## Example Category Variants

### MLOps Category
```json
[
    {
        "variant_name": "Model Deployment Platform",
        "rationale": "Focuses on getting models into production environments",
        "summary": {
            "primary_purpose": "Streamline ML model deployment and serving",
            "key_technologies": ["kubernetes", "docker", "REST APIs", "gRPC"],
            "target_users": "ML Engineers and DevOps teams",
            "main_features": ["model serving", "scaling", "versioning", "A/B testing"],
            "technical_domain": "Production ML Infrastructure"
        }
    },
    {
        "variant_name": "ML Pipeline Orchestrator",
        "rationale": "Manages end-to-end ML workflows",
        "summary": {
            "primary_purpose": "Automate and monitor ML pipelines",
            "key_technologies": ["airflow", "kubeflow", "mlflow", "prefect"],
            "target_users": "Data Scientists and ML Engineers",
            "main_features": ["workflow automation", "dependency management", "monitoring"],
            "technical_domain": "ML Pipeline Management"
        }
    }
]
```

### Large Language Models Category
```json
[
    {
        "variant_name": "Model Implementation",
        "rationale": "Core LLM architecture implementation",
        "summary": {
            "primary_purpose": "Implement LLM architecture and training",
            "key_technologies": ["pytorch", "tensorflow", "transformers"],
            "target_users": "ML Researchers and Engineers",
            "main_features": ["model architecture", "training scripts", "optimization"],
            "technical_domain": "Deep Learning"
        }
    },
    {
        "variant_name": "Application Framework",
        "rationale": "Building applications with LLMs",
        "summary": {
            "primary_purpose": "Simplify LLM integration into applications",
            "key_technologies": ["langchain", "llamaindex", "openai-api"],
            "target_users": "Application Developers",
            "main_features": ["API integration", "prompt management", "output parsing"],
            "technical_domain": "LLM Applications"
        }
    }
]
```

## Benefits of This Approach

1. More Accurate Categorization:
   - Rich context from README content
   - Dynamic category variants
   - Semantic similarity matching

2. Maintainable System:
   - Versioned category prototypes
   - Clear migration path
   - Structured data format

3. Flexible Architecture:
   - Category variants can evolve
   - New categories easily added
   - Prototype updates possible

4. Efficient Processing:
   - One-time prototype generation
   - Batched repository processing
   - Reusable embeddings
