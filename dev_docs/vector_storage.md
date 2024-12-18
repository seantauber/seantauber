# Vector Storage Documentation

## Overview

The system uses Embedchain for vector storage operations, providing semantic search capabilities for repository content and newsletters. This document outlines the vector storage architecture, usage patterns, and best practices.

## Architecture

### Components

1. **EmbedchainStore**
   - Core vector storage implementation
   - Handles embedding generation and storage
   - Provides semantic search capabilities
   - Manages vector lifecycle

2. **Vector Collections**
   - Newsletters: Stores newsletter content embeddings
   - Repositories: Stores repository content embeddings
   - Each collection maintains metadata for traceability

### Integration Points

1. **Newsletter Monitor**
   - Embeds newsletter content
   - Stores vector IDs for future reference

2. **Content Extractor**
   - Uses vector search for content similarity
   - Extracts and embeds repository information

## Usage

### Initialization

```python
from processing.embedchain_store import EmbedchainStore

store = EmbedchainStore(
    path="path/to/vector/storage",
    config={
        "collection_name": "repositories",
        "chunking": {"chunk_size": 500}
    }
)
```

### Adding Content

```python
# Add text content with metadata
vector_id = await store.add_text(
    content="Repository description and content",
    metadata={
        "url": "https://github.com/org/repo",
        "type": "repository"
    }
)

# Batch addition for multiple items
vector_ids = await store.add_many(
    contents=["content1", "content2"],
    metadata_list=[{"id": 1}, {"id": 2}]
)
```

### Searching

```python
# Basic semantic search
results = await store.search(
    query="machine learning framework",
    limit=5,
    threshold=0.7
)

# Search with filters
results = await store.search(
    query="neural networks",
    filters={"type": "repository"},
    limit=10
)
```

### Updating and Deleting

```python
# Update content
await store.update(
    vector_id="vec123",
    new_content="Updated description",
    new_metadata={"updated_at": "2024-01-15"}
)

# Delete vectors
await store.delete(vector_id="vec123")
```

## Best Practices

1. **Content Chunking**
   - Use appropriate chunk sizes (300-500 tokens recommended)
   - Consider content type when chunking
   - Maintain context in chunks

2. **Metadata Management**
   - Include essential metadata for filtering
   - Use consistent metadata schema
   - Keep metadata size reasonable

3. **Search Optimization**
   - Use specific queries for better results
   - Adjust similarity thresholds based on use case
   - Implement caching for frequent searches

4. **Resource Management**
   - Close connections properly
   - Implement batch operations for efficiency
   - Monitor storage size and cleanup old vectors

## Performance Considerations

1. **Batch Operations**
   ```python
   # Efficient batch processing
   async def process_batch(items):
       chunks = [store.prepare_chunk(item) for item in items]
       return await store.add_many(chunks)
   ```

2. **Caching**
   ```python
   # Example caching implementation
   from functools import lru_cache

   @lru_cache(maxsize=1000)
   async def cached_search(query: str, threshold: float = 0.7):
       return await store.search(query, threshold=threshold)
   ```

3. **Connection Management**
   ```python
   # Proper resource cleanup
   async with store.session() as session:
       await session.process_vectors()
   ```

## Error Handling

1. **Common Issues**
   - Connection failures
   - Embedding generation errors
   - Storage capacity limits

2. **Recovery Strategies**
   ```python
   try:
       await store.add_text(content)
   except EmbeddingError:
       # Retry with backoff
       await exponential_backoff_retry(store.add_text, content)
   except StorageFullError:
       # Cleanup old vectors
       await store.cleanup_old_vectors()
       await store.add_text(content)
   ```

## Monitoring

1. **Key Metrics**
   - Vector count per collection
   - Storage size
   - Query latency
   - Embedding generation time

2. **Health Checks**
   ```python
   async def check_store_health():
       try:
           # Test basic operations
           await store.add_text("test")
           await store.search("test")
           return True
       except Exception as e:
           logger.error(f"Store health check failed: {e}")
           return False
   ```

## Backup and Recovery

1. **Backup Strategy**
   - Regular vector exports
   - Metadata backups
   - Configuration backups

2. **Recovery Process**
   ```python
   async def restore_from_backup(backup_path: str):
       # Load backup data
       backup_data = load_backup(backup_path)
       
       # Restore vectors and metadata
       for item in backup_data:
           await store.restore_vector(
               vector_id=item['id'],
               content=item['content'],
               metadata=item['metadata']
           )
   ```

## Troubleshooting

1. **Slow Queries**
   - Check index optimization
   - Verify chunk sizes
   - Monitor resource usage

2. **Memory Issues**
   - Implement batch processing
   - Monitor vector count
   - Clean up unused vectors

3. **Quality Issues**
   - Adjust similarity thresholds
   - Review chunking strategy
   - Validate input content

## Maintenance

1. **Regular Tasks**
   - Vector cleanup
   - Index optimization
   - Backup verification

2. **Optimization**
   ```python
   async def optimize_store():
       # Compact storage
       await store.compact()
       
       # Optimize indexes
       await store.optimize_indexes()
       
       # Verify integrity
       await store.verify_integrity()
   ```

Remember to monitor system performance and adjust these configurations based on your specific use case and requirements.
