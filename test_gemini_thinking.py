#!/usr/bin/env python3
"""
Test script to verify Gemini thinking functionality works correctly.
This script tests both the new google.genai library with thinking and fallback to legacy library.
"""

import os
import sys
from config_manager import ConfigManager

def test_gemini_thinking():
    """Test Gemini thinking functionality."""
    
    # Initialize config manager
    config_manager = ConfigManager()
    api_key = config_manager.get('GOOGLE_API_KEY')
    
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY not found in config")
        return False
    
    print("🧪 Testing Gemini Thinking Functionality")
    print("=" * 50)
    
    # Test 1: Check if google.genai library is available
    try:
        from google import genai
        from google.genai import types
        print("✅ google.genai library is available")
        genai_available = True
    except ImportError as e:
        print(f"❌ google.genai library not available: {e}")
        genai_available = False
    
    # Test 2: Check if legacy google.generativeai library is available
    try:
        import google.generativeai as legacy_genai
        print("✅ google.generativeai (legacy) library is available")
        legacy_available = True
    except ImportError as e:
        print(f"❌ google.generativeai (legacy) library not available: {e}")
        legacy_available = False
    
    if not (genai_available or legacy_available):
        print("❌ No Gemini libraries available")
        return False
    
    # Test 3: Test thinking model with new library
    if genai_available:
        print("\n🧠 Testing thinking model with google.genai...")
        try:
            client = genai.Client(api_key=api_key)
            
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text="Create a simple Python class for a Book")]
                )
            ]
            
            generate_content_config = types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    thinking_budget=-1,
                ),
                response_mime_type="text/plain",
                temperature=1.0,
                top_p=0.95,
                top_k=40,
                max_output_tokens=8000  # Increased to allow for thinking + response
            )
            
            # Try different model names
            models_to_try = [
                "gemini-2.5-flash-preview-05-20",  # Your current model
                "gemini-2.5-flash",
                "gemini-2.5-pro"
            ]

            for model_name in models_to_try:
                try:
                    print(f"📡 Making API call to {model_name}...")
                    response = client.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=generate_content_config
                    )
                    break
                except Exception as e:
                    print(f"❌ Failed with {model_name}: {e}")
                    continue
            else:
                print("❌ All model attempts failed")
                return False

            print(f"🔍 Response object: {type(response)}")
            print(f"🔍 Usage metadata: {response.usage_metadata}")

            # Extract text from candidates
            response_text = ""
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                response_text += part.text

            if response_text:
                print("✅ Thinking model response received!")
                print(f"📝 Response length: {len(response_text)} characters")
                print(f"🔤 First 200 chars: {response_text[:200]}...")
                if hasattr(response, 'usage_metadata') and response.usage_metadata:
                    print(f"🧠 Thoughts tokens: {getattr(response.usage_metadata, 'thoughts_token_count', 0)}")
                    print(f"📊 Total tokens: {getattr(response.usage_metadata, 'total_token_count', 0)}")
                return True
            else:
                print("❌ Empty response from thinking model")
                print(f"🔍 Response text: {getattr(response, 'text', 'No text attribute')}")
                print(f"🔍 Candidates: {response.candidates}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing thinking model: {e}")
            
    # Test 4: Test regular model with legacy library
    if legacy_available:
        print("\n🔄 Testing regular model with legacy library...")
        try:
            legacy_genai.configure(api_key=api_key)
            model = legacy_genai.GenerativeModel("gemini-2.0-pro-exp-02-05")
            
            print("📡 Making API call to gemini-2.0-pro-exp-02-05...")
            response = model.generate_content(
                "Create a simple Python class for a Book",
                generation_config=legacy_genai.types.GenerationConfig(
                    max_output_tokens=1000,
                    temperature=1.0,
                    top_p=0.95,
                    top_k=40
                )
            )
            
            if response and hasattr(response, 'text') and response.text:
                print("✅ Legacy model response received!")
                print(f"📝 Response length: {len(response.text)} characters")
                print(f"🔤 First 200 chars: {response.text[:200]}...")
                return True
            else:
                print("❌ Empty response from legacy model")
                return False
                
        except Exception as e:
            print(f"❌ Error testing legacy model: {e}")
    
    return False

if __name__ == "__main__":
    print("🚀 Starting Gemini Thinking Test")
    success = test_gemini_thinking()
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("✅ Gemini thinking functionality is working")
    else:
        print("\n💥 Test failed!")
        print("❌ Gemini thinking functionality needs attention")
    
    sys.exit(0 if success else 1)
