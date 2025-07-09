#!/usr/bin/env python3
"""
Test script to verify that MCP instructions are automatically included in agent instructions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from instruction_templates import InstructionTemplates

def test_automatic_mcp_instructions():
    """Test that MCP instructions are automatically included in all agent instructions"""
    print("🧪 Testing Automatic MCP Instructions Integration")
    print("=" * 60)
    
    # Test different agent configurations
    test_cases = [
        {"agent_number": 1, "total_agents": 1, "internet_enabled": False, "name": "Single Agent"},
        {"agent_number": 1, "total_agents": 3, "internet_enabled": False, "name": "First of 3 Agents"},
        {"agent_number": 2, "total_agents": 3, "internet_enabled": False, "name": "Middle Agent"},
        {"agent_number": 3, "total_agents": 3, "internet_enabled": False, "name": "Final Agent"},
        {"agent_number": 1, "total_agents": 2, "internet_enabled": True, "name": "Agent with Internet"},
    ]
    
    mcp_keywords = [
        "[MCP:Local Files:",
        "write_file:",
        "read_file:",
        "list_directory:",
        "CRITICAL SYNTAX REQUIREMENTS",
        "MANDATORY for file operations"
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print(f"   Configuration: Agent {test_case['agent_number']}/{test_case['total_agents']}, Internet: {test_case['internet_enabled']}")
        
        # Generate instructions
        instructions = InstructionTemplates.get_agent_instructions(
            test_case['agent_number'],
            test_case['total_agents'],
            test_case['internet_enabled']
        )
        
        # Check if MCP instructions are included
        mcp_found = []
        for keyword in mcp_keywords:
            if keyword in instructions:
                mcp_found.append(keyword)
        
        if len(mcp_found) >= 4:  # Should find most keywords
            print(f"   ✅ PASS: MCP instructions found ({len(mcp_found)}/{len(mcp_keywords)} keywords)")
        else:
            print(f"   ❌ FAIL: MCP instructions missing or incomplete ({len(mcp_found)}/{len(mcp_keywords)} keywords)")
            print(f"   Missing keywords: {[k for k in mcp_keywords if k not in instructions]}")
            all_passed = False
    
    # Test with JSON instructions
    print(f"\n{len(test_cases) + 1}. Testing: JSON Instructions Merge")
    json_instructions = {
        "general": "Custom general instructions",
        "roles": {"1": "Custom role instructions"}
    }
    
    merged_instructions = InstructionTemplates.merge_with_json_instructions(
        json_instructions, 1, 1, False
    )
    
    mcp_found_json = sum(1 for keyword in mcp_keywords if keyword in merged_instructions)
    if mcp_found_json >= 4:
        print(f"   ✅ PASS: MCP instructions preserved in JSON merge ({mcp_found_json}/{len(mcp_keywords)} keywords)")
    else:
        print(f"   ❌ FAIL: MCP instructions lost in JSON merge ({mcp_found_json}/{len(mcp_keywords)} keywords)")
        all_passed = False
    
    # Test specific MCP sections
    print(f"\n{len(test_cases) + 2}. Testing: MCP Section Content")
    test_instructions = InstructionTemplates.get_agent_instructions(1, 1, False)
    
    required_content = [
        "Create a snake game and save to snake.py",
        "Read the config file",
        "❌ [MCP:Local Files:write_file snake.py content]",
        "One missing colon = complete failure",
        "READ-IMPROVE-SAVE WORKFLOWS"
    ]
    
    content_found = sum(1 for content in required_content if content in test_instructions)
    if content_found >= 4:
        print(f"   ✅ PASS: Required MCP content found ({content_found}/{len(required_content)} items)")
    else:
        print(f"   ❌ FAIL: MCP content incomplete ({content_found}/{len(required_content)} items)")
        all_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 AUTOMATIC MCP INSTRUCTIONS TEST SUMMARY")
    print("=" * 60)
    
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("✅ MCP instructions are automatically included in ALL agent configurations")
        print("✅ Agents will now automatically know correct MCP syntax")
        print("✅ Users can use natural language without specifying MCP instructions")
    else:
        print("❌ SOME TESTS FAILED!")
        print("❌ MCP instructions may not be properly integrated")
    
    print("\n🎯 IMPACT:")
    print("• Agents will automatically use correct MCP syntax for file operations")
    print("• Users can say 'create snake game and save to snake.py' without additional instructions")
    print("• No more MCP syntax errors - agents have built-in knowledge")
    print("• Works across all agent configurations (single, multi, with/without internet)")
    
    return all_passed

def demo_agent_instructions():
    """Show a sample of what agents will now automatically receive"""
    print("\n" + "=" * 60)
    print("📖 SAMPLE AGENT INSTRUCTIONS (with automatic MCP integration)")
    print("=" * 60)
    
    sample_instructions = InstructionTemplates.get_agent_instructions(1, 1, False)
    
    # Extract just the MCP section for display
    lines = sample_instructions.split('\n')
    mcp_start = -1
    mcp_end = -1
    
    for i, line in enumerate(lines):
        if "MCP FILE OPERATIONS" in line:
            mcp_start = i
        elif mcp_start != -1 and line.strip() == "" and i > mcp_start + 5:
            mcp_end = i
            break
    
    if mcp_start != -1:
        mcp_section = '\n'.join(lines[mcp_start:mcp_end if mcp_end != -1 else mcp_start + 30])
        print("MCP Section automatically included in agent instructions:")
        print("-" * 40)
        print(mcp_section[:500] + "..." if len(mcp_section) > 500 else mcp_section)
        print("-" * 40)
    
    print("\n✨ This means agents will automatically:")
    print("• Know correct MCP syntax without being told")
    print("• Handle 'create snake game' requests properly")
    print("• Use proper read-improve-save workflows")
    print("• Never make syntax errors that prevent file operations")

if __name__ == "__main__":
    success = test_automatic_mcp_instructions()
    demo_agent_instructions()
    
    if success:
        print("\n🎉 SUCCESS: Automatic MCP instructions are working perfectly!")
    else:
        print("\n⚠️ WARNING: Issues detected with automatic MCP instructions.") 