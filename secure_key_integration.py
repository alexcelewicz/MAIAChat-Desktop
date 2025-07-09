"""
Secure Key Integration - Example script showing how to use the secure key manager

This script demonstrates how to:
1. Import API keys from config.json or .env into secure storage
2. Use the secure key manager with the existing application
3. Export API keys from secure storage to config.json or .env

Usage:
    python secure_key_integration.py import  # Import keys from config.json/.env to secure storage
    python secure_key_integration.py export  # Export keys from secure storage to config.json/.env
    python secure_key_integration.py list    # List all keys in secure storage
"""

import sys
import os
import logging
from secure_key_manager import secure_key_manager
from config_manager import ConfigManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SecureKeyIntegration")

def import_keys():
    """Import API keys from config.json and .env into secure storage."""
    # Import from config.json
    config_count = secure_key_manager.import_from_config()
    logger.info(f"Imported {config_count} keys from config.json")
    
    # Import from .env
    env_count = secure_key_manager.import_from_env()
    logger.info(f"Imported {env_count} keys from .env")
    
    total = config_count + env_count
    if total > 0:
        print(f"Successfully imported {total} API keys into secure storage")
    else:
        print("No API keys were imported. Make sure config.json or .env exists with valid keys.")

def export_keys():
    """Export API keys from secure storage to config.json and .env."""
    # Export to config.json
    config_count = secure_key_manager.export_to_config()
    logger.info(f"Exported {config_count} keys to config.json")
    
    # Export to .env
    env_count = secure_key_manager.export_to_env()
    logger.info(f"Exported {env_count} keys to .env")
    
    total = config_count + env_count
    if total > 0:
        print(f"Successfully exported {total} API keys from secure storage")
    else:
        print("No API keys were exported. Make sure keys exist in secure storage.")

def list_keys():
    """List all API keys in secure storage."""
    keys = secure_key_manager.list_keys()
    if keys:
        print("API keys in secure storage:")
        for key in keys:
            print(f"- {key}")
    else:
        print("No API keys found in secure storage")

def integrate_with_config_manager():
    """
    Example of how to integrate secure key manager with the existing ConfigManager.
    
    This function demonstrates how you could modify the ConfigManager to use
    secure storage as a fallback when keys aren't found in config.json or .env.
    """
    # Create a ConfigManager instance
    config_manager = ConfigManager()
    
    # Example of how to modify get_api_key to use secure storage as fallback
    key_name = "OPENAI_API_KEY"
    value = config_manager.get_api_key(key_name)
    
    if not value:
        # Key not found in config.json or .env, try secure storage
        value = secure_key_manager.get_key(key_name)
        if value:
            print(f"Retrieved {key_name} from secure storage")
        else:
            print(f"{key_name} not found in any storage")
    else:
        print(f"Retrieved {key_name} from config.json or .env")

def main():
    """Main function to handle command-line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python secure_key_integration.py [import|export|list]")
        return 1
    
    command = sys.argv[1].lower()
    
    if command == "import":
        import_keys()
    elif command == "export":
        export_keys()
    elif command == "list":
        list_keys()
    elif command == "integrate":
        integrate_with_config_manager()
    else:
        print(f"Unknown command: {command}")
        print("Usage: python secure_key_integration.py [import|export|list|integrate]")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
