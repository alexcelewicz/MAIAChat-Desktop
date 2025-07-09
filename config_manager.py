# config_manager.py
import os
import json
import logging
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Callable, Type
from dataclasses import dataclass, field
from datetime import datetime
from dotenv import load_dotenv
import hashlib
import base64

# Optional dependencies for enhanced features
try:
    from cryptography.fernet import Fernet
    HAS_ENCRYPTION = True
except ImportError:
    HAS_ENCRYPTION = False

try:
    import jsonschema
    HAS_SCHEMA_VALIDATION = True
except ImportError:
    HAS_SCHEMA_VALIDATION = False

try:
    from secure_key_manager import secure_key_manager
    HAS_SECURE_KEY_MANAGER = True
except ImportError:
    HAS_SECURE_KEY_MANAGER = False

# Import api_key_manager for API key definitions
from api_key_manager import ApiKeyManager
api_key_manager = ApiKeyManager()

# Use a logger for better tracking
logger = logging.getLogger(__name__)

@dataclass
class ConfigValue:
    """Represents a configuration value with metadata."""
    value: Any
    source: str = "default"  # "default", "file", "env", "runtime"
    last_updated: datetime = field(default_factory=datetime.now)
    is_sensitive: bool = False
    validator: Optional[Callable[[Any], bool]] = None
    description: str = ""

