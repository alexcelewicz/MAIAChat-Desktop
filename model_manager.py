"""
Model manager for handling both hardcoded and custom models.
"""

import json
import os
import logging
from typing import Dict, List, Set, Optional
from custom_models_manager import custom_models_manager

# File to store disabled models
DISABLED_MODELS_FILE = "disabled_models.json"

class ModelManager:
    """Manager class for handling both hardcoded and custom models."""
    
    def __init__(self):
        self.disabled_models: Dict[str, List[str]] = {}
        self.load_disabled_models()
    
    def load_disabled_models(self) -> None:
        """Load disabled models from the JSON file."""
        if not os.path.exists(DISABLED_MODELS_FILE):
            self.disabled_models = {}
            return
        
        try:
            with open(DISABLED_MODELS_FILE, 'r') as f:
                self.disabled_models = json.load(f)
        except Exception as e:
            logging.error(f"Error loading disabled models: {e}")
            self.disabled_models = {}
    
    def save_disabled_models(self) -> None:
        """Save disabled models to the JSON file."""
        try:
            with open(DISABLED_MODELS_FILE, 'w') as f:
                json.dump(self.disabled_models, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving disabled models: {e}")
    
    def disable_model(self, provider: str, model: str) -> bool:
        """Disable a model for a provider."""
        if provider not in self.disabled_models:
            self.disabled_models[provider] = []
        
        # Check if model is already disabled
        if model in self.disabled_models[provider]:
            return False
        
        self.disabled_models[provider].append(model)
        self.save_disabled_models()
        return True
    
    def enable_model(self, provider: str, model: str) -> bool:
        """Enable a previously disabled model."""
        if provider not in self.disabled_models:
            return False
        
        if model not in self.disabled_models[provider]:
            return False
        
        self.disabled_models[provider].remove(model)
        self.save_disabled_models()
        return True
    
    def is_model_disabled(self, provider: str, model: str) -> bool:
        """Check if a model is disabled."""
        if provider not in self.disabled_models:
            return False
        
        return model in self.disabled_models[provider]
    
    def get_disabled_models(self, provider: str) -> List[str]:
        """Get all disabled models for a provider."""
        return self.disabled_models.get(provider, [])
    
    def get_all_models(self, provider: str, standard_models: List[str]) -> Dict[str, List[str]]:
        """Get all models (standard and custom) for a provider, categorized by status."""
        result = {
            "enabled_standard": [],
            "disabled_standard": [],
            "custom": custom_models_manager.get_models(provider)
        }
        
        disabled_models = self.get_disabled_models(provider)
        
        for model in standard_models:
            if model in disabled_models:
                result["disabled_standard"].append(model)
            else:
                result["enabled_standard"].append(model)
        
        return result


# Create a global instance of the model manager
model_manager = ModelManager()
