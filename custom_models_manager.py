"""
Custom models manager for handling user-added models.
"""

import json
import os
import logging
from typing import Dict, List, Optional

# File to store custom models
CUSTOM_MODELS_FILE = "custom_models.json"

class CustomModelsManager:
    """Manager class for handling custom models added by the user."""
    
    def __init__(self):
        self.custom_models: Dict[str, List[str]] = {}
        self.load_custom_models()
    
    def load_custom_models(self) -> None:
        """Load custom models from the JSON file."""
        if not os.path.exists(CUSTOM_MODELS_FILE):
            self.custom_models = {}
            return
        
        try:
            with open(CUSTOM_MODELS_FILE, 'r') as f:
                self.custom_models = json.load(f)
        except Exception as e:
            logging.error(f"Error loading custom models: {e}")
            self.custom_models = {}
    
    def save_custom_models(self) -> None:
        """Save custom models to the JSON file."""
        try:
            with open(CUSTOM_MODELS_FILE, 'w') as f:
                json.dump(self.custom_models, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving custom models: {e}")
    
    def add_model(self, provider: str, model: str) -> bool:
        """Add a custom model for a provider."""
        if provider not in self.custom_models:
            self.custom_models[provider] = []
        
        # Check if model already exists
        if model in self.custom_models[provider]:
            return False
        
        self.custom_models[provider].append(model)
        self.save_custom_models()
        return True
    
    def remove_model(self, provider: str, model: str) -> bool:
        """Remove a custom model for a provider."""
        if provider not in self.custom_models:
            return False
        
        if model not in self.custom_models[provider]:
            return False
        
        self.custom_models[provider].remove(model)
        self.save_custom_models()
        return True
    
    def get_models(self, provider: str) -> List[str]:
        """Get all custom models for a provider."""
        return self.custom_models.get(provider, [])
    
    def get_all_providers(self) -> List[str]:
        """Get all providers with custom models."""
        return list(self.custom_models.keys())


# Create a global instance of the custom models manager
custom_models_manager = CustomModelsManager()
