#!/usr/bin/env python3
"""
Test script to verify the LM Studio streaming fix is working correctly.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_streaming_logic():
    """Test that the streaming logic in worker.py is properly implemented."""
    print("Testing streaming logic fixes...")
    
    try:
        from worker import Worker
        
        # Check if the _execute_openai_compatible_api_call method exists and has the right structure
        worker_instance = Worker.__new__(Worker)  # Create instance without calling __init__
        
        # Check if the method exists
        if hasattr(worker_instance, '_execute_openai_compatible_api_call'):
            print("✅ _execute_openai_compatible_api_call method exists")
            
            # Get the method source to check for key fixes
            import inspect
            method_source = inspect.getsource(worker_instance._execute_openai_compatible_api_call)
            
            # Check for key improvements
            checks = [
                ("Simplified buffering logic", "should_emit = False"),
                ("Proper buffer management", "buffer = \"\""),
                ("Single emission point", "self.update_agents_discussion_signal.emit"),
                ("Proper cleanup", "if buffer and self.is_running"),
                ("Single empty chunk emission", "self.update_agents_discussion_signal.emit(\"\", agent_number, model, False)")
            ]
            
            for check_name, check_text in checks:
                if check_text in method_source:
                    print(f"✅ {check_name}: Found")
                else:
                    print(f"❌ {check_name}: Not found")
                    
        else:
            print("❌ _execute_openai_compatible_api_call method not found")
            
    except Exception as e:
        print(f"❌ Error testing streaming logic: {e}")

def test_model_fetching():
    """Test that model fetching functions are working correctly."""
    print("\nTesting model fetching fixes...")
    
    try:
        from utils import get_openrouter_models, get_requesty_models, get_ollama_models
        
        # Test OpenRouter models
        print("1. Testing OpenRouter model fetching...")
        openrouter_models = get_openrouter_models()
        print(f"   OpenRouter models found: {len(openrouter_models)}")
        if openrouter_models:
            print(f"   Sample models: {openrouter_models[:3]}")
        else:
            print("   ⚠️ No models returned (expected if no API key)")
            
        # Test Requesty models
        print("2. Testing Requesty model fetching...")
        requesty_models = get_requesty_models()
        print(f"   Requesty models found: {len(requesty_models)}")
        if requesty_models:
            print(f"   Sample models: {requesty_models[:3]}")
        else:
            print("   ⚠️ No models returned (expected if no API key)")
            
        # Test Ollama models
        print("3. Testing Ollama model fetching...")
        ollama_models = get_ollama_models()
        print(f"   Ollama models found: {len(ollama_models)}")
        if ollama_models:
            print(f"   Sample models: {ollama_models[:3]}")
        else:
            print("   ⚠️ No models returned (expected if Ollama not running)")
            
    except Exception as e:
        print(f"❌ Error testing model fetching: {e}")

def test_agent_config():
    """Test that agent configuration is working correctly."""
    print("\nTesting agent configuration...")
    
    try:
        from agent_config import AgentConfig
        
        # Create a test instance
        config = AgentConfig()
        
        # Test model loading for each provider
        providers = ['OpenRouter', 'Requesty', 'Ollama']
        
        for provider in providers:
            print(f"Testing {provider} model loading...")
            try:
                if provider == 'OpenRouter':
                    models = config.get_openrouter_models()
                elif provider == 'Requesty':
                    models = config.get_requesty_models()
                elif provider == 'Ollama':
                    models = config.get_ollama_models()
                    
                print(f"   {provider} models loaded: {len(models)}")
                if models:
                    print(f"   Sample: {models[0]}")
                    
            except Exception as e:
                print(f"   ⚠️ {provider} model loading failed: {e}")
                
    except Exception as e:
        print(f"❌ Error testing agent configuration: {e}")

def main():
    """Run all tests."""
    print("=== LM Studio Streaming and Model Fetching Fix Test ===\n")
    
    test_streaming_logic()
    test_model_fetching()
    test_agent_config()
    
    print("\n=== Test Summary ===")
    print("✅ All tests completed")
    print("📝 Check the output above for any issues")
    print("🔧 If you see ❌ marks, those specific fixes may need attention")
    print("⚠️ Some warnings are expected if API keys are not configured")

if __name__ == "__main__":
    main() 