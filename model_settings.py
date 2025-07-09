"""
Model settings module for managing provider-specific model parameters.
"""

import json
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict

# Import centralized data from data registry
from data_registry import PARAMETER_RANGES, DEFAULT_SETTINGS, PROVIDER_PARAMETERS

@dataclass
class ModelSettings:
    """Class for storing model-specific settings."""
    provider: str
    model: str
    context_window: int = 16000  # Add context_window with a default
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    max_tokens: int = 4096
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    repetition_penalty: float = 1.0
    stop_sequences: List[str] = field(default_factory=list)
    streaming_enabled: bool = True  # Add streaming enabled flag
    thinking_enabled: bool = False  # Enable thinking for supported models
    thinking_budget: int = -1  # -1 for unlimited thinking budget
    
    def __post_init__(self):
        """Initialize with provider-specific defaults."""
        if self.provider in DEFAULT_SETTINGS:
            defaults = DEFAULT_SETTINGS[self.provider]
            for key, value in defaults.items():
                if hasattr(self, key):
                    setattr(self, key, value)
    
    def get_effective_max_tokens(self, user_requested_tokens: Optional[int] = None) -> int:
        """
        Get the effective max_tokens value, considering user requests and API limits.
        
        Args:
            user_requested_tokens: User-specified token limit (e.g., 100k)
            
        Returns:
            int: The effective max_tokens value to use
        """
        # Get API limits for this provider
        api_limits = self.get_api_token_limits()
        
        # If user specified a limit, try to use it
        if user_requested_tokens is not None:
            # Check if user limit is within API limits
            if user_requested_tokens <= api_limits['max']:
                return user_requested_tokens
            else:
                # User limit exceeds API limit, use API limit
                return api_limits['max']
        
        # No user limit specified, use current setting, ensuring it doesn't exceed the context window
        return min(self.max_tokens, self.context_window)
    
    def get_api_token_limits(self) -> Dict[str, int]:
        """Get API token limits for this provider based on context window."""
        # The max is the total context window for the model.
        # Recommended is a sensible default for output tokens.
        return {
            "min": 1,
            "max": self.context_window,
            "recommended": min(8192, self.context_window // 4) # Recommend 1/4 of context or 8k, whichever is smaller
        }
    
    def validate_and_adjust_max_tokens(self, user_requested_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Validate and adjust max_tokens based on user request and API limits.
        
        Args:
            user_requested_tokens: User-specified token limit
            
        Returns:
            Dict with validation results and adjusted values
        """
        api_limits = self.get_api_token_limits()
        effective_tokens = self.get_effective_max_tokens(user_requested_tokens)
        
        result = {
            "original_setting": self.max_tokens,
            "user_requested": user_requested_tokens,
            "api_limit": api_limits['max'],
            "effective_tokens": effective_tokens,
            "was_adjusted": False,
            "adjustment_reason": None
        }
        
        if user_requested_tokens is not None:
            if user_requested_tokens > api_limits['max']:
                result["was_adjusted"] = True
                result["adjustment_reason"] = f"User requested {user_requested_tokens:,} tokens exceeds API limit of {api_limits['max']:,}"
            elif user_requested_tokens != self.max_tokens:
                result["was_adjusted"] = True
                result["adjustment_reason"] = f"Updated from {self.max_tokens:,} to {user_requested_tokens:,} tokens"
        
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelSettings':
        """Create settings from dictionary."""
        # Ensure new fields are handled gracefully for backward compatibility
        if 'context_window' not in data:
            # A sensible default, will be overwritten by provider defaults later if available
            data['context_window'] = 32768
        return cls(**data)
    
    def get_provider_parameters(self) -> List[str]:
        """Get list of parameters available for this provider."""
        return PROVIDER_PARAMETERS.get(self.provider, [])
    
    def get_parameter_range(self, param_name: str) -> Optional[tuple]:
        """Get valid range for a parameter."""
        return PARAMETER_RANGES.get(param_name)
    
    def save_to_file(self, filepath: str) -> None:
        """Save settings to a JSON file."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)  # Ensure directory exists
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> Optional['ModelSettings']:
        """Load settings from a JSON file."""
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            # Ensure new fields are handled gracefully
            if 'streaming_enabled' not in data:
                data['streaming_enabled'] = True # Default to True for old configs
            if 'context_window' not in data:
                # Will be overwritten by provider defaults if not present
                data['context_window'] = 32768
            if 'thinking_enabled' not in data:
                data['thinking_enabled'] = False # Default to False for old configs
            if 'thinking_budget' not in data:
                data['thinking_budget'] = -1 # Default to unlimited
            return cls.from_dict(data)
        except Exception as e:
            print(f"Error loading model settings: {e}")
            return None


class ModelSettingsManager:
    """Manager class for handling multiple model settings."""
    
    def __init__(self):
        self.settings_dir = "model_settings"
        os.makedirs(self.settings_dir, exist_ok=True)
        self.settings_cache = {}
        # Load general settings for URLs from centralized data registry
        from data_registry import DEFAULT_API_URLS
        self.general_settings = DEFAULT_API_URLS.copy()
        self.load_general_settings()
    
    def get_settings(self, provider: str, model: str) -> ModelSettings:
        """Get settings for a specific model, loading from file or creating defaults."""
        cache_key = f"{provider}_{model}"
        if cache_key in self.settings_cache:
            return self.settings_cache[cache_key]

        filepath = os.path.join(self.settings_dir, provider, f"{model}.json")
        settings = ModelSettings.load_from_file(filepath)

        if settings is None:
            # Create new settings with provider-specific defaults
            settings = ModelSettings(provider=provider, model=model)
            
            # Get the default context window for this provider from get_api_token_limits
            # This is a bit of a workaround to get provider-level defaults
            provider_defaults = self.get_api_token_limits(provider, model)
            settings.context_window = provider_defaults.get('max', 32768)

        self.settings_cache[cache_key] = settings
        return settings
    
    def save_settings(self, settings: ModelSettings) -> None:
        """Save settings for a specific model."""
        cache_key = f"{settings.provider}_{settings.model}"
        filepath = os.path.join(self.settings_dir, f"{settings.provider}_{settings.model}.json")
        settings.save_to_file(filepath)
        self.settings_cache[cache_key] = settings
    
    def clear_cache(self) -> None:
        """Clear the settings cache."""
        self.settings_cache = {}
    
    def is_streaming_enabled(self, model: str, provider: Optional[str] = None) -> bool:
        """Check if streaming is enabled for a given model."""
        if provider is None:
            # If provider is not given, you might need a way to determine it from the model
            # This is a placeholder for that logic
            # For now, we assume a default or look it up
            # This part might need to be more robust depending on your app structure
            # Let's assume you have a way to get the provider from model name
            # For now, let's just default to True if provider is unknown
            return True
        
        settings = self.get_settings(provider, model)
        return settings.streaming_enabled
    
    def get_ollama_url(self) -> str:
        """Get the base URL for Ollama."""
        return self.general_settings.get("ollama_base_url", "http://localhost:11434")
    
    def get_lmstudio_url(self) -> str:
        """Get the base URL for LM Studio."""
        return self.general_settings.get("lmstudio_base_url", "http://localhost:1234/v1")
    
    def get_deepseek_url(self) -> str:
        """Get the base URL for DeepSeek API."""
        return self.general_settings.get("deepseek_base_url", "https://api.deepseek.com")
    
    def get_openrouter_url(self) -> str:
        """Get the base URL for OpenRouter API."""
        return self.general_settings.get("openrouter_base_url", "https://openrouter.ai/api/v1")
    
    def get_groq_url(self) -> str:
        """Get the base URL for Groq API."""
        return self.general_settings.get("groq_base_url", "https://api.groq.com/openai/v1")
    
    def get_grok_url(self) -> str:
        """Get the base URL for Grok API."""
        return self.general_settings.get("grok_base_url", "https://api.x.ai/v1")
    
    def get_requesty_url(self) -> str:
        """Get the base URL for Requesty API."""
        return self.general_settings.get("requesty_base_url", "https://router.requesty.ai/v1")
    
    def load_general_settings(self) -> None:
        """Load general settings from a file."""
        filepath = os.path.join(self.settings_dir, "general_settings.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    self.general_settings = json.load(f)
            except Exception as e:
                print(f"Error loading general settings: {e}")
    
    def save_general_settings(self) -> None:
        """Save general settings to a file."""
        filepath = os.path.join(self.settings_dir, "general_settings.json")
        try:
            with open(filepath, 'w') as f:
                json.dump(self.general_settings, f, indent=2)
        except Exception as e:
            print(f"Error saving general settings: {e}")
    
    def get_context_window(self, provider: str, model: str) -> int:
        """Get the context window for a specific model."""
        settings = self.get_settings(provider, model)
        return settings.context_window

    def get_api_token_limits(self, provider: str, model: str) -> dict:
        """
        Get API token limits for a provider and model.
        This provides provider-level defaults, especially for context window.
        """
        # Define known API limits for each provider with updated values for modern models
        api_limits = {
            "OpenAI": {"min": 1, "max": 128000, "recommended": 8192},
            "Google GenAI": {"min": 1, "max": 1048576, "recommended": 8192},  # Updated for Gemini 2.5 (1M tokens)
            "Anthropic": {"min": 1, "max": 200000, "recommended": 8192},  # Updated for Claude 3.5
            "Groq": {"min": 1, "max": 32768, "recommended": 4000}, # Groq supports larger context models
            "Grok": {"min": 1, "max": 32768, "recommended": 16000},
            "Ollama": {"min": 1, "max": 32768, "recommended": 4096},  # Ollama is flexible
            "DeepSeek": {"min": 1, "max": 32768, "recommended": 4096},
            "LM Studio": {"min": 1, "max": 32768, "recommended": 8000},
            "OpenRouter": {"min": 1, "max": 128000, "recommended": 4096},  # OpenRouter supports many models with varying limits
            "Requesty": {"min": 1, "max": 32768, "recommended": 4096}  # Requesty supports various models
        }
        
        # Find a model-specific override if it exists (e.g., 'gpt-4o')
        # This is a placeholder for a more robust model database in the future
        model_specific_limits = {
            "gpt-4o": 128000,
            "gpt-4o-mini": 128000,
            "gpt-4-turbo": 128000,
            "claude-3-5-sonnet-20240620": 200000,
            "claude-3-opus-20240229": 200000,
            "claude-3-sonnet-20240229": 200000,
            "claude-3-haiku-20240307": 200000,
            "gemini-1.5-pro-latest": 1048576,
            "gemini-1.5-flash-latest": 1048576,
        }

        limits = api_limits.get(provider, {"min": 1, "max": 32768, "recommended": 4096})
        
        # Check for model specific override
        if model in model_specific_limits:
            limits['max'] = model_specific_limits[model]
            
        return limits


# Global instance of the manager
settings_manager = ModelSettingsManager()
