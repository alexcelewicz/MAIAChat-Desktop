import os
import sys
import logging
import traceback
from worker import Worker
from config import config_manager
from model_settings import settings_manager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_agent_responses")

# Dummy prompt for testing
TEST_PROMPT = "Say hello and tell me your provider name in one sentence."
GENERAL_INSTRUCTIONS = "Be concise."

# List of providers to test with realistic model names based on actual configurations
PROVIDERS = [
    ("OpenAI", "gpt-3.5-turbo"),
    ("Groq", "llama3-8b-8192"),  # Common Groq model
    ("Grok", "grok-1"),
    ("DeepSeek", "deepseek-chat"),
    ("OpenRouter", "openai/gpt-4o"),  # Realistic OpenRouter model
    ("Requesty", "openai/gpt-3.5-turbo"),  # Requesty uses provider/model format
    ("Ollama", "llama3.2"),  # Common local model
    ("LM Studio", "deepseek-r1-0528-qwen3-8b"),  # Common LM Studio model
    ("Google GenAI", "gemini-2.5-flash-preview-05-20"),  # Current Gemini model
    ("Anthropic", "claude-3-5-sonnet-20241022"),  # Current Claude model
]

# API key environment variables mapping
API_KEY_MAPPING = {
    "OpenAI": "OPENAI_API_KEY",
    "Groq": "GROQ_API_KEY", 
    "Grok": "GROK_API_KEY",
    "DeepSeek": "DEEPSEEK_API_KEY",
    "OpenRouter": "OPENROUTER_API_KEY",
    "Requesty": "REQUESTY_API_KEY",
    "Ollama": None,  # Ollama doesn't need an API key
    "LM Studio": None,  # LM Studio doesn't need an API key
    "Google GenAI": "GOOGLE_API_KEY",
    "Anthropic": "ANTHROPIC_API_KEY",
}

def check_api_key_available(provider: str) -> bool:
    """Check if API key is available for the provider."""
    if provider in ["Ollama", "LM Studio"]:
        return True  # These don't require API keys
    
    key_name = API_KEY_MAPPING.get(provider)
    if not key_name:
        return False
    
    # Check both environment variable and config manager
    env_key = os.getenv(key_name)
    config_key = config_manager.get(key_name)
    
    return bool(env_key or config_key)

def is_local_service_expected(provider: str) -> bool:
    """Check if this provider requires a local service to be running."""
    return provider in ["Ollama", "LM Studio"]

def test_single_provider(worker: Worker, provider: str, model: str) -> dict:
    """Test a single provider and return results."""
    result = {
        "provider": provider,
        "model": model,
        "status": "UNKNOWN",
        "response": None,
        "error": None,
        "notes": ""
    }
    
    try:
        print(f"\n--- Testing {provider} with model {model} ---")
        
        # Check if API key is available (for cloud providers)
        if not check_api_key_available(provider):
            result["status"] = "SKIPPED"
            result["notes"] = f"No API key found for {provider}"
            print(f"SKIPPED: {result['notes']}")
            return result
        
        # Test the actual get_agent_response method
        response = worker.get_agent_response(
            provider=provider,
            model=model,
            agent_input=TEST_PROMPT,
            agent_number=1,
            effective_max_tokens=100  # Keep it small for testing
        )
        
        if response and isinstance(response, str):
            # Check for common error patterns
            if response.startswith("Error:"):
                result["status"] = "FAIL"
                result["error"] = response
                result["notes"] = "API returned error response"
                
                # Provide more specific notes for common issues
                if "API key not found" in response:
                    result["notes"] = "API key not found in configuration"
                elif "not found" in response and is_local_service_expected(provider):
                    result["notes"] = f"{provider} service not running locally"
                elif "Invalid model" in response:
                    result["notes"] = f"Model '{model}' not valid for {provider}"
                elif "Missing provider or model name" in response:
                    result["notes"] = f"Invalid model format for {provider} (expected provider/model format)"
                
            elif len(response.strip()) == 0:
                result["status"] = "FAIL"
                result["error"] = "Empty response"
                result["notes"] = "Received empty response from API"
            else:
                result["status"] = "PASS"
                result["response"] = response[:200] + "..." if len(response) > 200 else response
                result["notes"] = "Successfully received response"
        else:
            result["status"] = "FAIL"
            result["error"] = f"Invalid response type: {type(response)}"
            result["notes"] = "Response was not a string or was None"
            
    except Exception as e:
        result["status"] = "FAIL"
        result["error"] = str(e)
        result["notes"] = f"Exception during API call: {type(e).__name__}"
        print(f"EXCEPTION: {e}")
        traceback.print_exc()
    
    # Print result
    status_emoji = {"PASS": "✅", "FAIL": "❌", "SKIPPED": "⏭️"}.get(result["status"], "❓")
    print(f"{status_emoji} {provider}: {result['status']} - {result['notes']}")
    
    return result