class ConfigManager:
    """
    Advanced configuration manager with enhanced features:
    - Multi-source configuration loading with clear precedence
    - Type validation and schema support
    - Encrypted storage for sensitive values
    - Auto-reload capability
    - Thread-safe operations
    - Comprehensive logging and auditing
    - Backward compatibility maintained
    
    Loading priority:
    1. Default values set in code
    2. Values from the config.json file
    3. Values from environment variables (highest priority)
    4. Runtime values set via set() method
    """

    # --- Constants ---
    DEFAULT_CONFIG_FILE = "config.json"
    ENCRYPTED_CONFIG_FILE = "config.encrypted"
    
    # Environment variables that should be loaded into the config
    RECOGNIZED_ENV_KEYS: List[str] = [
        'OPENAI_API_KEY', 'GOOGLE_API_KEY', 'GOOGLE_SEARCH_ENGINE_ID',
        'GEMINI_API_KEY', 'ANTHROPIC_API_KEY', 'GROQ_API_KEY',
        'DEEPSEEK_API_KEY', 'SERPER_API_KEY', 'OPENROUTER_API_KEY',
        'POLYGON_API_KEY', 'RAG_ULTRA_SAFE_MODE', 'RAG_SAFE_RETRIEVAL_MODE', 'EMBEDDING_DEVICE'
    ]
    
    # Sensitive keys that should be encrypted when saved
    SENSITIVE_KEYS = {
        'OPENAI_API_KEY', 'GOOGLE_API_KEY', 'GEMINI_API_KEY',
        'ANTHROPIC_API_KEY', 'GROQ_API_KEY', 'DEEPSEEK_API_KEY',
        'SERPER_API_KEY', 'OPENROUTER_API_KEY', 'POLYGON_API_KEY'
    }

    # Configuration schema for validation
    DEFAULT_SCHEMA = {
        "type": "object",
        "properties": {
            "MAX_RESPONSE_CONTEXT": {"type": "integer", "minimum": 1024},
            "AUTO_RELOAD_CONFIG": {"type": "boolean"},
            "CONFIG_WATCH_INTERVAL": {"type": "number", "minimum": 1.0},
            "RAG_ULTRA_SAFE_MODE": {"type": "boolean", "default": False},
            "RAG_SAFE_RETRIEVAL_MODE": {"type": "boolean", "default": False},
            "EMBEDDING_DEVICE": {"type": "string", "enum": ["cpu", "cuda", "mps", "auto"], "default": "cpu"}
        }
    }

    def __init__(self, 
                 config_file: str = DEFAULT_CONFIG_FILE,
                 auto_reload: bool = False,
                 watch_interval: float = 5.0,
                 encryption_key: Optional[str] = None,
                 schema: Optional[Dict] = None):
        """
        Initializes the ConfigManager with enhanced features.

        Args:
            config_file (str): The path to the configuration file
            auto_reload (bool): Whether to automatically reload config when file changes
            watch_interval (float): Interval in seconds for checking config file changes
            encryption_key (Optional[str]): Key for encrypting sensitive configuration data
            schema (Optional[Dict]): JSON schema for configuration validation
        """
        self.config_path = Path(config_file)
        self.encrypted_path = Path(self.ENCRYPTED_CONFIG_FILE)
        self.auto_reload = auto_reload
        self.watch_interval = watch_interval
        self.schema = schema or self.DEFAULT_SCHEMA.copy()
        
        # Thread safety
        self._lock = threading.RLock()
        self._stop_watching = threading.Event()
        self._watch_thread: Optional[threading.Thread] = None
        
        # Configuration storage with metadata
        self._config_values: Dict[str, ConfigValue] = {}
        self._file_hash = ""
        self._last_reload = datetime.now()
        
        # Encryption setup
        self._cipher = None
        if encryption_key and HAS_ENCRYPTION:
            self._setup_encryption(encryption_key)
        elif self.SENSITIVE_KEYS and not HAS_ENCRYPTION:
            logger.warning("Encryption requested but cryptography library not available. "
                         "Install with: pip install cryptography")
        
        # Callbacks for configuration changes
        self._change_callbacks: List[Callable[[str, Any, Any], None]] = []
        
        # Load initial configuration
        self.load_config()
        
        # Start auto-reload if requested
        if auto_reload:
            self.start_auto_reload()
    
    def _setup_encryption(self, key: str) -> None:
        """Set up encryption for sensitive configuration values."""
        try:
            # Convert string key to proper Fernet key
            key_bytes = key.encode()
            if len(key_bytes) != 32:
                # Hash the key to get consistent 32 bytes
                key_bytes = hashlib.sha256(key_bytes).digest()
            
            fernet_key = base64.urlsafe_b64encode(key_bytes)
            self._cipher = Fernet(fernet_key)
            logger.info("Encryption enabled for sensitive configuration values")
        except Exception as e:
            logger.error(f"Failed to setup encryption: {e}")
            self._cipher = None
    
    def _encrypt_value(self, value: str) -> str:
        """Encrypt a sensitive value."""
        if not self._cipher:
            return value
        try:
            return self._cipher.encrypt(value.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt value: {e}")
            return value
    
    def _decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a sensitive value."""
        if not self._cipher:
            return encrypted_value
        try:
            return self._cipher.decrypt(encrypted_value.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to decrypt value: {e}")
            return encrypted_value
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Get hash of configuration file for change detection."""
        if not file_path.exists():
            return ""
        try:
            with file_path.open('rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""
    
    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value to appropriate type."""
        if not value:
            return value
        
        # Try to parse as JSON first (for complex types)
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass
        
        # Handle common boolean values
        if value.lower() in ('true', 'yes', '1', 'on'):
            return True
        elif value.lower() in ('false', 'no', '0', 'off'):
            return False
        
        # Try to parse as number
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def _validate_config(self) -> bool:
        """Validate configuration against schema."""
        if not HAS_SCHEMA_VALIDATION or not self.schema:
            return True
        
        try:
            # Convert ConfigValue objects to plain values for validation
            config_dict = {k: v.value for k, v in self._config_values.items()}
            jsonschema.validate(config_dict, self.schema)
            return True
        except jsonschema.ValidationError as e:
            logger.error(f"Configuration validation failed: {e.message}")
            return False
        except Exception as e:
            logger.error(f"Configuration validation error: {e}")
            return False
    
    def add_change_callback(self, callback: Callable[[str, Any, Any], None]) -> None:
        """Add a callback to be called when configuration changes."""
        with self._lock:
            self._change_callbacks.append(callback)
    
    def remove_change_callback(self, callback: Callable[[str, Any, Any], None]) -> None:
        """Remove a change callback."""
        with self._lock:
            if callback in self._change_callbacks:
                self._change_callbacks.remove(callback)
    
    def _notify_change(self, key: str, old_value: Any, new_value: Any) -> None:
        """Notify all callbacks of a configuration change."""
        for callback in self._change_callbacks:
            try:
                callback(key, old_value, new_value)
            except Exception as e:
                logger.error(f"Error in change callback: {e}")
    
    def load_config(self) -> None:
        """
        Loads configuration from multiple sources with proper precedence.
        """
        with self._lock:
            logger.info("Loading configuration from all sources...")
            
            # Load .env file into environment variables
            load_dotenv()
            
            # 1. Load from JSON config file
            config_from_file = {}
            if self.config_path.exists():
                try:
                    with self.config_path.open('r', encoding='utf-8') as f:
                        config_from_file = json.load(f)
                    logger.info(f"Loaded {len(config_from_file)} settings from {self.config_path}")
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding JSON from {self.config_path}: {e}")
                except IOError as e:
                    logger.error(f"Error reading config file {self.config_path}: {e}")
            
            # 2. Load from encrypted file if available
            encrypted_config = {}
            if self.encrypted_path.exists() and self._cipher:
                try:
                    with self.encrypted_path.open('r', encoding='utf-8') as f:
                        encrypted_data = json.load(f)
                    
                    for key, encrypted_value in encrypted_data.items():
                        try:
                            encrypted_config[key] = self._decrypt_value(encrypted_value)
                        except Exception as e:
                            logger.error(f"Failed to decrypt config key {key}: {e}")
                    
                    logger.info(f"Loaded {len(encrypted_config)} encrypted settings")
                except Exception as e:
                    logger.error(f"Error loading encrypted config: {e}")
            
            # 3. Load from environment variables
            config_from_env = {}
            for key in self.RECOGNIZED_ENV_KEYS:
                env_value = os.getenv(key)
                if env_value:
                    config_from_env[key] = self._parse_env_value(env_value)
            
            # Also check for any environment variables starting with CONFIG_
            for env_key, env_value in os.environ.items():
                if env_key.startswith('CONFIG_') and env_key not in config_from_env:
                    config_key = env_key[7:]  # Remove CONFIG_ prefix
                    config_from_env[config_key] = self._parse_env_value(env_value)
            
            if config_from_env:
                logger.info(f"Loaded {len(config_from_env)} settings from environment")
            
            # 4. Load from secure storage if available
            config_from_secure_storage = {}
            if HAS_SECURE_KEY_MANAGER:
                logger.info("Attempting to load sensitive keys from secure storage...")
                for key in self.SENSITIVE_KEYS: # Or self.RECOGNIZED_ENV_KEYS for all known
                    if key not in config_from_file and key not in config_from_env: # Only if not already loaded from file/env
                        secure_value = secure_key_manager.get_key(key)
                        if secure_value:
                            config_from_secure_storage[key] = self._parse_env_value(secure_value) # Parse like env
                            logger.info(f"Loaded '{key}' from secure storage.")
            
            # 5. Merge all sources into ConfigValue objects
            all_sources = [
                (config_from_file, "file"),
                (encrypted_config, "file"),
                (config_from_env, "env"),
                (config_from_secure_storage, "secure_storage")
            ]
            
            for config_dict, source in all_sources:
                for key, value in config_dict.items():
                    old_value = self._config_values.get(key)
                    
                    self._config_values[key] = ConfigValue(
                        value=value,
                        source=source,
                        last_updated=datetime.now(),
                        is_sensitive=key in self.SENSITIVE_KEYS
                    )
                    
                    # Notify of changes
                    if old_value and old_value.value != value:
                        self._notify_change(key, old_value.value, value)
            
            # 6. Validate configuration
            if not self._validate_config():
                logger.warning("Configuration validation failed")
            
            # 7. Update file hash for change detection
            self._file_hash = self._get_file_hash(self.config_path)
            self._last_reload = datetime.now()
            
            logger.info(f"Configuration loaded successfully. Total keys: {len(self._config_values)}")

            # Log missing required API keys if any
            missing_keys = self.missing_required_api_keys
            if missing_keys:
                logger.warning(f"Missing required API keys: {', '.join(missing_keys)}. Some functionalities might be limited.")
    
    def save_config(self) -> None:
        """
        Saves the current configuration state, handling encryption for sensitive values.
        """
        with self._lock:
            try:
                # Separate regular and sensitive config
                regular_config = {}
                sensitive_config = {}
                
                for key, config_value in self._config_values.items():
                    # Only save values that came from file or were set at runtime
                    if config_value.source in ("file", "runtime"):
                        if config_value.is_sensitive and self._cipher:
                            sensitive_config[key] = self._encrypt_value(str(config_value.value))
                        else:
                            regular_config[key] = config_value.value
                
                # Save regular config
                if regular_config:
                    with self.config_path.open('w', encoding='utf-8') as f:
                        json.dump(regular_config, f, indent=4, default=str)
                    logger.info(f"Saved {len(regular_config)} settings to {self.config_path}")
                
                # Save sensitive config if encryption is available
                if sensitive_config and self._cipher:
                    with self.encrypted_path.open('w', encoding='utf-8') as f:
                        json.dump(sensitive_config, f, indent=4)
                    logger.info(f"Saved {len(sensitive_config)} encrypted settings")
                
                # Update file hash
                self._file_hash = self._get_file_hash(self.config_path)
                
            except IOError as e:
                logger.error(f"Failed to save configuration: {e}")
    
    def start_auto_reload(self) -> None:
        """Start watching configuration file for changes."""
        if self._watch_thread and self._watch_thread.is_alive():
            return
        
        self._stop_watching.clear()
        self._watch_thread = threading.Thread(target=self._watch_config_file, daemon=True)
        self._watch_thread.start()
        logger.info("Started auto-reload for configuration file")
    
    def stop_auto_reload(self) -> None:
        """Stop watching configuration file for changes."""
        self._stop_watching.set()
        if self._watch_thread:
            self._watch_thread.join(timeout=1.0)
        logger.info("Stopped auto-reload for configuration file")
    
    def _watch_config_file(self) -> None:
        """Watch configuration file for changes and reload when necessary."""
        while not self._stop_watching.is_set():
            try:
                current_hash = self._get_file_hash(self.config_path)
                if current_hash and current_hash != self._file_hash:
                    logger.info("Configuration file changed, reloading...")
                    self.load_config()
                
                self._stop_watching.wait(self.watch_interval)
            except Exception as e:
                logger.error(f"Error in config file watcher: {e}")
                self._stop_watching.wait(self.watch_interval)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieves a configuration value.

        Args:
            key (str): The configuration key to retrieve.
            default (Any): The value to return if the key is not found.

        Returns:
            Any: The configuration value or the default.
        """
        with self._lock:
            config_value_obj = self._config_values.get(key)
            if config_value_obj is not None:
                return config_value_obj.value
            
            # Fallback: Try to get from secure storage if not in memory
            if HAS_SECURE_KEY_MANAGER and key in self.SENSITIVE_KEYS: # Or all RECOGNIZED_ENV_KEYS
                logger.debug(f"Key '{key}' not in config, trying secure storage...")
                secure_value_str = secure_key_manager.get_key(key)
                if secure_value_str is not None:
                    # Parse and store it in memory for future gets (as runtime override)
                    parsed_value = self._parse_env_value(secure_value_str)
                    self._config_values[key] = ConfigValue(
                        value=parsed_value,
                        source="secure_storage_fallback", # Indicate it was loaded on demand
                        last_updated=datetime.now(),
                        is_sensitive=key in self.SENSITIVE_KEYS
                    )
                    logger.info(f"Retrieved and cached '{key}' from secure storage on demand.")
                    return parsed_value
            
            return default
    
    def set(self, key: str, value: Any, save: bool = True) -> None:
        """
        Sets a configuration value with enhanced metadata tracking.

        Args:
            key (str): The configuration key to set.
            value (Any): The value to assign to the key.
            save (bool): Whether to save the configuration immediately.
        """
        with self._lock:
            old_value = self._config_values.get(key)
            old_val = old_value.value if old_value else None
            
            self._config_values[key] = ConfigValue(
                value=value,
                source="runtime",
                last_updated=datetime.now(),
                is_sensitive=key in self.SENSITIVE_KEYS
            )
            
            self._notify_change(key, old_val, value)
            
            if save:
                self.save_config()
            
            logger.debug(f"Set configuration key '{key}' = '{value}' (source: runtime)")
    
    def remove(self, key: str, save: bool = True) -> None:
        """
        Removes a key from the configuration.

        Args:
            key (str): The key to remove.
            save (bool): Whether to save the configuration immediately.
        """
        with self._lock:
            if key in self._config_values:
                old_value = self._config_values[key].value
                del self._config_values[key]
                self._notify_change(key, old_value, None)
                
                if save:
                    self.save_config()
                
                logger.debug(f"Removed configuration key '{key}'")
    
    def get_config_info(self, key: str) -> Optional[ConfigValue]:
        """Get detailed information about a configuration key."""
        with self._lock:
            return self._config_values.get(key)
    
    def list_keys(self, include_sensitive: bool = False) -> List[str]:
        """List all configuration keys."""
        with self._lock:
            if include_sensitive:
                return list(self._config_values.keys())
            else:
                return [k for k, v in self._config_values.items() if not v.is_sensitive]
    
    def export_config(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Export current configuration as a dictionary."""
        with self._lock:
            result = {}
            for key, config_value in self._config_values.items():
                if include_sensitive or not config_value.is_sensitive:
                    result[key] = config_value.value
            return result
    
    def validate_required_keys(self, required_keys: List[str]) -> bool:
        """
        Validates that required keys are present and have non-empty values.

        Args:
            required_keys (List[str]): A list of keys that must exist.

        Returns:
            bool: True if all keys are present and valid, False otherwise.
        """
        with self._lock:
            missing_keys = []
            empty_keys = []
            
            for key in required_keys:
                if key not in self._config_values:
                    missing_keys.append(key)
                elif not self._config_values[key].value:
                    empty_keys.append(key)
            
            if missing_keys or empty_keys:
                if missing_keys:
                    logger.warning(f"Missing required configuration keys: {missing_keys}")
                if empty_keys:
                    logger.warning(f"Empty required configuration keys: {empty_keys}")
                return False
            
            return True
    
    # --- Backward Compatibility Methods ---
    # These maintain the exact same interface as the original implementation
    
    @property
    def config(self) -> Dict[str, Any]:
        """Backward compatibility property for direct config access."""
        with self._lock:
            return {k: v.value for k, v in self._config_values.items()}
    
    def validate(self) -> bool:
        """
        DEPRECATED: Validate that required API keys are present (backward compatibility).
        Use missing_required_api_keys property instead for better API key validation.
        """
        # Check if any required API keys are missing
        missing_keys = self.missing_required_api_keys
        if missing_keys:
            logger.warning(f"Missing required API keys: {', '.join(missing_keys)}. Some functionalities might be limited.")
            return False
        return True
    
    def get_api_key(self, key_name: str) -> Optional[str]:
        """Get API key value (backward compatibility)."""
        return self.get(key_name)
    
    def set_api_key(self, key_name: str, value: str):
        """Set API key value and save (backward compatibility)."""
        self.set(key_name, value)
    
    def remove_api_key(self, key_name: str):
        """Remove API key from configuration (backward compatibility)."""
        self.remove(key_name)
    
    def get_max_response_context(self) -> int:
        """Get maximum response context size (backward compatibility)."""
        return int(self.get('MAX_RESPONSE_CONTEXT', 16384))
    
    def set_max_response_context(self, value: int):
        """Set maximum response context size (backward compatibility)."""
        self.set('MAX_RESPONSE_CONTEXT', value)
    
    @property
    def missing_required_api_keys(self) -> list:
        """
        Return a list of missing required API key display names.
        This property is computed based on ApiKeyManager definitions with required=True.
        """
        missing_keys = []
        for definition in api_key_manager.get_all_definitions():
            if getattr(definition, 'required', False):
                if not self.get(definition.id):
                    missing_keys.append(definition.name)
        return missing_keys
    
    def __del__(self):
        """Cleanup when the object is destroyed."""
        try:
            self.stop_auto_reload()
        except Exception:
            pass  # Ignore errors during cleanup

    def get_default_config(self):
        """Get default configuration with enhanced timeout settings for challenging tasks."""
        return {
            # API Keys
            "OPENAI_API_KEY": "",
            "ANTHROPIC_API_KEY": "",
            "GROQ_API_KEY": "",
            "GROK_API_KEY": "",
            "COHERE_API_KEY": "",
            "GOOGLE_API_KEY": "",
            "GOOGLE_SEARCH_ENGINE_ID": "",
            "OPENROUTER_API_KEY": "",
            "DEEPSEEK_API_KEY": "",
            
            # RAG Settings
            "RAG_ULTRA_SAFE_MODE": False,
            "RAG_SAFE_RETRIEVAL_MODE": False,
            "EMBEDDING_DEVICE": "cpu",
            
            # Timeout Settings for Challenging Tasks
            "AGENT_PROCESSING_TIMEOUT": 90,  # 1.5 minutes timeout for challenging tasks
            "API_CALL_TIMEOUT": 60,  # 1 minute timeout for API calls
            "CHUNK_TIMEOUT": 20,  # 20 seconds timeout between chunks
            "MAX_RETRIES": 1,  # Maximum retry attempts (reduced to prevent long delays)
            "RETRY_DELAY": 3,  # Delay between retries in seconds (reduced)
            
            # Response Processing Settings
            "DISABLE_RESPONSE_CLEANING": False,  # Disable response cleaning for testing
            "MCP_SINGLE_PASS_MODE": True,  # Use single-pass MCP processing to improve performance
            
            # Performance Settings
            "ENABLE_STREAMING": True,
            "ENABLE_CACHING": True,
            "MAX_CONCURRENT_REQUESTS": 3,
            
            # UI Settings
            "AUTO_SAVE_INTERVAL": 30,
            "MAX_HISTORY_ITEMS": 100,
            "ENABLE_ANIMATIONS": True,
            
            # Debug Settings
            "ENABLE_DEBUG_LOGGING": False,
            "LOG_LEVEL": "INFO",
            "SAVE_ERROR_LOGS": True
        }
