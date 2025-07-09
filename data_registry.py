# data_registry.py
"""
Centralized registry for static data and configuration.
This module consolidates scattered hardcoded lists, models, providers, and URLs
to improve maintainability and make updates easier without code changes.
"""

# From agent_config.py - Provider definitions
PROVIDERS = [
    "OpenAI", "Google GenAI", "Anthropic", "Groq",
    "Grok", "Ollama", "DeepSeek", "LM Studio", "OpenRouter", "Requesty"
]

# From agent_config.py - Model mappings for each provider
MODEL_MAPPINGS = {
    "OpenAI": ['gpt-4o-mini', 'gpt-4o'],
    "Google GenAI": ['gemini-2.0-pro-exp-02-05', 'gemini-2.0-flash-thinking-exp-01-21'],
    "Anthropic": ['claude-3-7-sonnet-20250219'],
    "Groq": ['llama-3.3-70b-versatile', 'llama-3.3-70b-specdec', 'qwen-qwq-32b'],
    "Grok": ['grok-2-latest'],
    "DeepSeek": ['deepseek-chat', 'deepseek-reasoner'],
    "LM Studio": ['model_name'],
    "Requesty": [],  # Will be populated by API
}

# From agent_config.py - Default Ollama models
DEFAULT_OLLAMA_MODELS = ['mistral:latest', 'llama3.1:latest', 'llama3:latest']

# From agent_config.py - Models that support thinking
THINKING_CAPABLE_MODELS = {
    "Ollama": [
        "deepseek-r1:70b", "deepseek-r1:8b", "deepseek-r1:32b", 
        "qwen3", "qwen3:4b", "qwen3:7b", "qwen3:14b", "qwen3:32b",
        "deepseek-r1:latest"
    ],
    "DeepSeek": ["deepseek-reasoner"]  # DeepSeek R1 models
}

# From model_settings.py - Default API URLs
DEFAULT_API_URLS = {
    "ollama_base_url": "http://localhost:11434",
    "lmstudio_base_url": "http://localhost:1234/v1",
    "deepseek_base_url": "https://api.deepseek.com",
    "openrouter_base_url": "https://openrouter.ai/api/v1",
    "groq_base_url": "https://api.groq.com/openai/v1",
    "grok_base_url": "https://api.x.ai/v1",
    "requesty_base_url": "https://router.requesty.ai/v1"
}

# From model_settings.py - Parameter ranges
PARAMETER_RANGES = {
    "temperature": (0.0, 2.0),
    "top_p": (0.0, 1.0),
    "top_k": (1, 100),
    "max_tokens": (16, 100000),
    "frequency_penalty": (0.0, 2.0),
    "presence_penalty": (0.0, 2.0),
    "repetition_penalty": (0.0, 2.0),
    "stop_sequences": None,  # List of strings
    "thinking_enabled": None,  # Boolean
    "thinking_budget": (-1, 10000),  # -1 for unlimited, or positive integer
}

# From model_settings.py - Provider-specific default settings
DEFAULT_SETTINGS = {
    "OpenAI": {
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 16384,
        "frequency_penalty": 0.5,
        "presence_penalty": 0.3,
        "stop_sequences": []
    },
    "Google GenAI": {
        "temperature": 0.6,
        "top_p": 0.9,
        "top_k": 40,
        "max_tokens": 8192,
        "stop_sequences": [],
        "thinking_enabled": True,
        "thinking_budget": -1
    },
    "Anthropic": {
        "temperature": 0.6,
        "top_p": 0.9,
        "max_tokens": 32768,
        "stop_sequences": []
    },
    "Groq": {
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 16384,
        "frequency_penalty": 0.4,
        "presence_penalty": 0.6,
        "stop_sequences": []
    },
    "Grok": {
        "temperature": 0.5,
        "top_p": 0.9,
        "max_tokens": 32768,
        "frequency_penalty": 0.4,
        "presence_penalty": 0.6,
        "stop_sequences": []
    },
    "Ollama": {
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40,
        "max_tokens": 32768,
        "repetition_penalty": 1.1,
        "stop_sequences": []
    },
    "DeepSeek": {
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 32768,
        "stop_sequences": []
    },
    "LM Studio": {
        "temperature": 0.5,
        "top_p": 0.9,
        "max_tokens": 32768,
        "stop_sequences": []
    },
    "OpenRouter": {
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 20000,
        "stop_sequences": []
    },
    "Requesty": {
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 32768,
        "stop_sequences": []
    }
}

# From model_settings.py - Provider parameters mapping
PROVIDER_PARAMETERS = {
    "OpenAI": ["temperature", "top_p", "max_tokens", "frequency_penalty", "presence_penalty", "stop_sequences"],
    "Google GenAI": ["temperature", "top_p", "top_k", "max_tokens", "stop_sequences", "thinking_enabled", "thinking_budget"],
    "Anthropic": ["temperature", "top_p", "max_tokens", "stop_sequences"],
    "Groq": ["temperature", "top_p", "max_tokens", "frequency_penalty", "presence_penalty", "stop_sequences"],
    "Grok": ["temperature", "top_p", "max_tokens", "frequency_penalty", "presence_penalty", "stop_sequences"],
    "Ollama": ["temperature", "top_p", "top_k", "max_tokens", "repetition_penalty", "stop_sequences"],
    "DeepSeek": ["temperature", "top_p", "max_tokens", "stop_sequences"],
    "LM Studio": ["temperature", "top_p", "max_tokens", "stop_sequences"],
    "OpenRouter": ["temperature", "top_p", "max_tokens", "stop_sequences"],
    "Requesty": ["temperature", "top_p", "max_tokens", "stop_sequences"]
} 