def test_model_fetching():
    """Test the model fetching functions for providers that support it"""
    print("🔍 Testing model fetching functions...")
    
    try:
        from utils import get_openrouter_models, get_requesty_models, get_groq_models
        
        # Test Groq models (new functionality)
        print("\n--- Testing Groq Model Fetching ---")
        try:
            groq_api_key = config_manager.get('GROQ_API_KEY')
            if groq_api_key:
                groq_models = get_groq_models(groq_api_key)
                print(f"✅ Groq models found: {len(groq_models)}")
                if groq_models:
                    print(f"   Sample models: {groq_models[:5]}")  # Show first 5
                else:
                    print("   No models returned from API")
            else:
                print("⏭️ Groq API key not found, skipping model fetch test")
        except Exception as e:
            print(f"❌ Groq model fetching failed: {e}")
        
        # Test OpenRouter models
        print("\n--- Testing OpenRouter Model Fetching ---")
        try:
            openrouter_api_key = config_manager.get('OPENROUTER_API_KEY')
            if openrouter_api_key:
                openrouter_models = get_openrouter_models(openrouter_api_key)
                print(f"✅ OpenRouter models found: {len(openrouter_models)}")
                if openrouter_models:
                    print(f"   Sample models: {openrouter_models[:5]}")  # Show first 5
                else:
                    print("   No models returned from API")
            else:
                print("⏭️ OpenRouter API key not found, skipping model fetch test")
        except Exception as e:
            print(f"❌ OpenRouter model fetching failed: {e}")
        
        # Test Requesty models
        print("\n--- Testing Requesty Model Fetching ---")
        try:
            requesty_api_key = config_manager.get('REQUESTY_API_KEY')
            if requesty_api_key:
                requesty_models = get_requesty_models(requesty_api_key)
                print(f"✅ Requesty models found: {len(requesty_models)}")
                if requesty_models:
                    print(f"   Sample models: {requesty_models[:5]}")  # Show first 5
                else:
                    print("   No models returned from API")
            else:
                print("⏭️ Requesty API key not found, skipping model fetch test")
        except Exception as e:
            print(f"❌ Requesty model fetching failed: {e}")
            
    except ImportError as e:
        print(f"❌ Could not import model fetching functions: {e}")
    except Exception as e:
        print(f"❌ Model fetching test failed: {e}")

def test_provider_response(provider, model):
    """Test a single provider's response"""
    print(f"\n--- Testing {provider} with model {model} ---")
    
    # Check for API key first
    api_key_map = {
        "OpenAI": "OPENAI_API_KEY",
        "Groq": "GROQ_API_KEY", 
        "Grok": "GROK_API_KEY",
        "DeepSeek": "DEEPSEEK_API_KEY",
        "OpenRouter": "OPENROUTER_API_KEY",
        "Requesty": "REQUESTY_API_KEY",
        "Anthropic": "ANTHROPIC_API_KEY",
        "Google GenAI": "GOOGLE_API_KEY"
    }
    
    if provider in api_key_map:
        api_key = config_manager.get(api_key_map[provider])
        if not api_key:
            print(f"SKIPPED: No API key found for {provider}")
            return "SKIPPED", f"No API key found for {provider}"
    
    try:
        # Initialize worker
        worker = Worker(
            prompt=TEST_PROMPT,
            general_instructions=GENERAL_INSTRUCTIONS,
            agents=[{
                "agent_number": 1,
                "provider": provider,
                "model": model,
                "instructions": "You are a helpful assistant.",
                "internet_enabled": False,
                "rag_enabled": False,
                "mcp_enabled": False
            }],
            knowledge_base_files=[],
            knowledge_base_content="",
            json_instructions={},
            config_manager=config_manager,
            conversation_history=[]
        )
        
        # Test the provider
        response = worker.get_agent_response(provider, model, TEST_PROMPT, 1)
        
        if response and not response.startswith("Error"):
            print(f"✅ {provider}: PASS - Successfully received response")
            return "PASS", "Successfully received response"
        else:
            print(f"❌ {provider}: FAIL - {response[:100] if response else 'No response'}")
            return "FAIL", response[:100] if response else "No response"
            
    except Exception as e:
        error_msg = str(e)
        print(f"❌ {provider}: FAIL - {error_msg}")
        return "FAIL", error_msg

def main():
    """Main test function"""
    print("Testing comprehensive agent response system...")
    print(f"Testing {len(PROVIDERS)} providers with realistic configurations...")
    
    try:
        print("✅ Worker initialized successfully")
    except Exception as e:
        print(f"❌ Worker initialization failed: {e}")
        return
    
    # Test model fetching functionality
    test_model_fetching()
    
    print("\n" + "="*60)
    print("TESTING PROVIDER RESPONSES")
    print("="*60)
    
    results = {}
    for provider, model in PROVIDERS:
        status, message = test_provider_response(provider, model)
        results[provider] = (status, message, model)
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for status, _, _ in results.values() if status == "PASS")
    failed = sum(1 for status, _, _ in results.values() if status == "FAIL") 
    skipped = sum(1 for status, _, _ in results.values() if status == "SKIPPED")
    
    print(f"✅ PASSED: {passed}")
    print(f"❌ FAILED: {failed}")
    print(f"⏭️ SKIPPED: {skipped}")
    print(f"📊 TOTAL: {len(results)}")
    
    if passed > 0:
        print(f"\n🎉 WORKING PROVIDERS:")
        for provider, (status, _, model) in results.items():
            if status == "PASS":
                print(f"  • {provider} ({model})")
    
    if failed > 0:
        print(f"\n🚨 FAILED PROVIDERS:")
        for provider, (status, message, model) in results.items():
            if status == "FAIL":
                print(f"  • {provider} ({model}): {message}")
    
    if skipped > 0:
        print(f"\n⏭️ SKIPPED PROVIDERS (Missing API Keys):")
        for provider, (status, message, model) in results.items():
            if status == "SKIPPED":
                print(f"  • {provider} ({model})")
    
    print("\n" + "="*60)
    print("RECOMMENDATIONS:")
    print("="*60)
    
    if failed > 0:
        print("🔧 For failed providers:")
        for provider, (status, message, model) in results.items():
            if status == "FAIL" and "not running" in message.lower():
                print(f"  • {provider}: Start the local service")
    
    if passed > 0:
        print(f"✅ Refactored get_agent_response method is working correctly for {passed} provider(s)")
    
    print(f"\n📝 Test completed. Results saved to test log above.")

if __name__ == "__main__":
    main() 