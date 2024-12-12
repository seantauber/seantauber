# Agent Guidelines

## Topic Analysis Agent Guidelines

### Purpose
The Topic Analysis Agent is responsible for identifying, tracking, and evolving topics from newsletter content in a flexible and organic way.

### Core Responsibilities

1. Daily Newsletter Analysis
- Extract and identify key topics from each newsletter
- Consider context and relationships between topics
- Store topic information with temporal metadata
- Link topics to relevant repositories and content

2. Topic Management
- Maintain a dynamic topic vocabulary
- Bias towards reusing existing topics when appropriate
- Create new topics when genuinely new concepts emerge
- Track topic relationships and hierarchies

### Topic Identification Guidelines

1. Topic Reuse Guidelines
```python
"""
When identifying topics, consider:
- Exact matches with existing topics
- Semantic similarity to existing topics
- Contextual alignment with existing topics
- Historical usage patterns
"""
```

2. New Topic Creation Guidelines
```python
"""
Create new topics when:
- The concept is distinctly different from existing topics
- The technology or approach represents a new paradigm
- The topic has significant presence in multiple newsletters
- The concept cannot be accurately represented by combining existing topics
"""
```

3. Topic Relationship Guidelines
```python
"""
Track relationships between topics:
- Parent/child relationships (e.g., 'LLMs' -> 'Instruction Tuning')
- Sibling relationships (e.g., 'RAG' <-> 'Fine-tuning')
- Historical evolution (e.g., 'Neural Networks' -> 'Deep Learning' -> 'Foundation Models')
"""
```

## README Generation Agent Guidelines

### Purpose
The README Generation Agent uses historical topic information to create and maintain the repository's category structure.

### Core Responsibilities

1. Category Selection
- Analyze topic history and prevalence
- Identify stable, recurring topics
- Recognize emerging trends
- Balance between stability and evolution

2. Content Organization
- Group repositories within appropriate categories
- Maintain clear category hierarchies
- Ensure logical content flow
- Preserve important historical content

### Decision Making Guidelines

1. Category Inclusion Criteria
```python
"""
Consider including a category when:
- The topic shows consistent presence across newsletters
- Multiple high-quality repositories exist in the space
- The topic represents a distinct and important area
- The category adds value to the overall structure
"""
```

2. Category Removal Criteria
```python
"""
Consider removing a category when:
- Topic relevance has significantly decreased
- Limited new content in recent newsletters
- Category has merged with or been superseded by another
- Maintaining the category reduces overall clarity
"""
```

3. Repository Selection Criteria
```python
"""
Select repositories based on:
- Mention frequency across newsletters
- Recency of mentions
- Repository quality metrics
- Relevance to category focus
"""
```

## Vector Storage Integration

### Newsletter Content
```python
"""
Store in vector database:
- Full newsletter content
- Extracted topics and relationships
- Temporal metadata
- Source information
"""
```

### External Content
```python
"""
Store in vector database:
- Repository documentation
- Related blog posts
- Technical articles
- Discussion context
"""
```

### Search and Retrieval
```python
"""
Use vector search for:
- Topic similarity analysis
- Content relationship discovery
- Historical trend analysis
- Context enrichment
"""
```

## Example Topic Analysis

```python
# Example agent analysis process
def analyze_newsletter(content: str) -> List[Topic]:
    """
    1. Extract key concepts and technologies
    2. Compare with existing topics
    3. Identify relationships and hierarchies
    4. Make topic decisions based on guidelines
    5. Store results with metadata
    """
    pass

# Example topic decision process
def evaluate_topic(topic: str, context: Context) -> TopicDecision:
    """
    1. Check existing topic vocabulary
    2. Assess semantic similarity
    3. Evaluate contextual relevance
    4. Consider historical patterns
    5. Make create/reuse decision
    """
    pass
```

## Example README Generation

```python
# Example category selection process
def select_categories(topics: List[Topic]) -> List[Category]:
    """
    1. Analyze topic history
    2. Evaluate current relevance
    3. Consider relationship patterns
    4. Balance stability and evolution
    """
    pass

# Example repository organization process
def organize_repositories(
    categories: List[Category],
    repositories: List[Repository]
) -> Structure:
    """
    1. Match repositories to categories
    2. Consider multiple categorizations
    3. Evaluate repository importance
    4. Create logical hierarchy
    """
    pass
```

## Monitoring and Adjustment

1. Track agent decisions and outcomes
2. Analyze topic evolution patterns
3. Monitor category effectiveness
4. Adjust guidelines based on results

## Success Metrics

1. Topic Consistency
- Reuse rate of existing topics
- New topic creation rate
- Topic relationship accuracy

2. Category Effectiveness
- User navigation patterns
- Repository discoverability
- Category stability over time

3. Content Quality
- Repository relevance scores
- Category coherence
- Information accessibility
