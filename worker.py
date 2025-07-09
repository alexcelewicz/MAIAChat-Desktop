# worker.py - Streaming

from PyQt6.QtCore import QObject, pyqtSignal, QMutex, QMutexLocker, Qt
from utils import (google_search, openai_client, genai, groq_client, anthropic_client, grok_client, groq_rate_limiter, call_deepseek_api)
from mcp_client import mcp_client
import traceback
import re
import json
import time
import random
import logging
import os
from instruction_templates import InstructionTemplates
from google.ai import generativelanguage as glm
from datetime import datetime
from conversation_manager import ConversationManager
from typing import List, Dict, Optional, Tuple, Any
from utils import groq_rate_limiter
from openai import OpenAI

# Import specific OpenAI error classes

try:

    from openai import APITimeoutError, APIConnectionError, APIStatusError, BadRequestError

except ImportError:
    # Fallback for older versions or missing imports

    class APITimeoutError(Exception): pass

    class APIConnectionError(Exception): pass

    class APIStatusError(Exception): pass

    class BadRequestError(Exception): pass

import os
from internet_search import EnhancedSearchManager, SearchResult
import base64
from io import BytesIO
from PyQt6.QtGui import QTextDocument, QTextBlock, QImage
from PyQt6.QtCore import QBuffer, QByteArray, QIODevice
import logging
from rag_handler import RAGHandler
import requests
import concurrent.futures
from performance_monitor import performance_monitor, track_performance
from model_settings import settings_manager, ModelSettings
from pathlib import Path

# Import token counter

try:

    from token_counter import token_counter

except ImportError:
    token_counter = None
# Import and cache for tiktoken

try:

    import tiktoken

    TIKTOKEN_CACHE = {}
except ImportError:
    tiktoken = None
    TIKTOKEN_CACHE = {}
logger = logging.getLogger(__name__)  # Get the logger instance

def sanitize_response(response):
    """
    Sanitize the response while preserving formatting and handling large content.
    """
    if not response:
        return ""
    # Remove any potentially harmful content while preserving newlines and formatting
    sanitized = response.strip()
    # Check if response is extremely large and might cause issues
    if len(sanitized) > 1000000:  # 1MB limit
        # Truncate to a reasonable size while preserving structure
        truncated = sanitized[:1000000]
        # Try to end at a complete sentence or paragraph
        last_period = truncated.rfind('.')
        last_newline = truncated.rfind('\n')
        cutoff = max(last_period, last_newline)
        if cutoff > 900000:  # Only truncate if we can find a good break point
            sanitized = truncated[:cutoff + 1] + "\n\n[Response truncated due to size limitations]"
        else:
            sanitized = truncated + "\n\n[Response truncated due to size limitations]"
    return sanitized

