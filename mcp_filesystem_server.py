"""
Secure Local Filesystem MCP Server

This module provides a secure Model Context Protocol (MCP) server for filesystem operations.
It implements proper security controls including:
- Path traversal protection
- Directory restriction (sandboxing)
- File size limits
- Safe file operations
- Comprehensive logging
- PDF content processing (reading, searching, metadata extraction)
"""

import os
import json
import logging
import mimetypes
import pathlib
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
import hashlib
import time
from pathlib import Path

# PDF processing imports
try:
    import fitz  # PyMuPDF for PDF processing
    PDF_SUPPORT_AVAILABLE = True
except ImportError:
    PDF_SUPPORT_AVAILABLE = False
    logging.warning("PyMuPDF not available - PDF processing features will be disabled")

try:
    import pdfplumber  # Alternative PDF processor
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logging.warning("pdfplumber not available - some PDF features will be limited")

# Set up logging
logger = logging.getLogger("MCP_Filesystem")

@dataclass
class FileSystemConfig:
    """Configuration for the filesystem MCP server."""
    allowed_directory: str  # Primary allowed directory (for backward compatibility)
    allowed_directories: Dict[str, Dict[str, bool]] = None  # Multiple directories with permissions
    max_file_size: int = 10 * 1024 * 1024  # 10MB default
    allowed_extensions: List[str] = None  # None means all extensions allowed
    read_only: bool = False
    enable_logging: bool = True
    
    def __post_init__(self):
        if self.allowed_extensions is None:
            # Default safe extensions for text files
            self.allowed_extensions = [
                '.txt', '.md', '.json', '.xml', '.csv', '.log',
                '.py', '.js', '.html', '.css', '.sql', '.yml', '.yaml',
                '.ini', '.cfg', '.conf', '.sh', '.bat', '.pdf'  # Added PDF support
            ]
        
        # If allowed_directories is not provided, create it from the primary directory
        if self.allowed_directories is None:
            self.allowed_directories = {
                self.allowed_directory: {
                    "read_file": True,
                    "write_file": not self.read_only,
                    "edit_file": not self.read_only,
                    "create_directory": not self.read_only,
                    "list_directory": True,
                    "move_file": not self.read_only,
                    "search_files": True,
                    "get_file_info": True
                }
            }

