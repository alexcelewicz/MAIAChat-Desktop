"""
API Key Manager for handling API keys in a more flexible way.
"""

import json
import os
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

# File to store API key definitions
API_KEYS_FILE = "api_keys.json"

@dataclass
class ApiKeyDefinition:
    """Class for storing API key definition."""
    id: str  # Internal ID (e.g., 'OPENAI_API_KEY')
    name: str  # Display name (e.g., 'OpenAI API Key')
    description: str = ""  # Optional description
    url: str = ""  # Optional URL for getting the API key
    required: bool = False  # Whether this API key is required
    category: str = "General"  # Category for grouping
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class ApiKeyManager:
    """Manager class for handling API keys."""
    
    def __init__(self):
        self.api_keys: Dict[str, str] = {}  # Actual API key values
        self.definitions: Dict[str, ApiKeyDefinition] = {}  # API key definitions
        self.load_definitions()
        
    def load_definitions(self) -> None:
        """Load API key definitions from file or create default ones."""
        if os.path.exists(API_KEYS_FILE):
            try:
                with open(API_KEYS_FILE, 'r') as f:
                    data = json.load(f)
                    self.definitions = {
                        key_id: ApiKeyDefinition(**definition)
                        for key_id, definition in data.items()
                    }
            except Exception as e:
                logging.error(f"Error loading API key definitions: {e}")
                self.create_default_definitions()
        else:
            self.create_default_definitions()
    
    def create_default_definitions(self) -> None:
        """Create default API key definitions."""
        default_definitions = [
            ApiKeyDefinition(
                id="OPENAI_API_KEY",
                name="OpenAI API Key",
                description="API key for OpenAI models (GPT-3.5, GPT-4, etc.)",
                url="https://platform.openai.com/account/api-keys",
                category="LLM Providers"
            ),
            ApiKeyDefinition(
                id="GOOGLE_API_KEY",
                name="Google API Key",
                description="API key for Google services",
                url="https://console.cloud.google.com/apis/credentials",
                category="LLM Providers"
            ),
            ApiKeyDefinition(
                id="GEMINI_API_KEY",
                name="Gemini API Key",
                description="API key for Google Gemini models (often same as Google API key)",
                url="https://ai.google.dev/",
                category="LLM Providers"
            ),
            ApiKeyDefinition(
                id="ANTHROPIC_API_KEY",
                name="Anthropic API Key",
                description="API key for Anthropic Claude models",
                url="https://console.anthropic.com/settings/keys",
                category="LLM Providers"
            ),
            ApiKeyDefinition(
                id="GROQ_API_KEY",
                name="Groq API Key",
                description="API key for Groq models",
                url="https://console.groq.com/keys",
                category="LLM Providers"
            ),
            ApiKeyDefinition(
                id="GROK_API_KEY",
                name="Grok API Key",
                description="API key for xAI Grok models",
                url="https://grok.x.ai/",
                category="LLM Providers"
            ),
            ApiKeyDefinition(
                id="DEEPSEEK_API_KEY",
                name="DeepSeek API Key",
                description="API key for DeepSeek models",
                url="https://platform.deepseek.com/",
                category="LLM Providers"
            ),
            ApiKeyDefinition(
                id="OPENROUTER_API_KEY",
                name="OpenRouter API Key",
                description="API key for OpenRouter (access to multiple models)",
                url="https://openrouter.ai/keys",
                category="LLM Providers"
            ),
            ApiKeyDefinition(
                id="REQUESTY_API_KEY",
                name="Requesty API Key",
                description="API key for Requesty Router (access to multiple models)",
                url="https://requesty.ai/",
                category="LLM Providers"
            ),
            ApiKeyDefinition(
                id="POLYGON_API_KEY",
                name="Polygon.io API Key",
                description="API key for Polygon.io financial data",
                url="https://polygon.io/dashboard/api-keys",
                category="Financial Data Providers"
            ),
            ApiKeyDefinition(
                id="SERPER_API_KEY",
                name="Serper API Key",
                description="API key for Serper web search",
                url="https://serper.dev/api-key",
                category="Search Providers"
            ),
            ApiKeyDefinition(
                id="GOOGLE_SEARCH_ENGINE_ID",
                name="Google Search Engine ID",
                description="Custom Search Engine ID for Google Search",
                url="https://programmablesearchengine.google.com/",
                category="Search Providers"
            ),
        ]
        
        self.definitions = {definition.id: definition for definition in default_definitions}
        self.save_definitions()
    
    def save_definitions(self) -> None:
        """Save API key definitions to file."""
        try:
            with open(API_KEYS_FILE, 'w') as f:
                json.dump(
                    {key_id: definition.to_dict() for key_id, definition in self.definitions.items()},
                    f,
                    indent=2
                )
        except Exception as e:
            logging.error(f"Error saving API key definitions: {e}")
    
    def add_definition(self, definition: ApiKeyDefinition) -> bool:
        """Add a new API key definition."""
        if definition.id in self.definitions:
            return False
        
        self.definitions[definition.id] = definition
        self.save_definitions()
        return True
    
    def update_definition(self, definition: ApiKeyDefinition) -> bool:
        """Update an existing API key definition."""
        if definition.id not in self.definitions:
            return False
        
        self.definitions[definition.id] = definition
        self.save_definitions()
        return True
    
    def remove_definition(self, key_id: str) -> bool:
        """Remove an API key definition."""
        if key_id not in self.definitions:
            return False
        
        del self.definitions[key_id]
        self.save_definitions()
        return True
    
    def get_definition(self, key_id: str) -> Optional[ApiKeyDefinition]:
        """Get an API key definition."""
        return self.definitions.get(key_id)
    
    def get_all_definitions(self) -> List[ApiKeyDefinition]:
        """Get all API key definitions."""
        return list(self.definitions.values())
    
    def get_definitions_by_category(self) -> Dict[str, List[ApiKeyDefinition]]:
        """Get API key definitions grouped by category."""
        result: Dict[str, List[ApiKeyDefinition]] = {}
        
        for definition in self.definitions.values():
            if definition.category not in result:
                result[definition.category] = []
            
            result[definition.category].append(definition)
        
        return result
    
    def load_api_keys(self, config: Dict[str, Any]) -> None:
        """Load API key values from config."""
        self.api_keys = {
            key_id: config.get(key_id, "")
            for key_id in self.definitions.keys()
        }
    
    def get_api_key(self, key_id: str) -> str:
        """Get an API key value."""
        return self.api_keys.get(key_id, "")
    
    def set_api_key(self, key_id: str, value: str) -> None:
        """Set an API key value."""
        self.api_keys[key_id] = value
    
    def get_all_api_keys(self) -> Dict[str, str]:
        """Get all API key values."""
        return self.api_keys.copy()


# Create a global instance of the API key manager
api_key_manager = ApiKeyManager()
