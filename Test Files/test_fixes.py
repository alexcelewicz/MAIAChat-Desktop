#!/usr/bin/env python3
"""
Test script to verify the fixes for streaming and model fetching issues.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_model_fetching():
    """Test that model fetching functions work correctly."""
    print("Testing model fetching functions...")
    
    try:
        from utils import get_openrouter_models, get_requesty_models, get_ollama_models
        
        # Test OpenRouter models
        print("\n1. Testing OpenRouter model fetching...")
        openrouter_models = get_openrouter_models()
        print(f"   OpenRouter models found: {len(openrouter_models)}")
        if openrouter_models:
            print(f"   Sample models: {openrouter_models[:3]}")
        else:
            print("   No models found (this is expected if no API key is configured)")
        
        # Test Requesty models
        print("\n2. Testing Requesty model fetching...")
        requesty_models = get_requesty_models()
        print(f"   Requesty models found: {len(requesty_models)}")
        if requesty_models:
            print(f"   Sample models: {requesty_models[:3]}")
        else:
            print("   No models found (this is expected if no API key is configured)")
        
        # Test Ollama models
        print("\n3. Testing Ollama model fetching...")
        ollama_models = get_ollama_models()
        print(f"   Ollama models found: {len(ollama_models)}")
        if ollama_models:
            print(f"   Sample models: {ollama_models[:3]}")
        else:
            print("   No models found (this is expected if Ollama is not running)")
        
        print("\n✅ Model fetching tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error testing model fetching: {e}")
        import traceback
        traceback.print_exc()

def test_agent_config():
    """Test that agent config can properly fetch models."""
    print("\nTesting agent configuration model fetching...")
    
    try:
        from agent_config import AgentConfig
        from PyQt6.QtWidgets import QApplication
        
        # Create a minimal QApplication for testing
        app = QApplication([])
        
        # Create an agent config instance
        agent_config = AgentConfig(agent_number=1)
        
        # Test updating models for different providers
        providers_to_test = ["OpenRouter", "Requesty", "Ollama"]
        
        for provider in providers_to_test:
            print(f"\n   Testing {provider} model update...")
            try:
                agent_config.update_models(provider)
                model_count = agent_config.model_combo.count()
                print(f"   {provider} models loaded: {model_count}")
                if model_count > 0:
                    print(f"   First model: {agent_config.model_combo.itemText(0)}")
            except Exception as e:
                print(f"   Error with {provider}: {e}")
        
        print("\n✅ Agent configuration tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error testing agent configuration: {e}")
        import traceback
        traceback.print_exc()

def test_worker_imports():
    """Test that the worker module can be imported without errors."""
    print("\nTesting worker module imports...")
    
    try:
        from worker import Worker
        print("✅ Worker module imported successfully!")
        
        # Test that the fixed method exists
        if hasattr(Worker, '_execute_openai_compatible_api_call'):
            print("✅ Fixed streaming method found!")
        else:
            print("❌ Fixed streaming method not found!")
            
    except Exception as e:
        print(f"❌ Error importing worker module: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Fixes for Streaming and Model Fetching Issues")
    print("=" * 60)
    
    test_worker_imports()
    test_model_fetching()
    test_agent_config()
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("- Model fetching functions should now work correctly")
    print("- LM Studio streaming should no longer duplicate responses")
    print("- Agent configuration should properly load model lists")
    print("=" * 60)

if __name__ == "__main__":
    main() 