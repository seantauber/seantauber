# GitHub GenAI List Requirements

## Project Overview

A system to maintain a curated list of GitHub repositories related to AI/ML/GenAI, using CrewAI flows for automated processing and analysis.

## Core Requirements

### 1. Repository Management

#### Data Collection
- Fetch starred repositories from configured GitHub user
- Search trending GenAI repositories
- Store repository metadata:
  * Full name
  * Description
  * URL
  * Stars count
  * Topics
  * Creation/update dates
  * Primary language

#### Processing
- Combine and deduplicate repositories
- Clean and standardize metadata
- Track processing state
- Handle batch operations

### 2. Analysis Requirements

#### Repository Analysis
- Evaluate code quality and documentation
- Assess community engagement
- Calculate relevance to AI/ML/GenAI
- Determine categories and subcategories
- Generate quality scores

#### Categories
- Generative AI
- Artificial Intelligence
- MLOps & AI Infrastructure
- Machine Learning Tools
- Development Tools
- Other AI-Related

#### Analysis Data
```python
{
    'raw_repo_id': str,
    'quality_score': float,  # 0.0 to 1.0
    'category': str,
    'subcategory': Optional[str],
    'include': bool,
    'justification': str
}
```

### 3. Content Generation

#### README Structure
- Table of contents
- Introduction section
- Categorized repository listings
- Contribution guidelines
- License information

#### Content Requirements
- Consistent formatting
- Working repository links
- Brief descriptions
- Category organization
- Last update timestamp

### 4. Technical Requirements

#### State Management
```python
class FlowState:
    # Raw data
    raw_repos: List[GitHubRepoData]
    
    # Processing state
    processing: RepoProcessingState
    
    # Analysis results
    analyzed_repos: List[RepoAnalysis]
    
    # README state
    readme: ReadmeState
```

#### Database Requirements
- State persistence
- Batch processing support
- Transaction management
- Error recovery
- State cleanup

#### Flow Control
- Event-driven processing
- Error handling
- Progress tracking
- State management

### 5. Performance Requirements

#### Processing
- Batch size: 10 repositories
- Parallel processing support
- Efficient state updates
- Resource optimization

#### Response Times
- GitHub API calls: < 5s
- Batch processing: < 30s
- Analysis: < 60s per batch
- README generation: < 30s

### 6. Error Handling

#### Requirements
- Graceful failure recovery
- State preservation
- Error logging
- Cleanup procedures

#### Error Types
- API failures
- Processing errors
- Analysis failures
- State corruption

### 7. Monitoring Requirements

#### Logging
- Flow state changes
- Stage transitions
- Error conditions
- Performance metrics

#### Visualization
- Flow structure
- State transitions
- Error paths
- Progress tracking

## Implementation Requirements

### 1. CrewAI Flow Integration

#### Flow Structure
- Deterministic processing stages
- Agent-based analysis stages
- Event-driven control
- State management

#### Stage Requirements
1. **Fetch Stage**
   - GitHub API integration
   - Error handling
   - State updates

2. **Process Stage**
   - Batch processing
   - Data cleaning
   - State management

3. **Analysis Stage**
   - LLM agent integration
   - Categorization
   - Quality scoring

4. **README Stage**
   - Content generation
   - Format validation
   - File management

### 2. Agent Requirements

#### Analyzer Agent
- Repository evaluation
- Category assignment
- Quality scoring
- Batch processing

#### Content Generator Agent
- README generation
- Content organization
- Format consistency
- Output validation

### 3. Tool Requirements

#### GitHub Tools
- API interaction
- Rate limiting
- Error handling
- Data validation

#### Processing Tools
- Batch operations
- Data cleaning
- State updates
- Error recovery

#### Analysis Tools
- LLM integration
- Category management
- Score calculation
- Result validation

## Success Criteria

### 1. Functionality
- Successful repository processing
- Accurate categorization
- Quality README generation
- Proper error handling

### 2. Performance
- Meeting response times
- Efficient resource usage
- Minimal LLM costs
- Reliable processing

### 3. Reliability
- Error recovery
- State consistency
- Data integrity
- System stability

### 4. Maintainability
- Clear documentation
- Easy debugging
- Simple updates
- Comprehensive testing
