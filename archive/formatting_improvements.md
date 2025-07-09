# Text Formatting Improvements

This document outlines the changes needed to improve text formatting in the final response window, particularly for code blocks.

## Changes to Implement

### 1. Update `format_code_block` method in `main_window.py`

Replace the current `format_code_block` method with this improved version:

```python
def format_code_block(self, code: str, language: str = None):
    """
    Format code blocks with proper indentation and syntax highlighting.
    Uses pre tags to preserve whitespace and indentation.
    """
    # Apply syntax highlighting based on language
    highlighted_code = code
    
    if language and language.lower() == 'python':
        # Apply Python syntax highlighting
        highlighted_code = self.format_python_keywords(highlighted_code)
        highlighted_code = self.format_python_strings(highlighted_code)
        highlighted_code = self.format_python_numbers(highlighted_code)
        highlighted_code = self.format_python_comments(highlighted_code)
    
    # Escape HTML entities to prevent rendering issues
    # But preserve the syntax highlighting spans we just added
    if '<span' not in highlighted_code:
        highlighted_code = highlighted_code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # Different background colors for different languages
    bg_colors = {
        'python': '#f6f8fa',
        'javascript': '#f7f7f7',
        'html': '#f8f8f8',
        'css': '#f5f5f5',
        'json': '#f6f8fa',
        'bash': '#f5f5f5',
        'sql': '#f8f8f8'
    }

    bg_color = bg_colors.get(language.lower() if language else None, '#f6f8fa')
    
    # Use pre tag to preserve whitespace and indentation
    return f"""
    <div style='
        background-color: {bg_color};
        border: 1px solid #e1e4e8;
        border-radius: 6px;
        padding: 16px;
        margin: 8px 0;
        overflow-x: auto;
    '>
    <pre style='
        font-family: "Consolas", "Monaco", "Courier New", monospace;
        font-size: 14px;
        line-height: 1.45;
        margin: 0;
        white-space: pre;
        tab-size: 4;
        color: #24292e;
    '><code>{highlighted_code}</code></pre>
    </div>
    """
```

### 2. Update `format_text_content` method in `main_window.py`

Replace the current `format_text_content` method with this improved version:

```python
def format_text_content(self, text: str):
    """Format text content with improved code block handling"""
    paragraphs = text.split('\n')
    formatted_parts = []

    in_code_block = False
    code_content = []
    code_language = None

    i = 0
    while i < len(paragraphs):
        paragraph = paragraphs[i]
        
        # Handle code blocks with language specification
        if paragraph.strip().startswith("```"):
            if in_code_block:
                # End of code block
                in_code_block = False
                code_text = "\n".join(code_content)
                formatted_parts.append(self.format_code_block(code_text, code_language))
                code_content = []
                code_language = None
            else:
                # Start of code block - check for language specification
                in_code_block = True
                lang_spec = paragraph.strip().lstrip('```').strip()
                if lang_spec:
                    code_language = lang_spec
            i += 1
            continue

        if in_code_block:
            code_content.append(paragraph)
            i += 1
            continue

        # Handle different types of content
        stripped = paragraph.strip()
        if not stripped:
            formatted_parts.append("<br>")
        elif stripped.startswith("#"):
            formatted_parts.append(self.format_header(stripped))
        elif stripped.startswith("- ") or stripped.startswith("* "):
            formatted_parts.append(self.format_list_item(stripped))
        elif stripped.startswith(">"):
            formatted_parts.append(self.format_blockquote(stripped))
        else:
            formatted_parts.append(self.format_paragraph(stripped))
        
        i += 1

    # Handle unclosed code blocks
    if in_code_block and code_content:
        code_text = "\n".join(code_content)
        formatted_parts.append(self.format_code_block(code_text, code_language))

    return "\n".join(formatted_parts)
```

### 3. Update `format_python_strings` method in `main_window.py`

Replace the current `format_python_strings` method with this improved version:

```python
def format_python_strings(self, code: str) -> str:
    """Add syntax highlighting for string literals"""
    import re

    # Handle single quotes
    code = re.sub(
        r"'([^']*)'",
        r'<span style="color: #067d17;">\0</span>',
        code
    )

    # Handle double quotes
    code = re.sub(
        r'"([^"]*)"',
        r'<span style="color: #067d17;">\0</span>',
        code
    )

    # Handle triple single quotes
    code = re.sub(
        r"'''([\s\S]*?)'''",
        r'<span style="color: #067d17;">\0</span>',
        code
    )

    # Handle triple double quotes
    code = re.sub(
        r'"""([\s\S]*?)"""',
        r'<span style="color: #067d17;">\0</span>',
        code
    )

    return code
```

### 4. Update `format_python_keywords` method in `main_window.py`

Replace the current `format_python_keywords` method with this improved version:

```python
def format_python_keywords(self, code: str) -> str:
    """Add syntax highlighting for Python keywords"""
    import re
    
    keywords = [
        'def', 'class', 'if', 'else', 'elif', 'for', 'while',
        'try', 'except', 'finally', 'with', 'as', 'import',
        'from', 'return', 'yield', 'break', 'continue', 'pass',
        'True', 'False', 'None', 'and', 'or', 'not', 'is', 'in',
        'lambda', 'nonlocal', 'global', 'assert', 'del', 'raise'
    ]

    # Use regex to match whole words only
    for keyword in keywords:
        # Match the keyword as a whole word with word boundaries
        pattern = r'\b(' + keyword + r')\b'
        replacement = r'<span style="color: #0000ff;">\1</span>'
        code = re.sub(pattern, replacement, code)

    return code
```

### 5. Update `format_python_numbers` method in `main_window.py` (Optional)

You can enhance the `format_python_numbers` method with this improved version:

```python
def format_python_numbers(self, code: str) -> str:
    """Add syntax highlighting for numbers"""
    import re

    # Handle integers and floats
    code = re.sub(
        r'\b(\d+\.?\d*)\b',
        r'<span style="color: #098658;">\1</span>',
        code
    )

    # Handle hexadecimal numbers
    code = re.sub(
        r'\b(0x[0-9a-fA-F]+)\b',
        r'<span style="color: #098658;">\1</span>',
        code
    )

    # Handle binary numbers
    code = re.sub(
        r'\b(0b[01]+)\b',
        r'<span style="color: #098658;">\1</span>',
        code
    )

    return code
```

## Testing the Changes

You can test these changes by running the included `test_formatting.py` script, which provides a simple UI to see how the formatting works.

```bash
python3 test_formatting.py
```

## Benefits of These Changes

1. **Improved Code Block Formatting**:
   - Proper indentation preservation using `<pre>` tags
   - Better syntax highlighting for different programming languages
   - Horizontal scrolling for long lines instead of wrapping
   - Consistent monospace font for code

2. **Better Text Content Processing**:
   - More robust code block detection
   - Proper handling of language specification
   - Better handling of unclosed code blocks

3. **Enhanced Syntax Highlighting**:
   - More comprehensive keyword highlighting
   - Better string literal detection (including triple quotes)
   - Improved number formatting
   - Comment highlighting

These changes will make the final response window much more readable, especially when displaying code snippets.
