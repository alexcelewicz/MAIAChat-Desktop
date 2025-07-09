#!/usr/bin/env python3
"""
Test script to verify token usage tracking for agents.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from worker import Worker
from token_counter import TokenCounter

def test_token_usage_tracking():
    """Test the token usage tracking functionality."""
    print("Testing token usage tracking...")
    
    # Create a mock worker instance
    worker = Worker(
        prompt="Test prompt",
        general_instructions="Test instructions",
        agents=[],
        knowledge_base_files=[],
        internet_enabled=False,
        config_manager=None
    )
    
    # Test token usage capture
    print("\nTest 1 - Token usage capture:")
    agent_input = "This is a test input prompt for the agent."
    response = "This is a test response from the agent with some content."
    
    token_usage = worker._capture_agent_token_usage(
        agent_number=1,
        agent_input=agent_input,
        response=response,
        provider="OpenRouter",
        model="anthropic/claude-3-5-sonnet"
    )
    
    print(f"Agent 1 token usage:")
    print(f"  Input tokens: {token_usage['input_tokens']:,}")
    print(f"  Output tokens: {token_usage['output_tokens']:,}")
    print(f"  Total tokens: {token_usage['total_tokens']:,}")
    print(f"  Cost: ${token_usage['cost']:.4f}")
    print(f"  Precise: {token_usage['is_precise']}")
    
    # Test token usage summary
    print("\nTest 2 - Token usage summary:")
    agent_token_usage = [
        {
            "agent_number": 1,
            "input_tokens": 100,
            "output_tokens": 200,
            "total_tokens": 300,
            "cost": 0.0015,
            "is_precise": True,
            "provider": "OpenRouter",
            "model": "anthropic/claude-3-5-sonnet"
        },
        {
            "agent_number": 2,
            "input_tokens": 150,
            "output_tokens": 250,
            "total_tokens": 400,
            "cost": 0.0020,
            "is_precise": True,
            "provider": "OpenRouter",
            "model": "anthropic/claude-3-5-sonnet"
        },
        {
            "agent_number": 3,
            "input_tokens": 200,
            "output_tokens": 300,
            "total_tokens": 500,
            "cost": 0.0025,
            "is_precise": False,
            "provider": "OpenRouter",
            "model": "anthropic/claude-3-5-sonnet"
        }
    ]
    
    # Test the summary calculation logic directly
    total_input_tokens = sum(usage.get('input_tokens', 0) for usage in agent_token_usage)
    total_output_tokens = sum(usage.get('output_tokens', 0) for usage in agent_token_usage)
    total_tokens = sum(usage.get('total_tokens', 0) for usage in agent_token_usage)
    total_cost = sum(usage.get('cost', 0.0) for usage in agent_token_usage)
    all_precise = all(usage.get('is_precise', False) for usage in agent_token_usage)
    
    print("Summary calculation:")
    print(f"  Total input tokens: {total_input_tokens:,}")
    print(f"  Total output tokens: {total_output_tokens:,}")
    print(f"  Total tokens: {total_tokens:,}")
    print(f"  Total cost: ${total_cost:.4f}")
    print(f"  All precise: {all_precise}")
    
    # Test individual agent usage
    print("\nIndividual agent usage:")
    for usage in agent_token_usage:
        print(f"  Agent {usage['agent_number']}: {usage['input_tokens']:,} input + {usage['output_tokens']:,} output = {usage['total_tokens']:,} total (${usage['cost']:.4f})")
    
    print("\n✓ Token usage tracking test completed!")

if __name__ == "__main__":
    test_token_usage_tracking() 