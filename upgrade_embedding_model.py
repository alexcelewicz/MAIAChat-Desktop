# upgrade_embedding_model.py
from rag_handler import RAGHandler
import os
import sys
from pathlib import Path

def upgrade_embedding_model():
    print("=" * 80)
    print("EMBEDDING MODEL UPGRADE UTILITY".center(80))
    print("=" * 80)
    print("This script will upgrade your embedding model from all-MiniLM-L6-v2 (384 dimensions)")
    print("to all-mpnet-base-v2 (768 dimensions), which provides significantly better performance.")
    print()
    print("WARNING: This process will clear your existing knowledge base index to rebuild it.")
    print("         Your original files will not be deleted, but the embeddings will be regenerated.")
    print()
    
    if input("Do you wish to continue? (y/n): ").lower() != 'y':
        print("Upgrade cancelled.")
        return
    
    try:
        print("\nInitializing RAG handler with the new model...")
        
        # Initialize the RAG handler with the new model
        rag_handler = RAGHandler(
            persist_directory="./knowledge_base",
            use_openai=False,
            embedding_model="all-mpnet-base-v2",
            dimension=768,  # New dimension for all-mpnet-base-v2
            chunk_size=500,
            chunk_overlap=50,
            chunking_strategy="contextual"
        )
        
        # Get a list of indexed files before clearing
        print("Getting list of currently indexed files...")
        indexed_files = rag_handler.get_indexed_files_detailed()
        
        # Clear the existing knowledge base
        print("Clearing existing knowledge base to rebuild with new model dimensions...")
        rag_handler.clear_knowledge_base()
        
        # Rebuild the index
        print("Knowledge base cleared successfully.")
        
        # Ask to re-add previously indexed files
        if indexed_files and input("\nWould you like to re-add previously indexed files? (y/n): ").lower() == 'y':
            file_paths = []
            for file_info in indexed_files:
                file_path = file_info.get('path')
                if file_path and os.path.exists(file_path):
                    file_paths.append(file_path)
                    
            if file_paths:
                print(f"\nRe-adding {len(file_paths)} previously indexed files...")
                results = rag_handler.batch_add_files(file_paths)
                success_count = sum(1 for result in results.values() if result)
                print(f"Successfully re-added {success_count} of {len(file_paths)} files.")
            else:
                print("No valid files found to re-add.")
        
        # Optionally re-add files from code_archives
        code_archives_dir = Path("./code_archives")
        if code_archives_dir.exists() and input("\nWould you like to add files from code_archives directory? (y/n): ").lower() == 'y':
            print(f"Adding files from {code_archives_dir}...")
            results = rag_handler.add_directory(str(code_archives_dir), recursive=True)
            success = sum(1 for result in results.values() if result)
            print(f"Successfully added {success} of {len(results)} files.")
        
        print("\n" + "=" * 80)
        print("EMBEDDING MODEL UPGRADE COMPLETE".center(80))
        print("=" * 80)
        print("The system will now use the all-mpnet-base-v2 model (768 dimensions) for embeddings.")
        print("You can now run the application normally.")
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        print("Upgrade failed. Please check the error message above.")
        sys.exit(1)

if __name__ == "__main__":
    upgrade_embedding_model() 