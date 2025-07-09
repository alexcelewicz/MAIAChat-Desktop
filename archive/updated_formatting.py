"""
This file contains updated formatting methods for the main_window.py file.
"""

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

def format_python_comments(self, code: str) -> str:
    """Add syntax highlighting for comments"""
    import re

    # Handle single-line comments
    code = re.sub(
        r'(#.*)$',
        r'<span style="color: #008000;">\1</span>',
        code,
        flags=re.MULTILINE
    )

    return code
