# config.py
"""
Global configuration manager instance for MAIAChat Desktop.

This module provides a single, centralized ConfigManager instance that should be
imported and used by all other modules instead of creating their own instances
or loading configuration separately.

Usage:
    from config import config_manager
    
    # Get a configuration value
    api_key = config_manager.get('OPENAI_API_KEY')
    
    # Set a configuration value  
    config_manager.set('SOME_SETTING', 'value')
    
    # Save configuration
    config_manager.save_config()
"""

from config_manager import ConfigManager

# Global ConfigManager instance with auto-reload enabled
# This instance will be imported and used by all other modules
config_manager = ConfigManager(auto_reload=True)

# Convenience functions for common operations
def get_api_key(provider: str) -> str:
    """
    Get API key for a specific provider.
    
    Args:
        provider: Provider name (e.g., 'openai', 'anthropic', 'google')
        
    Returns:
        API key string or empty string if not found
    """
    key_mappings = {
        'openai': 'OPENAI_API_KEY',
        'anthropic': 'ANTHROPIC_API_KEY', 
        'google': 'GOOGLE_API_KEY',
        'groq': 'GROQ_API_KEY',
        'grok': 'GROK_API_KEY',
        'cohere': 'COHERE_API_KEY',
        'openrouter': 'OPENROUTER_API_KEY'
    }
    
    key_name = key_mappings.get(provider.lower())
    if not key_name:
        return ""
        
    return config_manager.get(key_name, "")

def get_rag_setting(setting_name: str, default_value=None):
    """
    Get RAG-specific setting with proper defaults.
    
    Args:
        setting_name: Setting name (without RAG_ prefix)
        default_value: Default value if setting not found
        
    Returns:
        Setting value or default
    """
    full_setting_name = f"RAG_{setting_name.upper()}"
    return config_manager.get(full_setting_name, default_value)

def is_provider_available(provider: str) -> bool:
    """
    Check if a provider has a valid API key configured.
    
    Args:
        provider: Provider name
        
    Returns:
        True if API key is available, False otherwise
    """
    api_key = get_api_key(provider)
    return bool(api_key and api_key.strip())

def get_embedding_settings() -> dict:
    """
    Get all embedding-related settings.
    
    Returns:
        Dictionary of embedding settings
    """
    return {
        'provider': config_manager.get('EMBEDDING_PROVIDER', 'sentence_transformer'),
        'model': config_manager.get('EMBEDDING_MODEL', 'all-mpnet-base-v2'),
        'dimension': config_manager.get('EMBEDDING_DIMENSION', 768),
        'device': config_manager.get('EMBEDDING_DEVICE', 'auto'),
        'batch_size': config_manager.get('EMBEDDING_BATCH_SIZE', 32)
    }

def get_chunking_settings() -> dict:
    """
    Get all text chunking settings.
    
    Returns:
        Dictionary of chunking settings
    """
    return {
        'strategy': config_manager.get('CHUNKING_STRATEGY', 'semantic'),
        'chunk_size': config_manager.get('CHUNK_SIZE', 500),
        'chunk_overlap': config_manager.get('CHUNK_OVERLAP', 50),
        'max_chunks': config_manager.get('MAX_CHUNKS_PER_FILE', 1000)
    }

def get_network_settings() -> dict:
    """
    Get network-related settings.
    
    Returns:
        Dictionary of network settings
    """
    return {
        'timeout': config_manager.get('NETWORK_TIMEOUT', 30),
        'max_retries': config_manager.get('MAX_RETRIES', 3),
        'retry_delay': config_manager.get('RETRY_DELAY', 1),
        'enable_internet': config_manager.get('ENABLE_INTERNET_SEARCH', True)
    } 