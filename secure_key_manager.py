"""
Secure Key Manager - Uses OS-native secure storage for API keys

This module provides a secure way to store and retrieve API keys using:
- macOS Keychain on macOS systems
- Windows Credential Manager on Windows systems
- Secret Service API on Linux systems (requires secretstorage package)

It serves as an optional enhancement to the existing file-based storage.
"""

import os
import sys
import logging
import keyring
import json
from typing import Dict, Optional, Any, List

logger = logging.getLogger(__name__)

# Service name used for storing keys in the keychain
SERVICE_NAME = "PythonAgentsApp"

class SecureKeyManager:
    """
    Manages API keys using OS-native secure storage.
    
    This class provides methods to:
    - Store API keys securely in the OS keychain/credential manager
    - Retrieve API keys from secure storage
    - Import keys from config.json or .env file
    - Export keys to config.json or .env file (for compatibility)
    """
    
    def __init__(self):
        """Initialize the secure key manager."""
        self.available = self._check_keyring_available()
        if not self.available:
            logger.warning("Secure key storage is not available on this system.")
    
    def _check_keyring_available(self) -> bool:
        """Check if keyring is available and working on this system."""
        try:
            # Try to set and get a test value
            test_key = "TEST_KEY"
            test_value = "test_value"
            keyring.set_password(SERVICE_NAME, test_key, test_value)
            retrieved = keyring.get_password(SERVICE_NAME, test_key)
            
            # Clean up the test key
            keyring.delete_password(SERVICE_NAME, test_key)
            
            return retrieved == test_value
        except Exception as e:
            logger.error(f"Error testing keyring functionality: {e}")
            return False
    
    def store_key(self, key_name: str, value: str) -> bool:
        """
        Store an API key securely.
        
        Args:
            key_name: The name of the API key (e.g., 'OPENAI_API_KEY')
            value: The API key value
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.available:
            logger.warning("Secure key storage is not available. Key not stored.")
            return False
            
        try:
            keyring.set_password(SERVICE_NAME, key_name, value)
            logger.info(f"API key '{key_name}' stored securely")
            return True
        except Exception as e:
            logger.error(f"Error storing API key '{key_name}': {e}")
            return False
    
    def get_key(self, key_name: str) -> Optional[str]:
        """
        Retrieve an API key from secure storage.
        
        Args:
            key_name: The name of the API key to retrieve
            
        Returns:
            str: The API key value, or None if not found
        """
        if not self.available:
            logger.warning("Secure key storage is not available. Cannot retrieve key.")
            return None
            
        try:
            value = keyring.get_password(SERVICE_NAME, key_name)
            return value
        except Exception as e:
            logger.error(f"Error retrieving API key '{key_name}': {e}")
            return None
    
    def delete_key(self, key_name: str) -> bool:
        """
        Delete an API key from secure storage.
        
        Args:
            key_name: The name of the API key to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.available:
            return False
            
        try:
            if self.get_key(key_name) is not None:
                keyring.delete_password(SERVICE_NAME, key_name)
                logger.info(f"API key '{key_name}' deleted")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting API key '{key_name}': {e}")
            return False
    
    def list_keys(self) -> List[str]:
        """
        List all stored API key names.
        
        Note: This is a best-effort function as keyring doesn't natively
        support listing all keys. It tries to retrieve known key names.
        
        Returns:
            List[str]: List of key names that exist in the keychain
        """
        if not self.available:
            return []
            
        # Common API key names used in the application
        common_keys = [
            'OPENAI_API_KEY',
            'GOOGLE_API_KEY',
            'GOOGLE_SEARCH_ENGINE_ID',
            'GEMINI_API_KEY',
            'ANTHROPIC_API_KEY',
            'GROQ_API_KEY',
            'GROK_API_KEY',
            'DEEPSEEK_API_KEY',
            'SERPER_API_KEY',
            'OPENROUTER_API_KEY',
        ]
        
        # Check which keys exist in the keychain
        existing_keys = []
        for key in common_keys:
            if self.get_key(key) is not None:
                existing_keys.append(key)
                
        return existing_keys
    
    def import_from_config(self, config_path: str = 'config.json') -> int:
        """
        Import API keys from config.json file into secure storage.
        
        Args:
            config_path: Path to the config.json file
            
        Returns:
            int: Number of keys imported
        """
        if not self.available or not os.path.exists(config_path):
            return 0
            
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                
            count = 0
            for key_name, value in config.items():
                if value and self.store_key(key_name, value):
                    count += 1
                    
            logger.info(f"Imported {count} API keys from {config_path}")
            return count
        except Exception as e:
            logger.error(f"Error importing API keys from {config_path}: {e}")
            return 0
    
    def import_from_env(self, env_path: str = '.env') -> int:
        """
        Import API keys from .env file into secure storage.
        
        Args:
            env_path: Path to the .env file
            
        Returns:
            int: Number of keys imported
        """
        if not self.available or not os.path.exists(env_path):
            return 0
            
        try:
            count = 0
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                        
                    if '=' in line:
                        key_name, value = line.split('=', 1)
                        key_name = key_name.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                            
                        if value and self.store_key(key_name, value):
                            count += 1
                            
            logger.info(f"Imported {count} API keys from {env_path}")
            return count
        except Exception as e:
            logger.error(f"Error importing API keys from {env_path}: {e}")
            return 0
    
    def export_to_config(self, config_path: str = 'config.json') -> int:
        """
        Export API keys from secure storage to config.json file.
        
        Args:
            config_path: Path to the config.json file
            
        Returns:
            int: Number of keys exported
        """
        if not self.available:
            return 0
            
        try:
            # Get existing config if it exists
            config = {}
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    
            # Update config with keys from secure storage
            keys = self.list_keys()
            count = 0
            for key_name in keys:
                value = self.get_key(key_name)
                if value:
                    config[key_name] = value
                    count += 1
                    
            # Write updated config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
                
            logger.info(f"Exported {count} API keys to {config_path}")
            return count
        except Exception as e:
            logger.error(f"Error exporting API keys to {config_path}: {e}")
            return 0
    
    def export_to_env(self, env_path: str = '.env') -> int:
        """
        Export API keys from secure storage to .env file.
        
        Args:
            env_path: Path to the .env file
            
        Returns:
            int: Number of keys exported
        """
        if not self.available:
            return 0
            
        try:
            # Get existing env vars if file exists
            env_vars = {}
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                            
                        if '=' in line:
                            key_name, value = line.split('=', 1)
                            env_vars[key_name.strip()] = value.strip()
                            
            # Update env vars with keys from secure storage
            keys = self.list_keys()
            count = 0
            for key_name in keys:
                value = self.get_key(key_name)
                if value:
                    env_vars[key_name] = value
                    count += 1
                    
            # Write updated env file
            with open(env_path, 'w') as f:
                for key_name, value in env_vars.items():
                    f.write(f"{key_name}={value}\n")
                    
            logger.info(f"Exported {count} API keys to {env_path}")
            return count
        except Exception as e:
            logger.error(f"Error exporting API keys to {env_path}: {e}")
            return 0


