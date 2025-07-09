import re

class TextFormatter:
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

    def format_python_keywords(self, code: str) -> str:
        """Add syntax highlighting for Python keywords"""
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

    def format_python_strings(self, code: str) -> str:
        """Add syntax highlighting for string literals"""
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

    def format_python_numbers(self, code: str) -> str:
        """Add syntax highlighting for numbers"""
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

    def format_python_comments(self, code: str) -> str:
        """Add syntax highlighting for comments"""
        # Handle single-line comments
        code = re.sub(
            r'(#.*)$',
            r'<span style="color: #008000;">\1</span>',
            code,
            flags=re.MULTILINE
        )

        return code

    def format_header(self, text: str):
        level = len(text) - len(text.lstrip('#'))
        text = text.lstrip('#').strip()
        size = max(24 - (level * 2), 14)  # Decrease size for each header level
        return f"""
        <div style='
            margin: 20px 0 10px 0;
            font-family: Arial, sans-serif;
            font-size: {size}px;
            font-weight: bold;
            color: #24292e;
            border-bottom: 1px solid #eaecef;
            padding-bottom: 0.3em;
        '>
        {text}
        </div>
        """

    def format_paragraph(self, text: str):
        return f"""
        <div style='
            margin: 8px 0;
            line-height: 1.6;
            font-family: Arial, sans-serif;
            font-size: 14px;
            color: #24292e;
            text-align: justify;
        '>
        {text}
        </div>
        """

    def format_list_item(self, text: str):
        text = text.lstrip('- ').lstrip('* ')
        return f"""
        <div style='
            margin: 4px 0 4px 20px;
            line-height: 1.6;
            font-family: Arial, sans-serif;
            font-size: 14px;
            color: #24292e;
        '>
        • {text}
        </div>
        """

    def format_blockquote(self, text: str):
        text = text.lstrip('>').strip()
        return f"""
        <div style='
            margin: 8px 0;
            padding: 0 16px;
            color: #6a737d;
            border-left: 4px solid #dfe2e5;
            font-family: Arial, sans-serif;
            font-size: 14px;
            font-style: italic;
            line-height: 1.6;
        '>
        {text}
        </div>
        """