class SecureFilesystemMCPServer:
    """
    Secure filesystem MCP server that provides controlled access to local files.
    
    Security Features:
    - Path traversal prevention
    - Directory sandboxing  
    - File size limits
    - Extension filtering
    - Read-only mode support
    - Comprehensive audit logging
    """
    
    def __init__(self, config: FileSystemConfig):
        """Initialize the secure filesystem server."""
        self.config = config
        self.allowed_path = Path(config.allowed_directory).resolve()
        
        # Validate allowed directory exists and is accessible
        if not self.allowed_path.exists():
            raise ValueError(f"Allowed directory does not exist: {config.allowed_directory}")
        if not self.allowed_path.is_dir():
            raise ValueError(f"Allowed path is not a directory: {config.allowed_directory}")
        
        logger.info(f"Initialized secure filesystem server for: {self.allowed_path}")
        if config.read_only:
            logger.info("Server running in READ-ONLY mode")

    def _validate_path(self, file_path: str) -> Path:
        """
        Validate and resolve a file path, ensuring it's within one of the allowed directories.
        
        Args:
            file_path: The file path to validate
            
        Returns:
            Resolved Path object
            
        Raises:
            ValueError: If path is invalid or outside all allowed directories
        """
        try:
            # Fix common path format issues from agent requests
            # Handle colon-separated paths like "E:/Vibe_Coding/Python_Agents:requirements.txt"
            if ':' in file_path and not (len(file_path) > 1 and file_path[1] == ':'):  # Not a Windows drive letter
                # Split on the last colon to separate directory from filename
                if file_path.count(':') == 1 and '/' in file_path:
                    parts = file_path.rsplit(':', 1)
                    if len(parts) == 2:
                        directory_part, filename_part = parts
                        # Reconstruct as proper path
                        file_path = directory_part + '/' + filename_part
                        logger.info(f"Fixed malformed path: original='{file_path}' -> corrected='{file_path}'")
            
            # Convert to Path and resolve
            path = Path(file_path)
            
            # If relative path, try to make it relative to primary allowed directory first
            if not path.is_absolute():
                full_path = (self.allowed_path / path).resolve()
            else:
                full_path = path.resolve()
            
            # Check if path is within any of the allowed directories
            allowed_directories = list(self.config.allowed_directories.keys())
            path_allowed = False
            
            for allowed_dir in allowed_directories:
                try:
                    allowed_path = Path(allowed_dir).resolve()
                    full_path.relative_to(allowed_path)
                    path_allowed = True
                    break
                except ValueError:
                    continue
            
            if not path_allowed:
                allowed_dirs_str = ', '.join(allowed_directories)
                raise ValueError(f"Path outside allowed directories: {file_path}. Allowed directories: {allowed_dirs_str}")
            
            return full_path
            
        except Exception as e:
            logger.warning(f"Path validation failed for '{file_path}': {e}")
            raise ValueError(f"Invalid path: {file_path}")

    def _validate_extension(self, file_path: Path) -> bool:
        """Check if file extension is allowed."""
        if not self.config.allowed_extensions:
            return True
        return file_path.suffix.lower() in [ext.lower() for ext in self.config.allowed_extensions]
    
    def _check_operation_permission(self, file_path: str, operation: str) -> bool:
        """
        Check if the specified operation is allowed for the given file path.
        
        Args:
            file_path: The file path to check
            operation: The operation to check (e.g., 'read_file', 'write_file')
            
        Returns:
            bool: True if operation is allowed, False otherwise
        """
        try:
            full_path = Path(file_path).resolve()
            
            # Find which allowed directory contains this path
            for allowed_dir, permissions in self.config.allowed_directories.items():
                try:
                    allowed_path = Path(allowed_dir).resolve()
                    full_path.relative_to(allowed_path)
                    # Path is within this directory, check permissions
                    return permissions.get(operation, False)
                except ValueError:
                    continue
            
            # Path not in any allowed directory
            return False
            
        except Exception as e:
            logger.warning(f"Permission check failed for '{file_path}', operation '{operation}': {e}")
            return False

    def _log_operation(self, operation: str, path: str, success: bool, details: str = ""):
        """Log filesystem operations for audit trail."""
        if self.config.enable_logging:
            status = "SUCCESS" if success else "FAILED"
            logger.info(f"FILESYSTEM_OP: {operation} | {status} | {path} | {details}")

    def _detect_tables_in_page(self, page, page_text: str) -> bool:
        """
        Safely detect if a page contains tables using multiple methods.
        
        Args:
            page: PyMuPDF page object
            page_text: Text content of the page
            
        Returns:
            bool: True if tables are detected, False otherwise
        """
        try:
            # Method 1: Try PyMuPDF table detection if available
            if hasattr(page, 'find_tables'):
                try:
                    tables = page.find_tables()
                    # Handle TableFinder object properly
                    if hasattr(tables, '__len__'):
                        return len(tables) > 0
                    elif hasattr(tables, '__iter__'):
                        # Try to iterate and count
                        return len(list(tables)) > 0
                    else:
                        # Fallback to checking if object exists
                        return tables is not None
                except:
                    # If PyMuPDF table detection fails, fall back to text heuristics
                    pass
            
            # Method 2: Text-based heuristics for table detection
            # Look for common table patterns
            table_indicators = [
                '\t' in page_text,  # Tab-separated values
                page_text.count('|') > 10,  # Pipe-separated columns
                page_text.count('\n') > 5 and page_text.count(' ') / page_text.count('\n') > 20,  # Multiple aligned columns
                # Look for repeated patterns that might indicate table rows
                len([line for line in page_text.split('\n') if line.count(' ') > 5]) > 3
            ]
            
            return any(table_indicators)
            
        except Exception as e:
            # If all detection methods fail, return False
            logger.debug(f"Table detection failed for page: {e}")
            return False

    def list_directory(self, directory_path: str = "") -> Dict[str, Any]:
        """
        List contents of a directory within the allowed path.
        
        Args:
            directory_path: Relative path within allowed directory (empty for root)
            
        Returns:
            Dictionary with directory contents and metadata
        """
        try:
            if directory_path:
                target_path = self._validate_path(directory_path)
            else:
                target_path = self.allowed_path
                
            if not target_path.exists():
                self._log_operation("LIST_DIR", str(target_path), False, "Directory not found")
                return {"error": "Directory not found", "path": directory_path}
                
            if not target_path.is_dir():
                self._log_operation("LIST_DIR", str(target_path), False, "Not a directory")
                return {"error": "Path is not a directory", "path": directory_path}
            
            items = []
            for item in sorted(target_path.iterdir()):
                try:
                    stat = item.stat()
                    items.append({
                        "name": item.name,
                        "type": "directory" if item.is_dir() else "file",
                        "size": stat.st_size if item.is_file() else None,
                        "modified": stat.st_mtime,
                        "extension": item.suffix if item.is_file() else None,
                        "relative_path": str(item.relative_to(self.allowed_path))
                    })
                except (OSError, PermissionError) as e:
                    logger.warning(f"Could not stat {item}: {e}")
                    continue
            
            result = {
                "path": str(target_path.relative_to(self.allowed_path)),
                "items": items,
                "total_items": len(items)
            }
            
            self._log_operation("LIST_DIR", str(target_path), True, f"Listed {len(items)} items")
            return result
            
        except Exception as e:
            self._log_operation("LIST_DIR", directory_path, False, str(e))
            return {"error": str(e), "path": directory_path}

    def read_file(self, file_path: str, max_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Read contents of a file within the allowed directories.
        
        Args:
            file_path: Path to file within allowed directories
            max_size: Maximum file size to read (overrides config default)
            
        Returns:
            Dictionary with file contents and metadata
        """
        try:
            # Check read permission first
            if not self._check_operation_permission(file_path, "read_file"):
                self._log_operation("READ_FILE", file_path, False, "Permission denied")
                return {"error": "Permission denied: read_file not allowed for this path", "path": file_path}
            
            target_path = self._validate_path(file_path)
            
            if not target_path.exists():
                self._log_operation("READ_FILE", str(target_path), False, "File not found")
                return {"error": "File not found", "path": file_path}
                
            if not target_path.is_file():
                self._log_operation("READ_FILE", str(target_path), False, "Not a file")
                return {"error": "Path is not a file", "path": file_path}
            
            # Check file size
            file_size = target_path.stat().st_size
            size_limit = max_size or self.config.max_file_size
            if file_size > size_limit:
                self._log_operation("READ_FILE", str(target_path), False, f"File too large: {file_size} bytes")
                return {"error": f"File too large ({file_size} bytes, limit: {size_limit})", "path": file_path}
            
            # Check extension
            if not self._validate_extension(target_path):
                self._log_operation("READ_FILE", str(target_path), False, f"Extension not allowed: {target_path.suffix}")
                return {"error": f"File extension not allowed: {target_path.suffix}", "path": file_path}
            
            # Determine if file is text or binary
            mime_type, _ = mimetypes.guess_type(str(target_path))
            is_text = mime_type and mime_type.startswith('text/')
            
            try:
                if is_text or target_path.suffix.lower() in ['.txt', '.md', '.json', '.xml', '.csv', '.log', '.py', '.js', '.html', '.css']:
                    # Read as text
                    content = target_path.read_text(encoding='utf-8')
                    content_type = "text"
                else:
                    # Read as binary and encode as base64
                    import base64
                    content = base64.b64encode(target_path.read_bytes()).decode('ascii')
                    content_type = "binary"
                    
            except UnicodeDecodeError:
                # Fall back to binary if text decoding fails
                import base64
                content = base64.b64encode(target_path.read_bytes()).decode('ascii')
                content_type = "binary"
            
            stat = target_path.stat()
            result = {
                "path": file_path,
                "content": content,
                "content_type": content_type,
                "size": file_size,
                "modified": stat.st_mtime,
                "mime_type": mime_type,
                "encoding": "utf-8" if content_type == "text" else "base64"
            }
            
            self._log_operation("READ_FILE", str(target_path), True, f"Read {file_size} bytes")
            return result
            
        except Exception as e:
            self._log_operation("READ_FILE", file_path, False, str(e))
            return {"error": str(e), "path": file_path}

    def write_file(self, file_path: str, content: str, encoding: str = "utf-8", create_dirs: bool = False) -> Dict[str, Any]:
        """
        Write content to a file within the allowed directories.
        
        Args:
            file_path: Path to file within allowed directories
            content: Content to write (text or base64 for binary)
            encoding: Content encoding ('utf-8' or 'base64')
            create_dirs: Whether to create parent directories if they don't exist
            
        Returns:
            Dictionary with operation result
        """
        if self.config.read_only:
            self._log_operation("WRITE_FILE", file_path, False, "Server in read-only mode")
            return {"error": "Server is in read-only mode", "path": file_path}
        
        try:
            # Check write permission first
            if not self._check_operation_permission(file_path, "write_file"):
                self._log_operation("WRITE_FILE", file_path, False, "Permission denied")
                return {"error": "Permission denied: write_file not allowed for this path", "path": file_path}
            
            target_path = self._validate_path(file_path)
            
            # Check extension
            if not self._validate_extension(target_path):
                self._log_operation("WRITE_FILE", str(target_path), False, f"Extension not allowed: {target_path.suffix}")
                return {"error": f"File extension not allowed: {target_path.suffix}", "path": file_path}
            
            # Create parent directories if requested
            if create_dirs:
                target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if parent directory exists
            if not target_path.parent.exists():
                self._log_operation("WRITE_FILE", str(target_path), False, "Parent directory does not exist")
                return {"error": "Parent directory does not exist", "path": file_path}
            
            # Prepare content
            if encoding == "base64":
                import base64
                try:
                    binary_content = base64.b64decode(content)
                    if len(binary_content) > self.config.max_file_size:
                        return {"error": f"Content too large ({len(binary_content)} bytes)", "path": file_path}
                    target_path.write_bytes(binary_content)
                    content_size = len(binary_content)
                except Exception as e:
                    self._log_operation("WRITE_FILE", str(target_path), False, f"Base64 decode error: {e}")
                    return {"error": f"Invalid base64 content: {e}", "path": file_path}
            else:
                # Text content
                content_bytes = content.encode('utf-8')
                if len(content_bytes) > self.config.max_file_size:
                    return {"error": f"Content too large ({len(content_bytes)} bytes)", "path": file_path}
                target_path.write_text(content, encoding='utf-8')
                content_size = len(content_bytes)
            
            result = {
                "path": file_path,
                "size": content_size,
                "encoding": encoding,
                "created": not target_path.existed_before_write if hasattr(target_path, 'existed_before_write') else "unknown"
            }
            
            self._log_operation("WRITE_FILE", str(target_path), True, f"Wrote {content_size} bytes")
            return result
            
        except Exception as e:
            self._log_operation("WRITE_FILE", file_path, False, str(e))
            return {"error": str(e), "path": file_path}

    def delete_file(self, file_path: str) -> Dict[str, Any]:
        """
        Delete a file within the allowed directory.
        
        Args:
            file_path: Relative path to file within allowed directory
            
        Returns:
            Dictionary with operation result
        """
        if self.config.read_only:
            self._log_operation("DELETE_FILE", file_path, False, "Server in read-only mode")
            return {"error": "Server is in read-only mode", "path": file_path}
        
        try:
            target_path = self._validate_path(file_path)
            
            if not target_path.exists():
                self._log_operation("DELETE_FILE", str(target_path), False, "File not found")
                return {"error": "File not found", "path": file_path}
                
            if not target_path.is_file():
                self._log_operation("DELETE_FILE", str(target_path), False, "Not a file")
                return {"error": "Path is not a file", "path": file_path}
            
            file_size = target_path.stat().st_size
            target_path.unlink()
            
            result = {
                "path": file_path,
                "deleted": True,
                "size": file_size
            }
            
            self._log_operation("DELETE_FILE", str(target_path), True, f"Deleted {file_size} bytes")
            return result
            
        except Exception as e:
            self._log_operation("DELETE_FILE", file_path, False, str(e))
            return {"error": str(e), "path": file_path}

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get metadata about a file or directory.
        
        Args:
            file_path: Relative path within allowed directory
            
        Returns:
            Dictionary with file metadata
        """
        try:
            target_path = self._validate_path(file_path)
            
            if not target_path.exists():
                self._log_operation("GET_INFO", str(target_path), False, "Path not found")
                return {"error": "Path not found", "path": file_path}
            
            stat = target_path.stat()
            mime_type, _ = mimetypes.guess_type(str(target_path))
            
            result = {
                "path": file_path,
                "name": target_path.name,
                "type": "directory" if target_path.is_dir() else "file",
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "created": stat.st_ctime,
                "permissions": oct(stat.st_mode)[-3:],
                "extension": target_path.suffix if target_path.is_file() else None,
                "mime_type": mime_type,
                "is_readable": os.access(target_path, os.R_OK),
                "is_writable": os.access(target_path, os.W_OK) and not self.config.read_only
            }
            
            self._log_operation("GET_INFO", str(target_path), True, f"Retrieved info for {result['type']}")
            return result
            
        except Exception as e:
            self._log_operation("GET_INFO", file_path, False, str(e))
            return {"error": str(e), "path": file_path}

    def search_files(self, pattern: str, directory: str = "", recursive: bool = True) -> Dict[str, Any]:
        """
        Search for files matching a pattern within the allowed directories.
        
        Args:
            pattern: Filename pattern to search for (supports wildcards)
            directory: Directory to search in (empty searches all allowed directories)
            recursive: Whether to search recursively
            
        Returns:
            Dictionary with search results
        """
        try:
            import fnmatch
            
            # Check search permission first
            if directory and not self._check_operation_permission(directory, "search_files"):
                self._log_operation("SEARCH_FILES", directory, False, "Permission denied")
                return {"error": "Permission denied: search_files not allowed for this path", "pattern": pattern}
            
            matches = []
            search_paths = []
            
            if directory:
                # Search in specific directory
                try:
                    search_path = self._validate_path(directory)
                    if search_path.exists() and search_path.is_dir():
                        search_paths = [search_path]
                    else:
                        self._log_operation("SEARCH_FILES", directory, False, "Search directory not found")
                        return {"error": "Search directory not found", "pattern": pattern}
                except Exception as e:
                    self._log_operation("SEARCH_FILES", directory, False, str(e))
                    return {"error": str(e), "pattern": pattern}
            else:
                # Search in all allowed directories
                for allowed_dir in self.config.allowed_directories.keys():
                    if self._check_operation_permission(allowed_dir, "search_files"):
                        allowed_path = Path(allowed_dir).resolve()
                        if allowed_path.exists() and allowed_path.is_dir():
                            search_paths.append(allowed_path)
            
            # Perform search in all valid paths
            for search_path in search_paths:
                # Find the base directory for relative path calculation
                base_dir = None
                for allowed_dir in self.config.allowed_directories.keys():
                    try:
                        allowed_path = Path(allowed_dir).resolve()
                        search_path.relative_to(allowed_path)
                        base_dir = allowed_path
                        break
                    except ValueError:
                        continue
                
                if not base_dir:
                    continue
                
                if recursive:
                    for item in search_path.rglob(pattern):
                        if item.is_file():
                            try:
                                stat = item.stat()
                                matches.append({
                                    "path": str(item.relative_to(base_dir)),
                                    "absolute_path": str(item),
                                    "name": item.name,
                                    "size": stat.st_size,
                                    "modified": stat.st_mtime,
                                    "directory": str(item.parent.relative_to(base_dir))
                                })
                            except (OSError, PermissionError, ValueError):
                                continue
                else:
                    for item in search_path.iterdir():
                        if item.is_file() and fnmatch.fnmatch(item.name, pattern):
                            try:
                                stat = item.stat()
                                matches.append({
                                    "path": str(item.relative_to(base_dir)),
                                    "absolute_path": str(item),
                                    "name": item.name,
                                    "size": stat.st_size,
                                    "modified": stat.st_mtime,
                                    "directory": str(item.parent.relative_to(base_dir))
                                })
                            except (OSError, PermissionError, ValueError):
                                continue
            
            result = {
                "pattern": pattern,
                "search_directory": directory,
                "recursive": recursive,
                "matches": matches,
                "total_matches": len(matches)
            }
            
            search_desc = directory if directory else "all allowed directories"
            self._log_operation("SEARCH_FILES", search_desc, True, f"Found {len(matches)} matches for '{pattern}'")
            return result
            
        except Exception as e:
            self._log_operation("SEARCH_FILES", directory, False, str(e))
            return {"error": str(e), "pattern": pattern}

    def read_pdf_page(self, file_path: str, page_number: int = None, start_page: int = None, end_page: int = None) -> Dict[str, Any]:
        """
        Extract text from specific page(s) of a PDF file.
        
        Args:
            file_path: Path to the PDF file
            page_number: Single page to extract (1-based indexing)
            start_page: Start page for range extraction (1-based indexing)
            end_page: End page for range extraction (1-based indexing, inclusive)
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            if not PDF_SUPPORT_AVAILABLE and not PDFPLUMBER_AVAILABLE:
                self._log_operation("READ_PDF_PAGE", file_path, False, "PDF processing not available")
                return {"error": "PDF processing not available - PyMuPDF or pdfplumber required", "file_path": file_path}
            
            # Check read permission
            if not self._check_operation_permission(file_path, "read_file"):
                self._log_operation("READ_PDF_PAGE", file_path, False, "Permission denied")
                return {"error": "Permission denied: read_file not allowed for this path", "file_path": file_path}
            
            # Validate path
            target_path = self._validate_path(file_path)
            
            if not target_path.exists():
                self._log_operation("READ_PDF_PAGE", file_path, False, "File not found")
                return {"error": "File not found", "file_path": file_path}
            
            if not target_path.is_file():
                self._log_operation("READ_PDF_PAGE", file_path, False, "Path is not a file")
                return {"error": "Path is not a file", "file_path": file_path}
            
            # Check if it's a PDF file
            if target_path.suffix.lower() != '.pdf':
                self._log_operation("READ_PDF_PAGE", file_path, False, "File is not a PDF")
                return {"error": "File is not a PDF", "file_path": file_path}
            
            # Open PDF
            doc = fitz.open(str(target_path))
            total_pages = len(doc)
            
            # Determine page range
            if page_number is not None:
                # Single page
                if page_number < 1 or page_number > total_pages:
                    doc.close()
                    return {"error": f"Page {page_number} out of range (1-{total_pages})", "file_path": file_path}
                start_idx = page_number - 1
                end_idx = page_number - 1
            elif start_page is not None and end_page is not None:
                # Page range
                if start_page < 1 or end_page < 1 or start_page > total_pages or end_page > total_pages:
                    doc.close()
                    return {"error": f"Page range {start_page}-{end_page} out of range (1-{total_pages})", "file_path": file_path}
                if start_page > end_page:
                    doc.close()
                    return {"error": f"Start page {start_page} cannot be greater than end page {end_page}", "file_path": file_path}
                start_idx = start_page - 1
                end_idx = end_page - 1
            else:
                # Default to first page if no parameters specified
                start_idx = 0
                end_idx = 0
            
            # Extract text from specified pages
            extracted_text = ""
            page_info = []
            
            for page_idx in range(start_idx, end_idx + 1):
                page = doc[page_idx]
                page_text = page.get_text()
                extracted_text += f"\n--- Page {page_idx + 1} ---\n{page_text}\n"
                
                # Get page metadata
                page_info.append({
                    "page_number": page_idx + 1,
                    "text_length": len(page_text),
                    "has_images": len(page.get_images()) > 0,
                    "has_tables": self._detect_tables_in_page(page, page_text)
                })
            
            doc.close()
            
            result = {
                "file_path": file_path,
                "total_pages": total_pages,
                "extracted_pages": list(range(start_idx + 1, end_idx + 2)),
                "text": extracted_text.strip(),
                "page_info": page_info,
                "text_length": len(extracted_text.strip())
            }
            
            self._log_operation("READ_PDF_PAGE", file_path, True, f"Extracted {len(page_info)} pages")
            return result
            
        except Exception as e:
            self._log_operation("READ_PDF_PAGE", file_path, False, str(e))
            return {"error": str(e), "file_path": file_path}

    def search_pdf_content(self, file_path: str, search_term: str, case_sensitive: bool = False) -> Dict[str, Any]:
        """
        Search for text within a PDF file.
        
        Args:
            file_path: Path to the PDF file
            search_term: Text to search for
            case_sensitive: Whether search should be case-sensitive
            
        Returns:
            Dictionary with search results and metadata
        """
        try:
            if not PDF_SUPPORT_AVAILABLE:
                self._log_operation("SEARCH_PDF_CONTENT", file_path, False, "PDF processing not available")
                return {"error": "PDF processing not available - PyMuPDF not installed", "file_path": file_path}
            
            # Check read permission
            if not self._check_operation_permission(file_path, "read_file"):
                self._log_operation("SEARCH_PDF_CONTENT", file_path, False, "Permission denied")
                return {"error": "Permission denied: read_file not allowed for this path", "file_path": file_path}
            
            # Validate path
            target_path = self._validate_path(file_path)
            
            if not target_path.exists():
                self._log_operation("SEARCH_PDF_CONTENT", file_path, False, "File not found")
                return {"error": "File not found", "file_path": file_path}
            
            if not target_path.is_file():
                self._log_operation("SEARCH_PDF_CONTENT", file_path, False, "Path is not a file")
                return {"error": "Path is not a file", "file_path": file_path}
            
            # Check if it's a PDF file
            if target_path.suffix.lower() != '.pdf':
                self._log_operation("SEARCH_PDF_CONTENT", file_path, False, "File is not a PDF")
                return {"error": "File is not a PDF", "file_path": file_path}
            
            # Open PDF
            doc = fitz.open(str(target_path))
            total_pages = len(doc)
            
            # Prepare search term
            search_text = search_term if case_sensitive else search_term.lower()
            
            # Search through all pages
            matches = []
            total_occurrences = 0
            
            for page_num in range(total_pages):
                page = doc[page_num]
                page_text = page.get_text()
                
                # Prepare page text for comparison
                comparison_text = page_text if case_sensitive else page_text.lower()
                
                # Find all occurrences in this page
                start_idx = 0
                page_matches = []
                
                while True:
                    match_idx = comparison_text.find(search_text, start_idx)
                    if match_idx == -1:
                        break
                    
                    # Extract context around the match
                    context_start = max(0, match_idx - 100)
                    context_end = min(len(page_text), match_idx + len(search_term) + 100)
                    context = page_text[context_start:context_end]
                    
                    # Find line number (approximate)
                    lines_before = page_text[:match_idx].count('\n')
                    
                    page_matches.append({
                        "position": match_idx,
                        "line_number": lines_before + 1,
                        "context": context,
                        "matched_text": page_text[match_idx:match_idx + len(search_term)]
                    })
                    
                    start_idx = match_idx + 1
                    total_occurrences += 1
                
                if page_matches:
                    matches.append({
                        "page_number": page_num + 1,
                        "matches_count": len(page_matches),
                        "matches": page_matches
                    })
            
            doc.close()
            
            result = {
                "file_path": file_path,
                "search_term": search_term,
                "case_sensitive": case_sensitive,
                "total_pages": total_pages,
                "pages_with_matches": len(matches),
                "total_occurrences": total_occurrences,
                "matches": matches
            }
            
            self._log_operation("SEARCH_PDF_CONTENT", file_path, True, f"Found {total_occurrences} occurrences")
            return result
            
        except Exception as e:
            self._log_operation("SEARCH_PDF_CONTENT", file_path, False, str(e))
            return {"error": str(e), "file_path": file_path}

    def get_pdf_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get PDF metadata and information.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary with PDF metadata
        """
        try:
            if not PDF_SUPPORT_AVAILABLE:
                self._log_operation("GET_PDF_INFO", file_path, False, "PDF processing not available")
                return {"error": "PDF processing not available - PyMuPDF not installed", "file_path": file_path}
            
            # Check read permission
            if not self._check_operation_permission(file_path, "read_file"):
                self._log_operation("GET_PDF_INFO", file_path, False, "Permission denied")
                return {"error": "Permission denied: read_file not allowed for this path", "file_path": file_path}
            
            # Validate path
            target_path = self._validate_path(file_path)
            
            if not target_path.exists():
                self._log_operation("GET_PDF_INFO", file_path, False, "File not found")
                return {"error": "File not found", "file_path": file_path}
            
            if not target_path.is_file():
                self._log_operation("GET_PDF_INFO", file_path, False, "Path is not a file")
                return {"error": "Path is not a file", "file_path": file_path}
            
            # Check if it's a PDF file
            if target_path.suffix.lower() != '.pdf':
                self._log_operation("GET_PDF_INFO", file_path, False, "File is not a PDF")
                return {"error": "File is not a PDF", "file_path": file_path}
            
            # Open PDF
            doc = fitz.open(str(target_path))
            
            # Get basic info
            page_count = len(doc)
            metadata = doc.metadata
            
            # Get file size
            file_size = target_path.stat().st_size
            
            # Analyze first few pages for content type detection
            has_text = False
            has_images = False
            has_tables = False
            total_characters = 0
            
            # Check up to first 5 pages or all pages if less than 5
            pages_to_check = min(5, page_count)
            
            for page_num in range(pages_to_check):
                page = doc[page_num]
                page_text = page.get_text()
                
                if page_text.strip():
                    has_text = True
                    total_characters += len(page_text)
                
                if page.get_images():
                    has_images = True
                
                # Check for tables using helper method
                if self._detect_tables_in_page(page, page_text):
                    has_tables = True
            
            # Try to detect if PDF is password protected
            is_encrypted = doc.needs_pass
            
            doc.close()
            
            result = {
                "file_path": file_path,
                "file_size_bytes": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "page_count": page_count,
                "is_encrypted": is_encrypted,
                "has_text": has_text,
                "has_images": has_images,
                "has_tables": has_tables,
                "estimated_characters": total_characters,
                "metadata": {
                    "title": metadata.get("title", ""),
                    "author": metadata.get("author", ""),
                    "subject": metadata.get("subject", ""),
                    "creator": metadata.get("creator", ""),
                    "producer": metadata.get("producer", ""),
                    "creation_date": metadata.get("creationDate", ""),
                    "modification_date": metadata.get("modDate", ""),
                    "keywords": metadata.get("keywords", "")
                }
            }
            
            self._log_operation("GET_PDF_INFO", file_path, True, f"Retrieved info for {page_count}-page PDF")
            return result
            
        except Exception as e:
            self._log_operation("GET_PDF_INFO", file_path, False, str(e))
            return {"error": str(e), "file_path": file_path}

    def get_capabilities(self) -> List[str]:
        """Get list of available capabilities."""
        capabilities = [
            "list_directory",
            "read_file", 
            "get_file_info",
            "search_files"
        ]
        
        # Add PDF capabilities if available
        if PDF_SUPPORT_AVAILABLE:
            capabilities.extend([
                "read_pdf_page",
                "search_pdf_content", 
                "get_pdf_info"
            ])
        
        if not self.config.read_only:
            capabilities.extend([
                "write_file",
                "delete_file"
            ])
            
        return capabilities

    def get_server_info(self) -> Dict[str, Any]:
        """Get server configuration and status information."""
        return {
            "name": "Secure Filesystem MCP Server",
            "version": "1.0.0",
            "allowed_directory": str(self.allowed_path),
            "read_only": self.config.read_only,
            "max_file_size": self.config.max_file_size,
            "allowed_extensions": self.config.allowed_extensions,
            "capabilities": self.get_capabilities(),
            "logging_enabled": self.config.enable_logging
        }


def create_filesystem_server(allowed_directory: str, **kwargs) -> SecureFilesystemMCPServer:
    """
    Factory function to create a secure filesystem MCP server.
    
    Args:
        allowed_directory: Directory to restrict access to
        **kwargs: Additional configuration options
        
    Returns:
        Configured SecureFilesystemMCPServer instance
    """
    config = FileSystemConfig(allowed_directory=allowed_directory, **kwargs)
    return SecureFilesystemMCPServer(config)


# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example: Create a server for a specific directory
    try:
        server = create_filesystem_server(
            allowed_directory="./test_sandbox",
            max_file_size=5 * 1024 * 1024,  # 5MB
            read_only=False,
            enable_logging=True
        )
        
        print("Filesystem MCP Server created successfully!")
        print("Server info:", json.dumps(server.get_server_info(), indent=2))
        
        # Test operations
        print("\nTesting directory listing:")
        result = server.list_directory()
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Error creating server: {e}") 