#!/usr/bin/env python3
"""
Test different agent response scenarios for MCP file creation
Simulates what happens when asking agents to create snake.py
"""

from mcp_client import mcp_client
import re

class AgentMCPScenarioTester:
    """Tests different ways agents might respond to file creation requests"""
    
    def __init__(self):
        self.server = mcp_client.get_server("Local Files")
        self.test_filename = "snake_test_scenario.py"
        
    def cleanup_test_file(self):
        """Clean up any test files created"""
        try:
            import os
            if os.path.exists(self.test_filename):
                os.remove(self.test_filename)
                print(f"🧹 Cleaned up: {self.test_filename}")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")
    
    def test_scenario_1_correct_mcp(self):
        """Test: Agent uses CORRECT MCP syntax"""
        print("\n🎯 SCENARIO 1: Agent uses CORRECT MCP syntax")
        print("Agent Response: [MCP:Local Files:write_file:snake_test_scenario.py:game_code]")
        
        snake_code = '''import pygame
import random

# Simple Snake Game Test
print("Snake game created via CORRECT MCP syntax!")
'''
        
        # Simulate correct MCP request
        mcp_request = f"write_file:{self.test_filename}:{snake_code}"
        result = mcp_client.query_mcp_server(self.server, mcp_request)
        
        if "error" not in result:
            print("✅ SUCCESS: File created using correct MCP syntax")
            return True
        else:
            print(f"❌ FAILED: {result}")
            return False
    
    def test_scenario_2_wrong_mcp_syntax(self):
        """Test: Agent uses WRONG MCP syntax (common mistakes)"""
        print("\n🎯 SCENARIO 2: Agent uses WRONG MCP syntax")
        
        wrong_syntaxes = [
            "[MCP:Local Files:write_file snake_test.py content]",  # Missing colons
            "[MCP Local Files:write_file:snake_test.py:content]",   # Missing colon after MCP
            "[MCP:Local Files write_file:snake_test.py:content]",   # Missing colon after Files
            "[MCP:Local Files:write_file:snake_test.py]",           # Missing content
        ]
        
        for i, wrong_syntax in enumerate(wrong_syntaxes, 1):
            print(f"Agent Response {i}: {wrong_syntax}")
            print(f"❌ RESULT: Invalid syntax - file will NOT be created")
        
        print("❌ OVERALL: All wrong syntax examples would FAIL")
        return False
    
    def test_scenario_3_no_mcp_knowledge(self):
        """Test: Agent provides code but doesn't know about MCP"""
        print("\n🎯 SCENARIO 3: Agent doesn't use MCP (just provides code)")
        
        agent_response = '''Here's a Python snake game:

```python
import pygame
import random

class SnakeGame:
    def __init__(self):
        pygame.init()
        # ... game code here ...
        
if __name__ == "__main__":
    game = SnakeGame()
    game.run()
```

This creates a complete snake game with pygame!'''
        
        print("Agent Response: [Provides code in markdown, no MCP syntax]")
        print("❌ RESULT: Code provided but file NOT automatically created")
        print("❌ MANUAL ACTION REQUIRED: User must copy/paste code manually")
        return False
    
    def test_scenario_4_alternative_approaches(self):
        """Test: Alternative approaches that would work"""
        print("\n🎯 SCENARIO 4: Alternative approaches that WOULD work")
        
        alternatives = [
            "✅ Agent uses application's edit_file tool",
            "✅ Agent uses direct Python file operations", 
            "✅ Agent uses MCP syntax validator before sending request",
            "✅ User manually creates file after agent provides code"
        ]
        
        for alt in alternatives:
            print(f"   {alt}")
        
        return True
    
    def run_all_scenarios(self):
        """Run all test scenarios"""
        print("🧪 TESTING AGENT MCP SCENARIOS FOR SNAKE GAME CREATION")
        print("=" * 60)
        
        scenario_results = []
        
        # Test each scenario
        scenario_results.append(("Correct MCP Syntax", self.test_scenario_1_correct_mcp()))
        scenario_results.append(("Wrong MCP Syntax", self.test_scenario_2_wrong_mcp_syntax()))
        scenario_results.append(("No MCP Knowledge", self.test_scenario_3_no_mcp_knowledge()))
        scenario_results.append(("Alternative Approaches", self.test_scenario_4_alternative_approaches()))
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 SCENARIO TEST SUMMARY")
        print("=" * 60)
        
        for scenario_name, success in scenario_results:
            status = "✅ WOULD WORK" if success else "❌ WOULD FAIL"
            print(f"{status}: {scenario_name}")
        
        print("\n🎯 CONCLUSION:")
        print("Whether asking an agent to 'Write python game snake and save it to snake.py'")
        print("works depends ENTIRELY on the agent's knowledge of correct MCP syntax!")
        
        # Cleanup
        self.cleanup_test_file()

def main():
    """Main test runner"""
    tester = AgentMCPScenarioTester()
    tester.run_all_scenarios()

if __name__ == "__main__":
    main() 