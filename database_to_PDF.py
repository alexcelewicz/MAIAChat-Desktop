import os
import hashlib
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
import re

# This is a test comment to check if file editing is working.

class CodeArchiver:
    def __init__(self, archive_dir='code_archives', included_extensions=None):
        self.archive_dir = archive_dir
        self.last_hash = None
        self._ensure_archive_directory()
        # Define excluded patterns
        self.excluded_patterns = [
            'conversation_history',
            '.venv',
            '.cache',
            'venv',
            'env',
            'backup',
            '__pycache__',
            '.git',
            '.idea',
            '.vscode',
            'node_modules',
            'dist',
            'build',
            '.pytest_cache',
            '.coverage',
            '.DS_Store',
            'package-lock.json', # Exclude lock files
            'yarn.lock',
            # Model and cache related directories
            'model_cache',
            'models--sentence-transformers',
            'models--',  # Catch any huggingface model directory pattern
            'snapshots',
            'transformers_cache',
            'huggingface_cache',
            '.transformers',
            'pytorch_model_cache',
            'sentence_transformers_cache',
            # Other common cache/temp directories
            'temp',
            'tmp', 
            'logs',
            'log',
            '.logs',
            'cache',
            'cached_models',
            'downloads',
            '.downloads',
            # Additional model file patterns
            'checkpoints',
            'trained_models',
            'pretrained_models',
            'model_weights',
            'embeddings_cache',
            'tokenizer_cache',
            # History and data directories
            'history',
            'histories',
            'data',
            'datasets',
            'backup',
            'backups',
            'archive',
            'archives'
        ]
        # Define file extensions/patterns that are typically large model files
        self.excluded_model_extensions = [
            '.bin', '.safetensors', '.pt', '.pth', '.ckpt', '.h5', 
            '.pb', '.onnx', '.tflite', '.pkl', '.pickle'
        ]
        # Define included file extensions - use provided or default
        if included_extensions is not None:
            self.included_extensions = included_extensions
        else:
            self.included_extensions = [
                '.py', '.ts', '.tsx', '.js', '.jsx', # Code
                '.html', '.css', '.scss', '.less',   # Web Frontend
                '.json', '.yml', '.yaml',           # Config
                '.md', '.txt',                      # Documentation/Text
                '.sql',                             # Database
                '.sh', '.bat',                      # Scripts
                'dockerfile', '.dockerignore',      # Docker
                '.env', '.env.example',             # Environment
                '.gitignore',                       # Git
                'requirements.txt',                 # Python requirements (handle files without extension)
                'makefile'                          # Build
            ]
        # Define specific filenames to always include (regardless of extension)
        self.include_filenames = [
            'requirements.txt', 'README.md', 'Dockerfile', 'docker-compose.yml',
            'Makefile', 'package.json', 'tsconfig.json', 'vite.config.ts',
            'tailwind.config.js', 'postcss.config.js', '.gitignore', '.dockerignore',
            '.env.example', 'Prompt.md', 'TODO.md' # Project specific
        ]
        # Define specific filenames to always exclude
        self.exclude_filenames = [
            'package-lock.json', 'yarn.lock', 'steps_completed.txt', 'last_hash.txt' # Lowercase for comparison
        ]
        # Define development and debug files to exclude from documentation
        self.development_files = [
            'debug_build.py', 'debug_profiles.py', 'debug_app.py',
            'database_to_PDF.py', 'test_*.py', '*_test.py',
            'build_exe.py', 'build_*.py'
        ]
        # Define specific filename patterns to exclude (supports partial matching)
        self.excluded_filename_patterns = [
            'history', 'usage_history', 'token_usage', 'conversation_log',
            'chat_history', 'session_history', 'activity_log', 'access_log',
            'error_log', 'debug_log', 'trace_log', 'audit_log',
            'backup_', 'temp_', 'tmp_', '.log', '.bak', '.old',
            'cache_', 'cached_', '_cache', 'dump_', 'data_export',
            'statistics', 'metrics', 'analytics', 'usage_stats'
        ]

    @staticmethod
    def prompt_for_extensions():
        """Prompts the user to select which file extensions to include."""
        default_extensions = [
            '.py', '.ts', '.tsx', '.js', '.jsx',    # Code
            '.html', '.css', '.scss', '.less',      # Web Frontend  
            '.json', '.yml', '.yaml',               # Config
            '.sql',                                 # Database
            '.sh', '.bat',                          # Scripts
            'dockerfile', '.dockerignore',          # Docker
            '.env', '.env.example',                 # Environment
            '.gitignore',                           # Git
            'requirements.txt',                     # Python requirements
            'makefile'                              # Build
        ]
        
        print("\n--- File Extension Selection ---")
        print("Default extensions (without .md, .txt):")
        for i, ext in enumerate(default_extensions, 1):
            print(f"  {i:2d}. {ext}")
        
        print("\nOptions:")
        print("1. Use default extensions (recommended for code-only)")
        print("2. Use default + .md .txt (includes documentation)")
        print("3. Custom selection")
        print("4. Enter manually")
        
        while True:
            choice = input("\nChoose an option (1-4): ").strip()
            
            if choice == '1':
                return default_extensions
            elif choice == '2':
                return default_extensions + ['.md', '.txt']
            elif choice == '3':
                return CodeArchiver._custom_extension_selection(default_extensions)
            elif choice == '4':
                return CodeArchiver._manual_extension_entry()
            else:
                print("Invalid choice. Please enter 1, 2, 3, or 4.")
    
    @staticmethod
    def _custom_extension_selection(available_extensions):
        """Allow user to select from available extensions."""
        all_possible = available_extensions + ['.md', '.txt', '.xml', '.csv', '.log', '.ini', '.cfg', '.conf']
        
        print("\nAvailable extensions:")
        for i, ext in enumerate(all_possible, 1):
            print(f"  {i:2d}. {ext}")
        
        print("\nEnter the numbers of extensions you want to include (e.g., 1,2,5-8):")
        print("Or 'all' for all extensions, 'none' for none")
        
        while True:
            selection = input("Selection: ").strip().lower()
            
            if selection == 'all':
                return all_possible
            elif selection == 'none':
                return []
            
            try:
                selected_extensions = []
                parts = selection.split(',')
                
                for part in parts:
                    part = part.strip()
                    if '-' in part:
                        # Handle ranges like "1-5"
                        start, end = map(int, part.split('-'))
                        for i in range(start, end + 1):
                            if 1 <= i <= len(all_possible):
                                selected_extensions.append(all_possible[i-1])
                    else:
                        # Handle single numbers
                        i = int(part)
                        if 1 <= i <= len(all_possible):
                            selected_extensions.append(all_possible[i-1])
                
                # Remove duplicates while preserving order
                selected_extensions = list(dict.fromkeys(selected_extensions))
                return selected_extensions
                
            except ValueError:
                print("Invalid input. Please use numbers, ranges (1-5), or 'all'/'none'.")
    
    @staticmethod
    def _manual_extension_entry():
        """Allow user to manually enter extensions."""
        print("\nEnter file extensions manually, separated by spaces or commas.")
        print("Include the dot (e.g., .py .js .html)")
        print("For files without extensions, just enter the name (e.g., Dockerfile)")
        
        while True:
            extensions_input = input("Extensions: ").strip()
            if not extensions_input:
                print("Please enter at least one extension.")
                continue
            
            # Split by spaces or commas
            extensions = []
            for ext in extensions_input.replace(',', ' ').split():
                ext = ext.strip()
                if ext:
                    extensions.append(ext)
            
            if extensions:
                print(f"Selected extensions: {extensions}")
                confirm = input("Confirm? (y/n): ").strip().lower()
                if confirm in ['y', 'yes']:
                    return extensions
            else:
                print("No valid extensions found.")

    def _should_exclude(self, path, is_dir):
        """Check if a file or directory path should be excluded."""
        # Normalize path separators for consistent matching
        normalized_path = path.replace('\\', '/').lower()
        path_components = normalized_path.split('/')
        filename = os.path.basename(normalized_path) # Already lowercase

        # 1. Check specific filenames first (takes precedence)
        if not is_dir and filename in self.exclude_filenames:
            # print(f"Excluding filename: {filename}")
            return True

        # 2. Check directory components against excluded patterns
        # Match if any *component* of the path is exactly one of the excluded patterns
        # Ensure patterns like '.git' or 'node_modules' are matched anywhere in the path
        for excluded in self.excluded_patterns:
            if excluded in path_components:
                if 'model' in excluded.lower() or 'cache' in excluded.lower():
                    print(f"Excluding model/cache path: {path}")
                return True

        # 3. Check specifically for cache/uploads/archive directories (more robust)
        # Handles cases like backend/cache/Xenova or just cache/
        if any(f"/{excluded}/" in normalized_path or normalized_path.endswith(f"/{excluded}") for excluded in ['cache', 'uploads', 'code_archives']):
             # print(f"Excluding special dir in: {normalized_path}")
             return True

        return False

    def _should_include_file(self, file_path):
        """Determine if a file should be included based on exclusion rules, specific inclusions, and extensions."""
        # --- Exclusion Check First ---
        # This checks excluded patterns, directories, and specific excluded filenames
        if self._should_exclude(file_path, is_dir=False):
            # print(f"Excluding via _should_exclude: {file_path}")
            return False

        # --- Exclude this script itself ---
        try:
            # Get absolute paths for reliable comparison
            script_path_abs = os.path.abspath(__file__)
            file_path_abs = os.path.abspath(file_path)
            # Use os.path.samefile to handle different path representations (e.g., case sensitivity, symlinks)
            if os.path.samefile(file_path_abs, script_path_abs):
                # print(f"Excluding self: {file_path}")
                return False
        except FileNotFoundError:
             # Handle case where __file__ might not be resolvable or file_path doesn't exist.
             pass # Proceed with other checks, though unlikely during os.walk
        except Exception as e:
            # Log potential errors during comparison but proceed.
            print(f"Warning: Error comparing script path with {file_path}: {e}")
            pass

        filename = os.path.basename(file_path).lower()
        
        # --- Exclude files with history/log/data patterns in filename ---
        for pattern in self.excluded_filename_patterns:
            if pattern.lower() in filename:
                print(f"Excluding history/data file: {file_path}")
                return False
        
        # --- Exclude large model files by extension ---
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext in self.excluded_model_extensions:
            print(f"Excluding model file: {file_path}")
            return False

        # --- Inclusion Rules ---
        # 1. Always include specific important filenames (if not already excluded by _should_exclude)
        if filename in self.include_filenames:
            # print(f"Including filename: {filename}")
            return True

        # 2. Check for relevant extensions
        is_relevant_extension = any(filename.endswith(ext) for ext in self.included_extensions)

        # 3. Handle common extensionless files if not caught by include_filenames
        #    (Ensure these filenames are lowercase in the check)
        if not is_relevant_extension and filename in ['dockerfile', 'makefile', 'requirements.txt', 'procfile']: # Added Procfile as example
             # print(f"Including extensionless: {filename}")
             is_relevant_extension = True

        # Include if it has a relevant extension or is a specifically included filename type
        # if is_relevant_extension:
        #     print(f"Including extension/type: {filename}")

        # If it passed exclusions and wasn't specifically included by name or extension, exclude it.
        return is_relevant_extension

    def _ensure_archive_directory(self):
        """Ensures the archive directory exists."""
        if not os.path.exists(self.archive_dir):
            os.makedirs(self.archive_dir)

    def _calculate_files_hash(self, directory='.'):
        """Calculates an MD5 hash of the content of all included files."""
        hasher = hashlib.md5()
        file_list = self._get_included_files(directory)

        for file_path in sorted(file_list):
            try:
                with open(file_path, 'rb') as file: # Read as binary for hashing
                    while chunk := file.read(4096):
                        hasher.update(chunk)
            except Exception as e:
                print(f"Warning: Could not read file {file_path} for hashing: {e}")
                # Optionally add a placeholder to the hash to indicate the file was skipped
                hasher.update(f"Error reading {os.path.basename(file_path)}".encode())

        return hasher.hexdigest()

    def _get_included_files(self, directory='.'):
        """Recursively finds all files to be included."""
        included_files = []
        for root, dirs, files in os.walk(directory, topdown=True):
            # Filter directories in-place to prevent walking excluded ones
            dirs[:] = [d for d in dirs if not self._should_exclude(os.path.join(root, d), is_dir=True)]

            for filename in files:
                file_path = os.path.join(root, filename)
                if self._should_include_file(file_path):
                    included_files.append(file_path)
        return included_files

    def _generate_directory_tree(self, directory='.', included_files=None):
        """Generates an indented directory tree string for included files/folders."""
        if included_files is None:
            included_files = self._get_included_files(directory)

        tree_lines = ["Project Structure:", ""]
        processed_dirs = set()
        included_files_relative = sorted([os.path.relpath(f, directory) for f in included_files])

        # Add root indicator
        tree_lines.append(f". ({os.path.basename(os.path.abspath(directory))})")

        for file_rel_path in included_files_relative:
            path_parts = file_rel_path.split(os.sep)
            indent = ""
            current_path = ""

            # Create directory entries
            for i, part in enumerate(path_parts[:-1]): # Iterate through directories
                current_path = os.path.join(current_path, part)
                if current_path not in processed_dirs:
                    prefix = "│   " * i + "├── "
                    tree_lines.append(f"{prefix}📁 {part}")
                    processed_dirs.add(current_path)

            # Create file entry
            prefix = "│   " * (len(path_parts) - 1) + "├── "
            tree_lines.append(f"{prefix}📄 {path_parts[-1]}")

        # Simple cleanup for tree structure (replace intermediate markers) - might need refinement
        final_tree = []
        for i, line in enumerate(tree_lines):
            is_last_in_level = True
            if i + 1 < len(tree_lines):
                current_indent = line.find('├') if '├' in line else -1
                next_indent = tree_lines[i+1].find('├') if '├' in tree_lines[i+1] else -1
                if current_indent != -1 and next_indent != -1 and next_indent > current_indent:
                    is_last_in_level = False # It has children
                elif current_indent != -1 and next_indent != -1 and next_indent == current_indent:
                     is_last_in_level = False # It has siblings
                elif current_indent == -1 and next_indent != -1: # Root or similar case
                     is_last_in_level = False

            if is_last_in_level and '├──' in line:
                 final_tree.append(line.replace('├──', '└──', 1))
            else:
                 final_tree.append(line)

        # Replace dangling pipes - This part is tricky and might need a more robust tree library
        # For now, let's do a basic pass
        cleaned_tree = []
        for i, line in enumerate(final_tree):
            cleaned_line = list(line)
            for j, char in enumerate(cleaned_line):
                if char == '│':
                    # Check if any line below at the same level has a '├' or '└' or '│'
                    has_connection_below = False
                    for k in range(i + 1, len(final_tree)):
                        if len(final_tree[k]) > j and final_tree[k][j] in ['├', '└', '│']:
                            has_connection_below = True
                            break
                        # Stop if we encounter a line with less indentation
                        if len(final_tree[k]) <= j or final_tree[k][j] == ' ':
                            pass # Continue checking lines below
                        if len(final_tree[k]) > j and final_tree[k][j] != ' ': # Found something else at same level
                             break


                    if not has_connection_below:
                        cleaned_line[j] = ' '
            cleaned_tree.append("".join(cleaned_line))


        return "\n".join(cleaned_tree)

    def _generate_pdf_name(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        """Generates a timestamped PDF filename."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"code_snapshot_{timestamp}.pdf"

    def _generate_md_name(self):
        """Generates a timestamped Markdown filename."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"code_snapshot_{timestamp}.md"

    def _get_language_for_file(self, file_path):
        """Map file extensions to syntax-highlight languages for Markdown code fences."""
        ext = os.path.splitext(file_path)[1].lower()
        mapping = {
            '.py': 'python', '.js': 'javascript', '.ts': 'typescript', '.tsx': 'tsx', '.jsx': 'jsx',
            '.json': 'json', '.html': 'html', '.css': 'css', '.scss': 'scss', '.less': 'less',
            '.sql': 'sql', '.sh': 'bash', '.bat': 'bat', '.yml': 'yaml', '.yaml': 'yaml',
            '.md': 'markdown', '.dockerignore': ''
        }
        # Special case: Dockerfile has no extension
        if os.path.basename(file_path).lower() == 'dockerfile':
            return 'docker'
        return mapping.get(ext, '')

    def _create_markdown(self, directory, output_path, included_files):
        """Creates a Markdown document containing the directory tree and file contents."""
        try:
            md_lines = []
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            md_lines.append(f"# Code Archive - {timestamp}\n")

            # Project structure
            md_lines.append("## Project Structure\n")
            tree_string = self._generate_directory_tree(directory, included_files)
            md_lines.append("```")
            md_lines.append(tree_string)
            md_lines.append("```\n")

            # File contents
            md_lines.append("## File Contents\n")
            for file_path in sorted(included_files):
                rel_path = os.path.relpath(file_path, directory)
                md_lines.append(f"### File: {rel_path}\n")

                language = self._get_language_for_file(file_path)
                md_lines.append(f"```{language}")

                # Read file content with fallback encodings
                content = None
                for enc in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        with open(file_path, 'r', encoding=enc) as f:
                            content = f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                    except Exception as err:
                        content = f"Error reading file: {err}"
                        break

                if content is None:
                    content = "Error: Could not decode file content with the tried encodings."

                md_lines.append(content.replace('\t', '    '))
                md_lines.append("```\n")

            # Write to disk
            with open(output_path, 'w', encoding='utf-8') as md_file:
                md_file.write('\n'.join(md_lines))

            print(f"Markdown successfully created: {output_path}")
            return True
        except Exception as e:
            print(f"Error building Markdown: {e}")
            return False

    def archive_if_changed(self, directory='.', force=False):
        """Archives the code to PDF if changes are detected or forced."""
        print("Calculating hash of included files...")
        current_hash = self._calculate_files_hash(directory)
        print(f"Current hash: {current_hash}")

        last_hash = None
        hash_file_path = os.path.join(self.archive_dir, 'last_hash.txt')
        if os.path.exists(hash_file_path):
            try:
                with open(hash_file_path, 'r') as f:
                    last_hash = f.read().strip()
                print(f"Last hash found: {last_hash}")
            except Exception as e:
                print(f"Warning: Could not read last hash file: {e}")

        if force or current_hash != last_hash:
            pdf_filename = self._generate_pdf_name()
            pdf_path = os.path.join(self.archive_dir, pdf_filename)
            print(f"Change detected or force=True. Generating PDF: {pdf_filename}")

            included_files = self._get_included_files(directory)
            if not included_files:
                print("No files to include found. Aborting PDF creation.")
                return None

            pdf_created = self._create_pdf(directory, pdf_path, included_files)

            if pdf_created:
                try:
                    with open(hash_file_path, 'w') as f:
                        f.write(current_hash)
                    print(f"Updated last hash file: {hash_file_path}")
                except Exception as e:
                    print(f"Error: Could not write last hash file: {e}")
                print(f"{'Changes detected' if not force else 'Forced archive'}! Created new archive: {pdf_path}")
                return pdf_path
            else:
                print("PDF creation failed.")
                return None
        else:
            print("No changes detected since last archive.")
            return None

    def _create_pdf(self, directory, output_path, included_files):
        """Creates the PDF document with structure and file contents."""
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Define styles
        title_style = styles['Title']
        heading1_style = styles['h1']
        heading2_style = styles['h2']
        heading3_style = styles['h3']
        normal_style = styles['Normal']
        code_style = ParagraphStyle(
            name='CodeStyle',
            parent=styles['Code'], # Inherit from default Code style
            fontName='Courier',   # Monospaced font
            fontSize=8,
            leading=9.6,          # Line spacing
            leftIndent=6,
            firstLineIndent=0,
            spaceBefore=2,
            spaceAfter=2,
            alignment=TA_LEFT,
            # Optional: Add background color
            # backColor=colors.HexColor('#f0f0f0'),
            # Optional: Add border
            # borderPadding=2,
            # borderColor=colors.grey,
            # borderWidth=0.5,
        )
        tree_style = ParagraphStyle( # Style for the directory tree
            name='TreeStyle',
            parent=styles['Code'],
            fontName='Courier',
            fontSize=9,
            leading=11,
            leftIndent=6,
        )


        # 1. Add Timestamp Header
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        story.append(Paragraph(f"Code Archive - {timestamp}", title_style))
        story.append(Spacer(1, 12))

        # 2. Add Project Structure Tree
        story.append(Paragraph("Project Structure", heading2_style))
        story.append(Spacer(1, 6))
        try:
            tree_string = self._generate_directory_tree(directory, included_files)
            # Use Preformatted for the tree to preserve spacing
            story.append(Preformatted(tree_string, tree_style))
            story.append(Spacer(1, 12))
        except Exception as e:
            story.append(Paragraph(f"Error generating directory tree: {e}", normal_style))
            print(f"Error generating directory tree: {e}")
        story.append(Spacer(1, 12))


        # 3. Add File Contents
        story.append(Paragraph("File Contents", heading2_style))
        story.append(Spacer(1, 6))

        for file_path in sorted(included_files):
            rel_path = os.path.relpath(file_path, directory)
            story.append(Paragraph(f"File: {rel_path}", heading3_style))
            story.append(Spacer(1, 4))

            try:
                # Read content, attempting different encodings if utf-8 fails
                content = None
                encodings_to_try = ['utf-8', 'latin-1', 'cp1252']
                for enc in encodings_to_try:
                    try:
                        with open(file_path, 'r', encoding=enc) as file:
                            content = file.read()
                        break # Stop if successful
                    except UnicodeDecodeError:
                        continue # Try next encoding
                    except Exception as read_err: # Catch other file read errors
                         print(f"Error reading file {file_path} with encoding {enc}: {read_err}")
                         content = f"Error reading file: {read_err}"
                         break # Stop trying encodings

                if content is None:
                    content = f"Error: Could not decode file content with tried encodings: {', '.join(encodings_to_try)}"
                    print(f"Error: Could not decode file {file_path}")


                # Use Preformatted for code content
                # Replace tabs with spaces for consistent rendering in PDF
                content_for_pdf = content.replace('\t', '    ')
                story.append(Preformatted(content_for_pdf, code_style))
                story.append(Spacer(1, 12)) # Space after each file

            except Exception as e:
                error_msg = f"Error processing file {file_path}: {e}"
                story.append(Paragraph(error_msg, normal_style))
                story.append(Spacer(1, 12))
                print(error_msg)

        # Build the PDF
        try:
            print(f"Building PDF document: {output_path}")
            doc.build(story)
            print(f"PDF successfully created: {output_path}")
            return True
        except Exception as e:
            print(f"Error building PDF: {e}")
            # Consider logging the full traceback here for debugging
            # import traceback
            # print(traceback.format_exc())
            return False

    def archive_if_changed_markdown(self, directory='.', force=False):
        """Archives code to a Markdown file when changes are detected or when forced."""
        print("Calculating hash of included files...")
        current_hash = self._calculate_files_hash(directory)
        print(f"Current hash: {current_hash}")

        hash_file_path = os.path.join(self.archive_dir, 'last_hash.txt')
        last_hash = None
        if os.path.exists(hash_file_path):
            try:
                with open(hash_file_path, 'r') as f:
                    last_hash = f.read().strip()
                print(f"Last hash found: {last_hash}")
            except Exception as e:
                print(f"Warning: Could not read last hash file: {e}")

        if force or current_hash != last_hash:
            md_filename = self._generate_md_name()
            md_path = os.path.join(self.archive_dir, md_filename)
            print(f"Change detected or force=True. Generating Markdown: {md_filename}")

            included_files = self._get_included_files(directory)
            if not included_files:
                print("No files to include found. Aborting Markdown creation.")
                return None

            md_created = self._create_markdown(directory, md_path, included_files)

            if md_created:
                try:
                    with open(hash_file_path, 'w') as f:
                        f.write(current_hash)
                    print(f"Updated last hash file: {hash_file_path}")
                except Exception as e:
                    print(f"Error: Could not write last hash file: {e}")
                print(f"{'Changes detected' if not force else 'Forced archive'}! Created new archive: {md_path}")
                return md_path
            else:
                print("Markdown creation failed.")
                return None
        else:
            print("No changes detected since last archive.")
            return None


def py_to_pdf(directory='.', archive_dir='code_archives', force=False):
    """Main function to trigger the code archiving process."""
    archiver = CodeArchiver(archive_dir)
    return archiver.archive_if_changed(directory, force)

def py_to_md(directory='.', archive_dir='code_archives', force=False, included_extensions=None):
    """Convenience wrapper to generate a Markdown snapshot of the project."""
    archiver = CodeArchiver(archive_dir, included_extensions)
    return archiver.archive_if_changed_markdown(directory, force)

if __name__ == "__main__":
    print("--- Running Code Archiver ---")
    
    # Prompt user for file extensions to include
    selected_extensions = CodeArchiver.prompt_for_extensions()
    print(f"\nSelected extensions: {selected_extensions}")
    
    # Use current script's directory as the base for finding the project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = script_dir # Assume script is in project root, adjust if needed
    archive_target_dir = os.path.join(project_root, 'code_archives') # Store archives inside project

    print(f"Project Root: {project_root}")
    print(f"Archive Directory: {archive_target_dir}")

    # Instantiate archiver with selected extensions and list files it intends to include
    archiver_instance = CodeArchiver(archive_dir=archive_target_dir, included_extensions=selected_extensions)
    print("\nIdentifying files to include...")
    files_to_include = archiver_instance._get_included_files(project_root)

    if not files_to_include:
        print("No relevant files found to include.")
    else:
        print(f"Found {len(files_to_include)} files/items to potentially include:")
        # Sort relative paths for display
        relative_files = sorted([os.path.relpath(f, project_root) for f in files_to_include])
        for rel_path in relative_files:
            print(f"  - {rel_path}")

        # Generate the PDF (force=True for testing, change to False for normal use)
        # print("\nAttempting to generate PDF (force=True)...")
        # pdf_path_result = py_to_pdf(directory=project_root, archive_dir=archive_target_dir, force=True)

        # if pdf_path_result:
        #     print(f"\nPDF generation successful: {pdf_path_result}")
        # else:
        #     print("\nPDF generation failed or no changes detected.")

        # Generate the Markdown (force=True for testing, change to False for normal use)
        print("\nAttempting to generate Markdown (force=True)...")
        md_path_result = py_to_md(directory=project_root, archive_dir=archive_target_dir, force=True, included_extensions=selected_extensions)

        if md_path_result:
            print(f"\nMarkdown generation successful: {md_path_result}")
        else:
            print("\nMarkdown generation failed or no changes detected.")

    print("\n--- Code Archiver Finished ---")
