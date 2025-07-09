# Code Formatting Improvements for Unified Response Panel

## Overview

The Unified Response Panel has been enhanced with comprehensive code formatting capabilities that provide proper indentation, syntax highlighting, and language-specific styling for code blocks.

## Key Improvements

### 1. **Proper Indentation Preservation**
- Code blocks now use `<pre>` tags to preserve whitespace and indentation
- Tab size is set to 4 spaces for consistent formatting
- Line breaks and spacing are maintained exactly as provided

### 2. **Multi-Language Syntax Highlighting**
The system now supports syntax highlighting for the following languages:

#### **Python**
- Keywords: `def`, `class`, `if`, `else`, `for`, `while`, `try`, `except`, etc.
- Strings: Single quotes, double quotes, triple quotes
- Numbers: Integers, floats, hexadecimal, binary
- Comments: Single-line comments with `#`

#### **JavaScript**
- Keywords: `function`, `const`, `let`, `var`, `if`, `else`, `for`, `while`, etc.
- Strings: Single quotes, double quotes, template literals
- Numbers: Integers, floats
- Comments: Single-line (`//`) and multi-line (`/* */`)

#### **HTML**
- Tags: Opening and closing tags
- Attributes: Attribute names and values
- Comments: HTML comments (`<!-- -->`)

#### **CSS**
- Properties: Common CSS properties like `color`, `background`, `margin`, etc.
- Values: Property values after colons
- Comments: CSS comments (`/* */`)

#### **JSON**
- Keys: Object property names
- String values: Quoted strings
- Numbers: Numeric values
- Booleans and null: `true`, `false`, `null`

#### **Bash/Shell**
- Keywords: `if`, `then`, `else`, `for`, `while`, `do`, `done`, etc.
- Comments: Single-line comments with `#`
- Variables: Variables starting with `$`

#### **SQL**
- Keywords: `SELECT`, `FROM`, `WHERE`, `INSERT`, `UPDATE`, etc.
- String literals: Quoted strings
- Numbers: Numeric values
- Comments: Single-line (`--`) and multi-line (`/* */`)

### 3. **Language-Specific Background Colors**
Each language has a distinct background color for easy identification:
- Python: `#f6f8fa` (light gray-blue)
- JavaScript: `#f7f7f7` (light gray)
- HTML: `#f8f8f8` (very light gray)
- CSS: `#f5f5f5` (light gray)
- JSON: `#f6f8fa` (light gray-blue)
- Bash: `#f5f5f5` (light gray)
- SQL: `#f8f8f8` (very light gray)

### 4. **Enhanced Text Formatting**
The system also supports:
- **Headers**: Markdown-style headers (`#`, `##`, `###`)
- **Lists**: Bullet points (`-`, `*`)
- **Blockquotes**: Quoted text (`>`)
- **Paragraphs**: Regular text with proper spacing

## Implementation Details

### TextFormatter Class
The `TextFormatter` class in `ui/text_formatter.py` handles all formatting:

```python
from ui.text_formatter import TextFormatter

# Initialize the formatter
text_formatter = TextFormatter()

# Format text with code blocks
formatted_text = text_formatter.format_text_content(text)
```

### Code Block Detection
Code blocks are detected using markdown-style syntax:
- Start: ` ```language `
- End: ` ``` `
- Language specification is optional but recommended

### Integration with Unified Response Panel
The `UnifiedResponsePanel` now automatically formats all content:
- Agent discussions
- Final answers
- Mixed content with headers, paragraphs, and code blocks

## Usage Examples

### Python Code Block
```python
def hello_world():
    # This is a comment
    print("Hello, world!")
    
    for i in range(10):
        if i % 2 == 0:
            print(f"Even number: {i}")
        else:
            print(f"Odd number: {i}")
            
    return True
```

### JavaScript Code Block
```javascript
function calculateSum(a, b) {
    // Add two numbers
    return a + b;
}

const result = calculateSum(5, 10);
console.log(result);
```

### HTML Code Block
```html
<!DOCTYPE html>
<html>
<head>
    <title>Example</title>
</head>
<body>
    <h1>Hello World</h1>
    <p>This is a paragraph.</p>
</body>
</html>
```

## Testing

A test script `test_code_formatting.py` is provided to demonstrate all formatting features:

```bash
python test_code_formatting.py
```

This opens a test window with buttons to test different language formatting.

## Benefits

1. **Improved Readability**: Code is now properly indented and syntax-highlighted
2. **Language Recognition**: Different languages are visually distinct
3. **Professional Appearance**: Code blocks look like they belong in a modern IDE
4. **Consistent Formatting**: All code blocks follow the same formatting rules
5. **Easy Maintenance**: Centralized formatting logic in the TextFormatter class

## Future Enhancements

Potential improvements for the future:
- Support for more programming languages (C++, Java, Rust, etc.)
- Custom color themes
- Line numbering for code blocks
- Copy-to-clipboard functionality
- Code folding for long blocks
- Search and replace within code blocks

## Technical Notes

- The formatting uses HTML and CSS for rendering
- Syntax highlighting is implemented using regex patterns and tokenization
- Python syntax highlighting uses the `tokenize` module for accuracy
- All HTML entities are properly escaped to prevent rendering issues
- The system gracefully handles malformed code blocks 