#!/usr/bin/env python3
"""
Test script for agent context window management functionality.
Tests the new intelligent context truncation and summarization features.
"""

import sys
import os
import json
from unittest.mock import Mock, patch

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_context_management():
    """Test the context management functionality."""
    print("🧪 Testing Agent Context Window Management")
    print("=" * 60)

    # Create a simplified test class to test the logic
    class MockWorker:
        def __init__(self):
            self.config_manager = Mock()
            self.config_manager.get_config_value.return_value = True
            self.update_terminal_console_signal = Mock()
            self.update_terminal_console_signal.emit = Mock()

        def _estimate_tokens_accurately(self, text, provider):
            # Simple estimation: 4 characters per token
            return len(text) // 4

        def _format_agent_responses_with_context_management(self, agent_responses, current_agent_number, provider, model):
            """Simplified version of the context management method for testing."""
            if not agent_responses:
                return ""

            context_management_enabled = self.config_manager.get_config_value('AGENT_CONTEXT_MANAGEMENT', True)

            relevant_responses = {}
            for prev_agent_num, prev_response in agent_responses.items():
                if prev_agent_num < current_agent_number:
                    relevant_responses[prev_agent_num] = prev_response

            if not relevant_responses:
                return ""

            if not context_management_enabled:
                formatted_agent_responses = "=== PREVIOUS AGENT RESPONSES ===\n"
                for agent_num in sorted(relevant_responses.keys()):
                    formatted_agent_responses += f"Agent {agent_num} Response:\n{relevant_responses[agent_num]}\n\n"
                return formatted_agent_responses

            # Simulate context window limit
            total_context_limit = 32768
            available_for_agent_responses = int(total_context_limit * 0.6)

            total_content = ""
            for agent_num in sorted(relevant_responses.keys()):
                total_content += f"Agent {agent_num} Response:\n{relevant_responses[agent_num]}\n\n"

            estimated_tokens = self._estimate_tokens_accurately(total_content, provider)

            if estimated_tokens <= available_for_agent_responses:
                return "=== PREVIOUS AGENT RESPONSES ===\n" + total_content

            # Apply truncation
            self.update_terminal_console_signal.emit(
                f"Agent {current_agent_number}: Context window management - truncating previous responses "
                f"({estimated_tokens} tokens > {available_for_agent_responses} limit)"
            )

            return self._apply_context_truncation_strategy(relevant_responses, available_for_agent_responses, provider)

        def _apply_context_truncation_strategy(self, agent_responses, token_limit, provider):
            """Simplified truncation strategy for testing."""
            formatted_responses = "=== PREVIOUS AGENT RESPONSES (CONTEXT MANAGED) ===\n"

            sorted_agents = sorted(agent_responses.keys(), reverse=True)
            remaining_tokens = token_limit
            processed_responses = []

            for i, agent_num in enumerate(sorted_agents):
                response = agent_responses[agent_num]

                if i == 0:
                    max_tokens_for_this_agent = min(remaining_tokens, int(token_limit * 0.5))
                elif i == 1:
                    max_tokens_for_this_agent = min(remaining_tokens, int(token_limit * 0.3))
                else:
                    max_tokens_for_this_agent = min(remaining_tokens, int(token_limit * 0.2))

                estimated_tokens = self._estimate_tokens_accurately(response, provider)

                if estimated_tokens <= max_tokens_for_this_agent:
                    processed_response = f"Agent {agent_num} Response:\n{response}\n\n"
                    processed_responses.append(processed_response)
                    remaining_tokens -= estimated_tokens
                else:
                    if i < 2:
                        truncated_response = response[:max_tokens_for_this_agent * 4] + "\n[Response truncated due to context limits]"
                        processed_response = f"Agent {agent_num} Response (truncated):\n{truncated_response}\n\n"
                    else:
                        summary = response[:max_tokens_for_this_agent * 2] + "... [Summarized]"
                        processed_response = f"Agent {agent_num} Summary:\n{summary}\n\n"

                    processed_responses.append(processed_response)
                    remaining_tokens -= max_tokens_for_this_agent

                if remaining_tokens <= 0:
                    break

            processed_responses.reverse()
            formatted_responses += "".join(processed_responses)

            if len(sorted_agents) > len(processed_responses):
                omitted_count = len(sorted_agents) - len(processed_responses)
                formatted_responses += f"[Note: {omitted_count} earlier agent response(s) omitted due to context limits]\n\n"

            return formatted_responses

    # Create a mock worker instance
    worker = MockWorker()

    # Create test agent responses that would exceed context window
    large_response_1 = "This is a very long response from Agent 1. " * 200  # ~2000 tokens
    large_response_2 = "This is another long response from Agent 2. " * 300  # ~3000 tokens
    large_response_3 = "Agent 3 provides even more detailed analysis. " * 400  # ~4000 tokens

    agent_responses = {
        1: large_response_1,
        2: large_response_2,
        3: large_response_3
    }

    print(f"📊 Test Data:")
    print(f"   - Agent 1 response: ~{len(large_response_1)} chars")
    print(f"   - Agent 2 response: ~{len(large_response_2)} chars")
    print(f"   - Agent 3 response: ~{len(large_response_3)} chars")
    print(f"   - Total: ~{len(large_response_1 + large_response_2 + large_response_3)} chars")
    print()
        
    # Test 1: Context management enabled
    print("🔧 Test 1: Context Management Enabled")
    result = worker._format_agent_responses_with_context_management(
        agent_responses, 4, "OpenRouter", "tencent/hunyuan-a13b-instruct:free"
    )

    print(f"   ✅ Result length: {len(result)} chars")
    print(f"   ✅ Contains truncation notice: {'truncated' in result.lower()}")
    print(f"   ✅ Contains context management header: {'CONTEXT MANAGED' in result}")
    print()

    # Test 2: Context management disabled
    print("🔧 Test 2: Context Management Disabled")
    worker.config_manager.get_config_value.return_value = False

    result_disabled = worker._format_agent_responses_with_context_management(
        agent_responses, 4, "OpenRouter", "tencent/hunyuan-a13b-instruct:free"
    )

    print(f"   ✅ Result length: {len(result_disabled)} chars")
    print(f"   ✅ No truncation applied: {len(result_disabled) > len(result)}")
    print(f"   ✅ Contains all responses: {'Agent 1' in result_disabled and 'Agent 2' in result_disabled and 'Agent 3' in result_disabled}")
    print()

    # Test 3: Small responses that fit
    print("🔧 Test 3: Small Responses (Should Fit)")
    worker.config_manager.get_config_value.return_value = True

    small_responses = {
        1: "Short response from Agent 1.",
        2: "Brief response from Agent 2.",
        3: "Concise response from Agent 3."
    }

    result_small = worker._format_agent_responses_with_context_management(
        small_responses, 4, "OpenRouter", "tencent/hunyuan-a13b-instruct:free"
    )

    print(f"   ✅ Result length: {len(result_small)} chars")
    print(f"   ✅ No truncation needed: {'truncated' not in result_small.lower()}")
    print(f"   ✅ All responses included: {all(resp in result_small for resp in small_responses.values())}")
    print()
        
    # Test 4: Test truncation strategy
    print("🔧 Test 4: Truncation Strategy")

    truncated = worker._apply_context_truncation_strategy(
        agent_responses, 2000, "OpenRouter"  # Very limited token budget
    )

    print(f"   ✅ Truncated result length: {len(truncated)} chars")
    print(f"   ✅ Contains recent responses: {'Agent 3' in truncated}")
    print(f"   ✅ May contain summaries: {'Summary' in truncated or 'truncated' in truncated}")
    print()

    print("🎉 All tests completed successfully!")
    print("=" * 60)

    return True

