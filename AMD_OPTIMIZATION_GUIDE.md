# AMD Ryzen Optimization Guide for Python Agents

## Overview

This guide provides specific optimization recommendations for AMD Ryzen systems with integrated graphics (like your AMD Ryzen Max AI 395) to achieve the best performance and stability with the Python Agents application.

## AMD Ryzen Specific Considerations

### Why CPU Mode is Recommended for AMD Integrated Graphics

1. **Stability**: AMD integrated graphics drivers can sometimes have compatibility issues with PyTorch GPU acceleration
2. **Memory Management**: Integrated graphics share system memory, which can lead to memory conflicts
3. **Driver Maturity**: GPU acceleration libraries are primarily optimized for NVIDIA CUDA
4. **Performance**: For RAG operations, CPU mode often provides more consistent performance on AMD systems

## Current Configuration

Your system is now configured with AMD-optimized settings:

```json
{
    "RAG_ULTRA_SAFE_MODE": false,
    "RAG_SAFE_RETRIEVAL_MODE": false,
    "EMBEDDING_DEVICE": "cpu"
}
```

## Performance Optimizations

### 1. RAG Quality Improvements

The recent updates have improved RAG response quality by:

- **Increased Results**: From 15 to 25 chunks per query
- **Better Filtering**: Reduced importance score threshold from 0.5 to 0.3
- **More Context**: Increased token limit from 4096 to 8192 tokens
- **Improved Balance**: Alpha parameter increased from 0.5 to 0.6

### 2. AMD-Specific Performance Tips

#### Memory Management
```bash
# Monitor memory usage during RAG operations
python -c "import psutil; print(f'Memory: {psutil.virtual_memory().percent}%')"
```

#### CPU Optimization
- Ensure your AMD Ryzen is running in performance mode
- Close unnecessary background applications during RAG operations
- Consider using smaller embedding models for faster processing

#### Recommended Embedding Models for AMD
- `all-MiniLM-L6-v2` (384 dimensions) - Fastest, good quality
- `all-mpnet-base-v2` (768 dimensions) - Better quality, moderate speed
- Avoid very large models like `all-mpnet-base-v2` on integrated graphics

## Troubleshooting

### Common Issues and Solutions

#### 1. Slow RAG Performance
**Symptoms**: RAG operations take a long time
**Solutions**:
- Use smaller embedding models
- Reduce the number of files in knowledge base
- Enable safe retrieval mode temporarily

#### 2. Memory Issues
**Symptoms**: Application crashes or becomes unresponsive
**Solutions**:
- Reduce chunk size in RAG handler
- Process fewer files at once
- Monitor system memory usage

#### 3. Inconsistent Results
**Symptoms**: RAG responses vary in quality
**Solutions**:
- Ensure knowledge base is properly indexed
- Check file formats are supported
- Verify embedding model compatibility

## Advanced Configuration

### Custom RAG Settings for AMD

You can further customize RAG behavior by editing `worker.py`:

```python
# In load_knowledge_base_content method
chunks = self.rag_handler.get_relevant_chunks(
    query,
    n_results=20,  # Adjust based on your needs
    alpha=0.6,     # Balance between semantic and keyword search
    filter_criteria={
        "importance_score": 0.3,  # Lower = more results
        "language": "en"
    },
    reranking=True,
    cross_encoder_reranking=False,  # Disable for better performance
    query_expansion=True
)
```

### Performance Monitoring

Use the built-in performance monitor:

```python
# Check performance metrics
from performance_monitor import performance_monitor
stats = performance_monitor.get_stats()
print(f"API calls: {len(stats['api_calls'])}")
print(f"Average latency: {sum(call['latency'] for call in stats['api_calls']) / len(stats['api_calls']):.2f}s")
```

## Future GPU Support

### AMD ROCm (Future Consideration)

If you upgrade to a dedicated AMD GPU with ROCm support:

1. Install PyTorch with ROCm support
2. Change `EMBEDDING_DEVICE` to `"auto"`
3. Disable safe modes for better performance

### OpenCL Support (Experimental)

For integrated graphics acceleration:

```bash
pip install pyopencl
```

Then modify the RAG handler to use OpenCL acceleration (experimental).

## Testing Your Configuration

### 1. Run the AMD Optimization Script

```bash
python gpu_optimization.py
```

This will automatically detect your AMD system and apply optimal settings.

### 2. Test RAG Quality

```bash
python rag_quality_optimizer.py
```

This will analyze your current RAG configuration and provide recommendations.

### 3. Performance Benchmark

1. Add some test files to your knowledge base
2. Run a query that should use RAG
3. Monitor response time and quality
4. Compare with previous results

## Expected Performance

With these optimizations, you should see:

- **Stability**: No crashes or memory issues
- **Quality**: More detailed and relevant RAG responses
- **Speed**: Reasonable performance for RAG operations
- **Consistency**: Reliable results across different queries

## Support

If you encounter issues:

1. Check the application logs for error messages
2. Run the optimization scripts to verify settings
3. Monitor system resources during operation
4. Consider reducing the scope of RAG operations if needed

## Summary

Your AMD Ryzen Max AI 395 is now optimized for:

✅ **Stable Performance**: CPU mode prevents GPU-related issues  
✅ **Better Quality**: Improved RAG settings for more detailed responses  
✅ **Memory Efficiency**: Optimized settings for integrated graphics  
✅ **Consistent Results**: Reliable RAG functionality  

The application should now provide better RAG response quality while maintaining stability on your AMD system. 