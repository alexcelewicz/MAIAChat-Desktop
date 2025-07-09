# MCP (Model Context Protocol) Syntax Guide for Agents

## 🎯 **CRITICAL: Agents MUST use this exact syntax for file operations to work!**

### **📋 Required Format**
```
[MCP:ServerName:operation:parameter1:parameter2:...]
```

**⚠️ CRITICAL RULES:**
1. **MUST** start with `[MCP:`
2. **MUST** end with `]`
3. **MUST** use colons `:` as separators
4. **NO SPACES** around colons
5. **Case sensitive** - use exact server names

---

## 🔧 **Available MCP Servers**

### **Local Files Server**
- **Server Name**: `Local Files`
- **Purpose**: Read, write, list, delete files in the project directory
- **Security**: Sandboxed to allowed directory only

---

## 📖 **MCP Operations Reference**

### **1. 📁 List Directory Contents**
```
[MCP:Local Files:list_directory:]
```
**Purpose**: List all files and folders in the project directory

**Example Usage**:
```
User: "Show me all files in the project"
Agent: [MCP:Local Files:list_directory:]
```

---

### **2. 📄 Read File**
```
[MCP:Local Files:read_file:filename.ext]
```
**Purpose**: Read the contents of a specific file

**Examples**:
```
[MCP:Local Files:read_file:config.json]
[MCP:Local Files:read_file:snake.py]
[MCP:Local Files:read_file:docs/README.md]
```

**Use Cases**:
- User: "Read the snake.py file"
- User: "Show me the config.json contents"
- User: "What's in the README file?"

---

### **3. ✏️ Write/Create File**
```
[MCP:Local Files:write_file:filename.ext:content_here]
```
**Purpose**: Create a new file or overwrite existing file with content

**Examples**:
```
[MCP:Local Files:write_file:snake.py:import pygame
import random

class SnakeGame:
    def __init__(self):
        self.width = 800
        self.height = 600
    
    def run(self):
        print("Snake game running!")

if __name__ == "__main__":
    game = SnakeGame()
    game.run()]

[MCP:Local Files:write_file:config.json:{"setting": "value", "enabled": true}]

[MCP:Local Files:write_file:test.py:print("Hello World!")]
```

**Use Cases**:
- User: "Create a snake game and save it to snake.py"
- User: "Write a test script to test.py"
- User: "Save this configuration to config.json"

---

### **4. 🗑️ Delete File**
```
[MCP:Local Files:delete_file:filename.ext]
```
**Purpose**: Delete a specific file

**Examples**:
```
[MCP:Local Files:delete_file:temp.py]
[MCP:Local Files:delete_file:old_backup.json]
```

**Use Cases**:
- User: "Delete the temporary file"
- User: "Remove the old backup"

---

### **5. 🔍 Search Files**
```
[MCP:Local Files:search_files:pattern:]
```
**Purpose**: Find files matching a pattern

**Examples**:
```
[MCP:Local Files:search_files:*.py:]
[MCP:Local Files:search_files:test_*:]
[MCP:Local Files:search_files:*.json:]
```

**Use Cases**:
- User: "Find all Python files"
- User: "Show me all test files"
- User: "List all JSON configuration files"

---

## ⚠️ **COMMON SYNTAX ERRORS TO AVOID**

### **❌ WRONG Examples**
```
❌ [MCP:Local Files:write_file snake.py content]     # Missing colons
❌ [MCP Local Files:write_file:snake.py:content]     # Missing colon after MCP
❌ [MCP:Local Files write_file:snake.py:content]     # Missing colon after Files
❌ [MCP:Local Files:write_file:snake.py]             # Missing content parameter
❌ MCP:Local Files:list_directory:                   # Missing brackets
❌ [MCP:local files:read_file:test.py]               # Wrong case (should be "Local Files")
```

### **✅ CORRECT Examples**
```
✅ [MCP:Local Files:write_file:snake.py:content]
✅ [MCP:Local Files:read_file:config.json]
✅ [MCP:Local Files:list_directory:]
✅ [MCP:Local Files:delete_file:temp.py]
✅ [MCP:Local Files:search_files:*.py:]
```

---

## 🎯 **Common Use Case Examples**

### **Scenario 1: Read, Improve, and Save Code**
```
User: "Read the snake.py file, improve the code, and save it back"

Agent Response:
1. First, I'll read the current file:
[MCP:Local Files:read_file:snake.py]

2. After analyzing the code, I'll write the improved version:
[MCP:Local Files:write_file:snake.py:# Improved Snake Game
import pygame
import random

class ImprovedSnakeGame:
    def __init__(self):
        # Improved initialization with better parameters
        self.width = 800
        self.height = 600
        self.fps = 60
        # ... improved code here ...
    
    def run(self):
        # Enhanced game loop
        # ... improved game logic ...
        pass

if __name__ == "__main__":
    game = ImprovedSnakeGame()
    game.run()]
```

### **Scenario 2: Create New Game from Scratch**
```
User: "Create a tetris game and save it to tetris.py"

Agent Response:
I'll create a Tetris game for you:

[MCP:Local Files:write_file:tetris.py:import pygame
import random

class TetrisGame:
    def __init__(self):
        self.width = 600
        self.height = 800
        self.grid_width = 10
        self.grid_height = 20
        # ... tetris game code ...
    
    def run(self):
        # Tetris game loop
        pass

if __name__ == "__main__":
    game = TetrisGame()
    game.run()]
```

### **Scenario 3: Backup and Modify Configuration**
```
User: "Backup the current config.json and then update it with new settings"

Agent Response:
1. First, I'll read the current configuration:
[MCP:Local Files:read_file:config.json]

2. I'll create a backup:
[MCP:Local Files:write_file:config_backup.json:current_config_content_here]

3. Now I'll update the configuration with new settings:
[MCP:Local Files:write_file:config.json:{"new_setting": "value", "updated": true}]
```

---

## 🛡️ **Error Handling and Validation**

### **Before Sending MCP Requests**
1. **Check syntax**: Ensure proper bracket, colon, and parameter format
2. **Verify server name**: Use exact case "Local Files"
3. **Include all parameters**: Don't forget content for write operations
4. **Test with simple operations first**: Try list_directory before complex writes

### **If MCP Fails**
1. **Double-check syntax**: Review this guide for correct format
2. **Use alternatives**: Direct Python file operations as backup
3. **Manual fallback**: Provide code for user to copy/paste manually
4. **Report the issue**: Let user know MCP syntax didn't work

---

## 📚 **Quick Reference Card**

```
📁 List:    [MCP:Local Files:list_directory:]
📄 Read:    [MCP:Local Files:read_file:filename]
✏️ Write:   [MCP:Local Files:write_file:filename:content]
🗑️ Delete:  [MCP:Local Files:delete_file:filename]
🔍 Search:  [MCP:Local Files:search_files:pattern:]
```

---

## 🎯 **Success Checklist for Agents**

Before sending any MCP request, verify:
- [ ] Starts with `[MCP:`
- [ ] Ends with `]`
- [ ] Uses `Local Files` (correct case)
- [ ] Has proper colons as separators
- [ ] Includes all required parameters
- [ ] Content parameter included for write operations

**Remember**: Exact syntax is critical! One missing colon means the operation will fail completely.

---

*This guide ensures 100% success rate for MCP file operations when followed correctly.* 