import os
import hashlib
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from pygments.lexers import PythonLexer
from pygments.token import Token

class CodeArchiver:
    def __init__(self, archive_dir='code_archives'):
        self.archive_dir = archive_dir
        self.last_hash = None
        self._ensure_archive_directory()

    def _ensure_archive_directory(self):
        if not os.path.exists(self.archive_dir):
            os.makedirs(self.archive_dir)

    def _calculate_files_hash(self, directory='.'):
        combined_content = ''
        for filename in sorted(os.listdir(directory)):
            if filename.endswith('.py'):
                with open(os.path.join(directory, filename), 'r', encoding='utf-8') as file:
                    combined_content += file.read()
        return hashlib.md5(combined_content.encode()).hexdigest()

    def _generate_pdf_name(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"code_snapshot_{timestamp}.pdf"

    def archive_if_changed(self, directory='.', force=False):
        current_hash = self._calculate_files_hash(directory)

        hash_file = os.path.join(self.archive_dir, 'last_hash.txt')
        if os.path.exists(hash_file):
            with open(hash_file, 'r') as f:
                self.last_hash = f.read().strip()

        if force or current_hash != self.last_hash:
            pdf_path = os.path.join(self.archive_dir, self._generate_pdf_name())
            self._create_pdf(directory, pdf_path)

            with open(hash_file, 'w') as f:
                f.write(current_hash)

            print(f"{'Changes detected' if not force else 'Forced archive'}! Created new archive: {pdf_path}")
            return pdf_path
        else:
            print("No changes detected in Python files.")
            return None

    def _create_pdf(self, directory, output_path):
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Add timestamp header
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        story.append(Paragraph(f"Code Archive - {timestamp}", styles['Title']))
        story.append(Spacer(1, 12))

        py_files = [f for f in sorted(os.listdir(directory)) if f.endswith('.py')]

        if not py_files:
            story.append(Paragraph("No Python files found in the directory.", styles['Normal']))
        else:
            # Create a monospace style for code
            code_style = ParagraphStyle(
                'Code',
                fontName='Courier',
                fontSize=8,
                leading=10,
                spaceAfter=0,
                spaceBefore=0,
                leftIndent=0,
                rightIndent=0,
                firstLineIndent=0
            )
            lexer = PythonLexer() 

            style_map = {
                Token.Keyword: '#000080',       # Navy
                Token.Keyword.Constant: '#000080', # For True, False, None
                Token.Keyword.Namespace: '#550055', # Purplish for import, from
                Token.Name.Function: '#007700',  # Darker Green
                Token.Name.Class: '#0000FF',    # Blue
                Token.String: '#A52A2A',        # Brown
                Token.Comment: '#808080',        # Gray
                Token.Operator: '#AA0000',        # Darker Red
                Token.Number: '#FF8C00',        # DarkOrange
                Token.Punctuation: '#555555',     # Dark Gray for (), [], {} , :
                Token.Name.Builtin: '#007777', # Teal for builtins
                Token.Name.Exception: '#CC0000', # Red for exceptions
            }
            default_color_hex = '#000000'  # Assuming base code style is black

            for filename in py_files:
                try:
                    with open(os.path.join(directory, filename), 'r', encoding='utf-8') as file:
                        code = file.read()

                    story.append(Paragraph(f"File: {filename}", styles['Heading2']))
                    story.append(Spacer(1, 6))

                    for line_content in code.split('\n'):
                        leading_spaces = len(line_content) - len(line_content.lstrip())
                        indentation_html = "&nbsp;" * leading_spaces 
                        
                        processed_line_parts = [indentation_html]
                        stripped_line = line_content.lstrip()

                        if not stripped_line:
                            story.append(Paragraph("&nbsp;", code_style))
                            continue
                        
                        tokens = lexer.get_tokens(stripped_line)

                        for tokentype, text_value in tokens:
                            escaped_text_value = (
                                text_value
                                .replace('&', '&amp;')
                                .replace('<', '&lt;')
                                .replace('>', '&gt;')
                            )
                            
                            current_tokentype = tokentype
                            color_hex = None
                            # Iterate up the token type hierarchy (e.g., Token.Comment.Single -> Token.Comment -> Token)
                            while current_tokentype != Token and current_tokentype.parent:
                                if current_tokentype in style_map:
                                    color_hex = style_map[current_tokentype]
                                    break
                                current_tokentype = current_tokentype.parent
                            # If not found by iterating up, check the final current_tokentype 
                            # (it could be Token itself, or a type like Token.Text for which we have no specific style)
                            if not color_hex and current_tokentype in style_map:
                                color_hex = style_map[current_tokentype]
                            
                            final_text_color = color_hex if color_hex else default_color_hex
                            
                            if final_text_color != default_color_hex: # Apply font tag only if color is not default
                                processed_line_parts.append(f'<font color="{final_text_color}">{escaped_text_value}</font>')
                            else:
                                processed_line_parts.append(escaped_text_value)
                                
                        final_line_html = "".join(processed_line_parts)
                        story.append(Paragraph(final_line_html, code_style))

                    story.append(Spacer(1, 12)) # End of the new code processing block

                except Exception as e: # This line provides context for after the new block
                    error_msg = f"Error processing {filename}: {str(e)}"
                    story.append(Paragraph(error_msg, styles['Normal']))
                    story.append(Spacer(1, 12))

        try:
            doc.build(story)
            print(f"PDF successfully created at: {output_path}")
        except Exception as e:
            print(f"Error saving PDF: {str(e)}")
            return None

def py_to_pdf(directory='.', archive_dir='code_archives', force=False):
    archiver = CodeArchiver(archive_dir)
    return archiver.archive_if_changed(directory, force)

if __name__ == "__main__":
    print("Running py_to_pdf_converter as standalone script...")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Current directory: {current_dir}")
    print("Looking for Python files...")
    py_files = [f for f in os.listdir(current_dir) if f.endswith('.py')]
    print(f"Found {len(py_files)} Python files: {', '.join(py_files)}")

    pdf_path = py_to_pdf(directory=current_dir, force=True)
    if pdf_path:
        print(f"PDF created at: {pdf_path}")
    else:
        print("No PDF was created.")
