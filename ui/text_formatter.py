from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound
from html import escape

class TextFormatter:
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.formatter = HtmlFormatter(noclasses=True, style='default')

    def format_code_block(self, code: str, language: str) -> str:
        if not code.strip(): 
            return ""
        try: 
            lexer = get_lexer_by_name(language.lower(), stripall=True)
        except ClassNotFound:
            try: 
                lexer = guess_lexer(code, stripall=True)
            except ClassNotFound: 
                lexer = get_lexer_by_name('text', stripall=True)
        
        highlighted_code = highlight(code, lexer, self.formatter)
        
        pre_start = highlighted_code.find('<pre>')
        pre_end = highlighted_code.rfind('</pre>')
        if pre_start != -1 and pre_end != -1:
            inner_code = highlighted_code[pre_start + 5 : pre_end]
            return f'<pre style="margin:0;padding:10px;font-family:Consolas,monospace;font-size:13px;line-height:1.4;white-space:pre-wrap;word-wrap:break-word;">{inner_code}</pre>'
        
        return f'<pre style="margin:0;padding:10px;font-family:Consolas,monospace;font-size:13px;line-height:1.4;white-space:pre-wrap;word-wrap:break-word;">{escape(code)}</pre>'

    def format_text_content(self, text: str) -> str:
        return f'<div>{escape(text).replace(chr(10), "<br>")}</div>'

    # Legacy method for compatibility
    def format_code_block_streaming(self, code: str, language: str = None) -> str:
        return self.format_code_block(code, language or '')

    # Legacy method for compatibility  
    def detect_complete_code_block(self, text: str) -> bool:
        return True  # Simple implementation for compatibility

    def format_streaming_chunk(self, content: str, is_first_chunk: bool = False) -> str:
        """Format a streaming chunk for agent responses. Currently uses format_text_content for compatibility."""
        return self.format_text_content(content)
