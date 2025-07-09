#!/usr/bin/env python3
import pickle
import json
import os

def check_rag_metadata():
    print("=== RAG Metadata Check ===")
    
    # Check file registry
    registry_path = "knowledge_base/file_registry.json"
    if os.path.exists(registry_path):
        with open(registry_path, 'r') as f:
            registry = json.load(f)
        print(f"File registry contains {len(registry)} files:")
        for filename, info in registry.items():
            print(f"  - {filename}: {info.get('chunk_count', 'unknown')} chunks")
    else:
        print("File registry not found")
    
    # Check metadata
    metadata_path = "knowledge_base/metadata.pkl"
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'rb') as f:
                data = pickle.load(f)
            
            chunks = data.get('chunks', [])
            metadatas = data.get('metadatas', [])
            
            print(f"\nMetadata contains {len(chunks)} chunks and {len(metadatas)} metadata entries")
            
            if metadatas:
                print("\nSample metadata entries:")
                for i, metadata in enumerate(metadatas[:3]):
                    print(f"  {i+1}. File: {metadata.file_name}, Type: {metadata.source_type}, Page: {metadata.page_num}")
            
            # Check for file names in metadata
            unique_files = set()
            for metadata in metadatas:
                unique_files.add(metadata.file_name)
            
            print(f"\nUnique files in metadata: {len(unique_files)}")
            for filename in sorted(unique_files):
                print(f"  - {filename}")
                
        except Exception as e:
            print(f"Error reading metadata: {e}")
    else:
        print("Metadata file not found")

if __name__ == "__main__":
    check_rag_metadata() 