# Create a global instance of the secure key manager
secure_key_manager = SecureKeyManager()


def main():
    """Command-line interface for the secure key manager."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Secure API Key Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Store command
    store_parser = subparsers.add_parser("store", help="Store an API key")
    store_parser.add_argument("key", help="API key name (e.g., OPENAI_API_KEY)")
    store_parser.add_argument("value", help="API key value")
    
    # Get command
    get_parser = subparsers.add_parser("get", help="Get an API key")
    get_parser.add_argument("key", help="API key name to retrieve")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete an API key")
    delete_parser.add_argument("key", help="API key name to delete")
    
    # List command
    subparsers.add_parser("list", help="List all stored API keys")
    
    # Import command
    import_parser = subparsers.add_parser("import", help="Import API keys from file")
    import_parser.add_argument("--config", action="store_true", help="Import from config.json")
    import_parser.add_argument("--env", action="store_true", help="Import from .env")
    import_parser.add_argument("--path", help="Custom file path to import from")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export API keys to file")
    export_parser.add_argument("--config", action="store_true", help="Export to config.json")
    export_parser.add_argument("--env", action="store_true", help="Export to .env")
    export_parser.add_argument("--path", help="Custom file path to export to")
    
    args = parser.parse_args()
    
    # Check if secure storage is available
    if not secure_key_manager.available:
        print("Error: Secure key storage is not available on this system.")
        return 1
    
    # Execute the requested command
    if args.command == "store":
        if secure_key_manager.store_key(args.key, args.value):
            print(f"API key '{args.key}' stored successfully")
            return 0
        else:
            print(f"Failed to store API key '{args.key}'")
            return 1
    
    elif args.command == "get":
        value = secure_key_manager.get_key(args.key)
        if value is not None:
            print(value)
            return 0
        else:
            print(f"API key '{args.key}' not found")
            return 1
    
    elif args.command == "delete":
        if secure_key_manager.delete_key(args.key):
            print(f"API key '{args.key}' deleted successfully")
            return 0
        else:
            print(f"Failed to delete API key '{args.key}'")
            return 1
    
    elif args.command == "list":
        keys = secure_key_manager.list_keys()
        if keys:
            print("Stored API keys:")
            for key in keys:
                print(f"- {key}")
        else:
            print("No API keys found in secure storage")
        return 0
    
    elif args.command == "import":
        count = 0
        if args.config:
            count = secure_key_manager.import_from_config()
        elif args.env:
            count = secure_key_manager.import_from_env()
        elif args.path:
            if args.path.endswith('.json'):
                count = secure_key_manager.import_from_config(args.path)
            elif args.path.endswith('.env'):
                count = secure_key_manager.import_from_env(args.path)
            else:
                print(f"Unsupported file format: {args.path}")
                return 1
        else:
            print("Please specify --config, --env, or --path")
            return 1
            
        print(f"Imported {count} API keys")
        return 0
    
    elif args.command == "export":
        count = 0
        if args.config:
            count = secure_key_manager.export_to_config()
        elif args.env:
            count = secure_key_manager.export_to_env()
        elif args.path:
            if args.path.endswith('.json'):
                count = secure_key_manager.export_to_config(args.path)
            elif args.path.endswith('.env'):
                count = secure_key_manager.export_to_env(args.path)
            else:
                print(f"Unsupported file format: {args.path}")
                return 1
        else:
            print("Please specify --config, --env, or --path")
            return 1
            
        print(f"Exported {count} API keys")
        return 0
    
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
