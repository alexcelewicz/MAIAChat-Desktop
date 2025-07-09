#!/usr/bin/env python3
import pickle
import sys
sys.path.append('.')

def check_importance_scores():
    try:
        with open('knowledge_base/metadata.pkl', 'rb') as f:
            data = pickle.load(f)
        
        metadatas = data.get('metadatas', [])
        print(f"Total metadata entries: {len(metadatas)}")
        
        if metadatas:
            print("\nFirst 5 importance scores:")
            for i, metadata in enumerate(metadatas[:5]):
                print(f"  {i+1}. {metadata.importance_score}")
            
            print(f"\nAll importance scores:")
            scores = [m.importance_score for m in metadatas]
            print(f"  Min: {min(scores)}")
            print(f"  Max: {max(scores)}")
            print(f"  Average: {sum(scores)/len(scores):.3f}")
            
            # Check how many would pass different thresholds
            thresholds = [0.1, 0.2, 0.3, 0.4, 0.5]
            for threshold in thresholds:
                count = sum(1 for s in scores if s >= threshold)
                print(f"  >= {threshold}: {count}/{len(scores)} ({count/len(scores)*100:.1f}%)")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_importance_scores() 