#!/usr/bin/env python3
"""
Fix RAG Index Corruption

This script fixes the issue where the FAISS index contains invalid indices
that are out of bounds for the current metadata.
"""

import pickle
import numpy as np
import faiss
import os
import sys
sys.path.append('.')
from rag_handler import RAGHandler

def fix_rag_index():
    print("=== Fixing RAG Index ===")
    
    # Initialize RAG handler
    rag_handler = RAGHandler(
        persist_directory="./knowledge_base",
        use_openai=False,
        embedding_model="all-mpnet-base-v2",
        dimension=768,
        chunk_size=500,
        chunk_overlap=50
    )
    
    print(f"Current chunks: {len(rag_handler.chunks)}")
    print(f"Current metadata: {len(rag_handler.metadatas)}")
    print(f"Current index size: {rag_handler.index.ntotal}")
    
    # Check if there's a mismatch
    if rag_handler.index.ntotal != len(rag_handler.chunks):
        print(f"WARNING: Index size ({rag_handler.index.ntotal}) doesn't match chunks ({len(rag_handler.chunks)})")
        print("Rebuilding index...")
        
        # Create a new index with the correct size
        new_index = rag_handler._create_index()
        
        # Get embeddings for the current chunks
        if rag_handler.chunks:
            print("Generating embeddings for current chunks...")
            embeddings = rag_handler._get_embeddings(rag_handler.chunks)
            new_index.add(embeddings.astype(np.float32))
            print(f"Added {len(rag_handler.chunks)} embeddings to new index")
        
        # Replace the old index
        rag_handler.index = new_index
        
        # Save the fixed index
        rag_handler.save_index()
        print("Index rebuilt and saved successfully")
    else:
        print("Index size matches chunks - no rebuild needed")
    
    # Test the fix
    print("\n--- Testing fixed index ---")
    test_query = "what is invoice for"
    chunks = rag_handler.get_relevant_chunks(
        test_query,
        n_results=3,
        filter_criteria=None,
        reranking=False,
        query_expansion=False
    )
    print(f"Test query returned {len(chunks)} chunks")
    
    if chunks:
        print("Sample chunk:")
        print(f"  Content: {chunks[0]['content'][:100]}...")
        print(f"  File: {chunks[0]['metadata'].file_name}")
        print(f"  Importance: {chunks[0]['metadata'].importance_score}")
    else:
        print("No chunks returned - there may still be an issue")

if __name__ == "__main__":
    fix_rag_index() 