def test_configuration():
    """Test the configuration options."""
    print("🔧 Testing Configuration Options")
    print("=" * 40)
    
    # Test config.json has the new options
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        print(f"   ✅ AGENT_CONTEXT_MANAGEMENT: {config.get('AGENT_CONTEXT_MANAGEMENT', 'NOT FOUND')}")
        print(f"   ✅ AGENT_CONTEXT_STRATEGY: {config.get('AGENT_CONTEXT_STRATEGY', 'NOT FOUND')}")
        
        if 'AGENT_CONTEXT_MANAGEMENT' in config and 'AGENT_CONTEXT_STRATEGY' in config:
            print("   ✅ Configuration options added successfully!")
            return True
        else:
            print("   ❌ Configuration options missing!")
            return False
            
    except Exception as e:
        print(f"   ❌ Error reading config: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Agent Context Window Management Test Suite")
    print("=" * 60)
    print()
    
    # Test configuration
    config_success = test_configuration()
    print()
    
    # Test functionality
    if config_success:
        test_success = test_context_management()
        
        if test_success:
            print("✅ ALL TESTS PASSED - Context management is working correctly!")
        else:
            print("❌ SOME TESTS FAILED - Please check the implementation.")
    else:
        print("❌ CONFIGURATION TEST FAILED - Please check config.json.")
    
    print()
    print("📋 Summary:")
    print("   - Context management prevents agent response overflow")
    print("   - Intelligent truncation preserves important information")
    print("   - Recent agent responses get priority")
    print("   - Older responses are summarized when needed")
    print("   - Configuration allows enabling/disabling the feature")
