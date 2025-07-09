# MCP Agent Instructions - Model Context Protocol File Operations

## 🚀 Overview
This guide provides agents with comprehensive instructions for using MCP (Model Context Protocol) to perform file operations in a multi-agent collaborative environment.

## 📋 MCP Command Syntax

### Basic File Operations

#### Reading Files
```
[MCP:Local Files:read_file:ABSOLUTE_FILE_PATH]
```
**Example:**
```
[MCP:Local Files:read_file:/home/alex/Desktop/Vibe_Coding/Python_Agents/test.txt]
```

#### Writing Files (Create/Overwrite)
```
[MCP:Local Files:write_file:ABSOLUTE_FILE_PATH:FILE_CONTENT]
```
**Example:**
```
[MCP:Local Files:write_file:/home/alex/Desktop/Vibe_Coding/Python_Agents/new_file.py:print("Hello World")]
```

#### Getting File Information
```
[MCP:Local Files:get_file_info:ABSOLUTE_FILE_PATH]
```

#### Listing Directory Contents
```
[MCP:Local Files:list_directory:ABSOLUTE_DIRECTORY_PATH]
```

#### Searching Files
```
[MCP:Local Files:search_files:DIRECTORY_PATH:SEARCH_PATTERN]
```

## 🔧 Multi-Agent Collaboration Rules

### 1. Backup Before Modification
**CRITICAL:** Always create backups before modifying any file.

```python
# Use the multi-agent file handler for coordination
from multi_agent_file_handler import MultiAgentFileHandler

handler = MultiAgentFileHandler("/home/alex/Desktop/Vibe_Coding/Python_Agents")
backup_path = handler.backup_file("target_file.py", "Agent1_Developer", "pre_modification")
```

### 2. Check File Access Permission
```python
can_modify, reason = handler.agent_can_modify("target_file.py", "Agent1_Developer")
if not can_modify:
    print(f"Cannot modify file: {reason}")
    # Coordinate with other agents or wait
```

### 3. Log Your Activities
```python
# The handler automatically logs when you use its methods
success = handler.write_file_for_agent("target_file.py", new_content, "Agent1_Developer")
```

## 🎯 Agent-Specific Workflows

### Agent 1: Developer & Enhancer
1. **Read Target File**: Use MCP to read the file you need to modify
2. **Analyze Content**: Understand the current implementation
3. **Plan Changes**: Based on user requirements, plan your modifications
4. **Create Backup**: Always backup before changes
5. **Implement**: Make the requested changes
6. **Document**: Explain what you changed and why

**Example Workflow:**
```
1. [MCP:Local Files:read_file:/path/to/file.py]
2. Analyze the code and plan improvements
3. Create backup using multi_agent_file_handler
4. [MCP:Local Files:write_file:/path/to/file.py:IMPROVED_CONTENT]
5. Document changes made
```

### Agent 2: QA & Code Reviewer
1. **Read Modified File**: Check what Agent 1 changed
2. **Read Backup**: Compare with original version
3. **Analyze Quality**: Check for bugs, performance, security issues
4. **Create Review Report**: Document findings and recommendations
5. **Coordinate**: Share feedback for Agent 3

**Example Workflow:**
```
1. [MCP:Local Files:read_file:/path/to/modified_file.py]
2. [MCP:Local Files:read_file:/path/to/backup/original_file.py]
3. Compare versions and analyze quality
4. [MCP:Local Files:write_file:/path/to/qa_review_report.md:REVIEW_CONTENT]
5. Provide specific feedback and test cases
```

### Agent 3: Optimizer & Final Implementation
1. **Read All Previous Work**: Original, modified version, and QA report
2. **Address QA Feedback**: Fix all identified issues
3. **Further Optimize**: Add your own improvements
4. **Create Final Version**: Polish the code
5. **Document Final State**: Create comprehensive documentation

**Example Workflow:**
```
1. [MCP:Local Files:read_file:/path/to/modified_file.py]
2. [MCP:Local Files:read_file:/path/to/qa_review_report.md]
3. Implement QA recommendations and optimizations
4. [MCP:Local Files:write_file:/path/to/file.py:FINAL_OPTIMIZED_CONTENT]
5. [MCP:Local Files:write_file:/path/to/final_documentation.md:DOCS]
```

## ⚠️ Critical Rules and Best Practices

### File Path Requirements
- **Always use ABSOLUTE paths** (starting with `/`)
- **Never use relative paths** like `./file.py` or `../folder/file.py`
- **Base path**: `/home/alex/Desktop/Vibe_Coding/Python_Agents/`

### Backup Strategy
- Create backups before ANY modification
- Use descriptive backup names with timestamps
- Store backups in `/home/alex/Desktop/Vibe_Coding/Python_Agents/code_backup/`

### Coordination Between Agents
- Check collaboration log before modifying files
- Use the multi-agent file handler for conflict prevention
- Document your role and activities clearly
- Wait for previous agent to complete before starting

### Error Handling
- Always verify file exists before reading
- Handle MCP operation failures gracefully
- Provide clear error messages and alternative solutions
- Don't proceed if critical operations fail

## 🔍 Troubleshooting Common Issues

### Issue: MCP Write Operation Fails
**Solution:** 
1. Check file permissions
2. Verify absolute path is correct
3. Ensure directory exists
4. Check file is not locked by another process

### Issue: File Content Not Updated
**Solution:**
1. Verify MCP syntax is exactly correct
2. Check if another agent is modifying the same file
3. Ensure backup was created successfully before writing

### Issue: Cannot Read File
**Solution:**
1. Verify file path is absolute and correct
2. Check file exists using list_directory first
3. Ensure you have read permissions

## 📊 Example Multi-Agent Collaboration Session

```
User Request: "Improve the Python file test.py by adding error handling"

Agent 1 (Developer):
1. [MCP:Local Files:read_file:/home/alex/Desktop/Vibe_Coding/Python_Agents/test.py]
2. Creates backup: test_Agent1_Developer_pre_modification_20250619_120000.py
3. Adds try-catch blocks and input validation
4. [MCP:Local Files:write_file:/home/alex/Desktop/Vibe_Coding/Python_Agents/test.py:IMPROVED_CODE]

Agent 2 (QA):
1. [MCP:Local Files:read_file:/home/alex/Desktop/Vibe_Coding/Python_Agents/test.py]
2. Reviews error handling implementation
3. Identifies missing edge cases
4. [MCP:Local Files:write_file:/home/alex/Desktop/Vibe_Coding/Python_Agents/qa_report.md:REVIEW]

Agent 3 (Optimizer):
1. [MCP:Local Files:read_file:/home/alex/Desktop/Vibe_Coding/Python_Agents/test.py]
2. [MCP:Local Files:read_file:/home/alex/Desktop/Vibe_Coding/Python_Agents/qa_report.md]
3. Addresses QA feedback and adds logging
4. [MCP:Local Files:write_file:/home/alex/Desktop/Vibe_Coding/Python_Agents/test.py:FINAL_CODE]
```

## 🎯 Success Criteria
- All file operations use correct MCP syntax
- Backups are created before modifications
- Agents coordinate properly without conflicts
- Final output meets user requirements
- All changes are properly documented

Remember: The goal is seamless collaboration where agents work together to deliver high-quality results while maintaining file integrity and version control.