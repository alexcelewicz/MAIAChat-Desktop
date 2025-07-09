#!/usr/bin/env python3
import sys
sys.path.append('.')
from rag_handler import RAGHandler

def test_rag_query():
    print("=== Testing RAG Query ===")
    
    # Initialize RAG handler
    rag_handler = RAGHandler(
        persist_directory="./knowledge_base",
        use_openai=False,
        embedding_model="all-mpnet-base-v2",
        dimension=768,
        chunk_size=500,
        chunk_overlap=50
    )
    
    # Test query
    query = "what is invoice for"
    
    print(f"Testing query: '{query}'")
    print(f"Total chunks in index: {len(rag_handler.chunks)}")
    print(f"Total metadata entries: {len(rag_handler.metadatas)}")
    
    # Test without any filters first
    print("\n--- Testing without filters ---")
    chunks_no_filter = rag_handler.get_relevant_chunks(
        query,
        n_results=5,
        filter_criteria=None,
        reranking=False,
        query_expansion=False
    )
    print(f"Results without filter: {len(chunks_no_filter)}")
    
    # Test with importance score filter
    print("\n--- Testing with importance score filter (0.3) ---")
    chunks_with_filter = rag_handler.get_relevant_chunks(
        query,
        n_results=5,
        filter_criteria={"importance_score": 0.3},
        reranking=False,
        query_expansion=False
    )
    print(f"Results with importance filter: {len(chunks_with_filter)}")
    
    # Test with language filter
    print("\n--- Testing with language filter (en) ---")
    chunks_with_lang_filter = rag_handler.get_relevant_chunks(
        query,
        n_results=5,
        filter_criteria={"language": "en"},
        reranking=False,
        query_expansion=False
    )
    print(f"Results with language filter: {len(chunks_with_lang_filter)}")
    
    # Test with both filters
    print("\n--- Testing with both filters ---")
    chunks_with_both = rag_handler.get_relevant_chunks(
        query,
        n_results=5,
        filter_criteria={"importance_score": 0.3, "language": "en"},
        reranking=False,
        query_expansion=False
    )
    print(f"Results with both filters: {len(chunks_with_both)}")
    
    # Check metadata details
    print("\n--- Metadata Details ---")
    for i, metadata in enumerate(rag_handler.metadatas[:3]):
        print(f"Metadata {i+1}:")
        print(f"  File: {metadata.file_name}")
        print(f"  Importance: {metadata.importance_score}")
        print(f"  Language: {metadata.language}")
        print(f"  Source type: {metadata.source_type}")

if __name__ == "__main__":
    test_rag_query() 