class Worker(QObject):
    # Define all signals at class level
    update_agents_discussion_signal = pyqtSignal(str, int, str, bool) # html_chunk, agent_number, model_name, is_first_chunk
    update_terminal_console_signal = pyqtSignal(str)
    update_conversation_history_signal = pyqtSignal(list)
    update_conversation_id_signal = pyqtSignal(str)  # New signal for conversation ID updates
    discussion_completed_signal = pyqtSignal()
    error_signal = pyqtSignal(str)
    # Add signals for token timing
    token_generation_started_signal = pyqtSignal(float)  # Signal with timestamp when generation starts
    token_generation_ended_signal = pyqtSignal(float, int)  # Signal with timestamp and total output tokens when generation ends

    def __init__(self, prompt, general_instructions, agents, knowledge_base_files,
                 knowledge_base_content="", json_instructions=None,
                 config_manager=None, conversation_history=None, format_response_handler=None):
        super().__init__()  # Initialize QObject first
        # Initialize instance variables
        self.prompt = prompt
        self.general_instructions = general_instructions
        self.agents = agents
        self.knowledge_base_files = knowledge_base_files
        self.knowledge_base_content = knowledge_base_content
        self.json_instructions = json_instructions or {}
        self.config_manager = config_manager
        self.conversation_history = conversation_history or []
        self.is_running = True
        self.format_response_handler = format_response_handler
        self.mutex = QMutex()
        # Initialize search manager - will be used dynamically per agent
        self.search_manager = None

        try:
            self.search_manager = EnhancedSearchManager(config_manager)
            self.update_terminal_console_signal.emit("Internet search manager initialized")
        except Exception as e:
            self.update_terminal_console_signal.emit(f"Error initializing internet search: {str(e)}")
            logger.error(f"Error initializing internet search: {str(e)}")
            logger.error(traceback.format_exc())
        # Initialize RAG handler with optimized settings
        self.rag_handler = RAGHandler(
            persist_directory="./knowledge_base",
            use_openai=False,  # Use sentence transformer by default
            embedding_model="all-mpnet-base-v2",
            dimension=768,  # Updated dimension for all-mpnet-base-v2
            chunk_size=500,
            chunk_overlap=50,
            chunking_strategy="contextual",  # Use contextual chunking for better context preservation
            cache_dir="./cache"  # Add cache directory for better performance
        )
        # Initialize conversation manager
        self.conversation_manager = ConversationManager()
        self.current_conversation_id = None  # Will be set in start_agent_discussion if needed
        # Use config_manager for API keys if available
        if self.config_manager:
            self.GOOGLE_API_KEY = self.config_manager.get('GOOGLE_API_KEY', '')
            self.GOOGLE_SEARCH_ENGINE_ID = self.config_manager.get('GOOGLE_SEARCH_ENGINE_ID', '')
        else:
            self.GOOGLE_API_KEY = ''
            self.GOOGLE_SEARCH_ENGINE_ID = ''
        self.agent_responses = {}
        # Initialize RAG cache
        self.rag_cache = {}
        self.rag_cache_ttl = 3600  # 1 hour TTL for RAG cache
        # UI update batching with adaptive performance
        self.ui_update_buffer = {}
        self.ui_update_interval = 0.1  # seconds - will be adjusted dynamically
        self.last_ui_update = {}
        # Performance tracking for adaptive batching
        self.update_count = 0
        self.last_performance_check = time.time()
        self.performance_check_interval = 5.0  # Check performance every 5 seconds
        self.high_speed_mode = False  # Flag for high-speed streaming
        # Batch processing
        self.max_workers = min(os.cpu_count() or 4, 8)  # Limit max threads
        # For agent inactivity tracking
        self.current_agent_last_activity_time = 0
    @track_performance

    def emit_update(self, signal, content):
        """
        Helper method to safely emit signals with adaptive batching support.
        Automatically adjusts batching parameters based on streaming speed to handle high-speed responses.
        """

        try:
            # Check if we should batch this update
            if signal == 'update_agents_discussion_signal':
                # For this signal, content is a tuple. We will not batch it.
                if hasattr(self, signal):
                    getattr(self, signal).emit(*content)
                    # Track update count for performance monitoring
                    self.update_count += 1
                    self._check_performance_and_adjust()
            elif signal == 'update_terminal_console_signal':
                current_time = time.time()
                # Initialize buffer and last update time if needed
                if signal not in self.ui_update_buffer:
                    self.ui_update_buffer[signal] = []
                    self.last_ui_update[signal] = 0
                # Add content to buffer
                self.ui_update_buffer[signal].append(content)
                # Check if it's time to emit the batched update
                time_since_last_update = current_time - self.last_ui_update.get(signal, 0)
                buffer_size = len(self.ui_update_buffer[signal])
                # Adaptive batching: adjust parameters based on streaming speed
                if self.high_speed_mode:
                    # High-speed mode: more aggressive batching
                    max_buffer_size = 20  # Larger buffer
                    min_interval = 0.05   # Shorter minimum interval
                else:
                    # Normal mode: standard batching
                    max_buffer_size = 10  # Standard buffer
                    min_interval = self.ui_update_interval
                # Emit if enough time has passed or buffer is large enough
                if (time_since_last_update >= min_interval or buffer_size >= max_buffer_size):
                    batched_content = '\n'.join(self.ui_update_buffer[signal])
                    # Emit the batched update
                    if hasattr(self, signal):
                        getattr(self, signal).emit(batched_content)
                    # Track UI update performance
                    update_type = signal.replace('_signal', '').replace('update_', '')
                    performance_monitor.track_ui_update(
                        update_type=update_type,
                        content_length=len(batched_content),
                        batch_size=buffer_size
                    )
                    # Reset buffer and update timestamp
                    self.ui_update_buffer[signal] = []
                    self.last_ui_update[signal] = current_time
            else:
                # For other non-batched signals, emit immediately
                if hasattr(self, signal):
                    getattr(self, signal).emit(content)
                    # Track individual UI update
                    update_type = signal.replace('_signal', '').replace('update_', '')
                    performance_monitor.track_ui_update(
                        update_type=update_type,
                        content_length=len(content) if isinstance(content, str) else 0,
                        batch_size=1
                    )
        except Exception as e:
            self.update_terminal_console_signal.emit(f"Error emitting signal {signal}: {str(e)}")

    def _check_performance_and_adjust(self):
        """Check performance and adjust batching parameters for high-speed streaming."""
        current_time = time.time()
        # Check performance every 5 seconds
        if current_time - self.last_performance_check >= self.performance_check_interval:
            updates_per_second = self.update_count / self.performance_check_interval
            # If we're getting more than 50 updates per second, switch to high-speed mode
            if updates_per_second > 50:
                if not self.high_speed_mode:
                    self.high_speed_mode = True
                    self.ui_update_interval = 0.05  # Reduce interval for faster updates
                    logger.info(f"Switched to high-speed mode: {updates_per_second:.1f} updates/sec")
            else:
                if self.high_speed_mode:
                    self.high_speed_mode = False
                    self.ui_update_interval = 0.1  # Return to normal interval
                    logger.info(f"Switched to normal mode: {updates_per_second:.1f} updates/sec")
            # Reset counters
            self.update_count = 0
            self.last_performance_check = current_time

    def stop(self):
        with QMutexLocker(self.mutex):
            self.is_running = False

    def update_worker_configuration(self):
        # Reinitialize search manager with proper error handling
        if self.search_manager:

            try:
                self.search_manager = EnhancedSearchManager(self.config_manager)
                self.update_terminal_console_signal.emit("Internet search reinitialized successfully")
            except Exception as e:
                self.update_terminal_console_signal.emit(f"Error reinitializing internet search: {str(e)}")
                logger.error(f"Error reinitializing internet search: {str(e)}")
                logger.error(traceback.format_exc())
                self.search_manager = None
        else:
            self.update_terminal_console_signal.emit("Internet search disabled")

    def _setup_worker_connections(self):
        if self.worker:
            self.worker.update_agents_discussion_signal.connect(
                self.update_agents_discussion,
                type=Qt.ConnectionType.QueuedConnection
            )
            self.worker.update_terminal_console_signal.connect(
                self.update_terminal_console,
                type=Qt.ConnectionType.QueuedConnection
            )
            self.worker.discussion_completed_signal.connect(
                self.on_discussion_completed,
                type=Qt.ConnectionType.QueuedConnection
            )
            self.worker.error_signal.connect(
                self.handle_error,
                type=Qt.ConnectionType.QueuedConnection
            )

    def reset_backoff(self):
        """Reset the backoff delay to initial value"""
        self.current_delay = self.initial_delay

    def clean_agent_response(self, response: str, previous_chunk: str = None) -> str:
        """
        Minimalistic agent response cleaning - only removes obvious formatting artifacts.
        Preserves all legitimate content to prevent truncation and empty responses.
        """
        if not response:
            return ""
        # Check if cleaning is disabled for testing
        if self.config_manager and self.config_manager.get('DISABLE_RESPONSE_CLEANING', False):
            logger.info("Response cleaning disabled for testing - returning original response")
            return response
        # Only do basic whitespace normalization
        cleaned = response.strip()
        # Remove only the most obvious formatting artifacts
        # Remove explicit internal thought process markers
        internal_block_pattern = r'<(?:think|thought|thinking|plan|planning|analysis|reasoning|tool_code|tool_output|scratchpad|inner_monologue|inner_thought)>.*?</(?:think|thought|thinking|plan|planning|analysis|reasoning|tool_code|tool_output|scratchpad|inner_monologue|inner_thought)>'
        cleaned = re.sub(internal_block_pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        # Remove explicit START/END markers
        cleaned = re.sub(r'\[(?:START OF|END OF|BEGIN|END)\s*(?:FINAL INSTRUCTIONS|SPEC|ARCHITECTURE|CODE|RUN_INSTRUCTIONS|TEST_SUITE|PATCH|REVIEW|DISCUSSION|RESPONSE)(?: FOR BOB)?\]', '', cleaned, flags=re.IGNORECASE)
        # Remove repeated placeholders
        cleaned = re.sub(r'\[Agent provided no discernible content\.\]\s*', '', cleaned)
        # Basic whitespace normalization
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)  # Max two newlines
        cleaned = re.sub(r'[ \t]{2,}', ' ', cleaned)  # Max one space
        cleaned = cleaned.strip()
        # If cleaning made it completely empty, return the original
        if not cleaned and response.strip():
            logger.warning("clean_agent_response made content empty, returning original")
            return response.strip()
        return cleaned

    def _should_flush_for_code_integrity(self, buffer: str) -> bool:
        """
        Determine if buffer should be flushed to preserve code syntax integrity.
        This method detects code patterns and flushes at appropriate boundaries.
        """
        if not buffer:
            return False

        # Check if we're likely inside a code block by looking for code patterns
        code_indicators = [
            # JavaScript/TypeScript patterns
            r'let\s+\w+',
            r'const\s+\w+',
            r'var\s+\w+',
            r'function\s+\w+\s*\(',
            r'class\s+\w+\s*{',
            # Python patterns
            r'def\s+\w+\s*\(',
            r'class\s+\w+\s*:',
            r'import\s+\w+',
            r'from\s+\w+\s+import',
            # General programming patterns
            r'if\s*\(',
            r'for\s*\(',
            r'while\s*\(',
            r'}\s*else\s*{',
            # HTML/CSS patterns
            r'<\w+[^>]*>',
            r'}\s*$',  # CSS rule ending
        ]

        # Check if buffer contains code patterns
        has_code_pattern = any(re.search(pattern, buffer, re.IGNORECASE) for pattern in code_indicators)

        if has_code_pattern:
            # For code content, flush on single newlines to preserve line structure
            if '\n' in buffer:
                return True
            # Flush after assignment operators to prevent variable name/value separation
            if '=' in buffer and any(keyword in buffer.lower() for keyword in ['let ', 'const ', 'var ']):
                return True
            # Also flush after semicolons in JavaScript-like code to preserve statement boundaries
            if ';' in buffer and any(keyword in buffer.lower() for keyword in ['let ', 'const ', 'var ', 'function']):
                return True

        return False

    @track_performance

    def start_agent_discussion(self):

        try:
            # Signal that token generation has started
            self.token_generation_started_signal.emit(time.time())
            # Initialize conversation handling
            # self.current_conversation_id is set by WorkerManager if it's a follow-up.
            if not self.current_conversation_id:  # This means it's a new conversation
                self.current_conversation_id = self.conversation_manager.start_new_conversation(
                    self.prompt,  # self.prompt is the initial user input for this new conversation
                    metadata={
                        "agent_count": len(self.agents),
                        "knowledge_base_files": self.knowledge_base_files
                    }
                )
                self.update_terminal_console_signal.emit(f"Started new conversation with ID: {self.current_conversation_id}")
                self.update_conversation_id_signal.emit(self.current_conversation_id)  # Emit the new ID
            else:  # This is a follow-up to an existing conversation
                self.conversation_manager.load_conversation(self.current_conversation_id)
                self.update_terminal_console_signal.emit(f"Continuing conversation with ID: {self.current_conversation_id}")
            # Add current user message (self.prompt) to conversation
            # For a new conversation, start_new_conversation already adds it.
            # For a follow-up, we need to add the new prompt.
            # Check if the current prompt is already the last message (to avoid duplication if start_new_conversation added it)
            last_message_content = ""
            if self.conversation_manager.current_conversation and self.conversation_manager.current_conversation.get("messages"):
                last_message_content = self.conversation_manager.current_conversation["messages"][-1].get("content")
            if self.prompt != last_message_content:  # Add only if it's a new prompt for this turn
                self.conversation_manager.add_message(
                    self.prompt,  # self.prompt is the current user input for this turn
                    role="user",
                    metadata={"timestamp": datetime.now().isoformat()}
                )
            # Get full conversation context
            context_window = self.conversation_manager.get_context_window()
            # Process agents sequentially - each agent builds on previous agents' responses
            # Dynamic features (Internet, RAG, MCP) will be handled per-agent in _process_agents_sequentially
            final_response_content = self._process_agents_sequentially(self.prompt, context_window)
            # Format and emit the final response
            if final_response_content:
                # Clean the final response before emitting
                # For final answer, we don't want to add agent headers again, just clean the content
                cleaned_final_response = self.clean_agent_response(final_response_content)
                # self.update_final_answer_signal.emit(cleaned_final_response)  # REMOVED: Final answer functionality
                # Emit signal that token generation has ended
                # To get the session total output tokens:
                if token_counter:  # Check if token_counter is available
                    self.token_generation_ended_signal.emit(time.time(), token_counter.get_session_stats()["output_tokens"])
            self.update_terminal_console_signal.emit("Agent discussion completed.")
            self.discussion_completed_signal.emit()
        except Exception as e:
            self.error_signal.emit(str(e))
            self.discussion_completed_signal.emit()

    def _process_agents_sequentially(self, current_user_input_for_token_count, context_window):
        """
        Processes agents sequentially, each building on the previous one's response.
        This is the intended 'chain of thought' workflow with dynamic per-agent features.
        Args:
            current_user_input_for_token_count: The user's explicit query for the current turn (for token counting)
            context_window: Conversation context (full history from conversation_manager)
        Returns:
            The final response string from the last agent, or an empty string if processing stopped.
        """
        agent_responses = {} # To store responses for subsequent agents
        final_agent_response = ""
        self.update_terminal_console_signal.emit(f"Processing {len(self.agents)} agents sequentially...")
        self.update_terminal_console_signal.emit(f"RAG will use the following indexed files: {self.knowledge_base_files}")
        logger.info(f"[Worker] RAG indexed files for this run: {self.knowledge_base_files}")
        for agent in self.agents:
            with QMutexLocker(self.mutex): # Ensure worker can be stopped
                if not self.is_running:
                    self.update_terminal_console_signal.emit("Agent processing stopped by user.")
                    break
            agent_number = agent['agent_number']
            model = agent['model']
            instructions = agent['instructions']
            # Check per-agent feature settings
            agent_internet_enabled = agent.get('internet_enabled', False)
            agent_rag_enabled = agent.get('rag_enabled', False)
            agent_mcp_enabled = agent.get('mcp_enabled', False)
            # Dynamic Internet search for this agent
            current_search_results_for_agent = []
            if agent_internet_enabled and self.search_manager:
                # Construct search query based on original prompt + previous agent responses
                search_query_for_agent = self.prompt
                for prev_agent_num, prev_response in agent_responses.items():
                    if prev_agent_num < agent_number:
                        search_query_for_agent += f"\n\nPrevious Agent {prev_agent_num} response: {prev_response}"

                try:
                    self.update_terminal_console_signal.emit(f"Agent {agent_number} starting internet search...")
                    current_search_results_for_agent = self.search_manager.search(search_query_for_agent)
                    if current_search_results_for_agent:
                        self.update_terminal_console_signal.emit(f"Agent {agent_number} found relevant sources:")
                        for res_item in current_search_results_for_agent:
                            self.update_terminal_console_signal.emit(f"- {res_item.url}")
                    else:
                        self.update_terminal_console_signal.emit(f"Agent {agent_number} found no search results.")
                except Exception as e:
                    self.update_terminal_console_signal.emit(f"Agent {agent_number} search error: {str(e)}")
                    logger.error(f"Agent {agent_number} internet search error: {str(e)}")
                    logger.error(traceback.format_exc())
                    current_search_results_for_agent = []
            else:
                self.update_terminal_console_signal.emit(f"Agent {agent_number} internet search is disabled.")
            # Dynamic RAG content loading for this agent
            current_knowledge_base_content_for_agent = ""
            if agent_rag_enabled and self.knowledge_base_files:
                # Construct RAG query based on original prompt + previous agent responses
                rag_query_for_agent = self.prompt
                for prev_agent_num, prev_response in agent_responses.items():
                    if prev_agent_num < agent_number:
                        rag_query_for_agent += f"\n\nPrevious Agent {prev_agent_num} response: {prev_response}"

                try:
                    self.update_terminal_console_signal.emit(f"Agent {agent_number} loading knowledge base content...")
                    current_knowledge_base_content_for_agent = self.load_knowledge_base_content(rag_query_for_agent)
                    # The load_knowledge_base_content method already returns formatted content
                    if current_knowledge_base_content_for_agent:
                        # Get RAG settings for token limit
                        rag_settings = self._get_rag_settings()
                        # Optimize the content for token limits
                        current_knowledge_base_content_for_agent = self.conversation_manager.optimize_rag_content(current_knowledge_base_content_for_agent, max_tokens=rag_settings['token_limit'])
                        self.update_terminal_console_signal.emit(f"Agent {agent_number} retrieved {len(current_knowledge_base_content_for_agent)} characters from knowledge base.")
                    else:
                        self.update_terminal_console_signal.emit(f"Agent {agent_number} found no relevant knowledge base content.")
                except Exception as e:
                    self.update_terminal_console_signal.emit(f"Agent {agent_number} knowledge base error: {str(e)}")
                    logger.error(f"Agent {agent_number} knowledge base error: {str(e)}")
                    logger.error(traceback.format_exc())
                    current_knowledge_base_content_for_agent = ""
            else:
                self.update_terminal_console_signal.emit(f"Agent {agent_number} RAG is disabled or no files loaded.")
            # Dynamic MCP context loading for this agent
            current_mcp_context_for_agent = {}
            if agent_mcp_enabled:

                try:
                    self.update_terminal_console_signal.emit(f"Agent {agent_number} preparing MCP context...")
                    current_mcp_context_for_agent = self.prepare_mcp_context()
                    self.update_terminal_console_signal.emit(f"Agent {agent_number} MCP context prepared.")
                except Exception as e:
                    self.update_terminal_console_signal.emit(f"Agent {agent_number} MCP context error: {str(e)}")
                    logger.error(f"Agent {agent_number} MCP context error: {str(e)}")
                    logger.error(traceback.format_exc())
                    current_mcp_context_for_agent = {}
            else:
                self.update_terminal_console_signal.emit(f"Agent {agent_number} MCP is disabled.")
            # Prepare the full prompt string to send to the LLM for this agent's turn.
            # This includes general instructions, previous agent responses, RAG, MCP, etc.
            agent_input_for_llm = self.prepare_agent_input(
                agent_number,
                instructions,
                # For `prepare_agent_input`, the `new_message` parameter represents the *user's original query*.
                # This is why it's `self.prompt` for the very first call, and `new_message` for follow-ups.
                # Here, for sequential processing, it's always the original prompt for the turn.
                current_user_input_for_token_count,
                current_search_results_for_agent,
                context_window,
                agent_responses, # Pass agent_responses accumulated so far
                current_knowledge_base_content_for_agent, # Use dynamic RAG content for this agent
                current_mcp_context_for_agent if current_mcp_context_for_agent else None
            )
            # Define the actual system and user parts for token counting for this *specific* LLM call.
            # `current_user_input_for_token_count` is what the user *typed* for this turn.
            # `system_prompt_for_token_count` is everything else in `agent_input_for_llm`.
            system_prompt_for_token_count = agent_input_for_llm.replace(current_user_input_for_token_count, "").strip()
            # If the replacement results in the original string, it means the user input wasn't explicitly subtracted
            # (e.g., if user_input_text is empty or not found in agent_input_for_llm).
            # In such cases, if `system_prompt_for_token_count` is identical to `agent_input_for_llm`,
            # it implies no distinct user input for this LLM call, so treat the full agent_input_for_llm as system.
            if system_prompt_for_token_count == agent_input_for_llm and current_user_input_for_token_count == "":
                system_prompt_for_token_count = agent_input_for_llm # No specific user input for this LLM call
            elif system_prompt_for_token_count == agent_input_for_llm: # User input exists but not in the original, treat as system
                system_prompt_for_token_count = agent_input_for_llm
                current_user_input_for_token_count = "" # Clear user input for this LLM call if not clearly isolated
            # Validate and adjust token limits for this agent
            token_validation = self._validate_and_adjust_token_limits(agent, agent_number, agent_input_for_llm)
            response = "" # Initialize response

            try:
                self.update_terminal_console_signal.emit(f"Agent {agent_number} ({model}) processing...")
                start_api_call_time = time.time() # Start timer for API call duration
                # Add timeout wrapper for the entire agent processing

                import threading
                import queue

                # Create a queue to store the result
                result_queue = queue.Queue()

                def process_agent_with_timeout():

                    try:
                        agent_response = self.get_agent_response(
                            agent['provider'],
                            agent['model'],
                            agent_input_for_llm, # This is the full content sent to the LLM
                            agent_number,
                            effective_max_tokens=token_validation['effective_max_tokens']
                        )
                        result_queue.put(('success', agent_response))
                    except Exception as e:
                        result_queue.put(('error', str(e)))
                # Start the agent processing in a separate thread
                self.current_agent_last_activity_time = time.time() # Initialize for inactivity tracking
                agent_thread = threading.Thread(target=process_agent_with_timeout)
                agent_thread.daemon = True # Ensures thread doesn't block app exit
                agent_thread.start()
                # Wait for the result with inactivity timeout and max overall timeout
                agent_inactivity_timeout_seconds = self.config_manager.get('AGENT_INACTIVITY_TIMEOUT', 60) if self.config_manager else 60
                agent_max_overall_timeout_seconds = self.config_manager.get('AGENT_MAX_OVERALL_TIMEOUT', 600) if self.config_manager else 600 # 10 minutes max overall
                response_received = False
                while agent_thread.is_alive():

                    try:
                        # Poll the queue with a short timeout
                        result_type, result_value = result_queue.get(timeout=1) # Poll every 1 second
                        if result_type == 'success':
                            response = result_value
                        else: # 'error'
                            raise Exception(result_value)
                        response_received = True
                        break # Exit loop once result is received
                    except queue.Empty:
                        # Queue is empty, check for timeouts
                        current_time = time.time()
                        if current_time - self.current_agent_last_activity_time > agent_inactivity_timeout_seconds:
                            logger.warning(f"AGENT_INACTIVITY_TIMEOUT: Agent {agent_number} detected no activity for {agent_inactivity_timeout_seconds} seconds.")
                            self.update_terminal_console_signal.emit(f"Agent {agent_number} timed out due to inactivity after {agent_inactivity_timeout_seconds} seconds. Proceeding to next agent if any.")
                            response = f"[Agent {agent_number} timed out due to inactivity after {agent_inactivity_timeout_seconds} seconds. The response may be incomplete.]"
                            # We don't need to actively stop the daemon thread here; it will exit when its task finishes or if self.is_running becomes false.
                            # The main goal is to stop waiting for *this* agent and move on.
                            break # Exit loop on inactivity timeout
                        if current_time - start_api_call_time > agent_max_overall_timeout_seconds:
                            logger.warning(f"AGENT_MAX_OVERALL_TIMEOUT: Agent {agent_number} exceeded max overall processing time of {agent_max_overall_timeout_seconds} seconds.")
                            self.update_terminal_console_signal.emit(f"Agent {agent_number} exceeded maximum overall processing time of {agent_max_overall_timeout_seconds} seconds. Proceeding to next agent if any.")
                            response = f"[Agent {agent_number} exceeded maximum overall processing time of {agent_max_overall_timeout_seconds} seconds. The response may be incomplete.]"
                            break # Exit loop on max overall timeout
                    except Exception as e: # Catch errors put into the queue by process_agent_with_timeout
                        logger.error(f"Error received from agent_thread for Agent {agent_number}: {str(e)}")
                        response = f"[Agent {agent_number} encountered an error: {str(e)}]"
                        response_received = True # Consider error as a form of "completion" for this agent's turn
                        break
                if not response_received and not agent_thread.is_alive():
                    # Thread finished but didn't put anything in queue (shouldn't happen with current process_agent_with_timeout)
                    logger.warning(f"Agent {agent_number} thread finished unexpectedly without result.")
                    response = f"[Agent {agent_number} processing ended unexpectedly.]"
                elif not response_received and agent_thread.is_alive():
                    # This case should ideally be caught by one of the timeouts above.
                    # If loop exited due to timeout, response is already set.
                    # If somehow loop exited while thread is alive and no response_received, it's an edge case.
                    logger.warning(f"Agent {agent_number} processing loop exited, but agent thread still alive and no response received. This might indicate an issue.")
                    if not response: # If response wasn't set by a timeout condition
                         response = f"[Agent {agent_number} processing did not complete within allocated checks.]"
                end_api_call_time = time.time() # End timer for API call duration
                api_call_duration = end_api_call_time - start_api_call_time
                response = sanitize_response(response) # Apply general sanitization
                response = self._handle_large_response(response, agent_number) # Handle large responses, may truncate
                # Clean the response before storing and adding to conversation history
                cleaned_response = self.clean_agent_response(response)
                agent_responses[agent_number] = cleaned_response # Store cleaned agent's response
                self.update_terminal_console_signal.emit(f"Agent {agent_number} ({model}) completed response.")
                # Track tokens for this exchange, passing the API call duration
                token_info_from_exchange = token_counter.track_tokens(
                    conversation_id=self.current_conversation_id,
                    user_input_text=current_user_input_for_token_count,
                    system_prompt_text=system_prompt_for_token_count,
                    output_text=cleaned_response, # Use cleaned response for token tracking
                    provider=agent['provider'],
                    model=agent['model'],
                    duration=api_call_duration
                )
                # Add cleaned agent response to conversation history

                try:
                    self.conversation_manager.add_message(
                        cleaned_response, # Use cleaned response for conversation history
                        role=f"agent_{agent_number}",
                        metadata={
                            "timestamp": datetime.now().isoformat(),
                            "model": model,
                            "provider": agent['provider'],
                            "token_info": token_info_from_exchange
                        }
                    )
                except ValueError as e:
                    # Handle validation failures gracefully
                    error_msg = f"Message validation failed for agent_{agent_number}: {str(e)}"
                    self.update_terminal_console_signal.emit(error_msg)
                    logger.error(error_msg)
                    # Try to add a fallback message instead

                    try:
                        fallback_content = f"[Agent {agent_number} response could not be validated: {cleaned_response[:200]}...]" if cleaned_response else f"[Agent {agent_number} provided no valid content]"
                        self.conversation_manager.add_message(
                            fallback_content,
                            role=f"agent_{agent_number}",
                            metadata={
                                "timestamp": datetime.now().isoformat(),
                                "model": model,
                                "provider": agent['provider'],
                                "error": True,
                                "original_error": str(e)
                            }
                        )
                    except Exception as fallback_error:
                        logger.error(f"Failed to add fallback message for agent_{agent_number}: {fallback_error}")
                        # Continue processing without adding to conversation history
                except Exception as e:
                    # Handle other conversation manager errors
                    error_msg = f"Error adding message to conversation for agent_{agent_number}: {str(e)}"
                    self.update_terminal_console_signal.emit(error_msg)
                    logger.error(error_msg)
                    # Continue processing without adding to conversation history
                # Update conversation history signal
                if hasattr(self.conversation_manager, 'current_conversation') and self.conversation_manager.current_conversation:
                    self.update_conversation_history_signal.emit(self.conversation_manager.current_conversation.get("messages", []))
                # Store the final response from the last agent
                if agent_number == len(self.agents):
                    final_agent_response = cleaned_response # Use cleaned response for final answer
            except Exception as e:
                error_message = f"Error processing Agent {agent_number} ({model}): {str(e)}"
                self.update_terminal_console_signal.emit(error_message)
                logger.error(error_message)
                logger.error(traceback.format_exc())
                # Add error message to conversation
                self.conversation_manager.add_message(
                    f"Error: {str(e)}",
                    role=f"agent_{agent_number}",
                    metadata={"timestamp": datetime.now().isoformat(), "error": True}
                )
                # Emit error as part of the discussion
                self.update_agents_discussion_signal.emit(
                    f"Error: {str(e)}",
                    agent_number,
                    model,
                    True
                )
                # Continue with next agent if possible
                continue
        return final_agent_response

    def load_knowledge_base_content(self, query: str) -> str:
        """
        Load relevant knowledge base content for the given query.
        Args:
            query: The query to search for relevant content
        Returns:
            Formatted string containing relevant knowledge base content
        """

        try:
            logger.info(f"Worker.load_knowledge_base_content: Processing {len(self.knowledge_base_files)} files for RAG")
            # Get RAG settings from config manager
            rag_settings = self._get_rag_settings()
            # Get relevant chunks from RAG handler with configurable settings
            logger.info(f"Worker.load_knowledge_base_content: Calling RAGHandler.get_relevant_chunks for query '{query[:50]}...'")
            chunks = self.rag_handler.get_relevant_chunks(
                query,
                n_results=rag_settings['n_results'],
                alpha=rag_settings['alpha'],
                filter_criteria={
                    "importance_score": rag_settings['importance_score'],
                    "language": "en"
                },
                reranking=rag_settings['reranking'],
                cross_encoder_reranking=rag_settings['cross_encoder_reranking'],
                query_expansion=rag_settings['query_expansion']
            )
            if not chunks:
                logger.info("Worker.load_knowledge_base_content: No relevant chunks found")
                return ""
            # Format the chunks into a single string for the prompt
            combined_content = ""
            for chunk in chunks:
                metadata = chunk.get('metadata', {})
                # Handle both ChunkMetadata objects and dictionaries
                if hasattr(metadata, 'file_name'):
                    # It's a ChunkMetadata object
                    file_name = metadata.file_name
                    section_title = getattr(metadata, 'section_title', None)
                    is_table = getattr(metadata, 'is_table', False)
                    source_type = getattr(metadata, 'source_type', 'unknown')
                    sheet_name = getattr(metadata, 'sheet_name', None)
                    importance_score = getattr(metadata, 'importance_score', 1.0)
                else:
                    # It's a dictionary
                    file_name = metadata.get('file_name', 'Unknown')
                    section_title = metadata.get('section_title')
                    is_table = metadata.get('is_table', False)
                    source_type = metadata.get('source_type', 'unknown')
                    sheet_name = metadata.get('sheet_name')
                    importance_score = metadata.get('importance_score', 1.0)
                combined_content += f"\n\nFile: {file_name}\n"
                if section_title:
                    combined_content += f"Section: {section_title}\n"
                if is_table:
                    combined_content += "[Table Content]\n"
                combined_content += f"Source Type: {source_type}\n"
                if sheet_name:
                    combined_content += f"Sheet: {sheet_name}\n"
                combined_content += chunk['content']
                combined_content += f"\nImportance Score: {importance_score:.2f}\n"
            # Optimize the content for token limits using configurable setting
            optimized_content = self.conversation_manager.optimize_rag_content(combined_content, max_tokens=rag_settings['token_limit'])
            logger.info(f"Worker.load_knowledge_base_content: Successfully loaded {len(combined_content)} characters, optimized to {len(optimized_content)} characters")
            return optimized_content
        except Exception as e:
            logger.error(f"Worker.load_knowledge_base_content: Error loading knowledge base content: {str(e)}")
            logger.error(traceback.format_exc())
            return ""

    def _get_rag_settings(self) -> dict:
        """
        Get RAG settings from config manager with fallback to defaults.
        Returns:
            Dict containing RAG configuration settings
        """

        try:
            # Try to load settings from config.json first
            config_path = Path("config.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                # Get system settings from config
                ultra_safe_mode = config.get('RAG_ULTRA_SAFE_MODE', False)
                safe_retrieval_mode = config.get('RAG_SAFE_RETRIEVAL_MODE', False)
                embedding_device = config.get('EMBEDDING_DEVICE', 'cpu')
                # Apply safe mode overrides
                if ultra_safe_mode:
                    # Ultra safe mode: conservative settings
                    n_results = 15
                    alpha = 0.5
                    importance_score = 0.5
                    token_limit = 4096
                    reranking = False
                    cross_encoder_reranking = False
                    query_expansion = False
                elif safe_retrieval_mode:
                    # Safe retrieval mode: balanced settings
                    n_results = 20
                    alpha = 0.6
                    importance_score = 0.4
                    token_limit = 6144
                    reranking = True
                    cross_encoder_reranking = False
                    query_expansion = True
                else:
                    # Performance mode: optimized settings
                    n_results = 25
                    alpha = 0.6
                    importance_score = 0.3
                    token_limit = 8192
                    reranking = True
                    cross_encoder_reranking = True
                    query_expansion = True
                return {
                    'n_results': n_results,
                    'alpha': alpha,
                    'importance_score': importance_score,
                    'token_limit': token_limit,
                    'reranking': reranking,
                    'cross_encoder_reranking': cross_encoder_reranking,
                    'query_expansion': query_expansion,
                    'ultra_safe_mode': ultra_safe_mode,
                    'safe_retrieval_mode': safe_retrieval_mode,
                    'embedding_device': embedding_device
                }
        except Exception as e:
            logger.warning(f"Error loading RAG settings from config: {e}")
        # Fallback to default optimized settings
        return {
            'n_results': 25,
            'alpha': 0.6,
            'importance_score': 0.3,
            'token_limit': 8192,
            'reranking': True,
            'cross_encoder_reranking': True,
            'query_expansion': True,
            'ultra_safe_mode': False,
            'safe_retrieval_mode': False,
            'embedding_device': 'cpu'
        }

    def stop(self):
        """Stop the worker's execution"""
        self.is_running = False
        self.update_terminal_console_signal.emit("Worker stopped.")

    def continue_discussion(self, new_message, is_follow_up=False):
        """Continue existing conversation or start new one."""

        try:
            if is_follow_up:
                # Already started new conversation in start_agent_discussion
                pass
            elif self.conversation_manager.is_conversation_active():
                # Add to existing conversation
                self.conversation_manager.add_message(
                    new_message,
                    role="user",
                    metadata={"timestamp": datetime.now().isoformat()}
                )
            else:
                # No active conversation, start new one
                self.current_conversation_id = self.conversation_manager.start_new_conversation(
                    new_message,
                    metadata={
                        "agent_count": len(self.agents),
                        "knowledge_base_files": self.knowledge_base_files
                    }
                )
            # Get full conversation context
            context_window = self.conversation_manager.get_context_window()
            # Process agents sequentially - each agent builds on previous agents' responses
            # Dynamic features (Internet, RAG, MCP) will be handled per-agent in _process_agents_sequentially
            final_response_content = self._process_agents_sequentially(new_message, context_window)
            # Format and emit the final response
            if final_response_content:
                # Clean the final response before emitting
                # For final answer, we don't want to add agent headers again, just clean the content
                cleaned_final_response = self.clean_agent_response(final_response_content)
                # self.update_final_answer_signal.emit(cleaned_final_response)  # REMOVED: Final answer functionality
                # Emit signal that token generation has ended
                # To get the session total output tokens:
                if token_counter: # Check if token_counter is available
                    self.token_generation_ended_signal.emit(time.time(), token_counter.get_session_stats()["output_tokens"])
            self.update_terminal_console_signal.emit("Agent discussion completed.")
            self.discussion_completed_signal.emit()
        except Exception as e:
            self.error_signal.emit(str(e))
            self.discussion_completed_signal.emit()

        finally:
            if not self.is_running:
                self.discussion_completed_signal.emit()

    def prepare_agent_input(self, agent_number: int, instructions: str, new_message: str, search_results: str, context_window: str, agent_responses: Dict[int, str] = None, agent_knowledge_base_content: str = None, mcp_context: Dict = None) -> str:
        # Get the current agent's feature settings
        current_agent = None
        for agent in self.agents:
            if agent['agent_number'] == agent_number:
                current_agent = agent
                break
        agent_internet_enabled = current_agent.get('internet_enabled', False) if current_agent else False
        agent_rag_enabled = current_agent.get('rag_enabled', False) if current_agent else False
        agent_mcp_enabled = current_agent.get('mcp_enabled', False) if current_agent else False

        # Get provider and model for context window calculation
        provider = current_agent.get('provider', 'unknown') if current_agent else 'unknown'
        model = current_agent.get('model', 'unknown') if current_agent else 'unknown'

        # Format context to clearly show previous agent responses
        formatted_context = ""
        if context_window:
            # Access messages from current conversation
            if (hasattr(self.conversation_manager, 'current_conversation') and
                isinstance(self.conversation_manager.current_conversation, dict) and
                'messages' in self.conversation_manager.current_conversation):
                formatted_context = "=== CONVERSATION HISTORY ===\n"
                # Organize messages by type and timestamp
                user_messages = []
                agent_messages = {}
                assistant_messages = []
                for message in self.conversation_manager.current_conversation['messages']:
                    role = message.get('role', 'unknown')
                    content = message.get('content', '')
                    timestamp = message.get('timestamp', '')
                    if role == "user":
                        user_messages.append((timestamp, f"User said:\n{content}\n\n"))
                    elif role.startswith('agent_'):
                        agent_num = int(role.split('_')[1])
                        if agent_num not in agent_messages:
                            agent_messages[agent_num] = []
                        agent_messages[agent_num].append((timestamp, f"Agent {agent_num} said:\n{content}\n\n"))
                    elif role == "assistant":
                        assistant_messages.append((timestamp, f"Assistant Response:\n{content}\n\n"))  # Changed from "Final Answer" to "Assistant Response"
                # Sort all messages by timestamp
                all_messages = []
                all_messages.extend(user_messages)
                for agent_num in agent_messages:
                    all_messages.extend(agent_messages[agent_num])
                all_messages.extend(assistant_messages)
                all_messages.sort(key=lambda x: x[0] if x[0] else '')
                # Add all messages to context
                for _, message_text in all_messages:
                    formatted_context += message_text

        # Format previous agent responses with intelligent truncation
        formatted_agent_responses = ""
        if agent_responses:
            formatted_agent_responses = self._format_agent_responses_with_context_management(
                agent_responses, agent_number, provider, model
            )
        # Format search results in a more structured way
        formatted_search_results = ""
        if isinstance(search_results, list):
            # Use the new helper method to format search results
            formatted_search_results = self.format_search_results(search_results, new_message)
        elif isinstance(search_results, str) and search_results.strip():
            formatted_search_results = search_results
        # Get optimized RAG content with better integration if RAG is enabled for this agent
        optimized_kb_content = ""
        if agent_rag_enabled:
            kb_content = agent_knowledge_base_content if agent_knowledge_base_content else ""
            if kb_content:
                # Get RAG settings for token limit
                rag_settings = self._get_rag_settings()
                optimized_kb_content = self.conversation_manager.optimize_rag_content(
                    kb_content,
                    max_tokens=rag_settings['token_limit']
                )
        # Add explicit RAG instructions with enhanced guidelines
        rag_instructions = """
When using knowledge base content:
1. Prioritize information from the provided knowledge base when relevant
2. Clearly indicate when using knowledge base information
3. Combine knowledge base information with other sources when appropriate
4. If knowledge base information is outdated or incomplete, note this
5. Pay attention to importance scores and context
6. Consider section titles and document structure
7. Handle table content appropriately
8. Use context before and after chunks when relevant
9. **Review and critically assess previous agent responses in 'PREVIOUS AGENT OUTPUTS' section. Identify areas for improvement, expansion, correction, or contradiction.**
10. **Focus on adding value and building upon the collective responses to provide a comprehensive and accurate response.**
        """
        # Format MCP context if available for this agent
        formatted_mcp_context = ""
        formatted_mcp_instructions = ""
        if mcp_context and agent_mcp_enabled:
            formatted_mcp_context = "=== MCP CONTEXT ===\n"
            # Add server information
            if "servers" in mcp_context:
                formatted_mcp_context += "Available MCP Servers:\n"
                for server_name, server_data in mcp_context["servers"].items():
                    formatted_mcp_context += f"- {server_name}: {server_data.get('description', '')}\n"
                    if "capabilities" in server_data:
                        formatted_mcp_context += f"  Capabilities: {', '.join(server_data['capabilities'])}\n"
            # Add task recommendations if available
            if "task_recommendations" in mcp_context:
                recommendations = mcp_context["task_recommendations"]
                if recommendations.get("recommended_servers"):
                    formatted_mcp_context += "\nRecommended MCP Servers for this task:\n"
                    for server in recommendations["recommended_servers"]:
                        formatted_mcp_context += f"- {server}\n"
                if recommendations.get("usage_instructions"):
                    formatted_mcp_context += "\n" + recommendations["usage_instructions"] + "\n"
            # Add MCP usage instructions
            formatted_mcp_instructions = """
=== MCP USAGE INSTRUCTIONS ===
When using Model Context Protocol (MCP) servers:
1. INTERNET ACCESS: Use search-capable MCP servers to find up-to-date information from the web
   - For factual queries, current events, or recent developments
   - Example: [MCP:Google Search:What are the latest AI developments?]
2. RAG (RETRIEVAL AUGMENTED GENERATION): Use document retrieval MCP servers to access specific knowledge bases
   - For domain-specific information or proprietary data
   - Example: [MCP:Context7:What is the syntax for Python async functions?]
3. CODE & DEVELOPMENT: Use GitHub or other code repository MCP servers for code-related tasks
   - For accessing repositories, issues, or pull requests
   - Example: [MCP:GitHub:Show open issues in repository X]
4. DATA ANALYSIS: Use database or visualization MCP servers for data queries
   - For SQL queries, data analysis, or visualization requests
   - Example: [MCP:Database:Show sales trends for Q1]
5. TOOL USE: Use appropriate MCP servers based on the specific task
   - Select the most relevant server for each subtask
   - Follow the recommended servers for this specific task when available
IMPORTANT USAGE GUIDELINES:
- To use an MCP server, use the format: [MCP:ServerName:Your request]
- The system will process your MCP request and provide the results
- You should then incorporate these results into your response
- If you mention that you'll use an MCP server, make sure to actually include the [MCP:...] syntax
- The system will automatically select the most appropriate MCP server if you use: [MCP:Auto:Your request]
- You can use multiple MCP requests in a single response if needed
            """
        # Internet usage instructions
        internet_instructions = """
=== INTERNET USAGE INSTRUCTIONS ===
When internet access is enabled:
1. Use [SEARCH: your query] to request additional web searches for specific information
2. Cite sources when using information from search results
3. Acknowledge when information might not be current
4. Request targeted searches rather than broad queries
5. Use search for factual information, current events, or verification
        """
        sections = [
            ("CONVERSATION HISTORY", formatted_context),
            ("PREVIOUS AGENT OUTPUTS", formatted_agent_responses),  # Include previous agent responses
            ("CURRENT MESSAGE", new_message),
            ("PRIMARY INSTRUCTIONS", instructions),
            ("GENERAL GUIDELINES", self.general_instructions),
            ("SEARCH RESULTS", formatted_search_results if formatted_search_results.strip() else "No search results available."),
        ]
        # Add knowledge base content if RAG is enabled for this agent
        if agent_rag_enabled and optimized_kb_content:
            sections.append(("KNOWLEDGE BASE CONTENT", optimized_kb_content))
        # Add MCP context if enabled for this agent
        if agent_mcp_enabled and formatted_mcp_context:
            sections.append(("MCP CONTEXT", formatted_mcp_context))
        # Add MCP instructions if enabled for this agent
        if agent_mcp_enabled:
            sections.append(("MCP USAGE INSTRUCTIONS", formatted_mcp_instructions))
        # Add internet instructions if enabled for this agent
        if agent_internet_enabled:
            sections.append(("INTERNET USAGE", internet_instructions))
        # Add RAG instructions if enabled for this agent
        if agent_rag_enabled and optimized_kb_content:
            sections.append(("RAG INSTRUCTIONS", rag_instructions))
        # Add response guidelines
        sections.append(("RESPONSE GUIDELINES", """
Please provide a response that:
1. Directly addresses the query using information from search results when available
2. Clearly cites sources when using information from search results
3. Maintains conversation context
4. Uses knowledge base content when relevant
5. Requests additional searches if needed using [SEARCH: query]
6. Uses MCP servers when appropriate with [MCP:ServerName:request] format
7. Focuses on providing accurate, up-to-date information
8. Acknowledges when information might not be current
9. Provides context and explanation for any cited information
10. Considers document structure and section organization
11. Handles table content appropriately
12. **Critically evaluate and build upon previous agent responses to refine and enhance the overall answer.**
"""))
        return "\n\n=== {} ===\n{}".format(*zip(*sections))

    def _format_agent_responses_with_context_management(self, agent_responses: Dict[int, str], current_agent_number: int, provider: str, model: str) -> str:
        """
        Format previous agent responses with intelligent context management to prevent overflow.

        Args:
            agent_responses: Dictionary of agent responses
            current_agent_number: Current agent number
            provider: API provider name
            model: Model name

        Returns:
            Formatted agent responses string with context management applied
        """
        if not agent_responses:
            return ""

        # Check if context management is enabled
        context_management_enabled = self.config_manager.get('AGENT_CONTEXT_MANAGEMENT', True)

        # Get responses from agents before current agent
        relevant_responses = {}
        for prev_agent_num, prev_response in agent_responses.items():
            if prev_agent_num < current_agent_number:
                relevant_responses[prev_agent_num] = prev_response

        if not relevant_responses:
            return ""

        # Format basic response without context management if disabled
        if not context_management_enabled:
            formatted_agent_responses = "=== PREVIOUS AGENT RESPONSES ===\n"
            for agent_num in sorted(relevant_responses.keys()):
                formatted_agent_responses += f"Agent {agent_num} Response:\n{relevant_responses[agent_num]}\n\n"
            return formatted_agent_responses

        # Get context window limit for this provider/model
        total_context_limit = settings_manager.get_context_window(provider, model)
        if not total_context_limit:
            total_context_limit = 32768  # Default fallback

        # Calculate available space for agent responses (reserve space for other sections)
        # Reserve 40% of context for instructions, current message, and output
        available_for_agent_responses = int(total_context_limit * 0.6)

        # Strategy 1: If total content fits, use all responses
        total_content = ""
        for agent_num in sorted(relevant_responses.keys()):
            total_content += f"Agent {agent_num} Response:\n{relevant_responses[agent_num]}\n\n"

        estimated_tokens = self._estimate_tokens_accurately(total_content, provider)

        if estimated_tokens <= available_for_agent_responses:
            # All responses fit, return as-is
            return "=== PREVIOUS AGENT RESPONSES ===\n" + total_content

        # Strategy 2: Intelligent truncation and summarization
        self.update_terminal_console_signal.emit(
            f"Agent {current_agent_number}: Context window management - truncating previous responses "
            f"({estimated_tokens} tokens > {available_for_agent_responses} limit)"
        )

        return self._apply_context_truncation_strategy(relevant_responses, available_for_agent_responses, provider)

    def _apply_context_truncation_strategy(self, agent_responses: Dict[int, str], token_limit: int, provider: str) -> str:
        """
        Apply intelligent truncation strategy to fit agent responses within token limit.

        Args:
            agent_responses: Dictionary of agent responses
            token_limit: Maximum tokens allowed
            provider: API provider for token estimation

        Returns:
            Truncated and formatted agent responses
        """
        formatted_responses = "=== PREVIOUS AGENT RESPONSES (CONTEXT MANAGED) ===\n"

        # Strategy: Recent responses get more space, older responses get summarized
        sorted_agents = sorted(agent_responses.keys(), reverse=True)  # Most recent first

        remaining_tokens = token_limit
        processed_responses = []

        for i, agent_num in enumerate(sorted_agents):
            response = agent_responses[agent_num]

            if i == 0:  # Most recent agent gets priority (up to 50% of available space)
                max_tokens_for_this_agent = min(remaining_tokens, int(token_limit * 0.5))
            elif i == 1:  # Second most recent gets up to 30%
                max_tokens_for_this_agent = min(remaining_tokens, int(token_limit * 0.3))
            else:  # Older agents get remaining space, but summarized
                max_tokens_for_this_agent = min(remaining_tokens, int(token_limit * 0.2))

            # Check if full response fits
            estimated_tokens = self._estimate_tokens_accurately(response, provider)

            if estimated_tokens <= max_tokens_for_this_agent:
                # Full response fits
                processed_response = f"Agent {agent_num} Response:\n{response}\n\n"
                processed_responses.append(processed_response)
                remaining_tokens -= estimated_tokens
            else:
                # Need to truncate or summarize
                if i < 2:  # For recent agents, truncate intelligently
                    truncated_response = self._intelligent_truncate_response(
                        response, max_tokens_for_this_agent, provider
                    )
                    processed_response = f"Agent {agent_num} Response (truncated):\n{truncated_response}\n\n"
                else:  # For older agents, create summary
                    summary = self._create_response_summary(response, max_tokens_for_this_agent)
                    processed_response = f"Agent {agent_num} Summary:\n{summary}\n\n"

                processed_responses.append(processed_response)
                remaining_tokens -= max_tokens_for_this_agent

            if remaining_tokens <= 0:
                break

        # Add responses in chronological order
        processed_responses.reverse()
        formatted_responses += "".join(processed_responses)

        # Add context management notice
        if len(sorted_agents) > len(processed_responses):
            omitted_count = len(sorted_agents) - len(processed_responses)
            formatted_responses += f"[Note: {omitted_count} earlier agent response(s) omitted due to context limits]\n\n"

        return formatted_responses

    def _intelligent_truncate_response(self, response: str, max_tokens: int, provider: str) -> str:
        """
        Intelligently truncate a response to fit within token limit while preserving key information.

        Args:
            response: Original response text
            max_tokens: Maximum tokens allowed
            provider: API provider for token estimation

        Returns:
            Truncated response
        """
        # Reserve tokens for truncation notice
        available_tokens = max_tokens - 50

        # Split into paragraphs and sentences
        paragraphs = response.split('\n\n')

        truncated_content = ""
        current_tokens = 0

        for paragraph in paragraphs:
            paragraph_tokens = self._estimate_tokens_accurately(paragraph, provider)

            if current_tokens + paragraph_tokens <= available_tokens:
                truncated_content += paragraph + "\n\n"
                current_tokens += paragraph_tokens
            else:
                # Try to fit part of this paragraph
                sentences = paragraph.split('. ')
                for sentence in sentences:
                    sentence_tokens = self._estimate_tokens_accurately(sentence, provider)
                    if current_tokens + sentence_tokens <= available_tokens:
                        truncated_content += sentence + ". "
                        current_tokens += sentence_tokens
                    else:
                        break
                break

        if truncated_content != response:
            truncated_content += "\n[Response truncated due to context limits]"

        return truncated_content.strip()

    def _create_response_summary(self, response: str, max_tokens: int) -> str:
        """
        Create a concise summary of an agent response.

        Args:
            response: Original response text
            max_tokens: Maximum tokens for summary

        Returns:
            Summary of the response
        """
        # Simple extractive summarization - take key sentences
        sentences = response.replace('\n', ' ').split('. ')

        # Prioritize sentences with key indicators
        key_indicators = ['conclusion', 'result', 'answer', 'solution', 'recommendation',
                         'important', 'key', 'main', 'primary', 'essential']

        scored_sentences = []
        for sentence in sentences:
            score = 0
            sentence_lower = sentence.lower()
            for indicator in key_indicators:
                if indicator in sentence_lower:
                    score += 1
            scored_sentences.append((score, sentence))

        # Sort by score and take top sentences that fit
        scored_sentences.sort(key=lambda x: x[0], reverse=True)

        summary = ""
        for score, sentence in scored_sentences:
            if len(summary + sentence) < max_tokens * 4:  # Rough token estimation
                summary += sentence + ". "
            else:
                break

        if not summary:
            # Fallback: take first few sentences
            summary = '. '.join(sentences[:2]) + "."

        return summary.strip()

    def format_conversation_history(self):
        return "\n\n".join(self.conversation_history)

    def prepare_mcp_context(self):
        """Prepare MCP context for agent input.
        Returns:
            Dict: MCP context information or empty dict if MCP is disabled
        """

        try:
            # Get MCP context from the MCP client
            mcp_context = mcp_client.prepare_mcp_context(self.prompt)
            # Add additional context about enabled servers
            enabled_servers = mcp_client.get_enabled_servers()
            server_info = {}
            for server in enabled_servers:
                server_info[server.name] = {
                    "capabilities": server.capabilities,
                    "description": server.description
                }
            # Combine contexts
            mcp_context["servers"] = server_info
            # Add task-specific MCP recommendations based on prompt analysis
            task_recommendations = self._analyze_task_for_mcp_recommendations(self.prompt)
            if task_recommendations:
                mcp_context["task_recommendations"] = task_recommendations
            return mcp_context
        except Exception as e:
            self.update_terminal_console_signal.emit(f"Error preparing MCP context: {str(e)}")
            return {}

    def _analyze_task_for_mcp_recommendations(self, prompt: str) -> Dict[str, Any]:
        """Analyze the user's prompt to recommend appropriate MCP servers for the task.
        Args:
            prompt: The user's prompt
        Returns:
            Dict[str, Any]: Recommended MCP servers and usage instructions
        """
        # Initialize recommendations
        recommendations = {
            "recommended_servers": [],
            "usage_instructions": ""
        }
        # Get all enabled servers
        enabled_servers = mcp_client.get_enabled_servers()
        if not enabled_servers:
            return recommendations
        # Convert prompt to lowercase for easier matching
        prompt_lower = prompt.lower()
        # Check for research/search related tasks
        if any(term in prompt_lower for term in ["search", "find", "research", "look up", "information", "data", "news"]):
            search_servers = [s for s in enabled_servers if any(cap in s.capabilities for cap in ["web_search", "news_search"])]
            if search_servers:
                recommendations["recommended_servers"].extend([s.name for s in search_servers])
                recommendations["usage_instructions"] += "\nFor research tasks, use the search capabilities of " + ", ".join([s.name for s in search_servers]) + " to find relevant information."
        # Check for code/development related tasks
        if any(term in prompt_lower for term in ["code", "program", "develop", "github", "repository", "git", "pull request", "issue", "bug"]):
            dev_servers = [s for s in enabled_servers if any(cap in s.capabilities for cap in ["repo_access", "code_execution", "pr_review"])]
            if dev_servers:
                recommendations["recommended_servers"].extend([s.name for s in dev_servers])
                recommendations["usage_instructions"] += "\nFor development tasks, use " + ", ".join([s.name for s in dev_servers]) + " to access code repositories and development tools."
        # Check for data analysis tasks
        if any(term in prompt_lower for term in ["analyze", "data", "statistics", "chart", "graph", "visualization", "database", "sql"]):
            data_servers = [s for s in enabled_servers if any(cap in s.capabilities for cap in ["sql_execution", "visualization", "schema_inspection"])]
            if data_servers:
                recommendations["recommended_servers"].extend([s.name for s in data_servers])
                recommendations["usage_instructions"] += "\nFor data analysis tasks, use " + ", ".join([s.name for s in data_servers]) + " to query databases and visualize data."
        # Check for document/content related tasks
        if any(term in prompt_lower for term in ["document", "file", "content", "write", "draft", "edit", "review"]):
            content_servers = [s for s in enabled_servers if any(cap in s.capabilities for cap in ["file_access", "file_creation", "document_retrieval"])]
            if content_servers:
                recommendations["recommended_servers"].extend([s.name for s in content_servers])
                recommendations["usage_instructions"] += "\nFor document and content tasks, use " + ", ".join([s.name for s in content_servers]) + " to access and manage files."
        # Remove duplicates while preserving order
        recommendations["recommended_servers"] = list(dict.fromkeys(recommendations["recommended_servers"]))
        return recommendations
    # Add a new signal
    update_conversation_history_signal = pyqtSignal(list)

    def format_mcp_search_results(self, result, query, server_name):
        """
        Format MCP search results in a more structured and readable way.
        Args:
            result (Dict): The search result from MCP server
            query (str): The search query
            server_name (str): The name of the MCP server
        Returns:
            str: Formatted search results
        """
        if not result or 'results' not in result or not result['results']:
            return f"### Search Results for '{query}'\n\nNo search results found."
        formatted_output = f"## Search Results for: '{query}'\n\n"
        # Add timestamp to indicate when the search was performed

        from datetime import datetime

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_output += f"*Search performed at: {current_time}*\n\n"
        # Check if this is a news-related query
        is_news_query = any(term in query.lower() for term in ["news", "latest", "recent", "today", "update", "headline", "current", "events", "breaking"])
        # Add source information
        formatted_output += f"*Source: {server_name}*\n\n"
        # Format each result
        for i, item in enumerate(result['results'], 1):
            title = item.get('title', 'No Title')
            link = item.get('link', '')
            snippet = item.get('snippet', '')
            content = item.get('content', '')
            # Format the header with number, title and URL
            formatted_output += f"### {i}. {title}\n"
            formatted_output += f"**Source:** [{link}]({link})\n\n"
            # Add special formatting for news articles
            if is_news_query:
                # Try to extract date from content
                date_match = re.search(r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|\d{4}-\d{2}-\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})', content)
                date_str = date_match.group(1) if date_match else "Recent"
                formatted_output += f"**Date:** {date_str}\n\n"
                # Try to extract author for news articles
                author_match = re.search(r'(?:By|Author)[:\s]+([A-Za-z\s\.-]+)', content, re.IGNORECASE)
                if author_match:
                    author = author_match.group(1).strip()
                    formatted_output += f"**Author:** {author}\n\n"
            # Add snippet as summary if available
            if snippet:
                formatted_output += f"**Summary:** {snippet}\n\n"
            # Format the main content with better structure
            if content and len(content) > len(snippet):
                # Remove the URL from the end if it exists
                content = re.sub(r'\n\nSource: .*$', '', content)
                # Split content into paragraphs for better readability
                paragraphs = content.split('\n\n')
                # Limit to a reasonable number of paragraphs
                max_paragraphs = 3 if is_news_query else 5
                paragraphs = paragraphs[:max_paragraphs]
                # Format content based on type
                formatted_output += "**Content:**\n"
                # For news articles, try to identify and highlight key information
                if is_news_query:
                    # Look for quotes in the content
                    quotes = re.findall(r'"([^"]+)"', content)
                    # Add paragraphs first
                    for paragraph in paragraphs:
                        paragraph = paragraph.strip()
                        if paragraph:
                            formatted_output += f"{paragraph}\n\n"
                    # Add quotes if found
                    if quotes:
                        formatted_output += "**Key Quotes:**\n"
                        for quote in quotes[:3]:  # Limit to 3 quotes
                            formatted_output += f"> {quote}\n\n"
                else:
                    # Regular content formatting
                    for paragraph in paragraphs:
                        paragraph = paragraph.strip()
                        if paragraph:
                            formatted_output += f"{paragraph}\n\n"
            elif snippet:
                # If no detailed content, use the snippet
                formatted_output += f"{snippet}\n\n"
            # Add separator between results
            formatted_output += "---\n\n"
        return formatted_output

    def format_search_results(self, search_results, query):
        """
        Format search results in a more structured and readable way.
        Args:
            search_results (List[SearchResult]): List of search results
            query (str): The search query
        Returns:
            str: Formatted search results
        """
        if not search_results:
            return "No search results found."
        formatted_output = f"## Search Results for: '{query}'\n\n"
        # Check if this is a news-related query
        is_news_query = any(term in query.lower() for term in ["news", "latest", "recent", "today", "update", "headline", "current", "events", "breaking"])
        # Add a timestamp for news queries to indicate when the search was performed
        if is_news_query:

            from datetime import datetime

            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted_output += f"*Search performed at: {current_time}*\n\n"
        for i, result in enumerate(search_results, 1):
            # Extract metadata
            title = result.metadata.get('title', 'No Title')
            snippet = result.metadata.get('snippet', '')
            source = result.metadata.get('source', 'Unknown Source')
            # Format the header with number, title and URL
            formatted_output += f"### {i}. {title}\n"
            formatted_output += f"**Source:** [{result.url}]({result.url})\n\n"
            # Add special formatting for news articles
            if is_news_query:
                # Try to extract date from content or metadata
                date_match = re.search(r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|\d{4}-\d{2}-\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})', result.content)
                date_str = date_match.group(1) if date_match else "Recent"
                formatted_output += f"**Date:** {date_str}\n\n"
                # Try to extract author for news articles
                author_match = re.search(r'(?:By|Author)[:\s]+([A-Za-z\s\.-]+)', result.content, re.IGNORECASE)
                if author_match:
                    author = author_match.group(1).strip()
                    formatted_output += f"**Author:** {author}\n\n"
            # Add snippet as summary if available
            if snippet:
                formatted_output += f"**Summary:** {snippet}\n\n"
            # Format the main content with better structure
            content = result.content
            # Remove the URL from the end if it exists (it was already included above)
            content = re.sub(r'\n\nSource: .*$', '', content)
            # Split content into paragraphs for better readability
            paragraphs = content.split('\n\n')
            # Limit to a reasonable number of paragraphs
            max_paragraphs = 3 if is_news_query else 5
            paragraphs = paragraphs[:max_paragraphs]
            # Format content based on type
            formatted_output += "**Content:**\n"
            # For news articles, try to identify and highlight key information
            if is_news_query:
                # Look for quotes in the content
                quotes = re.findall(r'"([^"]+)"', content)
                # Add paragraphs first
                for paragraph in paragraphs:
                    paragraph = paragraph.strip()
                    if paragraph:
                        formatted_output += f"{paragraph}\n\n"
                # Add quotes if found
                if quotes:
                    formatted_output += "**Key Quotes:**\n"
                    for quote in quotes[:3]:  # Limit to 3 quotes
                        formatted_output += f"> {quote}\n\n"
            else:
                # Regular content formatting
                for paragraph in paragraphs:
                    paragraph = paragraph.strip()
                    if paragraph:
                        formatted_output += f"{paragraph}\n\n"
            # Add separator between results
            formatted_output += "---\n\n"
        return formatted_output

    def process_additional_searches(self, response):
        """Process additional search requests in the response."""
        # Note: Internet search is now handled per-agent, so this method will only be called
        # if the agent has internet enabled and includes [SEARCH:] requests in their response
        search_pattern = r'\[SEARCH: (.*?)\]'
        search_requests = re.findall(search_pattern, response)
        for query in search_requests:
            self.update_terminal_console_signal.emit(f"\nPerforming additional search: {query}")

            try:
                # Use the new search manager instead of extract_info_from_web
                search_results = self.search_manager.search(query)
                if search_results:
                    # Log the found URLs
                    self.update_terminal_console_signal.emit("Found relevant sources:")
                    for result in search_results:
                        self.update_terminal_console_signal.emit(f"- {result.url}")
                    # Format the results using the new helper method
                    formatted_results = self.format_search_results(search_results, query)
                    # Replace the search placeholder with results
                    response = response.replace(
                        f"[SEARCH: {query}]",
                        f"Additional search results for '{query}':\n{formatted_results}\n"
                    )
                else:
                    response = response.replace(
                        f"[SEARCH: {query}]",
                        f"No relevant results found for '{query}'\n"
                    )
            except Exception as e:
                self.update_terminal_console_signal.emit(f"Search error: {str(e)}")
                response = response.replace(
                    f"[SEARCH: {query}]",
                    f"Error performing search for '{query}': {str(e)}\n"
                )
        # Process MCP requests if present
        # Note: Most MCP requests should already be processed in get_agent_response,
        # but this handles any that might have been added after that
        if "[MCP:" in response:
            response = self.process_mcp_requests(response)
        return response

    def process_mcp_requests(self, response, collect_results=False):
        """Process MCP requests in the response.
        Args:
            response: The agent response text
            collect_results: Whether to collect MCP results separately
        Returns:
            If collect_results is False: str - The updated response with MCP results
            If collect_results is True: tuple - (updated_response, mcp_results_dict)
        """
        # Note: MCP is now handled per-agent, so this method will only be called
        # if the agent has MCP enabled and includes [MCP:] requests in their response
        # Match MCP requests with format [MCP:ServerName:request] or [MCP:Auto:request]
        mcp_pattern = r'\[MCP:(.*?):(.*?)\]'
        mcp_requests = re.findall(mcp_pattern, response)
        # Dictionary to collect MCP results if needed
        mcp_results = {}
        updated_response = response
        for server_name, request in mcp_requests:
            self.update_terminal_console_signal.emit(f"\nProcessing MCP request for {server_name}: {request}")
            request_key = f"[MCP:{server_name}:{request}]"
            formatted_result = ""

            try:
                # Handle automatic server selection
                if server_name.lower() == "auto":
                    # Use task analysis to select the most appropriate server
                    task_recommendations = self._analyze_task_for_mcp_recommendations(request)
                    recommended_servers = task_recommendations.get("recommended_servers", [])
                    if recommended_servers:
                        # Enhanced server selection logic
                        selected_server = self._select_optimal_mcp_server(request, recommended_servers)
                        server_name = selected_server
                        self.update_terminal_console_signal.emit(f"Auto-selected MCP server: {server_name}")
                    else:
                        # No recommendation, use a default server if available
                        enabled_servers = mcp_client.get_enabled_servers()
                        if enabled_servers:
                            # Try to find a general-purpose server
                            general_servers = [s for s in enabled_servers if any(cap in s.capabilities for cap in ["web_search", "general"])]
                            if general_servers:
                                server_name = general_servers[0].name
                                self.update_terminal_console_signal.emit(f"No specific recommendation, using general-purpose MCP server: {server_name}")
                            else:
                                server_name = enabled_servers[0].name
                                self.update_terminal_console_signal.emit(f"No recommendation available, using default MCP server: {server_name}")
                        else:
                            error_msg = f"Error: No MCP servers available for auto-selection\n"
                            updated_response = updated_response.replace(request_key, error_msg)
                            if collect_results:
                                mcp_results[request_key] = {"error": "No MCP servers available for auto-selection"}
                            continue
                # Find the server by name
                server = None
                for s in mcp_client.get_enabled_servers():
                    if s.name.lower() == server_name.lower():
                        server = s
                        break
                if not server:
                    error_msg = f"Error: MCP server '{server_name}' not found or not enabled\n"
                    self.update_terminal_console_signal.emit(error_msg)
                    updated_response = updated_response.replace(request_key, error_msg)
                    if collect_results:
                        mcp_results[request_key] = {"error": f"MCP server '{server_name}' not found or not enabled"}
                    continue
                # Log the server details for debugging
                self.update_terminal_console_signal.emit(f"Using MCP server: {server.name}, URL: {server.url}")
                if server.name == "Google Search":
                    self.update_terminal_console_signal.emit(f"Google Search API Key: {server.auth_token[:5]}..., CX: {server.cx}")
                # Query the MCP server

                try:
                    self.update_terminal_console_signal.emit(f"Querying MCP server '{server_name}' with request: {request}")
                    result = mcp_client.query_mcp_server(server, request)
                    if "error" in result:
                        error_msg = f"Error from MCP server '{server_name}': {result['error']}\n"
                        self.update_terminal_console_signal.emit(error_msg)
                        updated_response = updated_response.replace(request_key, error_msg)
                        if collect_results:
                            mcp_results[request_key] = result
                except Exception as e:
                    error_msg = f"Exception querying MCP server '{server_name}': {str(e)}\n"
                    self.update_terminal_console_signal.emit(error_msg)
                    self.update_terminal_console_signal.emit(traceback.format_exc())
                    updated_response = updated_response.replace(request_key, error_msg)
                    if collect_results:
                        mcp_results[request_key] = {"error": str(e)}
                    continue
                else:
                    # Format the result based on server type
                    if server_name == "Context7":
                        formatted_result = f"### Documentation from Context7 for {result.get('library', '')}\n\n"
                        formatted_result += f"**Request:** {result.get('request', '')}\n\n"
                        formatted_result += f"{result.get('content', 'No content available')}\n\n"
                        formatted_result += f"**Source:** {result.get('source', '')}\n"
                    elif server_name == "Google Search" or "googleapis.com/customsearch" in server.url or server_name == "Brave Search" or "api.search.brave.com" in server.url or server_name == "Serper Search" or "serper.dev" in server.url:
                        # Use the new helper method for search results formatting
                        search_query = result.get('query', request)
                        formatted_result = self.format_mcp_search_results(result, search_query, server_name)
                        # If raw_data is available for Brave Search, log it for debugging
                        if server_name == "Brave Search" and 'raw_data' in result:
                            self.update_terminal_console_signal.emit(f"Brave Search raw data available with keys: {result['raw_data'].keys() if isinstance(result['raw_data'], dict) else 'not a dict'}")
                    else:
                        # Generic formatting for other servers
                        formatted_result = f"### Results from {server_name}\n\n"
                        for key, value in result.items():
                            if key != "error" and not isinstance(value, dict) and not isinstance(value, list):
                                formatted_result += f"**{key}:** {value}\n"
                    # Replace the MCP placeholder with results
                    updated_response = updated_response.replace(request_key, formatted_result)
                    # Store the result if collecting
                    if collect_results:
                        # Add formatted result and raw result
                        mcp_results[request_key] = {
                            "formatted_result": formatted_result,
                            "raw_result": result,
                            "server_name": server_name,
                            "request": request
                        }
            except Exception as e:
                error_msg = f"Error processing MCP request for '{server_name}': {str(e)}\n"
                self.update_terminal_console_signal.emit(f"MCP error: {str(e)}")
                updated_response = updated_response.replace(request_key, error_msg)
                if collect_results:
                    mcp_results[request_key] = {"error": str(e)}
        if collect_results:
            return (self.clean_agent_response(updated_response), mcp_results)
        else:
            return self.clean_agent_response(updated_response)

    def _execute_api_call(self, provider_name: str, model: str, prompt: str, agent_number: int, effective_max_tokens: int, settings: ModelSettings, client=None) -> str:
        """
        A centralized method to handle all streaming-capable API calls with retries and error handling.
        """
        # Centralize timeout/retry values
        timeout_seconds = self.config_manager.get('API_CALL_TIMEOUT', 120)
        max_retries = self.config_manager.get('MAX_RETRIES', 2)
        retry_delay = self.config_manager.get('RETRY_DELAY', 5)
        # Provider-specific logic
        if provider_name in ["OpenAI", "Groq", "OpenRouter", "DeepSeek", "Ollama", "LM Studio", "Grok", "Requesty"]:
             # These providers are OpenAI-compatible
            return self._execute_openai_compatible_api_call(
                provider_name, model, prompt, agent_number, effective_max_tokens, settings, client,
                timeout_seconds, max_retries, retry_delay
            )
        elif provider_name == "Google GenAI":
            return self.call_gemini_api(model, prompt, agent_number, effective_max_tokens)
        elif provider_name == "Anthropic":
            return self.call_anthropic_api(model, prompt, agent_number, effective_max_tokens)
        else:
            return f"Unknown or unsupported provider: {provider_name}"

    def _execute_openai_compatible_api_call(self, provider_name: str, model: str, prompt: str, agent_number: int, effective_max_tokens: int, settings: ModelSettings, client, timeout_seconds: int, max_retries: int, retry_delay: int) -> str:
        """Handles API calls for OpenAI-compatible services."""
        if not settings.streaming_enabled:
            # Centralized non-streaming logic for OpenAI-compatible APIs
            for attempt in range(max_retries + 1):

                try:
                    self.update_terminal_console_signal.emit(f"Getting non-streaming response from {provider_name} model: {model} (attempt {attempt + 1}/{max_retries + 1})")
                    response = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=effective_max_tokens,
                        temperature=settings.temperature,
                        top_p=settings.top_p,
                        stop=settings.stop_sequences if settings.stop_sequences else None,
                        timeout=timeout_seconds
                    )
                    content = response.choices[0].message.content
                    if not content or not content.strip():
                        if attempt < max_retries:
                            self.update_terminal_console_signal.emit(f"Empty non-streaming response, retrying... (attempt {attempt + 2}/{max_retries + 1})")
                            time.sleep(retry_delay * (2 ** attempt))
                            continue
                        self.update_terminal_console_signal.emit(f"Warning: Received empty non-streaming response from {provider_name} after all retries.")
                        return f"[Agent provided no discernible content after multiple non-streaming attempts via {provider_name}.]"
                    cleaned_content = self.clean_agent_response(content)
                    self.agent_responses[agent_number] = cleaned_content
                    self.update_agents_discussion_signal.emit(cleaned_content, agent_number, model, True)
                    return cleaned_content
                except (APITimeoutError, APIConnectionError, APIStatusError, BadRequestError) as e:
                    # Your robust, centralized error handling and retry logic here
                    error_msg = f"{provider_name} API error (attempt {attempt + 1}/{max_retries + 1}): {str(e)}"
                    self.update_terminal_console_signal.emit(error_msg)
                    if isinstance(e, BadRequestError) or attempt >= max_retries:
                        self.update_agents_discussion_signal.emit(f"API Error: {str(e)}", agent_number, model, True)
                        return f"Error: {provider_name} API Error - {str(e)}"
                    time.sleep(retry_delay * (2 ** attempt))
                except Exception as e:
                    # General exception handling
                    error_msg = f"Unexpected error in {provider_name} non-streaming (attempt {attempt + 1}/{max_retries + 1}): {str(e)}"
                    self.update_terminal_console_signal.emit(error_msg)
                    if attempt >= max_retries:
                        return f"[Agent failed to get response from {provider_name} after all retries.]"
                    time.sleep(retry_delay * (2 ** attempt))
            return f"[Agent failed to get non-streaming response from {provider_name} after multiple attempts.]"
        # Centralized streaming logic
        for attempt in range(max_retries + 1):

            try:
                self.update_terminal_console_signal.emit(f"Streaming from {provider_name}/{model} (Attempt {attempt + 1}/{max_retries + 1})")
                stream = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    stream=True,
                    max_tokens=effective_max_tokens,
                    temperature=settings.temperature,
                    top_p=settings.top_p,
                    stop=settings.stop_sequences or None,
                    timeout=timeout_seconds
                )
                full_response = ""
                first_chunk = True
                buffer = ""
                chunk_count = 0
                first_token_received_this_attempt = False
                
                # Variables for new buffering logic
                stream_buffer = ""
                
                for chunk in stream:
                    self.current_agent_last_activity_time = time.time()
                    if not self.is_running:
                        self.update_terminal_console_signal.emit("Streaming stopped by user or timeout.")
                        # Ensure stream is closed if possible
                        if hasattr(stream, 'close'):
                            try:
                                stream.close()
                            except Exception as e_close:
                                logger.warning(f"Error closing {provider_name} stream: {e_close}")
                        if hasattr(stream, 'close'):

                            try:
                                stream.close()
                            except Exception as e_close:
                                logger.warning(f"Error closing {provider_name} stream: {e_close}")
                        return "[Streaming stopped by user]"
                    content = chunk.choices[0].delta.content
                    if content:
                        if token_counter and not first_token_received_this_attempt:
                            token_counter.start_generation_timer()
                            first_token_received_this_attempt = True
                        if token_counter:

                            try:
                                n_tokens, _ = token_counter.count_tokens(content, model)
                                token_counter.increment_output_tokens(n_tokens)
                            except Exception as e_tc:
                                logger.error(f"Error counting tokens for {provider_name} chunk: {e_tc}")
                        buffer += content
                        full_response += content

                        # Code-aware buffering logic for smooth streaming
                        stream_buffer += content
                        flush_now = False
                        if first_chunk: # Always flush the very first piece of content
                            flush_now = True
                        elif self._should_flush_for_code_integrity(stream_buffer): # Code-aware flushing
                            flush_now = True
                        elif '\n\n' in stream_buffer: # Flush on paragraph breaks
                            flush_now = True
                        elif len(stream_buffer) > 50: # Flush every ~50 chars (configurable)
                            flush_now = True
                        
                        if flush_now and stream_buffer:
                            if self.format_response_handler:
                                formatted_html_chunk = self.format_response_handler.format_agent_response(
                                    agent_number, model, stream_buffer, first_chunk
                                )
                                self.update_agents_discussion_signal.emit(formatted_html_chunk, agent_number, model, first_chunk)
                            else: # Fallback if no formatter
                                self.update_agents_discussion_signal.emit(stream_buffer, agent_number, model, first_chunk)
                            
                            first_chunk = False
                            stream_buffer = "" # Reset buffer

                if not self.is_running:
                    return "[Streaming stopped by user or timeout]"
                if stream_buffer: # Emit any remaining buffered content
                    if self.format_response_handler:
                        formatted_html_chunk = self.format_response_handler.format_agent_response(
                            agent_number, model, stream_buffer, first_chunk
                        )
                        self.update_agents_discussion_signal.emit(formatted_html_chunk, agent_number, model, first_chunk)
                    else:
                        self.update_agents_discussion_signal.emit(stream_buffer, agent_number, model, first_chunk)
                if not full_response.strip():
                    if attempt < max_retries:
                        self.update_terminal_console_signal.emit(f"Empty response from {provider_name} stream, retrying... (attempt {attempt + 2}/{max_retries + 1})")
                        time.sleep(retry_delay * (2 ** attempt))
                        continue
                    else:
                        self.update_terminal_console_signal.emit(f"Warning: Received empty response from {provider_name} stream after all retries.")
                        return f"[Agent provided no discernible content after multiple attempts via {provider_name} stream.]"
                cleaned_response = self.clean_agent_response(full_response)
                self.agent_responses[agent_number] = cleaned_response
                return cleaned_response
            except (APITimeoutError, APIConnectionError, APIStatusError, BadRequestError) as e:
                error_msg = f"{provider_name} API error (attempt {attempt + 1}/{max_retries + 1}): {str(e)}"
                self.update_terminal_console_signal.emit(error_msg)
                if isinstance(e, BadRequestError) or attempt >= max_retries:
                     self.update_agents_discussion_signal.emit(f"API Error: {str(e)}", agent_number, model, True)
                     return f"Error: {provider_name} API Error - {str(e)}"
                time.sleep(retry_delay * (2 ** attempt))
            except Exception as e:
                error_msg = f"Unexpected error in {provider_name} streaming (attempt {attempt + 1}/{max_retries + 1}): {str(e)}"
                self.update_terminal_console_signal.emit(error_msg)
                if attempt >= max_retries:
                    break
                time.sleep(retry_delay * (2 ** attempt))
        return f"[Agent failed to get response from {provider_name} after all retries.]"
    @track_performance

    def get_agent_response(self, provider, model, agent_input, agent_number, effective_max_tokens=None):
        """
        Get response from an agent using the specified provider and model.
        Args:
            provider (str): The API provider name (e.g., "OpenAI", "Ollama", etc.)
            model (str): The model name to use
            agent_input (str): The input prompt for the agent
            agent_number (int): The agent number for tracking
            effective_max_tokens (int, optional): The effective max_tokens to use (overrides model settings)
        Returns:
            str: The agent's response text with processed MCP requests
        """

        try:
            # Find the current agent to get its thinking_enabled setting
            current_agent = None
            for agent in self.agents:
                if agent['agent_number'] == agent_number:
                    current_agent = agent
                    break
            thinking_enabled = current_agent.get('thinking_enabled', False) if current_agent else False
            # Make the API call
            start_time = time.time()
            success = True
            error = None

            try:
                # Get settings for this specific model and provider
                settings = settings_manager.get_settings(provider, model)
                client = None # Will be set for OpenAI-compatible providers
                response = ""
                if provider == "Ollama":
                    base_url = settings_manager.get_ollama_url() or "http://localhost:11434/v1"
                    client = OpenAI(base_url=base_url, api_key="ollama")
                    response = self._execute_api_call(provider, model, agent_input, agent_number, effective_max_tokens, settings, client)
                elif provider == "OpenAI":
                    api_key = self.config_manager.get('OPENAI_API_KEY')
                    if not api_key: return "Error: OpenAI API key not found."
                    client = OpenAI(api_key=api_key)
                    response = self._execute_api_call(provider, model, agent_input, agent_number, effective_max_tokens, settings, client)
                elif provider == "Google GenAI":
                    response = self.call_gemini_api(model, agent_input, agent_number, effective_max_tokens)
                elif provider == "Anthropic":
                    response = self.call_anthropic_api(model, agent_input, agent_number, effective_max_tokens)
                elif provider == "Groq":
                    api_key = self.config_manager.get('GROQ_API_KEY')
                    if not api_key: return "Error: Groq API key not found."
                    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key)
                    response = self._execute_api_call(provider, model, agent_input, agent_number, effective_max_tokens, settings, client)
                elif provider == "Grok":
                    api_key = self.config_manager.get('GROK_API_KEY')
                    if not api_key: return "Error: Grok API key not found."
                    client = OpenAI(base_url="https://api.x.ai/v1", api_key=api_key)
                    response = self._execute_api_call(provider, model, agent_input, agent_number, effective_max_tokens, settings, client)
                elif provider == "DeepSeek":
                    response = self.call_deepseek_api(model, agent_input, agent_number, effective_max_tokens)
                elif provider == "LM Studio":
                    # LM Studio has special health checks, handle it separately for now
                    response = self.call_lmstudio_api(model, agent_input, agent_number, effective_max_tokens)
                elif provider == "OpenRouter":
                    response = self.call_openrouter_api(model, agent_input, agent_number, effective_max_tokens)
                elif provider == "Requesty":
                    response = self.call_requesty_api(model, agent_input, agent_number, effective_max_tokens)
                else:
                    response = f"Unknown provider: {provider}"
                # Check for MCP requests in the response
                # Get the current agent's MCP setting
                current_agent = None
                for agent in self.agents:
                    if agent['agent_number'] == agent_number:
                        current_agent = agent
                        break
                agent_mcp_enabled = current_agent.get('mcp_enabled', False) if current_agent else False
                if agent_mcp_enabled and "[MCP:" in response:
                    # Process MCP requests and collect results
                    processed_response, mcp_results = self.process_mcp_requests(response, collect_results=True)
                    # If we have MCP results and this isn't the last agent, we might want to
                    # follow up with the model to incorporate the MCP results
                    if mcp_results and len(mcp_results) > 0 and agent_number < len(self.agents):
                        # Prepare a follow-up prompt with the MCP results
                        follow_up_prompt = agent_input + "\n\n=== MCP RESULTS ===\n"
                        # Add each MCP result to the follow-up prompt
                        for request_key, result_data in mcp_results.items():
                            if "formatted_result" in result_data:
                                follow_up_prompt += f"\n{result_data['formatted_result']}\n"
                        follow_up_prompt += "\n\nPlease incorporate these MCP results into your response."
                        # Make a follow-up call to the model with the MCP results
                        self.update_terminal_console_signal.emit(f"Making follow-up call to {provider}/{model} with MCP results")
                        # Re-call the appropriate function for the follow-up
                        # We can re-use the get_agent_response method recursively for this
                        follow_up_response = self.get_agent_response(
                            provider, model, follow_up_prompt, agent_number, effective_max_tokens
                        )
                        # Use the follow-up response as the final response
                        response = follow_up_response
                    else:
                        # Just use the processed response
                        response = processed_response
            except Exception as e:
                success = False
                error = str(e)
                raise

            finally:
                # Track API call performance
                end_time = time.time()
                duration = end_time - start_time # Calculate duration
                performance_monitor.track_api_call(
                    provider=provider,
                    model=model,
                    prompt_length=len(agent_input),
                    start_time=start_time,
                    end_time=end_time,
                    success=success,
                    error=error
                )
                # Track tokens if token counter is available and the call was successful
                if token_counter and self.current_conversation_id and success:
                    # Extract system prompt from agent_input
                    system_prompt = ""
                    user_prompt = agent_input
                    # Check if there are sections in the input that indicate system prompt
                    if "=== PRIMARY INSTRUCTIONS ===" in agent_input:
                        parts = agent_input.split("=== PRIMARY INSTRUCTIONS ===")
                        if len(parts) > 1:
                            system_prompt = "=== PRIMARY INSTRUCTIONS ===" + parts[1].split("=== CURRENT MESSAGE ===")[0]
                    # Track system prompt separately
                    if system_prompt:
                        token_counter.track_tokens(
                            conversation_id=self.current_conversation_id,
                            input_text=system_prompt,
                            output_text="",
                            provider=provider,
                            model=model,
                            is_system_prompt=True
                        )
                        # Track user input and output, passing the duration
                        token_counter.track_tokens(
                            conversation_id=self.current_conversation_id,
                            input_text=user_prompt,
                            output_text=response if not error else "",
                            provider=provider,
                            model=model,
                            duration=duration # Pass the calculated duration
                        )
            # Response caching has been removed
            self.update_terminal_console_signal.emit(f"API response received from {provider}")
            return response
        except Exception as e:
            self.update_terminal_console_signal.emit(f"Error in get_agent_response: {str(e)}")
            self.update_terminal_console_signal.emit(traceback.format_exc())
            return f"Error: {str(e)}"

    def __del__(self):
        """Cleanup when the worker is destroyed"""
        pass

    def call_lmstudio_api(self, model: str, prompt: str, agent_number: int, effective_max_tokens=None) -> str:
        """
        Call the LM Studio local inference server with enhanced error handling.
        """

        try:
            # Get base URL from settings manager
            lmstudio_base_url = settings_manager.get_lmstudio_url()
            if not lmstudio_base_url:
                self.update_terminal_console_signal.emit("Warning: LM Studio URL not found in settings. Using default.")
                lmstudio_base_url = "http://localhost:1234/v1"  # Default URL
            # First check if LM Studio server is running
            health_check_url = f"{lmstudio_base_url.rstrip('/')}/models"

            try:
                # Perform health check
                health_response = requests.get(health_check_url, timeout=5)
                health_response.raise_for_status()
                self.update_terminal_console_signal.emit("LM Studio server is running")
                # Get the actual model name from LM Studio
                models_data = health_response.json()
                if models_data.get("data"):
                    # Find the selected model in the list of loaded models
                    actual_model = None
                    for loaded_model in models_data["data"]:
                        # Check if the selected model name is part of the loaded model's ID
                        if model.lower() in loaded_model["id"].lower():
                            actual_model = loaded_model["id"]
                            self.update_terminal_console_signal.emit(f"Found matching LM Studio model: {actual_model}")
                            break
                    if not actual_model:
                        error_msg = f"Model '{model}' not found in LM Studio. Please ensure the model is loaded."
                        self.update_terminal_console_signal.emit(error_msg)
                        return error_msg
                else:
                    error_msg = "No models found in LM Studio. Please load a model first."
                    self.update_terminal_console_signal.emit(error_msg)
                    return error_msg
            except requests.exceptions.RequestException as e:
                error_msg = f"LM Studio server health check failed: {str(e)}\nPlease ensure:\n1. LM Studio is running\n2. Server is started in LM Studio\n3. A model is loaded"
                self.update_terminal_console_signal.emit(error_msg)
                return error_msg
            client = OpenAI(base_url=lmstudio_base_url, api_key="lm-studio")
            settings = settings_manager.get_settings("LM Studio", actual_model)
            return self._execute_openai_compatible_api_call("LM Studio", actual_model, prompt, agent_number, effective_max_tokens, settings, client,
                                                            self.config_manager.get('API_CALL_TIMEOUT', 120),
                                                            self.config_manager.get('MAX_RETRIES', 2),
                                                            self.config_manager.get('RETRY_DELAY', 5))
        except requests.exceptions.ConnectionError:
            error_msg = """Error: Cannot connect to LM Studio. Please ensure:
1. LM Studio application is running
2. Server is started (click 'Start Server' in LM Studio)
3. Server is running on port 1234 (check LM Studio settings)
4. A model is loaded in LM Studio"""
            self.update_terminal_console_signal.emit(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"LM Studio API error: {str(e)}"
            self.update_terminal_console_signal.emit(error_msg)
            return f"Error: {str(e)}"

    def call_openrouter_api(self, model, prompt, agent_number, effective_max_tokens=None):
        """Wrapper for calling the central API execution method for OpenRouter."""
        api_key = self.config_manager.get('OPENROUTER_API_KEY')
        if not api_key:
            return "Error: OpenRouter API key not found."
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
        settings = settings_manager.get_settings("OpenRouter", model)
        return self._execute_openai_compatible_api_call("OpenRouter", model, prompt, agent_number, effective_max_tokens, settings, client,
                                                       self.config_manager.get('API_CALL_TIMEOUT', 120),
                                                       self.config_manager.get('MAX_RETRIES', 2),
                                                       self.config_manager.get('RETRY_DELAY', 5))

    def call_requesty_api(self, model, prompt, agent_number, effective_max_tokens=None):
        """Wrapper for calling the central API execution method for Requesty."""
        api_key = self.config_manager.get('REQUESTY_API_KEY')
        if not api_key:
            return "Error: Requesty API key not found."
        client = OpenAI(base_url="https://router.requesty.ai/v1", api_key=api_key)
        settings = settings_manager.get_settings("Requesty", model)
        return self._execute_openai_compatible_api_call("Requesty", model, prompt, agent_number, effective_max_tokens, settings, client,
                                                       self.config_manager.get('API_CALL_TIMEOUT', 120),
                                                       self.config_manager.get('MAX_RETRIES', 2),
                                                       self.config_manager.get('RETRY_DELAY', 5))

    def _handle_large_response(self, response: str, agent_number: int) -> str:
        """
        Handle large agent responses with size checks, logging, and a single truncation point.
        """
        if not response:
            return response
        content_length = len(response)
        # Get the configurable maximum length for a response from an agent.
        # Default to 1,000,000 characters (a generous limit, ~250k tokens).
        max_len = self.config_manager.get('MAX_RESPONSE_LENGTH_PER_AGENT', 1000000) if self.config_manager else 1000000
        # 1. Truncation Logic: Perform truncation ONLY if the response exceeds the configured max_len.
        if content_length > max_len:
            logger.warning(f"TRUNCATION: Agent {agent_number} response (length {content_length}) exceeded MAX_RESPONSE_LENGTH_PER_AGENT ({max_len} chars) and was truncated.")
            self.update_terminal_console_signal.emit(
                f"Warning: Agent {agent_number}'s response was truncated because its length ({content_length:,} chars) exceeded the configured limit of {max_len:,}."
            )
            # Return the truncated response immediately.
            return response[:max_len] + f"\n\n[Response truncated by system due to exceeding character limit of {max_len}]"
        # 2. Informational Logging: Log messages for large, but not truncated, responses.
        # These are just for information and do not alter the response.
        if content_length > 100000:  # ~100KB
            self.update_terminal_console_signal.emit(f"Info: Received a large response from Agent {agent_number}: {content_length:,} characters.")
        elif content_length > 50000: # ~50KB
            self.update_terminal_console_signal.emit(f"Info: Received a moderate response from Agent {agent_number}: {content_length:,} characters.")
        return response

    def _validate_and_adjust_token_limits(self, agent: Dict, agent_number: int, agent_input: str = None) -> Dict[str, Any]:
        """
        Validate and adjust token limits for the agent based on provider and model constraints.
        Args:
            agent: Agent configuration dictionary
            agent_number: Agent number for logging
            agent_input: The input text to estimate tokens for
        Returns:
            Dict containing validated token limits and other parameters
        """
        provider = agent.get('provider', 'unknown')
        model = agent.get('model', 'unknown')
        token_mode = agent.get('token_mode', 'dynamic')  # Get token mode from agent config
        manual_max_tokens = agent.get('manual_max_tokens', 4096)  # Get manual token setting
        # Get provider-specific settings
        settings = settings_manager.get_settings(provider, model)
        if not settings:
            self.update_terminal_console_signal.emit(f"Warning: No settings found for {provider}/{model}, using defaults")
            settings = settings_manager.get_default_settings()
        # Get API limits for the provider
        api_limits = settings_manager.get_api_token_limits(provider, model)
        # Calculate dynamic max tokens based on input length and user's configured max output
        dynamic_max_tokens_for_output = self._calculate_dynamic_max_tokens(
            agent_input or "",
            provider,
            settings.max_tokens,  # Pass the agent's configured max_tokens as the desired output length
            model  # Pass the model name for specific context limits
        )
        effective_max_tokens = dynamic_max_tokens_for_output  # This is the final value for the API call.
        # Update logging to be more informative
        self.update_terminal_console_signal.emit(
            f"Agent {agent_number} ({provider}/{model}) token limits: "
            f"Agent Configured Max Output Tokens (UI): {settings.max_tokens}, "
            f"Dynamically Calculated Max Output Tokens (considering input & total context): {dynamic_max_tokens_for_output}, "
            f"Effective Max Output Tokens for API call: {effective_max_tokens}"
        )
        return {
            'effective_max_tokens': effective_max_tokens,
            'provider_limits': api_limits,  # These are total context limits from ModelSettings
            'settings': settings.to_dict(), 
            'dynamic_calculation_result': dynamic_max_tokens_for_output 
        }

    def _calculate_dynamic_max_tokens(self, agent_input: str, provider: str, user_configured_max_output_tokens: int = None, model: str = None) -> int:
        """
        Calculate dynamic max tokens for output based on input length and available context.
        Args:
            agent_input: The input text to estimate tokens for
            provider: The provider name
            user_configured_max_output_tokens: The user's configured max output tokens for this agent
            model: The model name for specific context limits
        Returns:
            The calculated max tokens for output
        """
        # Default total context limit if provider/model specific limit is not found
        default_total_context_limit = 20000 
        # Estimate input tokens
        estimated_input_tokens = self._estimate_tokens_accurately(agent_input, provider)
        # Fetch total context window limit from model_settings for the specific model
        total_context_limit = settings_manager.get_context_window(provider, model)
        if not total_context_limit:
            total_context_limit = default_total_context_limit # A safe default
        # Calculate safety margin (10% of total context or minimum 1024 tokens)
        safety_margin = max(1024, int(total_context_limit * 0.10))
        # For OpenRouter models, be more conservative to avoid 400 errors
        if provider.lower() == 'openrouter':
            safety_margin = max(4096, int(total_context_limit * 0.20))  # 20% safety margin for OpenRouter
        # For GLM models specifically, be even more conservative
        if provider.lower() == 'openrouter' and model and 'glm-4' in model.lower():
            safety_margin = max(6144, int(total_context_limit * 0.25))  # 25% safety margin for GLM models
        # Calculate available space for output
        available_for_output_raw = total_context_limit - estimated_input_tokens - safety_margin
        if available_for_output_raw <= 0:
            logger.warning(f"Input tokens ({estimated_input_tokens:.0f}) + safety margin ({safety_margin}) nearly or fully exceed total context limit ({total_context_limit}) for {provider}. Setting output to minimum (100).")
            return 100 
        # Cap by the user's configured desired output length for this agent
        max_output_tokens = min(user_configured_max_output_tokens or 4096, available_for_output_raw)
        # Ensure a minimum reasonable value for output
        final_max_output_tokens = max(100, int(max_output_tokens))
        logger.debug(
            f"Dynamic token calculation for {provider}: "
            f"Input Tokens (est): {estimated_input_tokens:.0f}, "
            f"Total Context Limit: {total_context_limit}, "
            f"Safety Margin: {safety_margin}, "
            f"Available for Output (raw): {available_for_output_raw:.0f}, "
            f"User Configured Output: {user_configured_max_output_tokens}, "
            f"Final Max Output Tokens: {final_max_output_tokens}"
        )
        return final_max_output_tokens

    def _estimate_tokens_accurately(self, text: str, provider: str) -> float:
        """
        Estimate tokens accurately using tiktoken or provider-specific methods.
        Args:
            text: The text to estimate tokens for
            provider: The provider name for encoding selection
        Returns:
            Estimated token count
        """
        if not tiktoken:
            return len(text) / 4 # Fallback estimation
        encoding_name = self._get_encoding_for_provider(provider)
        # Check cache first
        if encoding_name in TIKTOKEN_CACHE:
            encoding = TIKTOKEN_CACHE[encoding_name]
        else:
            try:
                encoding = tiktoken.get_encoding(encoding_name)
                TIKTOKEN_CACHE[encoding_name] = encoding
            except KeyError:
                # Fallback to cl100k_base if specific encoding not found
                logger.warning(f"Encoding {encoding_name} not found for {provider}, using cl100k_base")
                encoding = tiktoken.get_encoding("cl100k_base")
                TIKTOKEN_CACHE[encoding_name] = encoding # Cache the fallback too
        # Count tokens

        try:
            token_count = len(encoding.encode(text))
            return float(token_count)
        except Exception as e:
            logger.error(f"Error encoding text with tiktoken: {e}")
            return len(text) / 4 # Fallback on encoding error

    def _get_encoding_for_provider(self, provider: str) -> str:
        """
        Get the appropriate tiktoken encoding for a provider.
        Args:
            provider: The provider name
        Returns:
            Encoding name for tiktoken
        """
        encoding_map = {
            'openai': 'cl100k_base',  # GPT-4, GPT-3.5-turbo
            'anthropic': 'cl100k_base',  # Claude models
            'google': 'cl100k_base',  # Gemini models
            'openrouter': 'cl100k_base',  # Most OpenRouter models
            'ollama': 'cl100k_base',  # Most Ollama models
            'lmstudio': 'cl100k_base',  # LM Studio models
            'deepseek': 'cl100k_base',  # DeepSeek models
            'groq': 'cl100k_base',  # Groq models
            'grok': 'cl100k_base',  # Grok models
            'requesty': 'cl100k_base',  # Requesty models
        }
        return encoding_map.get(provider.lower(), 'cl100k_base')

    def call_deepseek_api(self, model, prompt, agent_number, effective_max_tokens=None):
        """Wrapper for calling the central API execution method for DeepSeek."""
        api_key = self.config_manager.get('DEEPSEEK_API_KEY')
        if not api_key:
            return "Error: DeepSeek API key not found."
        client = OpenAI(base_url="https://api.deepseek.com/v1", api_key=api_key)
        settings = settings_manager.get_settings("DeepSeek", model)
        return self._execute_api_call("DeepSeek", model, prompt, agent_number, effective_max_tokens, settings, client)

    def call_ollama_api(self, model: str, prompt: str, agent_number: int, thinking_enabled: bool = False, effective_max_tokens=None) -> str:
        """Wrapper for calling the central API execution method for Ollama."""
        self.update_terminal_console_signal.emit(f"Connecting to Ollama with model: {model}")
        # Get base URL from settings
        base_url = settings_manager.get_ollama_url()
        if not base_url:
            self.update_terminal_console_signal.emit("Warning: Ollama URL not found in settings. Using default.")
            base_url = "http://localhost:11434/v1" # Default URL
        client = OpenAI(base_url=base_url, api_key="ollama")
        settings = settings_manager.get_settings("Ollama", model)
        return self._execute_api_call("Ollama", model, prompt, agent_number, effective_max_tokens, settings, client)

    def call_openai_api(self, model, prompt, agent_number, effective_max_tokens=None):
        """Wrapper for calling the central API execution method for OpenAI."""
        api_key = self.config_manager.get('OPENAI_API_KEY')
        if not api_key:
            return "Error: OpenAI API key not found."
        client = OpenAI(api_key=api_key)
        settings = settings_manager.get_settings("OpenAI", model)
        return self._execute_api_call("OpenAI", model, prompt, agent_number, effective_max_tokens, settings, client)

    def call_gemini_api(self, model, prompt, agent_number, effective_max_tokens=None):
        """Call Google Gemini API with streaming support, thinking capabilities, and retry mechanism."""
        api_key = self.config_manager.get('GOOGLE_API_KEY')
        if not api_key:
            return "Error: Google API key not found."

        # Get settings for this specific model and provider
        settings = settings_manager.get_settings("Google GenAI", model)
        use_streaming = settings.streaming_enabled if settings else False
        temperature = settings.temperature if settings else 0.7
        top_p = settings.top_p if settings else 0.9
        top_k = settings.top_k if settings else 40
        thinking_enabled = settings.thinking_enabled if settings else False
        thinking_budget = settings.thinking_budget if settings else -1

        # Check if this is a thinking-capable model (newer Gemini models have thinking built-in)
        thinking_capable_models = [
            "gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash-thinking",
            "gemini-2.5-flash-preview", "gemini-2.5-pro-preview", "gemini-2.0-pro-exp"
        ]
        is_thinking_model = any(thinking_model in model.lower() for thinking_model in thinking_capable_models)

        # Use new google.genai library for thinking models, fallback to old library
        if is_thinking_model and thinking_enabled:
            return self._call_gemini_with_thinking(
                model, prompt, agent_number, effective_max_tokens,
                temperature, top_p, top_k, thinking_budget, use_streaming, api_key
            )
        else:
            return self._call_gemini_legacy(
                model, prompt, agent_number, effective_max_tokens,
                temperature, top_p, top_k, use_streaming, api_key
            )

    def _call_gemini_with_thinking(self, model, prompt, agent_number, effective_max_tokens,
                                 temperature, top_p, top_k, thinking_budget, use_streaming, api_key):
        """Call Gemini API using the new google.genai library with thinking capabilities."""
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)

            # Create content structure similar to AI Studio
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)]
                )
            ]

            # Configure generation with thinking
            generate_content_config = types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    thinking_budget=thinking_budget,
                ),
                response_mime_type="text/plain",
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                max_output_tokens=effective_max_tokens
            )

            if use_streaming:
                self.update_terminal_console_signal.emit(f"Streaming response from Gemini model with thinking: {model}")
                return self._process_gemini_thinking_stream(
                    client, model, contents, generate_content_config, agent_number
                )
            else:
                self.update_terminal_console_signal.emit(f"Getting non-streaming response from Gemini model with thinking: {model}")
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=generate_content_config
                )

                # Extract text from response candidates
                content = ""
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    content += part.text

                if not content:
                    content = response.text if hasattr(response, 'text') else str(response)

                cleaned_content = self.clean_agent_response(content)
                self.update_agents_discussion_signal.emit(cleaned_content, agent_number, model, True)

                # Log thinking usage if available
                if hasattr(response, 'usage_metadata') and response.usage_metadata:
                    thoughts_tokens = getattr(response.usage_metadata, 'thoughts_token_count', 0)
                    total_tokens = getattr(response.usage_metadata, 'total_token_count', 0)
                    if thoughts_tokens > 0:
                        self.update_terminal_console_signal.emit(f"🧠 Thinking tokens used: {thoughts_tokens}, Total: {total_tokens}")

                return cleaned_content

        except ImportError:
            self.update_terminal_console_signal.emit("Warning: google.genai library not available, falling back to legacy implementation")
            return self._call_gemini_legacy(
                model, prompt, agent_number, effective_max_tokens,
                temperature, top_p, top_k, use_streaming, api_key
            )
        except Exception as e:
            error_message = f"Error calling Gemini API with thinking: {str(e)}"
            self.update_terminal_console_signal.emit(error_message)
            return f"Error: {e}"

    def _process_gemini_thinking_stream(self, client, model, contents, config, agent_number):
        """Process streaming response from Gemini with thinking."""
        try:
            full_response = ""
            first_chunk = True
            stream_buffer = ""

            for chunk in client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=config
            ):
                self.current_agent_last_activity_time = time.time()
                if not self.is_running:
                    break

                # Extract text from chunk candidates
                chunk_text = ""
                if hasattr(chunk, 'candidates') and chunk.candidates:
                    for candidate in chunk.candidates:
                        if hasattr(candidate, 'content') and candidate.content:
                            if hasattr(candidate.content, 'parts') and candidate.content.parts:
                                for part in candidate.content.parts:
                                    if hasattr(part, 'text') and part.text:
                                        chunk_text += part.text
                elif hasattr(chunk, 'text') and chunk.text:
                    chunk_text = chunk.text

                if chunk_text:
                    stream_buffer += chunk_text
                    full_response += chunk_text

                    flush_now = False
                    if first_chunk:
                        flush_now = True
                    elif self._should_flush_for_code_integrity(stream_buffer): # Code-aware flushing
                        flush_now = True
                    elif '\n\n' in stream_buffer:
                        flush_now = True
                    elif len(stream_buffer) > 50:
                        flush_now = True

                    if flush_now and stream_buffer:
                        cleaned_chunk_for_display = self.clean_agent_response(stream_buffer)
                        if self.format_response_handler:
                            formatted_html_chunk = self.format_response_handler.format_agent_response(
                                agent_number, model, cleaned_chunk_for_display, first_chunk
                            )
                            self.update_agents_discussion_signal.emit(formatted_html_chunk, agent_number, model, first_chunk)
                        else:
                            self.update_agents_discussion_signal.emit(cleaned_chunk_for_display, agent_number, model, first_chunk)
                        first_chunk = False
                        stream_buffer = ""

            # Emit any remaining buffer
            if stream_buffer:
                cleaned_buffer = self.clean_agent_response(stream_buffer)
                self.current_agent_last_activity_time = time.time()
                if self.format_response_handler:
                    formatted_html_chunk = self.format_response_handler.format_agent_response(
                        agent_number, model, cleaned_buffer, first_chunk
                    )
                    self.update_agents_discussion_signal.emit(formatted_html_chunk, agent_number, model, first_chunk)
                else:
                    self.update_agents_discussion_signal.emit(cleaned_buffer, agent_number, model, first_chunk)

            if not full_response.strip():
                error_msg = "Gemini API with thinking returned empty response"
                self.update_terminal_console_signal.emit(f"Error: {error_msg}")
                return f"Error: {error_msg}"

            # Log thinking usage from the final chunk (streaming doesn't provide usage metadata per chunk)
            # We'll need to get this from the final response or implement a different approach
            self.update_terminal_console_signal.emit(f"🧠 Thinking mode was active for {model}")

            self.agent_responses[agent_number] = self.clean_agent_response(full_response)
            return self.agent_responses[agent_number]

        except Exception as e:
            error_message = f"Error processing Gemini thinking stream: {str(e)}"
            self.update_terminal_console_signal.emit(error_message)
            return f"Error: {e}"

    def _call_gemini_legacy(self, model, prompt, agent_number, effective_max_tokens,
                          temperature, top_p, top_k, use_streaming, api_key):
        """Call Gemini API using the legacy google.generativeai library."""
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        # Retry mechanism for finish_reason errors
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            try:
                model_instance = genai.GenerativeModel(model)
                if use_streaming:
                    self.update_terminal_console_signal.emit(f"Streaming response from Gemini model: {model}")
                    response_stream = model_instance.generate_content(
                        prompt,
                        stream=True,
                        generation_config=genai.types.GenerationConfig(
                            max_output_tokens=effective_max_tokens,
                            temperature=temperature,
                            top_p=top_p,
                            top_k=top_k
                        )
                    )
                    full_response = ""
                    first_chunk = True
                    buffer = ""
                    stream_buffer = "" # For new buffering logic

                    for chunk in response_stream:
                        # FIX: Update activity time for EVERY chunk received from the stream.
                        self.current_agent_last_activity_time = time.time()
                        if not self.is_running:
                            break
                        if chunk.text:
                            stream_buffer += chunk.text
                            full_response += chunk.text

                            flush_now = False
                            if first_chunk:
                                flush_now = True
                            elif self._should_flush_for_code_integrity(stream_buffer): # Code-aware flushing
                                flush_now = True
                            elif '\n\n' in stream_buffer:
                                flush_now = True
                            elif len(stream_buffer) > 50:
                                flush_now = True

                            if flush_now and stream_buffer:
                                cleaned_chunk_for_display = self.clean_agent_response(stream_buffer)
                                if self.format_response_handler:
                                    formatted_html_chunk = self.format_response_handler.format_agent_response(
                                        agent_number, model, cleaned_chunk_for_display, first_chunk
                                    )
                                    self.update_agents_discussion_signal.emit(formatted_html_chunk, agent_number, model, first_chunk)
                                else:
                                    self.update_agents_discussion_signal.emit(cleaned_chunk_for_display, agent_number, model, first_chunk)
                                first_chunk = False
                                stream_buffer = ""

                    # Emit any remaining buffer
                    if stream_buffer:
                        cleaned_buffer = self.clean_agent_response(stream_buffer)
                        self.current_agent_last_activity_time = time.time()
                        if self.format_response_handler:
                            formatted_html_chunk = self.format_response_handler.format_agent_response(
                                agent_number, model, cleaned_buffer, first_chunk
                            )
                            self.update_agents_discussion_signal.emit(formatted_html_chunk, agent_number, model, first_chunk)
                        else:
                            self.update_agents_discussion_signal.emit(cleaned_buffer, agent_number, model, first_chunk)
                    # Check if we got any response
                    if not full_response.strip():
                        if retry_count < max_retries - 1:
                            retry_count += 1
                            self.update_terminal_console_signal.emit(f"Empty response from Gemini, retrying ({retry_count}/{max_retries})...")
                            # Reduce max_tokens for retry
                            if effective_max_tokens:
                                effective_max_tokens = max(1000, effective_max_tokens // 2)
                            continue
                        else:
                            error_msg = "Gemini API returned empty response after retries (likely content filtered or token limit exceeded)"
                            self.update_terminal_console_signal.emit(f"Error calling Gemini API: {error_msg}")
                            return f"Error: {error_msg}"
                    self.agent_responses[agent_number] = self.clean_agent_response(full_response)
                    return self.agent_responses[agent_number]
                else: # Non-streaming
                    self.update_terminal_console_signal.emit(f"Getting non-streaming response from Gemini model: {model}")
                    response = model_instance.generate_content(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            max_output_tokens=effective_max_tokens,
                            temperature=temperature,
                            top_p=top_p,
                            top_k=top_k
                        )
                    )
                    # Check for response validity
                    if not response or not hasattr(response, 'text') or not response.text:
                        if retry_count < max_retries - 1:
                            retry_count += 1
                            self.update_terminal_console_signal.emit(f"Empty response from Gemini, retrying ({retry_count}/{max_retries})...")
                            # Reduce max_tokens for retry
                            if effective_max_tokens:
                                effective_max_tokens = max(1000, effective_max_tokens // 2)
                            continue
                        else:
                            error_msg = "Gemini API returned empty response after retries (likely content filtered or token limit exceeded)"
                            self.update_terminal_console_signal.emit(f"Error calling Gemini API: {error_msg}")
                            return f"Error: {error_msg}"
                    content = response.text
                    cleaned_content = self.clean_agent_response(content)
                    self.agent_responses[agent_number] = cleaned_content
                    self.update_agents_discussion_signal.emit(cleaned_content, agent_number, model, True)
                    return cleaned_content
            except Exception as e:
                error_str = str(e)
                # Check if it's a finish_reason error
                if "finish_reason" in error_str.lower() or "invalid operation" in error_str.lower():
                    if retry_count < max_retries - 1:
                        retry_count += 1
                        self.update_terminal_console_signal.emit(f"Gemini finish_reason error, retrying ({retry_count}/{max_retries})...")
                        # Reduce max_tokens for retry
                        if effective_max_tokens:
                            effective_max_tokens = max(1000, effective_max_tokens // 2)
                        continue
                    else:
                        error_message = f"Error calling Gemini API after retries: {error_str}"
                        self.update_terminal_console_signal.emit(error_message)
                        self.update_agents_discussion_signal.emit(f"Error: {e}", agent_number, model, True)
                        return f"Error: {e}"
                elif "400" in error_str and "API key not valid" in error_str:
                     # Non-retryable API key error
                    self.update_terminal_console_signal.emit(f"Error calling Gemini API: {error_str}")
                    self.update_agents_discussion_signal.emit(f"Error: {e}", agent_number, model, True)
                    return f"Error: {e}"
                else:
                    # Other non-retryable error
                    error_message = f"Error calling Gemini API: {error_str}"
                    self.update_terminal_console_signal.emit(error_message)
                    self.update_agents_discussion_signal.emit(f"Error: {e}", agent_number, model, True)
                    return f"Error: {e}"
        # Should not reach here, but just in case
        return "Error: Maximum retries exceeded for Gemini API call"

    def call_grok_api(self, model, prompt, agent_number, effective_max_tokens=None):
        """Wrapper for calling the central API execution method for Grok."""
        api_key = self.config_manager.get('GROK_API_KEY')
        if not api_key:
            return "Error: Grok API key not found."
        client = OpenAI(base_url="https://api.x.ai/v1", api_key=api_key)
        settings = settings_manager.get_settings("grok", model)
        return self._execute_api_call("Grok", model, prompt, agent_number, effective_max_tokens, settings, client)

    def call_anthropic_api(self, model, prompt, agent_number, effective_max_tokens=None):
        """Call Anthropic Claude API with streaming support."""
        api_key = self.config_manager.get('ANTHROPIC_API_KEY')
        if not api_key:
            return "Error: Anthropic API key not found."

        from anthropic import Anthropic

        client = Anthropic(api_key=api_key)
        # Get settings for this specific model and provider
        settings = settings_manager.get_settings("anthropic", model)
        # Use streaming_enabled directly from these specific settings
        use_streaming = settings.streaming_enabled if settings else False
        temperature = settings.get('temperature', 0.7) if settings else 0.7
        top_p = settings.get('top_p', 0.9) if settings else 0.9
        if use_streaming:

            try:
                self.update_terminal_console_signal.emit(f"Streaming response from Claude model: {model}")
                with client.messages.stream(
                    model=model,
                    max_tokens=effective_max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    messages=[{"role": "user", "content": prompt}]
                ) as stream:
                    full_response = ""
                    first_chunk = True
                    buffer = ""
                    stream_buffer = "" # For new buffering logic

                    for text in stream.text_stream:
                        # FIX: Update activity time for EVERY chunk received from the stream.
                        self.current_agent_last_activity_time = time.time()
                        if not self.is_running:
                            break
                        stream_buffer += text
                        full_response += text

                        flush_now = False
                        if first_chunk:
                            flush_now = True
                        elif self._should_flush_for_code_integrity(stream_buffer): # Code-aware flushing
                            flush_now = True
                        elif '\n\n' in stream_buffer:
                            flush_now = True
                        elif len(stream_buffer) > 50:
                            flush_now = True
                        
                        if flush_now and stream_buffer:
                            cleaned_chunk_for_display = self.clean_agent_response(stream_buffer)
                            if self.format_response_handler:
                                formatted_html_chunk = self.format_response_handler.format_agent_response(
                                    agent_number, model, cleaned_chunk_for_display, first_chunk
                                )
                                self.update_agents_discussion_signal.emit(formatted_html_chunk, agent_number, model, first_chunk)
                            else:
                                self.update_agents_discussion_signal.emit(cleaned_chunk_for_display, agent_number, model, first_chunk)
                            first_chunk = False
                            stream_buffer = ""

                    # Emit any remaining buffer
                    if stream_buffer:
                        cleaned_buffer = self.clean_agent_response(stream_buffer)
                        if self.format_response_handler:
                            formatted_html_chunk = self.format_response_handler.format_agent_response(
                                agent_number, model, cleaned_buffer, first_chunk
                            )
                            self.update_agents_discussion_signal.emit(formatted_html_chunk, agent_number, model, first_chunk)
                        else:
                            self.update_agents_discussion_signal.emit(cleaned_buffer, agent_number, model, first_chunk)
                self.agent_responses[agent_number] = self.clean_agent_response(full_response)
                return self.agent_responses[agent_number]
            except Exception as e:
                error_message = f"Error in Claude streaming: {str(e)}"
                self.update_terminal_console_signal.emit(error_message)
                self.update_agents_discussion_signal.emit(f"Error: {e}", agent_number, model, True)
                return f"Error: {e}"
        else: # Non-streaming
            try:
                self.update_terminal_console_signal.emit(f"Getting non-streaming response from Claude model: {model}")
                response = client.messages.create(
                    model=model,
                    max_tokens=effective_max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    messages=[{"role": "user", "content": prompt}]
                )
                content = response.content[0].text
                cleaned_content = self.clean_agent_response(content)
                self.agent_responses[agent_number] = cleaned_content
                self.update_agents_discussion_signal.emit(cleaned_content, agent_number, model, True)
                return cleaned_content
            except Exception as e:
                error_message = f"Error in Claude non-streaming: {str(e)}"
                self.update_terminal_console_signal.emit(error_message)
                self.update_agents_discussion_signal.emit(f"Error: {e}", agent_number, model, True)
                return f"Error: {e}"

    def call_groq_api(self, model, prompt, agent_number, effective_max_tokens=None):
        """Wrapper for calling the central API execution method for Groq."""
        api_key = self.config_manager.get('GROQ_API_KEY')
        if not api_key:
            return "Error: Groq API key not found."
        client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key)
        settings = settings_manager.get_settings("groq", model)
        return self._execute_api_call("Groq", model, prompt, agent_number, effective_max_tokens, settings, client)

    def _select_optimal_mcp_server(self, request: str, recommended_servers: List[str]) -> str:
        """
        Select the optimal MCP server from multiple recommendations based on query analysis.
        Args:
            request: The MCP request query
            recommended_servers: List of recommended server names
        Returns:
            The name of the optimal server to use
        """
        if not recommended_servers:
            return ""
        if len(recommended_servers) == 1:
            return recommended_servers[0]
        # Get detailed server information
        enabled_servers = mcp_client.get_enabled_servers()
        server_details = {}
        for server in enabled_servers:
            if server.name in recommended_servers:
                server_details[server.name] = {
                    'capabilities': server.capabilities,
                    'description': server.description,
                    'url': server.url
                }
        # Analyze the request for specific patterns
        request_lower = request.lower()
        # Scoring system for server selection
        server_scores = {}
        for server_name in recommended_servers:
            score = 0
            server_info = server_details.get(server_name, {})
            capabilities = server_info.get('capabilities', [])
            description = server_info.get('description', '').lower()
            # Score based on query type and server capabilities
            # Web search queries
            if any(term in request_lower for term in ["search", "find", "look up", "what is", "who is", "when", "where", "how to"]):
                if any(cap in capabilities for cap in ["web_search", "search"]):
                    score += 10
                if "google" in server_name.lower() or "brave" in server_name.lower():
                    score += 5  # Prefer well-known search engines
            # News and current events
            if any(term in request_lower for term in ["news", "latest", "recent", "today", "current", "breaking"]):
                if any(cap in capabilities for cap in ["news_search", "web_search"]):
                    score += 8
                if "news" in description:
                    score += 3
            # Code and development queries
            if any(term in request_lower for term in ["code", "program", "function", "api", "syntax", "error", "bug", "github"]):
                if any(cap in capabilities for cap in ["repo_access", "code_execution", "pr_review"]):
                    score += 10
                if "github" in server_name.lower() or "code" in description:
                    score += 5
            # Documentation queries
            if any(term in request_lower for term in ["documentation", "docs", "manual", "guide", "tutorial", "how to"]):
                if any(cap in capabilities for cap in ["document_retrieval", "file_access"]):
                    score += 8
                if "context" in server_name.lower() or "docs" in description:
                    score += 5
            # Data and analysis queries
            if any(term in request_lower for term in ["data", "statistics", "chart", "graph", "database", "sql", "analyze"]):
                if any(cap in capabilities for cap in ["sql_execution", "visualization", "schema_inspection"]):
                    score += 10
                if "data" in description or "database" in description:
                    score += 3
            # File and document queries
            if any(term in request_lower for term in ["file", "document", "read", "write", "create", "edit"]):
                if any(cap in capabilities for cap in ["file_access", "file_creation", "document_retrieval"]):
                    score += 8
                if "file" in description or "document" in description:
                    score += 3
            # General information queries (fallback)
            if score == 0:
                if any(cap in capabilities for cap in ["web_search", "general"]):
                    score += 5
                if "general" in description or "search" in description:
                    score += 2
            # Prefer servers with more specific capabilities
            if len(capabilities) > 1:
                score += 1
            # Prefer well-known or reliable servers
            if any(name in server_name.lower() for name in ["google", "github", "brave", "serper"]):
                score += 2
            server_scores[server_name] = score
        # Select the server with the highest score
        if server_scores:
            best_server = max(server_scores.keys(), key=lambda x: server_scores[x])
            self.update_terminal_console_signal.emit(f"Server selection scores: {server_scores}")
            return best_server
        # Fallback to first recommended server
        return recommended_servers[0]