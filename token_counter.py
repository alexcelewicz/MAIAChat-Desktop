# token_counter.py
import re
import json
import os
from typing import Dict, Optional, Tuple
import logging
from datetime import datetime
import time # Added for potential future use

# --- Import Tiktoken ---
try:
    import tiktoken
    tiktoken_available = True
except ImportError:
    tiktoken_available = False
    logging.warning("Tiktoken library not found. Falling back to word count estimation.")

class TokenCounter:
    """
    A class to count tokens and calculate costs for different LLM providers.
    Uses tiktoken for accurate counting where possible.
    """

    def __init__(self):
        # Load pricing from external file with fallback to hardcoded values
        self.pricing = self._load_pricing_from_file("pricing.json")
        if not self.pricing:
            # Fallback to hardcoded pricing if external file fails
            self.pricing = {
                "OpenAI": {
                    "gpt-4": {"input": 0.03, "output": 0.06},
                    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
                    "gpt-4o": {"input": 0.005, "output": 0.015 },
                    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015}
                },
                "Anthropic": {
                    "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
                    "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
                    "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125}
                },
                "Google": {
                    "gemini-2.0-pro-exp-02-05": {"input": 0.00125, "output": 0.00375},
                    "gemini-2.0-flash-thinking-exp-01-21": {"input": 0.00025, "output": 0.00075}
                },
                "Groq": {
                    "llama-3.3-70b-versatile": {"input": 0.0001, "output": 0.0002},
                    "llama-3.3-70b-specdec": {"input": 0.0001, "output": 0.0002},
                    "qwen-qwq-32b": {"input": 0.0001, "output": 0.0002}
                },
                "DeepSeek": {
                    "deepseek-chat": {"input": 0.00014, "output": 0.00028},
                    "deepseek-reasoner": {"input": 0.00014, "output": 0.00028}
                },
                "Ollama": {
                    "mistral:latest": {"input": 0.0, "output": 0.0},
                    "llama3.1:latest": {"input": 0.0, "output": 0.0},
                    "llama3:latest": {"input": 0.0, "output": 0.0},
                    "deepseek-r1:latest": {"input": 0.0, "output": 0.0}
                },
                "LM Studio": {
                    "model_name": {"input": 0.0, "output": 0.0}
                },
                "OpenRouter": {
                    "openrouter-model": {"input": 0.0, "output": 0.0}
                }
            }
            logging.warning("Failed to load pricing.json, using hardcoded default pricing.")
        else:
            logging.info("Successfully loaded pricing from pricing.json")

        # Add aliases or common model base names if needed
        self.model_aliases = {
             "gpt-4-turbo-preview": "gpt-4-turbo",
             "gpt-4-vision-preview": "gpt-4-turbo", # Cost might be different, check OpenAI docs
             "claude-3-opus": "claude-3-opus-20240229",
             "claude-3-sonnet": "claude-3-sonnet-20240229",
             "claude-3-haiku": "claude-3-haiku-20240307",
             # Add more as needed
        }

        # Token usage for current session
        self.current_session = {
            "input_tokens": 0,
            "system_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "estimated_cost": 0.0,
            "conversations": {},
            "start_time": datetime.now().isoformat(),
            "precise_input_tokens": 0, # Track precise counts separately
            "precise_output_tokens": 0,
            "precise_system_tokens": 0,
            "precise_total_tokens": 0,
            "cost_is_estimated": False # Flag if cost calculation used estimated tokens
        }

        # Store details of the last non-system-prompt exchange for Tokens/s calculation
        self.last_exchange_output_tokens: int = 0
        self.last_exchange_duration: Optional[float] = None
        self.last_exchange_precise: bool = True # Was the last counted exchange precise?

        # Timer-based token speed calculation
        self.generation_start_time: Optional[float] = None
        self.generation_end_time: Optional[float] = None
        self.total_output_tokens_generated: int = 0

        # Token usage history
        self.history = []
        self._tokenizer_cache = {} # Cache loaded tokenizers

        # Load any saved history
        self.load_history()

        # Ensure any loaded data has correct total tokens and precision flags
        self._recalculate_session_totals(self.current_session)
        for session in self.history:
            self._recalculate_session_totals(session)

    def _get_tokenizer(self, model_name: str):
        """Get a tiktoken tokenizer for the given model, handling aliases and fallbacks."""
        if not tiktoken_available:
            return None

        # Normalize model name (e.g., handle variations like -preview)
        normalized_model = self.model_aliases.get(model_name, model_name)

        if normalized_model in self._tokenizer_cache:
            return self._tokenizer_cache[normalized_model]

        try:
            encoding = tiktoken.encoding_for_model(normalized_model)
            self._tokenizer_cache[normalized_model] = encoding
            logging.debug(f"Using tiktoken tokenizer for model: {normalized_model}")
            return encoding
        except KeyError:
            # Model not directly supported by name, try a common base encoding
            logging.warning(f"Tiktoken encoding not found for '{normalized_model}'. Trying 'cl100k_base'.")
            try:
                encoding = tiktoken.get_encoding("cl100k_base")
                self._tokenizer_cache[normalized_model] = encoding # Cache fallback too
                return encoding
            except Exception as e:
                logging.error(f"Failed to load fallback tiktoken encoding 'cl100k_base': {e}")
                return None
        except Exception as e:
             logging.error(f"Unexpected error getting tiktoken tokenizer for {normalized_model}: {e}")
             return None

    def count_tokens(self, text: str, model_name: str) -> Tuple[int, bool]:
        """
        Counts tokens using tiktoken if possible.

        Args:
            text: The text to count tokens for.
            model_name: The model name (used to select the correct tokenizer).

        Returns:
            A tuple containing:
                - int: The estimated or precise token count.
                - bool: True if the count is precise (using tiktoken), False otherwise.
        """
        if not text:
            return 0, True  # 0 tokens is precise

        tokenizer = self._get_tokenizer(model_name)
        if tokenizer:
            try:
                tokens = tokenizer.encode(text, disallowed_special=()) # Allow special tokens
                return len(tokens), True
            except Exception as e:
                logging.error(f"Tiktoken encoding error for model {model_name}: {e}. Falling back to estimation.")
                # Fallback estimation (word count)
                words = len(re.findall(r'\b\w+\b', text))
                return int(words / 0.75), False
        else:
            # Fallback estimation (word count) if tiktoken unavailable or failed
            words = len(re.findall(r'\b\w+\b', text))
            return int(words / 0.75), False

    def track_tokens(self,
                     conversation_id: str,
                     user_input_text: str,    # The user's explicit query for this turn
                     system_prompt_text: str, # The instructions & context given to the LLM (excluding user_input_text)
                     output_text: str,        # The LLM's generated response
                     provider: str,
                     model: str,
                     duration: Optional[float] = None) -> Dict:
        """
        Track tokens for a conversation, calculate costs, store duration, use precise counting.

        Args:
            conversation_id: ID of the conversation.
            user_input_text: The user's explicit query for this turn.
            system_prompt_text: The instructions & context given to the LLM (excluding user_input_text).
            output_text: The LLM's generated response.
            provider: LLM provider (e.g., "OpenAI", "Anthropic").
            model: Model name (e.g., "gpt-4", "claude-3-sonnet").
            duration: Time taken for the LLM response generation.

        Returns:
            Dictionary with token counts and costs for this specific exchange.
        """
        # Count tokens for each component
        user_input_tokens, user_input_precise = self.count_tokens(user_input_text, model)
        system_prompt_tokens, system_prompt_precise = self.count_tokens(system_prompt_text, model)
        output_tokens, output_precise = self.count_tokens(output_text, model)

        total_tokens_exchange = user_input_tokens + system_prompt_tokens + output_tokens
        is_precise_exchange = user_input_precise and system_prompt_precise and output_precise

        # Calculate cost for this exchange
        cost = self.calculate_cost_new(user_input_tokens, system_prompt_tokens, output_tokens, provider, model)

        # Add debug logging for token tracking
        logging.debug(f"Token tracking: Provider={provider}, Model={model}, UserInput={user_input_tokens}, SystemPrompt={system_prompt_tokens}, Output={output_tokens}, Cost=${cost:.4f}, Precise={is_precise_exchange}")

        # Update session totals
        session = self.current_session
        session["input_tokens"] += user_input_tokens
        session["system_tokens"] += system_prompt_tokens
        session["output_tokens"] += output_tokens
        if user_input_precise:
            session["precise_input_tokens"] += user_input_tokens
        if system_prompt_precise:
            session["precise_system_tokens"] += system_prompt_tokens
        if output_precise:
            session["precise_output_tokens"] += output_tokens

        session["estimated_cost"] += cost
        # Recalculate total tokens from components
        session["total_tokens"] = session["input_tokens"] + session["system_tokens"] + session["output_tokens"]
        session["precise_total_tokens"] = session["precise_input_tokens"] + session["precise_system_tokens"] + session["precise_output_tokens"]

        # Update cost estimation flag
        if not is_precise_exchange:
            session["cost_is_estimated"] = True

        # Update conversation-specific tracking (simplified, assumes exists)
        if conversation_id not in session["conversations"]:
            session["conversations"][conversation_id] = {
                "input_tokens": 0, "system_tokens": 0, "output_tokens": 0,
                "total_tokens": 0, "estimated_cost": 0.0, "exchanges": [],
                "precise_input_tokens": 0, "precise_output_tokens": 0,
                "precise_system_tokens": 0, "precise_total_tokens": 0,
                "cost_is_estimated": False
            }
        conv_data = session["conversations"][conversation_id]

        conv_data["input_tokens"] += user_input_tokens
        conv_data["system_tokens"] += system_prompt_tokens
        conv_data["output_tokens"] += output_tokens
        if user_input_precise: conv_data["precise_input_tokens"] += user_input_tokens
        if system_prompt_precise: conv_data["precise_system_tokens"] += system_prompt_tokens
        if output_precise: conv_data["precise_output_tokens"] += output_tokens

        conv_data["estimated_cost"] += cost
        conv_data["total_tokens"] = conv_data["input_tokens"] + conv_data["system_tokens"] + conv_data["output_tokens"]
        conv_data["precise_total_tokens"] = conv_data["precise_input_tokens"] + conv_data["precise_system_tokens"] + conv_data["precise_output_tokens"]
        if not is_precise_exchange:
            conv_data["cost_is_estimated"] = True

        # Add exchange details
        exchange = {
            "timestamp": datetime.now().isoformat(),
            "provider": provider,
            "model": model,
            "user_input_tokens": user_input_tokens,
            "system_prompt_tokens": system_prompt_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens_exchange,
            "cost": cost,
            "duration": duration,
            "is_precise": is_precise_exchange
        }
        conv_data["exchanges"].append(exchange)

        # Update last exchange details for Tokens/s calculation
        if duration is not None and duration > 0 and output_tokens > 0:
            self.last_exchange_output_tokens = output_tokens
            self.last_exchange_duration = duration
            self.last_exchange_precise = output_precise
            logging.debug(f"Updated last exchange: {output_tokens} tokens / {duration:.2f}s (Precise: {output_precise})")
        else:
            logging.debug("Resetting last exchange details (no duration provided or no output).")
            self.last_exchange_output_tokens = 0
            self.last_exchange_duration = None
            self.last_exchange_precise = True

        # Save history periodically
        self.save_history()

        # Return the token information for THIS specific exchange
        return {
            "user_input_tokens": user_input_tokens,
            "system_prompt_tokens": system_prompt_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens_exchange,
            "cost": cost,
            "duration": duration,
            "is_precise": is_precise_exchange
        }

    def calculate_cost(self,
                      input_tokens: int,
                      output_tokens: int,
                      provider: str,
                      model: str) -> float:
        """
        Calculate the cost for token usage based on provider pricing.

        Args:
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.
            provider: LLM provider.
            model: Model name.

        Returns:
            Estimated cost in USD.
        """
        # Normalize model name using aliases
        normalized_model = self.model_aliases.get(model, model)

        # Default to zero cost if provider or model pricing not found
        if not provider or provider == "Unknown":
            logging.warning(f"Provider is empty or Unknown. Cannot calculate cost.")
            return 0.0

        if not model or model == "Unknown":
            logging.warning(f"Model is empty or Unknown. Cannot calculate cost.")
            return 0.0

        if provider not in self.pricing:
            logging.warning(f"Pricing not found for Provider: {provider}. Available providers: {list(self.pricing.keys())}. Cost will be $0.00.")
            return 0.0

        if normalized_model not in self.pricing[provider]:
            logging.warning(f"Pricing not found for Model: {normalized_model} (Original: {model}) in Provider: {provider}. Available models: {list(self.pricing[provider].keys())}. Cost will be $0.00.")
            return 0.0

        # Get pricing for the model
        pricing = self.pricing[provider][normalized_model]
        input_price_per_1k = pricing.get("input", 0.0)
        output_price_per_1k = pricing.get("output", 0.0)

        # Calculate cost (price per 1000 tokens * tokens / 1000)
        input_cost = input_price_per_1k * (input_tokens / 1000.0)
        output_cost = output_price_per_1k * (output_tokens / 1000.0)

        return input_cost + output_cost

    def calculate_cost_new(self,
                         user_input_tokens: int,
                         system_prompt_tokens: int, # New parameter
                         output_tokens: int,
                         provider: str,
                         model: str) -> float:
        """
        Calculate the cost for token usage based on provider pricing.
        Accounts for user input tokens and system prompt tokens as distinct parts of input cost.

        Args:
            user_input_tokens: Number of user input tokens.
            system_prompt_tokens: Number of system prompt tokens.
            output_tokens: Number of output tokens.
            provider: LLM provider.
            model: Model name.

        Returns:
            Estimated cost in USD.
        """
        # Normalize model name using aliases
        normalized_model = self.model_aliases.get(model, model)

        # Default to zero cost if pricing not found
        if not provider or provider == "Unknown":
            logging.warning(f"Provider is empty or Unknown. Cannot calculate cost.")
            return 0.0
        if not model or model == "Unknown":
            logging.warning(f"Model is empty or Unknown. Cannot calculate cost.")
            return 0.0
        if provider not in self.pricing:
            logging.warning(f"Pricing not found for Provider: {provider}. Available providers: {list(self.pricing.keys())}. Cost will be $0.00.")
            return 0.0
        if normalized_model not in self.pricing[provider]:
            logging.warning(f"Pricing not found for Model: {normalized_model} (Original: {model}) in Provider: {provider}. Available models: {list(self.pricing[provider].keys())}. Cost will be $0.00.")
            return 0.0

        # Get pricing for the model
        pricing = self.pricing[provider][normalized_model]
        input_price_per_1k = pricing.get("input", 0.0)
        output_price_per_1k = pricing.get("output", 0.0)

        # Calculate cost (price per 1000 tokens * tokens / 1000)
        # Combine user_input and system_prompt for input cost (they both count as input tokens)
        total_input_for_cost = user_input_tokens + system_prompt_tokens
        input_cost = input_price_per_1k * (total_input_for_cost / 1000.0)
        output_cost = output_price_per_1k * (output_tokens / 1000.0)

        return input_cost + output_cost

    def start_generation_timer(self):
        """Start timing token generation"""
        try:
            # Reset output tokens counter but keep end_time for display purposes
            self.total_output_tokens_generated = 0

            # Start new timer
            self.generation_start_time = time.time()
            logging.debug(f"Token generation timer started at {self.generation_start_time}")
        except Exception as e:
            logging.error(f"Exception in start_generation_timer: {str(e)}", exc_info=True)

    def end_generation_timer(self, total_output_tokens=None):
        """End timing token generation and calculate tokens/s"""
        if self.generation_start_time is None:
            logging.debug("TokenCounter.end_generation_timer called but generation_start_time is None")
            # Don't return early, we'll use an estimated start time

        # Set end time
        self.generation_end_time = time.time()
        if total_output_tokens is not None:
            self.total_output_tokens_generated = total_output_tokens

        # If start time is missing, estimate it (10 seconds before end time)
        if self.generation_start_time is None:
            estimated_start_time = self.generation_end_time - 10.0
            self.generation_start_time = estimated_start_time
            logging.debug(f"Using estimated start time: {estimated_start_time}")

        duration = self.generation_end_time - self.generation_start_time

        logging.debug(f"Token generation timer ended at {self.generation_end_time}")
        logging.debug(f"Total output tokens generated: {self.total_output_tokens_generated}")
        logging.debug(f"Duration: {duration:.2f} seconds")

        # Calculate tokens/s
        if duration > 0:
            tokens_per_second = self.total_output_tokens_generated / duration
            logging.debug(f"Timer-based tokens/s: {tokens_per_second:.2f} ({self.total_output_tokens_generated} tokens / {duration:.2f}s)")

        # Don't reset start time here - we'll keep it for the get_session_stats method
        # self.generation_start_time = None

    def get_session_stats(self) -> Dict:
        """
        Get statistics for the current session, including precision info.

        Returns:
            Dictionary with session statistics.
        """
        session = self.current_session
        input_system_tokens = session["input_tokens"] + session["system_tokens"]
        precise_input_system = session["precise_input_tokens"] + session["precise_system_tokens"]

        # Ensure total tokens is calculated from components
        total_tokens = input_system_tokens + session["output_tokens"]
        precise_total = precise_input_system + session["precise_output_tokens"]

        # Determine overall precision - if any part was estimated, the total is estimated
        session_precise = (session["input_tokens"] == session["precise_input_tokens"] and
                           session["system_tokens"] == session["precise_system_tokens"] and
                           session["output_tokens"] == session["precise_output_tokens"])

        # Calculate Tokens/s using the timer-based approach first
        tokens_per_second = 0.0
        tps_precise = True

        # Try timer-based calculation first - if both start and end times are set
        if (self.generation_end_time is not None and
            self.total_output_tokens_generated > 0):

            # If start time is missing but we have an end time, estimate the start time
            if self.generation_start_time is None:
                self.generation_start_time = self.generation_end_time - 10.0  # Estimate 10 seconds
                print(f"DEBUG: Using estimated start time in get_session_stats: {self.generation_start_time}")
                tps_precise = False  # Mark as imprecise since we're estimating

            duration = self.generation_end_time - self.generation_start_time
            if duration > 0:
                tokens_per_second = self.total_output_tokens_generated / duration
                # Only log to the debug file, not to the console
                logging.debug(f"Timer-based tokens/s: {tokens_per_second:.2f} ({self.total_output_tokens_generated} tokens / {duration:.2f}s)")

        # Fall back to the stored last exchange data if timer-based approach didn't work
        elif self.last_exchange_output_tokens > 0 and self.last_exchange_duration is not None and self.last_exchange_duration > 0:
            tokens_per_second = self.last_exchange_output_tokens / self.last_exchange_duration
            tps_precise = self.last_exchange_precise
            logging.debug(f"Exchange-based tokens/s: {tokens_per_second:.2f} ({self.last_exchange_output_tokens} tokens / {self.last_exchange_duration:.2f}s)")
        else:
            logging.debug("No valid token speed data available")

        return {
            "input_tokens": session["input_tokens"],
            "system_tokens": session["system_tokens"],
            "input_system_tokens": input_system_tokens,
            "output_tokens": session["output_tokens"],
            "total_tokens": total_tokens,
            "estimated_cost": session["estimated_cost"],
            "conversation_count": len(session["conversations"]),
            "start_time": session["start_time"],
            # Precision related stats
            "precise_input_tokens": session["precise_input_tokens"],
            "precise_system_tokens": session["precise_system_tokens"],
            "precise_output_tokens": session["precise_output_tokens"],
            "precise_total_tokens": precise_total,
            "session_token_count_precise": session_precise,
            "cost_is_estimated": session["cost_is_estimated"], # If any exchange used estimated tokens for cost
             # Tokens/s related stats
            "tokens_per_second": tokens_per_second,
            "tokens_per_second_precise": tps_precise
        }

    def _recalculate_session_totals(self, session_data: Dict):
        """Internal helper to recalculate totals and precision for a session dict."""
        input_t, system_t, output_t = 0, 0, 0
        precise_in, precise_sys, precise_out = 0, 0, 0
        cost = 0.0
        cost_estimated = False

        for conv_id, conv_data in session_data.get("conversations", {}).items():
             conv_in, conv_sys, conv_out = 0, 0, 0
             conv_pin, conv_psys, conv_pout = 0, 0, 0
             conv_cost = 0.0
             conv_cost_est = False
             for ex in conv_data.get("exchanges", []):
                 # Use new token structure keys
                 ex_user_in = ex.get("user_input_tokens", 0)
                 ex_sys_prompt = ex.get("system_prompt_tokens", 0)
                 ex_out = ex.get("output_tokens", 0)
                 ex_cost = ex.get("cost", 0.0)
                 ex_precise = ex.get("is_precise", False)

                 # Sum into conversation level totals
                 conv_in += ex_user_in
                 conv_sys += ex_sys_prompt
                 conv_out += ex_out
                 if ex_precise:
                     conv_pin += ex_user_in
                     conv_psys += ex_sys_prompt
                     conv_pout += ex_out

                 conv_cost += ex_cost
                 if not ex_precise:
                     conv_cost_est = True

             # Update conversation totals
             conv_data["input_tokens"] = conv_in
             conv_data["system_tokens"] = conv_sys
             conv_data["output_tokens"] = conv_out
             conv_data["total_tokens"] = conv_in + conv_sys + conv_out
             conv_data["precise_input_tokens"] = conv_pin
             conv_data["precise_system_tokens"] = conv_psys
             conv_data["precise_output_tokens"] = conv_pout
             conv_data["precise_total_tokens"] = conv_pin + conv_psys + conv_pout
             conv_data["estimated_cost"] = conv_cost
             conv_data["cost_is_estimated"] = conv_cost_est

             # Add to session totals
             input_t += conv_in
             system_t += conv_sys
             output_t += conv_out
             precise_in += conv_pin
             precise_sys += conv_psys
             precise_out += conv_pout
             cost += conv_cost
             if conv_cost_est: cost_estimated = True


        # Update session data directly
        session_data["input_tokens"] = input_t
        session_data["system_tokens"] = system_t
        session_data["output_tokens"] = output_t
        session_data["total_tokens"] = input_t + system_t + output_t
        session_data["precise_input_tokens"] = precise_in
        session_data["precise_system_tokens"] = precise_sys
        session_data["precise_output_tokens"] = precise_out
        session_data["precise_total_tokens"] = precise_in + precise_sys + precise_out
        session_data["estimated_cost"] = cost
        session_data["cost_is_estimated"] = cost_estimated
        
        # Update the session_precise check to verify all components
        session_precise = (session_data["input_tokens"] == session_data["precise_input_tokens"] and
                           session_data["system_tokens"] == session_data["precise_system_tokens"] and
                           session_data["output_tokens"] == session_data["precise_output_tokens"])
        
        # Add missing keys if loading old data
        if "precise_input_tokens" not in session_data: session_data["precise_input_tokens"] = 0
        if "precise_system_tokens" not in session_data: session_data["precise_system_tokens"] = 0
        if "precise_output_tokens" not in session_data: session_data["precise_output_tokens"] = 0
        if "precise_total_tokens" not in session_data: session_data["precise_total_tokens"] = 0
        if "cost_is_estimated" not in session_data: session_data["cost_is_estimated"] = False # Assume old data was precise unless recalculated

    def reset_session(self) -> None:
        """Reset the current session statistics after saving the old one."""
        # Save current session to history if it has tokens
        if self.current_session.get("total_tokens", 0) > 0:
            # Ensure totals are correct before saving
            self._recalculate_session_totals(self.current_session)
            self.history.append(self.current_session)

        # Create new session
        self.current_session = {
            "input_tokens": 0, "system_tokens": 0, "output_tokens": 0, "total_tokens": 0,
            "estimated_cost": 0.0, "conversations": {},
            "start_time": datetime.now().isoformat(),
            "precise_input_tokens": 0, "precise_output_tokens": 0,
            "precise_system_tokens": 0, "precise_total_tokens": 0,
            "cost_is_estimated": False
        }
        # Reset last exchange details
        self.last_exchange_output_tokens = 0
        self.last_exchange_duration = None
        self.last_exchange_precise = True

        # Don't reset timer variables here - they'll be reset when the next generation starts
        # This allows the UI to continue showing the last tokens/s value until a new generation starts
        # self.generation_start_time = None
        # self.generation_end_time = None
        # self.total_output_tokens_generated = 0

        logging.debug("Token counter session reset (keeping timer values for display)")

        # Save history (includes the reset session and adds previous one)
        self.save_history()

    def save_history(self) -> None:
        """Save token usage history to a file."""
        try:
            # Ensure current session totals are up-to-date before saving
            self._recalculate_session_totals(self.current_session)
            with open("token_usage_history.json", "w") as f:
                json.dump({
                    "history": self.history,
                    "current_session": self.current_session
                }, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving token history: {e}")

    def load_history(self) -> None:
        """Load token usage history from a file and recalculate totals."""
        try:
            with open("token_usage_history.json", "r") as f:
                data = json.load(f)
                self.history = data.get("history", [])
                current = data.get("current_session", {})

                # Recalculate totals for all loaded history sessions
                for session in self.history:
                     self._recalculate_session_totals(session)

                # Load current session only if it's from today and recalculate
                if current:
                    start_time_str = current.get("start_time", "")
                    try:
                        start_time_dt = datetime.fromisoformat(start_time_str)
                        if start_time_dt.date() == datetime.now().date():
                            self.current_session = current
                            self._recalculate_session_totals(self.current_session)
                        else:
                             logging.info("Loaded history contains a stale 'current_session'. Starting fresh.")
                             # Don't load the stale session, let init create a new one
                    except ValueError:
                         logging.warning(f"Invalid start_time format in loaded current_session: {start_time_str}. Starting fresh.")


        except FileNotFoundError:
            logging.info("No token history file found. Starting fresh.")
        except json.JSONDecodeError:
            logging.error("Error decoding token_usage_history.json. Starting fresh.")
        except Exception as e:
            logging.error(f"Error loading token history: {e}. Starting fresh.")

    def increment_output_tokens(self, n=1):
        """Increment the count of output tokens generated during streaming."""
        self.total_output_tokens_generated += n

    def _load_pricing_from_file(self, filepath: str) -> Dict:
        """
        Load pricing data from an external JSON file.
        
        Args:
            filepath: Path to the pricing JSON file
            
        Returns:
            Dictionary containing pricing data, or empty dict if loading fails
        """
        try:
            # Try to find the file relative to the current script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            full_path = os.path.join(script_dir, filepath)
            
            if not os.path.exists(full_path):
                logging.error(f"Pricing file '{filepath}' not found at {full_path}")
                return {}
                
            with open(full_path, 'r', encoding='utf-8') as f:
                pricing_data = json.load(f)
                
            # Validate the structure
            if not isinstance(pricing_data, dict):
                logging.error(f"Pricing file '{filepath}' does not contain a valid JSON object")
                return {}
                
            # Basic validation - check if it has at least one provider
            if not pricing_data:
                logging.error(f"Pricing file '{filepath}' is empty")
                return {}
                
            logging.info(f"Successfully loaded pricing data from {filepath}")
            return pricing_data
            
        except FileNotFoundError:
            logging.error(f"Pricing file '{filepath}' not found")
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding pricing file '{filepath}': {e}")
        except Exception as e:
            logging.error(f"Unexpected error loading pricing file '{filepath}': {e}")
        
        return {}

# Create a global instance
token_counter = TokenCounter()