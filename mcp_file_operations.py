"""
MCP File Operations Module

This module provides file system operations for MCP agents with proper permission checking.
It supports cross-platform file operations while respecting folder permissions configured
through the MCP configuration dialog.
"""

import os
import json
import shutil
import logging
import fnmatch
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import platform
import stat

# Set up logging
logger = logging.getLogger("MCP File Operations")

class MCPFileOperations:
    """Handle file operations for MCP agents with permission checking."""
    
    def __init__(self, config_dir: str = "mcp_config"):
        """Initialize file operations handler.
        
        Args:
            config_dir: Directory containing MCP configuration files
        """
        self.config_dir = config_dir
        self.permissions_file = os.path.join(config_dir, "folder_permissions.json")
        self._load_permissions()
    
    def _load_permissions(self):
        """Load folder permissions from configuration file."""
        self.folder_permissions = {}
        if os.path.exists(self.permissions_file):
            try:
                with open(self.permissions_file, 'r', encoding='utf-8') as f:
                    self.folder_permissions = json.load(f)
                logger.info(f"Loaded folder permissions from {self.permissions_file}")
            except Exception as e:
                logger.error(f"Error loading folder permissions: {e}")
                self.folder_permissions = {}
    
    def _check_permission(self, file_path: str, operation: str) -> bool:
        """Check if the operation is allowed on the given file path.
        
        Args:
            file_path: The file or directory path
            operation: The operation to check (read_file, write_file, etc.)
            
        Returns:
            bool: True if operation is allowed, False otherwise
        """
        file_path = os.path.abspath(file_path)
        
        # Check each configured folder to see if the file path is within it
        for folder_path, permissions in self.folder_permissions.items():
            folder_path = os.path.abspath(folder_path)
            
            # Check if file_path is within this folder
            try:
                os.path.commonpath([folder_path, file_path])
                if file_path.startswith(folder_path):
                    # File is within this folder, check permissions
                    return permissions.get(operation, False)
            except ValueError:
                # Paths are on different drives (Windows) or don't share common path
                continue
        
        # No matching folder found, operation not allowed
        logger.warning(f"Operation '{operation}' denied for path '{file_path}' - no folder permission configured")
        return False
    
    def _get_safe_path(self, file_path: str) -> str:
        """Get normalized, safe file path."""
        return os.path.normpath(os.path.abspath(file_path))
    
    def read_file(self, file_path: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """Read file contents.
        
        Args:
            file_path: Path to the file to read
            encoding: File encoding (default: utf-8)
            
        Returns:
            Dict containing success status, content, and metadata
        """
        try:
            safe_path = self._get_safe_path(file_path)
            
            if not self._check_permission(safe_path, 'read_file'):
                return {
                    "success": False,
                    "error": "Permission denied: read_file not allowed for this path",
                    "path": safe_path
                }
            
            if not os.path.exists(safe_path):
                return {
                    "success": False,
                    "error": "File not found",
                    "path": safe_path
                }
            
            if not os.path.isfile(safe_path):
                return {
                    "success": False,
                    "error": "Path is not a file",
                    "path": safe_path
                }
            
            with open(safe_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            # Get file metadata
            stat_info = os.stat(safe_path)
            
            return {
                "success": True,
                "content": content,
                "path": safe_path,
                "size": stat_info.st_size,
                "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                "encoding": encoding
            }
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "path": file_path
            }
    
    def write_file(self, file_path: str, content: str, encoding: str = 'utf-8', create_dirs: bool = True) -> Dict[str, Any]:
        """Write content to file.
        
        Args:
            file_path: Path to the file to write
            content: Content to write
            encoding: File encoding (default: utf-8)
            create_dirs: Whether to create parent directories if they don't exist
            
        Returns:
            Dict containing success status and metadata
        """
        try:
            safe_path = self._get_safe_path(file_path)
            
            if not self._check_permission(safe_path, 'write_file'):
                return {
                    "success": False,
                    "error": "Permission denied: write_file not allowed for this path",
                    "path": safe_path
                }
            
            # Check if we need to create directories
            parent_dir = os.path.dirname(safe_path)
            if create_dirs and not os.path.exists(parent_dir):
                if not self._check_permission(parent_dir, 'create_directory'):
                    return {
                        "success": False,
                        "error": "Permission denied: create_directory not allowed for parent path",
                        "path": safe_path
                    }
                os.makedirs(parent_dir, exist_ok=True)
            
            with open(safe_path, 'w', encoding=encoding) as f:
                f.write(content)
            
            # Get file metadata
            stat_info = os.stat(safe_path)
            
            return {
                "success": True,
                "path": safe_path,
                "size": stat_info.st_size,
                "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                "encoding": encoding
            }
            
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "path": file_path
            }
    
    def edit_file(self, file_path: str, content: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """Edit existing file content.
        
        Args:
            file_path: Path to the file to edit
            content: New content for the file
            encoding: File encoding (default: utf-8)
            
        Returns:
            Dict containing success status and metadata
        """
        try:
            safe_path = self._get_safe_path(file_path)
            
            if not self._check_permission(safe_path, 'edit_file'):
                return {
                    "success": False,
                    "error": "Permission denied: edit_file not allowed for this path",
                    "path": safe_path
                }
            
            if not os.path.exists(safe_path):
                return {
                    "success": False,
                    "error": "File not found - use write_file to create new files",
                    "path": safe_path
                }
            
            if not os.path.isfile(safe_path):
                return {
                    "success": False,
                    "error": "Path is not a file",
                    "path": safe_path
                }
            
            # Create backup
            backup_path = safe_path + ".backup"
            shutil.copy2(safe_path, backup_path)
            
            try:
                with open(safe_path, 'w', encoding=encoding) as f:
                    f.write(content)
                
                # Remove backup on success
                os.remove(backup_path)
                
                # Get file metadata
                stat_info = os.stat(safe_path)
                
                return {
                    "success": True,
                    "path": safe_path,
                    "size": stat_info.st_size,
                    "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                    "encoding": encoding
                }
                
            except Exception as e:
                # Restore from backup on error
                if os.path.exists(backup_path):
                    shutil.move(backup_path, safe_path)
                raise e
            
        except Exception as e:
            logger.error(f"Error editing file {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "path": file_path
            }
    
    def create_directory(self, dir_path: str, parents: bool = True) -> Dict[str, Any]:
        """Create directory.
        
        Args:
            dir_path: Path to the directory to create
            parents: Whether to create parent directories if they don't exist
            
        Returns:
            Dict containing success status and metadata
        """
        try:
            safe_path = self._get_safe_path(dir_path)
            
            if not self._check_permission(safe_path, 'create_directory'):
                return {
                    "success": False,
                    "error": "Permission denied: create_directory not allowed for this path",
                    "path": safe_path
                }
            
            if os.path.exists(safe_path):
                if os.path.isdir(safe_path):
                    return {
                        "success": True,
                        "path": safe_path,
                        "message": "Directory already exists"
                    }
                else:
                    return {
                        "success": False,
                        "error": "Path exists but is not a directory",
                        "path": safe_path
                    }
            
            os.makedirs(safe_path, exist_ok=parents)
            
            return {
                "success": True,
                "path": safe_path,
                "created": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating directory {dir_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "path": dir_path
            }
    
    def list_directory(self, dir_path: str, include_hidden: bool = False, recursive: bool = False) -> Dict[str, Any]:
        """List directory contents.
        
        Args:
            dir_path: Path to the directory to list
            include_hidden: Whether to include hidden files/folders
            recursive: Whether to list recursively
            
        Returns:
            Dict containing success status and directory contents
        """
        try:
            safe_path = self._get_safe_path(dir_path)
            
            if not self._check_permission(safe_path, 'list_directory'):
                return {
                    "success": False,
                    "error": "Permission denied: list_directory not allowed for this path",
                    "path": safe_path
                }
            
            if not os.path.exists(safe_path):
                return {
                    "success": False,
                    "error": "Directory not found",
                    "path": safe_path
                }
            
            if not os.path.isdir(safe_path):
                return {
                    "success": False,
                    "error": "Path is not a directory",
                    "path": safe_path
                }
            
            items = []
            
            if recursive:
                for root, dirs, files in os.walk(safe_path):
                    # Filter hidden items if not requested
                    if not include_hidden:
                        dirs[:] = [d for d in dirs if not d.startswith('.')]
                        files = [f for f in files if not f.startswith('.')]
                    
                    for name in dirs + files:
                        item_path = os.path.join(root, name)
                        items.append(self._get_item_info(item_path))
            else:
                for item_name in os.listdir(safe_path):
                    if not include_hidden and item_name.startswith('.'):
                        continue
                    
                    item_path = os.path.join(safe_path, item_name)
                    items.append(self._get_item_info(item_path))
            
            return {
                "success": True,
                "path": safe_path,
                "items": items,
                "count": len(items)
            }
            
        except Exception as e:
            logger.error(f"Error listing directory {dir_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "path": dir_path
            }
    
    def move_file(self, source_path: str, dest_path: str) -> Dict[str, Any]:
        """Move/rename file or directory.
        
        Args:
            source_path: Source file/directory path
            dest_path: Destination file/directory path
            
        Returns:
            Dict containing success status and metadata
        """
        try:
            safe_source = self._get_safe_path(source_path)
            safe_dest = self._get_safe_path(dest_path)
            
            if not self._check_permission(safe_source, 'move_file'):
                return {
                    "success": False,
                    "error": "Permission denied: move_file not allowed for source path",
                    "source": safe_source,
                    "destination": safe_dest
                }
            
            if not self._check_permission(safe_dest, 'move_file'):
                return {
                    "success": False,
                    "error": "Permission denied: move_file not allowed for destination path",
                    "source": safe_source,
                    "destination": safe_dest
                }
            
            if not os.path.exists(safe_source):
                return {
                    "success": False,
                    "error": "Source path not found",
                    "source": safe_source,
                    "destination": safe_dest
                }
            
            if os.path.exists(safe_dest):
                return {
                    "success": False,
                    "error": "Destination path already exists",
                    "source": safe_source,
                    "destination": safe_dest
                }
            
            # Create destination directory if needed
            dest_dir = os.path.dirname(safe_dest)
            if not os.path.exists(dest_dir):
                if not self._check_permission(dest_dir, 'create_directory'):
                    return {
                        "success": False,
                        "error": "Permission denied: create_directory not allowed for destination parent",
                        "source": safe_source,
                        "destination": safe_dest
                    }
                os.makedirs(dest_dir, exist_ok=True)
            
            shutil.move(safe_source, safe_dest)
            
            return {
                "success": True,
                "source": safe_source,
                "destination": safe_dest,
                "moved": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error moving {source_path} to {dest_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "source": source_path,
                "destination": dest_path
            }
    
    def search_files(self, search_path: str, pattern: str, recursive: bool = True, content_search: bool = False) -> Dict[str, Any]:
        """Search for files by name pattern or content.
        
        Args:
            search_path: Path to search in
            pattern: Search pattern (supports wildcards for filename, regex for content)
            recursive: Whether to search recursively
            content_search: Whether to search file contents (requires read_file permission)
            
        Returns:
            Dict containing success status and search results
        """
        try:
            safe_path = self._get_safe_path(search_path)
            
            if not self._check_permission(safe_path, 'search_files'):
                return {
                    "success": False,
                    "error": "Permission denied: search_files not allowed for this path",
                    "path": safe_path
                }
            
            if not os.path.exists(safe_path):
                return {
                    "success": False,
                    "error": "Search path not found",
                    "path": safe_path
                }
            
            if not os.path.isdir(safe_path):
                return {
                    "success": False,
                    "error": "Search path is not a directory",
                    "path": safe_path
                }
            
            matches = []
            
            if recursive:
                for root, dirs, files in os.walk(safe_path):
                    for file_name in files:
                        file_path = os.path.join(root, file_name)
                        
                        # Check filename pattern
                        if fnmatch.fnmatch(file_name, pattern):
                            match_info = self._get_item_info(file_path)
                            match_info["match_type"] = "filename"
                            matches.append(match_info)
                        
                        # Check content if requested
                        elif content_search and self._check_permission(file_path, 'read_file'):
                            try:
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                                    if pattern.lower() in content.lower():
                                        match_info = self._get_item_info(file_path)
                                        match_info["match_type"] = "content"
                                        matches.append(match_info)
                            except:
                                # Skip files that can't be read
                                continue
            else:
                for item_name in os.listdir(safe_path):
                    item_path = os.path.join(safe_path, item_name)
                    
                    if os.path.isfile(item_path):
                        # Check filename pattern
                        if fnmatch.fnmatch(item_name, pattern):
                            match_info = self._get_item_info(item_path)
                            match_info["match_type"] = "filename"
                            matches.append(match_info)
                        
                        # Check content if requested
                        elif content_search and self._check_permission(item_path, 'read_file'):
                            try:
                                with open(item_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                                    if pattern.lower() in content.lower():
                                        match_info = self._get_item_info(item_path)
                                        match_info["match_type"] = "content"
                                        matches.append(match_info)
                            except:
                                # Skip files that can't be read
                                continue
            
            return {
                "success": True,
                "path": safe_path,
                "pattern": pattern,
                "matches": matches,
                "count": len(matches),
                "content_search": content_search
            }
            
        except Exception as e:
            logger.error(f"Error searching files in {search_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "path": search_path
            }
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get detailed file/directory information.
        
        Args:
            file_path: Path to the file/directory
            
        Returns:
            Dict containing success status and file information
        """
        try:
            safe_path = self._get_safe_path(file_path)
            
            if not self._check_permission(safe_path, 'get_file_info'):
                return {
                    "success": False,
                    "error": "Permission denied: get_file_info not allowed for this path",
                    "path": safe_path
                }
            
            if not os.path.exists(safe_path):
                return {
                    "success": False,
                    "error": "Path not found",
                    "path": safe_path
                }
            
            info = self._get_item_info(safe_path)
            info["success"] = True
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "path": file_path
            }
    
    def _get_item_info(self, item_path: str) -> Dict[str, Any]:
        """Get detailed information about a file or directory item."""
        try:
            stat_info = os.stat(item_path)
            is_dir = os.path.isdir(item_path)
            
            info = {
                "path": item_path,
                "name": os.path.basename(item_path),
                "type": "directory" if is_dir else "file",
                "size": stat_info.st_size if not is_dir else None,
                "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                "accessed": datetime.fromtimestamp(stat_info.st_atime).isoformat(),
            }
            
            # Add file extension for files
            if not is_dir:
                info["extension"] = os.path.splitext(item_path)[1].lower()
            
            # Add permission info (Unix-like systems)
            if hasattr(stat, 'filemode'):
                info["permissions"] = stat.filemode(stat_info.st_mode)
            
            # Add platform-specific info
            if platform.system() == "Windows":
                info["attributes"] = []
                if stat_info.st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN:
                    info["attributes"].append("hidden")
                if stat_info.st_file_attributes & stat.FILE_ATTRIBUTE_READONLY:
                    info["attributes"].append("readonly")
            
            return info
            
        except Exception as e:
            return {
                "path": item_path,
                "error": str(e)
            }

# Global instance for easy access
file_ops = MCPFileOperations()

def get_file_operations() -> MCPFileOperations:
    """Get the global file operations instance."""
    return file_ops

def reload_permissions():
    """Reload folder permissions from configuration file."""
    file_ops._load_permissions()