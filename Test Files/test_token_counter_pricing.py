#!/usr/bin/env python3
# test_token_counter_pricing.py - Test script for token counter pricing loading

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from token_counter import TokenCounter
    
    print("Testing TokenCounter pricing loading...")
    
    # Create a new instance
    tc = TokenCounter()
    
    # Check if pricing was loaded
    print(f"Pricing loaded successfully: {bool(tc.pricing)}")
    
    # Check specific providers
    if tc.pricing:
        print(f"Number of providers: {len(tc.pricing)}")
        print(f"Providers: {list(tc.pricing.keys())}")
        
        # Check OpenAI models
        openai_models = tc.pricing.get('OpenAI', {})
        print(f"OpenAI models: {list(openai_models.keys())}")
        print(f"Number of OpenAI models: {len(openai_models)}")
        
        # Check Anthropic models
        anthropic_models = tc.pricing.get('Anthropic', {})
        print(f"Anthropic models: {list(anthropic_models.keys())}")
        print(f"Number of Anthropic models: {len(anthropic_models)}")
        
        # Test a specific model pricing
        if 'gpt-4o' in openai_models:
            gpt4o_pricing = openai_models['gpt-4o']
            print(f"GPT-4o pricing: {gpt4o_pricing}")
        
        print("✅ TokenCounter pricing loading test PASSED")
    else:
        print("❌ TokenCounter pricing loading test FAILED - No pricing loaded")
        
except Exception as e:
    print(f"❌ Error testing TokenCounter: {e}")
    import traceback
    traceback.print_exc() 