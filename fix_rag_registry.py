#!/usr/bin/env python3
"""
Fix RAG Registry Mismatch

This script fixes the issue where the file registry is empty but metadata contains chunks.
It rebuilds the file registry from the existing metadata to restore consistency.
"""

import pickle
import json
import os
import time
from pathlib import Path
from collections import defaultdict

def fix_rag_registry():
    print("=== RAG Registry Fix ===")
    
    metadata_path = "knowledge_base/metadata.pkl"
    registry_path = "knowledge_base/file_registry.json"
    
    if not os.path.exists(metadata_path):
        print("Metadata file not found. Cannot fix registry.")
        return False
    
    try:
        # Load existing metadata
        with open(metadata_path, 'rb') as f:
            data = pickle.load(f)
        
        chunks = data.get('chunks', [])
        metadatas = data.get('metadatas', [])
        
        print(f"Found {len(chunks)} chunks and {len(metadatas)} metadata entries")
        
        if not metadatas:
            print("No metadata entries found. Nothing to fix.")
            return False
        
        # Group metadata by file name
        file_groups = defaultdict(list)
        for metadata in metadatas:
            file_groups[metadata.file_name].append(metadata)
        
        print(f"Found {len(file_groups)} unique files in metadata:")
        for filename in sorted(file_groups.keys()):
            chunk_count = len(file_groups[filename])
            print(f"  - {filename}: {chunk_count} chunks")
        
        # Create new file registry
        new_registry = {}
        current_time = int(time.time() * 1000)
        
        for filename, metadata_list in file_groups.items():
            # Get the first metadata entry for this file
            first_metadata = metadata_list[0]
            
            # Check if file still exists
            file_exists = os.path.exists(filename)
            
            # Create registry entry
            registry_entry = {
                "hash": "unknown",  # We don't have the original hash
                "path": filename,
                "chunk_count": len(metadata_list),
                "timestamp": current_time,
                "last_modified": current_time,
                "size": 0,  # We don't have the original size
                "embedding_model": getattr(first_metadata, 'embedding_model', 'all-mpnet-base-v2'),
                "provider": "sentence_transformer",
                "previous_versions": [],
                "version_count": 1,
                "file_exists": file_exists
            }
            
            new_registry[filename] = registry_entry
        
        # Save the new registry
        with open(registry_path, 'w') as f:
            json.dump(new_registry, f, indent=4)
        
        print(f"\nFixed file registry with {len(new_registry)} files")
        print(f"Registry saved to {registry_path}")
        
        # Show summary
        existing_files = sum(1 for entry in new_registry.values() if entry.get('file_exists', False))
        missing_files = len(new_registry) - existing_files
        
        print(f"\nSummary:")
        print(f"  - Total files in registry: {len(new_registry)}")
        print(f"  - Files that still exist: {existing_files}")
        print(f"  - Files that are missing: {missing_files}")
        
        if missing_files > 0:
            print(f"\nMissing files (chunks still available but files deleted):")
            for filename, entry in new_registry.items():
                if not entry.get('file_exists', False):
                    print(f"  - {filename}")
        
        return True
        
    except Exception as e:
        print(f"Error fixing registry: {e}")
        import traceback
        traceback.print_exc()
        return False

def clean_missing_files():
    """
    Remove chunks for files that no longer exist.
    This is an optional cleanup step.
    """
    print("\n=== Cleaning Missing Files ===")
    
    metadata_path = "knowledge_base/metadata.pkl"
    registry_path = "knowledge_base/file_registry.json"
    
    if not os.path.exists(metadata_path):
        print("Metadata file not found.")
        return False
    
    try:
        # Load existing data
        with open(metadata_path, 'rb') as f:
            data = pickle.load(f)
        
        chunks = data.get('chunks', [])
        metadatas = data.get('metadatas', [])
        
        # Find missing files
        missing_files = set()
        for metadata in metadatas:
            if not os.path.exists(metadata.file_name):
                missing_files.add(metadata.file_name)
        
        if not missing_files:
            print("No missing files found.")
            return True
        
        print(f"Found {len(missing_files)} missing files:")
        for filename in sorted(missing_files):
            print(f"  - {filename}")
        
        # Ask user if they want to clean
        response = input("\nDo you want to remove chunks for missing files? (y/N): ").strip().lower()
        if response != 'y':
            print("Skipping cleanup.")
            return True
        
        # Remove chunks for missing files
        new_chunks = []
        new_metadatas = []
        
        for i, metadata in enumerate(metadatas):
            if metadata.file_name not in missing_files:
                new_chunks.append(chunks[i])
                new_metadatas.append(metadata)
        
        # Update data
        data['chunks'] = new_chunks
        data['metadatas'] = new_metadatas
        
        # Save updated metadata
        with open(metadata_path, 'wb') as f:
            pickle.dump(data, f)
        
        print(f"Removed {len(chunks) - len(new_chunks)} chunks for missing files")
        print(f"Remaining chunks: {len(new_chunks)}")
        
        # Update registry to remove missing files
        if os.path.exists(registry_path):
            with open(registry_path, 'r') as f:
                registry = json.load(f)
            
            # Remove missing files from registry
            for filename in missing_files:
                if filename in registry:
                    del registry[filename]
            
            with open(registry_path, 'w') as f:
                json.dump(registry, f, indent=4)
            
            print(f"Updated registry to remove {len(missing_files)} missing files")
        
        return True
        
    except Exception as e:
        print(f"Error cleaning missing files: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("RAG Registry Fix Tool")
    print("This tool fixes the mismatch between file registry and metadata.")
    print()
    
    # Fix the registry
    if fix_rag_registry():
        print("\nRegistry fix completed successfully!")
        
        # Offer to clean missing files
        print("\n" + "="*50)
        clean_missing_files()
    else:
        print("\nRegistry fix failed!") 