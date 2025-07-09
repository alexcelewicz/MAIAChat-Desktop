# worker.py - Streaming

from PyQt6.QtCore import QObject, pyqtSignal, QMutex, QMutexLocker, Qt
from utils import (google_search, openai_client, genai, groq_client, anthropic_client, grok_client, load_config, groq_rate_limiter, call_deepseek_api)
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
from model_settings import settings_manager

# Import token counter
try:
    from token_counter import token_counter
except ImportError:
    token_counter = None

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
    update_agents_discussion_signal = pyqtSignal(str, int, str, bool) # text_chunk, agent_number, model_name, is_first_chunk
    update_final_answer_signal = pyqtSignal(str)
    update_terminal_console_signal = pyqtSignal(str)
    update_conversation_history_signal = pyqtSignal(list)
    update_conversation_id_signal = pyqtSignal(str)  # New signal for conversation ID updates
    discussion_completed_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    # Add signals for token timing
    token_generation_started_signal = pyqtSignal(float)  # Signal with timestamp when generation starts
    token_generation_ended_signal = pyqtSignal(float, int)  # Signal with timestamp and total output tokens when generation ends


    def __init__(self, prompt, general_instructions, agents, knowledge_base_files,
                 internet_enabled=True, knowledge_base_content="", json_instructions=None,
                 config_manager=None, conversation_history=None, mcp_enabled=False, rag_enabled=False):
        super().__init__()  # Initialize QObject first

        # Initialize instance variables
        self.prompt = prompt
        self.general_instructions = general_instructions
        self.agents = agents
        self.knowledge_base_files = knowledge_base_files
        self.internet_enabled = internet_enabled
        self.knowledge_base_content = knowledge_base_content
        self.json_instructions = json_instructions or {}
        self.config_manager = config_manager
        self.conversation_history = conversation_history or []
        self.is_running = True
        self.mutex = QMutex()

        # Initialize search manager with proper error handling
        self.search_manager = None
        if internet_enabled:
            try:
                self.search_manager = EnhancedSearchManager(config_manager)
                self.update_terminal_console_signal.emit("Internet search initialized successfully")
            except Exception as e:
                self.update_terminal_console_signal.emit(f"Error initializing internet search: {str(e)}")
                logger.error(f"Error initializing internet search: {str(e)}")
                logger.error(traceback.format_exc())

        self.mcp_enabled = mcp_enabled
        self.mcp_context = {}
        self.rag_enabled = rag_enabled

        # Initialize RAG handler with optimized settings
        self.rag_handler = RAGHandler(
            persist_directory="./knowledge_base",
            embedding_model="all-mpnet-base-v2",
            dimension=768,  # Updated dimension for all-mpnet-base-v2
            chunk_size=500,
            chunk_overlap=50,
            chunking_strategy="contextual",  # Use contextual chunking for better context preservation
            cache_dir="./cache"  # Add cache directory for better performance
        )

        # Initialize conversation manager
        self.conversation_manager = ConversationManager()
        self.current_conversation_id = None
        if not conversation_history:
            self.conversation_id = self.conversation_manager.start_new_conversation(
                prompt,
                metadata={
                    "internet_enabled": internet_enabled,
                    "agent_count": len(agents),
                    "knowledge_base_files": knowledge_base_files
                }
            )

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

        # UI update batching
        self.ui_update_buffer = {}
        self.ui_update_interval = 0.1  # seconds
        self.last_ui_update = {}

        # Batch processing
        self.max_workers = min(os.cpu_count() or 4, 8)  # Limit max threads

    @track_performance
    def emit_update(self, signal, content):
        """
        Helper method to safely emit signals with batching support.
        Batches UI updates to reduce overhead and improve performance.
        """
        try:
            # Check if we should batch this update
            if signal == 'update_agents_discussion_signal':
                # For this signal, content is a tuple. We will not batch it.
                if hasattr(self, signal):
                    getattr(self, signal).emit(*content)
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

                # Emit if enough time has passed or buffer is large enough
                if time_since_last_update >= self.ui_update_interval or buffer_size >= 10:
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
            print(f"Error emitting signal {signal}: {str(e)}")

    def stop(self):
        with QMutexLocker(self.mutex):
            self.is_running = False

    def update_worker_configuration(self):
        # Reinitialize search manager with proper error handling
        if self.internet_enabled:
            try:
                self.search_manager = EnhancedSearchManager(self.config_manager)
                self.update_terminal_console_signal.emit("Internet search reinitialized successfully")
            except Exception as e:
                self.update_terminal_console_signal.emit(f"Error reinitializing internet search: {str(e)}")
                logger.error(f"Error reinitializing internet search: {str(e)}")
                logger.error(traceback.format_exc())
                self.search_manager = None
        else:
            self.search_manager = None
            self.update_terminal_console_signal.emit("Internet search disabled")

    def _setup_worker_connections(self):
        if self.worker:
            self.worker.update_agents_discussion_signal.connect(
                self.update_agents_discussion,
                type=Qt.ConnectionType.QueuedConnection
            )
            self.worker.update_final_answer_signal.connect(
                self.update_final_answer,
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

    def get_current_internet_state(self):
        return self.main_window.get_internet_enabled()

    async def process_message(self, message, is_follow_up=False):
        internet_enabled = self.get_current_internet_state()
        for agent in self.agents:
            agent.update_internet_access(internet_enabled)
        return await self.continue_discussion(message, is_follow_up)

    def reset_backoff(self):
        """Reset the backoff delay to initial value"""
        self.current_delay = self.initial_delay

    def clean_agent_response(self, response: str) -> str:
        """Remove unwanted markers like 'Discussion09:22:10' or 'Final Answer09:22:10' from agent responses, even if embedded in text or code."""
        if not response:
            return response
            
        # Remove patterns like 'Discussion09:22:10', 'Final Answer09:22:10', etc., even if embedded
        # This regex matches the pattern with any timestamp format
        cleaned = re.sub(r'(Discussion|Final Answer)\d{1,2}:\d{2}:\d{2}', '', response)
        
        # Also remove patterns where the marker might be embedded in words
        # This handles cases like "HereDiscussion09:22:10's" -> "Here's"
        cleaned = re.sub(r'([a-zA-Z])(Discussion|Final Answer)\d{1,2}:\d{2}:\d{2}', r'\1', cleaned)
        
        # Remove patterns where the marker appears at the end of words
        # This handles cases like "wordDiscussion09:22:10" -> "word"
        cleaned = re.sub(r'(Discussion|Final Answer)\d{1,2}:\d{2}:\d{2}([a-zA-Z])', r'\2', cleaned)
        
        # Remove patterns where the marker appears in the middle of words
        # This handles cases like "wordDiscussion09:22:10word" -> "wordword"
        cleaned = re.sub(r'([a-zA-Z])(Discussion|Final Answer)\d{1,2}:\d{2}:\d{2}([a-zA-Z])', r'\1\3', cleaned)
        
        # Remove any repeated whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Remove stray periods or colons left by marker removal
        cleaned = re.sub(r'([\.:])\s+', r'\1 ', cleaned)
        
        # Remove any remaining isolated timestamps that might be left
        cleaned = re.sub(r'\s+\d{1,2}:\d{2}:\d{2}\s+', ' ', cleaned)
        
        # Remove any remaining isolated "Discussion" or "Final Answer" without timestamps
        cleaned = re.sub(r'\s+(Discussion|Final Answer)\s+', ' ', cleaned)
        
        # NEW: Remove standalone "Discussion" words that appear throughout the text
        # This handles cases like "HereDiscussion's" -> "Here's"
        cleaned = re.sub(r'([a-zA-Z])Discussion([a-zA-Z])', r'\1\2', cleaned)
        
        # Remove "Discussion" at the beginning of words
        cleaned = re.sub(r'Discussion([a-zA-Z])', r'\1', cleaned)
        
        # Remove "Discussion" at the end of words
        cleaned = re.sub(r'([a-zA-Z])Discussion', r'\1', cleaned)
        
        # Remove standalone "Discussion" words (with word boundaries)
        cleaned = re.sub(r'\bDiscussion\b', '', cleaned)
        
        # Remove "Final Answer" at the beginning of words
        cleaned = re.sub(r'Final Answer([a-zA-Z])', r'\1', cleaned)
        
        # Remove "Final Answer" at the end of words
        cleaned = re.sub(r'([a-zA-Z])Final Answer', r'\1', cleaned)
        
        # Remove standalone "Final Answer" words (with word boundaries)
        cleaned = re.sub(r'\bFinal Answer\b', '', cleaned)
        
        # ENHANCED: More aggressive cleaning for embedded "Discussion" in various contexts
        # Handle cases like "textDiscussion." -> "text."
        cleaned = re.sub(r'([a-zA-Z0-9])Discussion([\.:,;!?])', r'\1\2', cleaned)
        
        # Handle cases like "textDiscussion " -> "text "
        cleaned = re.sub(r'([a-zA-Z0-9])Discussion\s+', r'\1 ', cleaned)
        
        # Handle cases like " textDiscussion" -> " text"
        cleaned = re.sub(r'\s+Discussion([a-zA-Z0-9])', r' \1', cleaned)
        
        # Handle cases like "textDiscussion\n" -> "text\n"
        cleaned = re.sub(r'([a-zA-Z0-9])Discussion\n', r'\1\n', cleaned)
        
        # Handle cases like "\ntextDiscussion" -> "\ntext"
        cleaned = re.sub(r'\nDiscussion([a-zA-Z0-9])', r'\n\1', cleaned)
        
        # Handle cases in code blocks where "Discussion" might be embedded
        # This is more aggressive for code contexts
        cleaned = re.sub(r'([a-zA-Z0-9_])Discussion([a-zA-Z0-9_])', r'\1\2', cleaned)
        
        # Handle cases where "Discussion" appears in function names or variables
        cleaned = re.sub(r'([a-zA-Z_])Discussion([a-zA-Z_])', r'\1\2', cleaned)
        
        # Handle cases where "Discussion" appears in strings or comments
        cleaned = re.sub(r'(["\'])[^"\']*Discussion[^"\']*(["\'])', r'\1\2', cleaned)
        
        # ULTRA AGGRESSIVE: Remove any remaining "Discussion" that might be left
        # This handles cases where the word is embedded in various ways
        cleaned = re.sub(r'Discussion', '', cleaned)
        
        # Clean up any double spaces that might have been created
        cleaned = re.sub(r' +', ' ', cleaned)
        
        # Remove any remaining isolated punctuation that might be left
        cleaned = re.sub(r'\s+([\.:,;!?])\s+', r'\1 ', cleaned)
        
        # Final cleanup of any remaining artifacts
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned.strip()

    @track_performance
    def start_agent_discussion(self):
        try:
            # Signal that token generation has started
            self.token_generation_started_signal.emit(time.time())

            # Initialize conversation handling
            if not self.conversation_history and not self.current_conversation_id:
                self.current_conversation_id = self.conversation_manager.start_new_conversation(
                    self.prompt,
                    metadata={
                        "internet_enabled": self.internet_enabled,
                        "agent_count": len(self.agents),
                        "knowledge_base_files": self.knowledge_base_files
                    }
                )
                # Emit signals to update the main window's conversation ID
                self.update_terminal_console_signal.emit(f"Started new conversation with ID: {self.current_conversation_id}")
                self.update_conversation_id_signal.emit(self.current_conversation_id)
            else:
                if self.current_conversation_id:
                    self.conversation_manager.load_conversation(self.current_conversation_id)

            # Add new message to conversation
            self.conversation_manager.add_message(
                self.prompt,
                role="user",
                metadata={"timestamp": datetime.now().isoformat()}
            )

            # Load knowledge base content if available
            if self.knowledge_base_files:
                self.update_terminal_console_signal.emit("Loading knowledge base content...")
                self.knowledge_base_content = self.load_knowledge_base_content()

            # Get full conversation context
            context_window = self.conversation_manager.get_context_window()

            # Initialize search results
            search_results = []
            initial_search_results = ""

            # Perform internet search if enabled
            if self.internet_enabled:
                if self.search_manager:
                    try:
                        self.update_terminal_console_signal.emit("Starting internet search...")
                        search_results = self.search_manager.search(self.prompt)

                        if search_results:
                            self.update_terminal_console_signal.emit("Found relevant sources:")
                            for result in search_results:
                                self.update_terminal_console_signal.emit(f"- {result.url}")

                            # Use the new helper method to format search results
                            initial_search_results = self.format_search_results(search_results, self.prompt)
                        else:
                            self.update_terminal_console_signal.emit("No search results found.")
                    except Exception as e:
                        self.update_terminal_console_signal.emit(f"Search error: {str(e)}")
                        logger.error(f"Internet search error: {str(e)}")
                        logger.error(traceback.format_exc())
                        search_results = []  # Reset on error
                else:
                    self.update_terminal_console_signal.emit("Internet search is enabled but search manager failed to initialize.")

            agent_responses = {}  # Initialize agent responses dictionary
            agent_token_usage = []  # Initialize token usage tracking

            # Process agents sequentially - each agent builds on previous agents' responses
            self.update_terminal_console_signal.emit(f"Processing {len(self.agents)} agents sequentially...")

            for agent in self.agents:
                if not self.is_running:
                    break

                # Get relevant chunks from knowledge base for each agent individually
                agent_knowledge_base_content = self.load_knowledge_base_content()

                agent_number = agent['agent_number']
                model = agent['model']
                instructions = agent['instructions']

                # Include conversation history and previous agent responses in agent input
                agent_input = self.prepare_agent_input(
                    agent_number,
                    instructions,
                    self.prompt,
                    search_results,
                    context_window,
                    agent_responses,  # Pass agent_responses so each agent can see previous agents' responses
                    agent_knowledge_base_content,  # Pass agent-specific knowledge base content
                    self.prepare_mcp_context()  # Add MCP context if enabled
                )

                # Validate and adjust token limits for this agent (now with agent_input)
                token_validation = self._validate_and_adjust_token_limits(agent, agent_number, agent_input)

                try:
                    self.update_terminal_console_signal.emit(f"Agent {agent_number} processing...")
                    # Pass the effective max_tokens to the API call
                    response = self.get_agent_response(
                        agent['provider'], 
                        agent['model'], 
                        agent_input, 
                        agent_number,
                        effective_max_tokens=token_validation['effective_max_tokens']
                    )
                    response = sanitize_response(response)
                    # Use unified formatting instead of separate cleaning
                    response = self._handle_large_response(response, agent_number)  # Handle large responses
                    agent_responses[agent_number] = response  # Store agent's response
                    self.update_terminal_console_signal.emit(f"Agent {agent_number} completed response")
                    
                    # Capture and display actual token usage
                    token_usage = self._capture_agent_token_usage(
                        agent_number, 
                        agent_input, 
                        response, 
                        agent['provider'], 
                        agent['model']
                    )
                    agent_token_usage.append(token_usage)
                    
                except Exception as e:
                    error_msg = f"Error from Agent {agent_number}: {str(e)}"
                    self.update_terminal_console_signal.emit(error_msg)
                    response = f"Error: {str(e)}"
                    agent_responses[agent_number] = response  # Store error response too

                # Update conversation history with proper agent identification
                try:
                    self.conversation_manager.add_message(
                        response,
                        role=f"agent_{agent_number}",
                        metadata={
                            "provider": agent['provider'],
                            "model": agent['model'],
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                except Exception as e:
                    # If adding to conversation fails, log the error but continue
                    self.update_terminal_console_signal.emit(f"Warning: Failed to add Agent {agent_number} response to conversation: {str(e)}")
                    # Try to add a truncated version
                    try:
                        truncated_response = response[:10000] + "\n\n[Response truncated due to conversation storage limitations]"
                        self.conversation_manager.add_message(
                            truncated_response,
                            role=f"agent_{agent_number}",
                            metadata={
                                "provider": agent['provider'],
                                "model": agent['model'],
                                "timestamp": datetime.now().isoformat(),
                                "truncated": True,
                                "original_length": len(response)
                            }
                        )
                    except Exception as truncate_error:
                        self.update_terminal_console_signal.emit(f"Error: Could not add Agent {agent_number} response even with truncation: {str(truncate_error)}")

            # Format and emit the final response (using the last agent's response)
            final_response = agent_responses.get(self.agents[-1]['agent_number'], "")  # Get last agent's response as final
            if final_response:
                # Track tokens for the final answer if token counter is available
                if token_counter and self.current_conversation_id:
                    # Get the last agent's provider and model
                    last_agent = self.agents[-1]
                    provider = last_agent['provider']
                    model = last_agent['model']

                    # Log for debugging
                    logging.debug(f"Tracking tokens for final answer - Provider: {provider}, Model: {model}")

                    # Track tokens for the final answer
                    token_counter.track_tokens(
                        conversation_id=self.current_conversation_id,
                        input_text="",  # No additional input for final answer
                        output_text=final_response,
                        provider=provider,
                        model=model
                    )

                    # Emit signal that token generation has ended
                    # Calculate total output tokens from all agents
                    total_output_tokens = sum(len(response.split()) for response in agent_responses.values())
                    self.token_generation_ended_signal.emit(time.time(), total_output_tokens)

                # Clean the final response before emitting
                # For final answer, we don't want to add agent headers again, just clean the content
                cleaned_final_response = self.clean_agent_response(final_response)
                self.update_final_answer_signal.emit(cleaned_final_response)

            # Display token usage summary
            self._display_token_usage_summary(agent_token_usage)

            self.update_terminal_console_signal.emit("Agent discussion completed.")
            self.discussion_completed_signal.emit()

        except Exception as e:
            self.error_signal.emit(str(e))
            self.discussion_completed_signal.emit()

        finally:
            if not self.is_running:
                self.discussion_completed_signal.emit()

    def _process_agents_in_parallel(self, search_results, context_window):
        """
        Process multiple agents in parallel using concurrent.futures.

        Args:
            search_results: Results from internet search
            context_window: Conversation context

        Returns:
            Dictionary of agent responses
        """
        agent_responses = {}
        agent_knowledge_base_content = self.load_knowledge_base_content()

        # Prepare all agent inputs first
        agent_tasks = []
        for agent in self.agents:
            if not self.is_running:
                break

            agent_number = agent['agent_number']
            instructions = agent['instructions']

            # Include conversation history and previous agent responses in agent input
            agent_input = self.prepare_agent_input(
                agent_number,
                instructions,
                self.prompt,
                search_results,
                context_window,
                agent_responses,  # This will be empty or partial depending on dependencies
                agent_knowledge_base_content,
                self.prepare_mcp_context() if self.mcp_enabled else None  # Add MCP context if enabled
            )

            # Add task to the list
            agent_tasks.append({
                'agent': agent,
                'agent_number': agent_number,
                'agent_input': agent_input
            })

        # Group agents by dependency level (agents that need responses from previous agents)
        # Level 0: Agents that don't depend on other agents' responses
        # Level 1+: Agents that depend on responses from agents in previous levels
        dependency_levels = []
        remaining_tasks = agent_tasks.copy()

        # First level has no dependencies
        current_level = [task for task in remaining_tasks if task['agent_number'] == 1]
        dependency_levels.append(current_level)
        remaining_tasks = [task for task in remaining_tasks if task not in current_level]

        # Process remaining levels based on dependencies
        while remaining_tasks:
            # Next level depends on the previous level
            next_level = []
            for task in remaining_tasks:
                # If all dependencies are satisfied (all previous agents have responses)
                dependencies_satisfied = all(dep_num in agent_responses for dep_num in range(1, task['agent_number']))
                if dependencies_satisfied:
                    next_level.append(task)

            if not next_level:  # If we can't satisfy any more dependencies, break
                break

            dependency_levels.append(next_level)
            remaining_tasks = [task for task in remaining_tasks if task not in next_level]

        # Process each dependency level in sequence, but process agents within each level in parallel
        for level_tasks in dependency_levels:
            if not level_tasks or not self.is_running:
                break

            # Process this level in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks in this level
                future_to_task = {}
                for task in level_tasks:
                    agent = task['agent']
                    agent_number = task['agent_number']
                    agent_input = task['agent_input']

                    # If this agent depends on previous agents, update its input
                    if agent_number > 1:
                        # Update agent input with latest responses
                        agent_input = self.prepare_agent_input(
                            agent_number,
                            agent['instructions'],
                            self.prompt,
                            search_results,
                            context_window,
                            agent_responses,  # Now contains responses from previous levels
                            agent_knowledge_base_content,
                            self.prepare_mcp_context() if self.mcp_enabled else None  # Add MCP context if enabled
                        )

                    # Validate and adjust token limits for this agent
                    token_validation = self._validate_and_adjust_token_limits(agent, agent_number, agent_input)

                    # Submit the task to the executor with effective max_tokens
                    future = executor.submit(
                        self.get_agent_response,
                        agent['provider'],
                        agent['model'],
                        agent_input,
                        agent_number,
                        effective_max_tokens=token_validation['effective_max_tokens']
                    )
                    future_to_task[future] = task

                # Process completed tasks as they finish
                for future in concurrent.futures.as_completed(future_to_task):
                    task = future_to_task[future]
                    agent = task['agent']
                    agent_number = task['agent_number']

                    try:
                        response = future.result()
                        response = sanitize_response(response)
                        response = self._handle_large_response(response, agent_number)  # Handle large responses
                        agent_responses[agent_number] = response

                        # Update conversation history
                        try:
                            self.conversation_manager.add_message(
                                response,
                                role=f"agent_{agent_number}",
                                metadata={
                                    "provider": agent['provider'],
                                    "model": agent['model'],
                                    "timestamp": datetime.now().isoformat()
                                }
                            )
                        except Exception as e:
                            # If adding to conversation fails, log the error but continue
                            self.update_terminal_console_signal.emit(f"Warning: Failed to add Agent {agent_number} response to conversation: {str(e)}")
                            # Try to add a truncated version
                            try:
                                truncated_response = response[:10000] + "\n\n[Response truncated due to conversation storage limitations]"
                                self.conversation_manager.add_message(
                                    truncated_response,
                                    role=f"agent_{agent_number}",
                                    metadata={
                                        "provider": agent['provider'],
                                        "model": agent['model'],
                                        "timestamp": datetime.now().isoformat(),
                                        "truncated": True,
                                        "original_length": len(response)
                                    }
                                )
                            except Exception as truncate_error:
                                self.update_terminal_console_signal.emit(f"Error: Could not add Agent {agent_number} response even with truncation: {str(truncate_error)}")
                    except Exception as e:
                        error_msg = f"Error from Agent {agent_number}: {str(e)}"
                        self.update_terminal_console_signal.emit(error_msg)
                        response = f"Error: {str(e)}"
                        agent_responses[agent_number] = response

                        # Update conversation history with error
                        try:
                            self.conversation_manager.add_message(
                                response,
                                role=f"agent_{agent_number}",
                                metadata={
                                    "provider": agent['provider'],
                                    "model": agent['model'],
                                    "timestamp": datetime.now().isoformat(),
                                    "error": True
                                }
                            )
                        except Exception as add_error:
                            self.update_terminal_console_signal.emit(f"Warning: Failed to add Agent {agent_number} error response to conversation: {str(add_error)}")

        return agent_responses

    def load_knowledge_base_content(self) -> str:
        """Load and process knowledge base files using RAG handler with enhanced features."""
        try:
            # If RAG is disabled or no knowledge base files, return empty string
            if not self.rag_enabled or not self.knowledge_base_files:
                if not self.rag_enabled:
                    self.update_terminal_console_signal.emit("RAG is disabled, skipping knowledge base content")
                return ""

            # Check cache first
            cache_key = hash(tuple(self.knowledge_base_files))
            if cache_key in self.rag_cache:
                cache_entry = self.rag_cache[cache_key]
                if time.time() - cache_entry['timestamp'] < self.rag_cache_ttl:
                    return cache_entry['content']

            # Add files to RAG handler with progress tracking
            total_files = len(self.knowledge_base_files)
            self.update_terminal_console_signal.emit(f"Processing {total_files} files...")
            self.rag_handler.batch_add_files(self.knowledge_base_files)

            # Get relevant chunks with enhanced parameters
            relevant_chunks = self.rag_handler.get_relevant_chunks(
                self.prompt,
                n_results=15,
                alpha=0.5,
                filter_criteria={
                    "importance_score": 0.5,  # Only high importance chunks
                    "language": "en"  # Filter by language if available
                },
                reranking=True,
                cross_encoder_reranking=True,  # Enable cross-encoder reranking
                query_expansion=True  # Enable query expansion
            )

            # Combine relevant chunks with metadata
            combined_content = ""
            for chunk in relevant_chunks:
                metadata = chunk['metadata']
                combined_content += f"\n\nFile: {metadata['file_name']}\n"

                # Add section information if available
                if metadata.get('section_title'):
                    combined_content += f"Section: {metadata['section_title']}\n"

                # Add table information if available
                if metadata.get('is_table'):
                    combined_content += "[Table Content]\n"

                # Add source information
                combined_content += f"Source Type: {metadata.get('source_type', 'unknown')}\n"
                if metadata.get('sheet_name'):
                    combined_content += f"Sheet: {metadata['sheet_name']}\n"

                # Add the actual content
                combined_content += chunk['content']

                # Add context if available
                if metadata.get('context_before'):
                    combined_content += f"\nPrevious Context: {metadata['context_before']}\n"
                if metadata.get('context_after'):
                    combined_content += f"\nFollowing Context: {metadata['context_after']}\n"

                # Add importance score
                combined_content += f"\nImportance Score: {metadata.get('importance_score', 1.0):.2f}\n"

            # Cache the result
            self.rag_cache[cache_key] = {
                'content': combined_content,
                'timestamp': time.time()
            }

            return combined_content

        except Exception as e:
            self.update_terminal_console_signal.emit(f"Error loading knowledge base content: {str(e)}")
            return ""

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
                        "internet_enabled": self.internet_enabled,
                        "agent_count": len(self.agents),
                        "knowledge_base_files": self.knowledge_base_files
                    }
                )

            # Get full conversation context
            context_window = self.conversation_manager.get_context_window()

            # Initialize search results
            search_results = []
            initial_search_results = ""

            # Perform internet search if enabled
            if self.internet_enabled:
                if self.search_manager:
                    try:
                        self.update_terminal_console_signal.emit("Starting internet search...")
                        search_results = self.search_manager.search(new_message)

                        if search_results:
                            self.update_terminal_console_signal.emit("Found relevant sources:")
                            for result in search_results:
                                self.update_terminal_console_signal.emit(f"- {result.url}")

                            # Use the new helper method to format search results
                            initial_search_results = self.format_search_results(search_results, new_message)
                        else:
                            self.update_terminal_console_signal.emit("No search results found.")
                    except Exception as e:
                        self.update_terminal_console_signal.emit(f"Search error: {str(e)}")
                        logger.error(f"Internet search error: {str(e)}")
                        logger.error(traceback.format_exc())
                        search_results = []  # Reset on error
                else:
                    self.update_terminal_console_signal.emit("Internet search is enabled but search manager failed to initialize.")

            agent_responses = {}  # Initialize agent responses dictionary
            agent_token_usage = []  # Initialize token usage tracking

            # Process agents sequentially - each agent builds on previous agents' responses
            self.update_terminal_console_signal.emit(f"Processing {len(self.agents)} agents sequentially...")

            for agent in self.agents:
                if not self.is_running:
                    break

                # Get relevant chunks from knowledge base for each agent individually
                agent_knowledge_base_content = self.load_knowledge_base_content()

                agent_number = agent['agent_number']
                model = agent['model']
                instructions = agent['instructions']

                # Include conversation history and previous agent responses in agent input
                agent_input = self.prepare_agent_input(
                    agent_number,
                    instructions,
                    new_message,
                    search_results,
                    context_window,
                    agent_responses,  # Pass agent_responses so each agent can see previous agents' responses
                    agent_knowledge_base_content,  # Pass agent-specific knowledge base content
                    self.prepare_mcp_context() if self.mcp_enabled else None  # Add MCP context if enabled
                )

                # Validate and adjust token limits for this agent (now with agent_input)
                token_validation = self._validate_and_adjust_token_limits(agent, agent_number, agent_input)

                try:
                    self.update_terminal_console_signal.emit(f"Agent {agent_number} processing...")
                    # Pass the effective max_tokens to the API call
                    response = self.get_agent_response(
                        agent['provider'], 
                        agent['model'], 
                        agent_input, 
                        agent_number,
                        effective_max_tokens=token_validation['effective_max_tokens']
                    )
                    response = sanitize_response(response)
                    # Use unified formatting instead of separate cleaning
                    response = self._handle_large_response(response, agent_number)  # Handle large responses
                    agent_responses[agent_number] = response  # Store agent's response
                    self.update_terminal_console_signal.emit(f"Agent {agent_number} completed response")
                    
                    # Capture and display actual token usage
                    token_usage = self._capture_agent_token_usage(
                        agent_number, 
                        agent_input, 
                        response, 
                        agent['provider'], 
                        agent['model']
                    )
                    agent_token_usage.append(token_usage)
                    
                except Exception as e:
                    error_msg = f"Error from Agent {agent_number}: {str(e)}"
                    self.update_terminal_console_signal.emit(error_msg)
                    response = f"Error: {str(e)}"
                    agent_responses[agent_number] = response  # Store error response too

                # Add agent's response to conversation history
                try:
                    self.conversation_manager.add_message(
                        response,
                        role=f"agent_{agent_number}",
                        metadata={
                            "provider": agent['provider'],
                            "model": agent['model'],
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                    )
                except Exception as e:
                    # If adding to conversation fails, log the error but continue
                    self.update_terminal_console_signal.emit(f"Warning: Failed to add Agent {agent_number} response to conversation: {str(e)}")
                    # Try to add a truncated version
                    try:
                        truncated_response = response[:10000] + "\n\n[Response truncated due to conversation storage limitations]"
                        self.conversation_manager.add_message(
                            truncated_response,
                            role=f"agent_{agent_number}",
                            metadata={
                                "provider": agent['provider'],
                                "model": agent['model'],
                                "timestamp": datetime.now().isoformat(),
                                "truncated": True,
                                "original_length": len(response)
                            }
                        )
                    except Exception as truncate_error:
                        self.update_terminal_console_signal.emit(f"Error: Could not add Agent {agent_number} response even with truncation: {str(truncate_error)}")

            # Update final answer using the last agent's response
            final_response = agent_responses.get(self.agents[-1]['agent_number'], "")  # Get last agent's response as final
            if final_response:
                # Track tokens for the final answer if token counter is available
                if token_counter and self.current_conversation_id:
                    # Get the last agent's provider and model
                    last_agent = self.agents[-1]
                    provider = last_agent['provider']
                    model = last_agent['model']

                    # Log for debugging
                    logging.debug(f"Tracking tokens for final answer - Provider: {provider}, Model: {model}")

                    # Track tokens for the final answer
                    token_counter.track_tokens(
                        conversation_id=self.current_conversation_id,
                        input_text="",  # No additional input for final answer
                        output_text=final_response,
                        provider=provider,
                        model=model
                    )

                # Clean the final response before emitting
                # For final answer, we don't want to add agent headers again, just clean the content
                cleaned_final_response = self.clean_agent_response(final_response)
                self.update_final_answer_signal.emit(cleaned_final_response)

            # Display token usage summary
            self._display_token_usage_summary(agent_token_usage)

            self.update_terminal_console_signal.emit("Agent discussion completed.")
            self.discussion_completed_signal.emit()

        except Exception as e:
            self.error_signal.emit(str(e))
            self.discussion_completed_signal.emit()
        finally:
            if not self.is_running:
                self.discussion_completed_signal.emit()

    def prepare_agent_input(self, agent_number: int, instructions: str, new_message: str, search_results: str, context_window: str, agent_responses: Dict[int, str] = None, agent_knowledge_base_content: str = None, mcp_context: Dict = None) -> str:
        # Format context to clearly show previous agent responses
        formatted_context = ""
        if context_window:
            # Access messages from current conversation
            if hasattr(self.conversation_manager, 'current_conversation') and \
            isinstance(self.conversation_manager.current_conversation, dict) and \
            'messages' in self.conversation_manager.current_conversation:

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
                        assistant_messages.append((timestamp, f"Final Answer:\n{content}\n\n"))

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

        # Format previous agent responses
        formatted_agent_responses = ""
        if agent_responses:
            formatted_agent_responses = "=== PREVIOUS AGENT RESPONSES ===\n"
            for prev_agent_num, prev_response in agent_responses.items():
                if prev_agent_num < agent_number:  # Only include responses from agents before current agent
                    formatted_agent_responses += f"Agent {prev_agent_num} Response:\n{prev_response}\n\n"

        # Format search results in a more structured way
        formatted_search_results = ""
        if isinstance(search_results, list):
            # Use the new helper method to format search results
            formatted_search_results = self.format_search_results(search_results, new_message)
        elif isinstance(search_results, str) and search_results.strip():
            formatted_search_results = search_results

        # Get optimized RAG content with better integration if RAG is enabled
        optimized_kb_content = ""
        if self.rag_enabled:
            kb_content = agent_knowledge_base_content if agent_knowledge_base_content else self.knowledge_base_content
            if kb_content:
                optimized_kb_content = self.conversation_manager.optimize_rag_content(
                    kb_content,
                    max_tokens=4096  # Reduced from 8192 to leave more room for other context
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
10. **Focus on adding value and building upon the collective responses to provide a comprehensive and accurate final answer.**
        """

        # If MCP context is not provided but MCP is enabled, prepare it
        if mcp_context is None and self.mcp_enabled:
            mcp_context = self.prepare_mcp_context()

        # Format MCP context if available
        formatted_mcp_context = ""
        formatted_mcp_instructions = ""
        if mcp_context and self.mcp_enabled:
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

        # Add knowledge base content if RAG is enabled
        if self.rag_enabled and optimized_kb_content:
            sections.append(("KNOWLEDGE BASE CONTENT", optimized_kb_content))

        # Add MCP context if enabled
        if self.mcp_enabled and formatted_mcp_context:
            sections.append(("MCP CONTEXT", formatted_mcp_context))

        # Add MCP instructions if enabled
        if self.mcp_enabled:
            sections.append(("MCP USAGE INSTRUCTIONS", formatted_mcp_instructions))

        # Add internet instructions if enabled
        if self.internet_enabled:
            sections.append(("INTERNET USAGE", internet_instructions))

        # Add RAG instructions if enabled
        if self.rag_enabled and optimized_kb_content:
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





    def format_conversation_history(self):
        return "\n\n".join(self.conversation_history)

    def prepare_mcp_context(self):
        """Prepare MCP context for agent input.

        Returns:
            Dict: MCP context information or empty dict if MCP is disabled
        """
        if not self.mcp_enabled:
            return {}

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

            self.mcp_context = mcp_context
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
        # Exit early if internet is disabled globally
        if not self.internet_enabled:
            return response.replace("[SEARCH:", "[SEARCH DISABLED:")

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

        # Process MCP requests if enabled
        # Note: Most MCP requests should already be processed in get_agent_response,
        # but this handles any that might have been added after that
        if self.mcp_enabled and "[MCP:" in response:
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
        # Exit early if MCP is disabled
        if not self.mcp_enabled:
            self.update_terminal_console_signal.emit("MCP is disabled. Skipping MCP requests.")
            return (response.replace("[MCP:", "[MCP DISABLED:"), {}) if collect_results else response.replace("[MCP:", "[MCP DISABLED:")

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
                        server_name = recommended_servers[0]  # Use the first recommended server
                        self.update_terminal_console_signal.emit(f"Auto-selected MCP server: {server_name}")
                    else:
                        # No recommendation, use a default server if available
                        enabled_servers = mcp_client.get_enabled_servers()
                        if enabled_servers:
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
            return [self.clean_agent_response(res) for res in mcp_results]
        else:
            return self.clean_agent_response(updated_response)

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
                if provider == "Ollama":
                    response = self.call_ollama_api(model, agent_input, agent_number, thinking_enabled, effective_max_tokens)
                elif provider == "OpenAI":
                    response = self.call_openai_api(model, agent_input, agent_number, effective_max_tokens)
                elif provider == "Google GenAI":
                    response = self.call_gemini_api(model, agent_input, agent_number, effective_max_tokens)
                elif provider == "Anthropic":
                    response = self.call_anthropic_api(model, agent_input, agent_number, effective_max_tokens)
                elif provider == "Groq":
                    response = self.call_groq_api(model, agent_input, agent_number, effective_max_tokens)
                elif provider == "Grok":
                    response = self.call_grok_api(model, agent_input, agent_number, effective_max_tokens)
                elif provider == "DeepSeek":
                    response = self.call_deepseek_api(model, agent_input, agent_number, effective_max_tokens)
                elif provider == "LM Studio":
                    response = self.call_lmstudio_api(model, agent_input, agent_number, effective_max_tokens)
                elif provider == "OpenRouter":
                    response = self.call_openrouter_api(model, agent_input, agent_number, effective_max_tokens)
                else:
                    response = "Unknown provider."

                # Check for MCP requests in the response
                if self.mcp_enabled and "[MCP:" in response:
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

                        follow_up_prompt += "\n\nPlease incorporate these MCP results into your response and provide a final answer."

                        # Make a follow-up call to the model with the MCP results
                        self.update_terminal_console_signal.emit(f"Making follow-up call to {provider}/{model} with MCP results")

                        # Make the follow-up call
                        if provider == "Ollama":
                            follow_up_response = self.call_ollama_api(model, follow_up_prompt, agent_number, thinking_enabled, effective_max_tokens)
                        elif provider == "OpenAI":
                            follow_up_response = self.call_openai_api(model, follow_up_prompt, agent_number, effective_max_tokens)
                        elif provider == "Google GenAI":
                            follow_up_response = self.call_gemini_api(model, follow_up_prompt, agent_number, effective_max_tokens)
                        elif provider == "Anthropic":
                            follow_up_response = self.call_anthropic_api(model, follow_up_prompt, agent_number, effective_max_tokens)
                        elif provider == "Groq":
                            follow_up_response = self.call_groq_api(model, follow_up_prompt, agent_number, effective_max_tokens)
                        elif provider == "Grok":
                            follow_up_response = self.call_grok_api(model, follow_up_prompt, agent_number, effective_max_tokens)
                        elif provider == "DeepSeek":
                            follow_up_response = self.call_deepseek_api(model, follow_up_prompt, agent_number, effective_max_tokens)
                        elif provider == "LM Studio":
                            follow_up_response = self.call_lmstudio_api(model, follow_up_prompt, agent_number, effective_max_tokens)
                        elif provider == "OpenRouter":
                            follow_up_response = self.call_openrouter_api(model, follow_up_prompt, agent_number, effective_max_tokens)

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

    def _extract_content(self, text_edit):
        """Extract both text and images from QTextEdit"""
        doc = text_edit.document()
        content = []
        current_block = doc.begin()

        while current_block.isValid():
            fragment = current_block.begin()
            while fragment.isValid():
                char_format = fragment.charFormat()
                if char_format.background().style() != Qt.BrushStyle.NoBrush:
                    # This fragment contains an image
                    image = QImage(char_format.background().texture())
                    if not image.isNull():
                        # Convert image to base64
                        byte_array = QByteArray()
                        buffer = QBuffer(byte_array)
                        buffer.open(QIODevice.OpenModeFlag.WriteOnly)

                        # Determine format and save
                        if image.save(buffer, "PNG"):
                            img_format = "PNG"
                        elif image.save(buffer, "JPG"):
                            img_format = "JPG"
                        elif image.save(buffer, "JPEG"):
                            img_format = "JPEG"
                        elif image.save(buffer, "GIF"):
                            img_format = "GIF"
                        else:
                            print("Error: Could not determine image format.")
                            fragment = fragment.next()
                            continue

                        img_base64 = base64.b64encode(byte_array.data()).decode()

                        content.append({
                            'type': 'image',
                            'data': img_base64,
                            'format': img_format  # Store the format
                        })
                        print(f"Extracted image in format: {img_format}")  # Debugging print
                    else:
                        print("Error: Could not extract image from QTextEdit.")

                text = fragment.text()
                if text and text != "\u200B":  # Ignore zero-width spaces used for images
                    content.append({
                        'type': 'text',
                        'data': text
                    })

                fragment = fragment.next()
            current_block = current_block.next()

        return content

    def process_prompt(self, prompt_text_edit):
        """Process the prompt including both text and images"""
        content = self._extract_content(prompt_text_edit)

        # Construct message for API
        message = ""
        for item in content:
            if item['type'] == 'text':
                message += item['data']
            elif item['type'] == 'image':
                # Add image reference in markdown format with format
                message += f"\n![Image](data:image/{item['format'].lower()};base64,{item['data']})\n"

        print(f"Processed prompt: {message}")  # Debugging print
        return message

    def call_lmstudio_api(self, model: str, prompt: str, agent_number: int, effective_max_tokens=None) -> str:
        """
        Call the LM Studio local inference server with enhanced error handling.
        """
        try:
            # First check if LM Studio server is running
            health_check_url = "http://localhost:1234/v1/models"
            headers = {"Content-Type": "application/json"}

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
                    
                    if actual_model:
                        self.update_terminal_console_signal.emit(f"Using LM Studio model: {actual_model}")
                    else:
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

            url = "http://localhost:1234/v1/chat/completions"

            # Initialize agent response storage
            if agent_number not in self.agent_responses:
                self.agent_responses[agent_number] = ""

            # Clean up and format the prompt
            cleaned_prompt = prompt
            if isinstance(cleaned_prompt, tuple):
                # Extract the actual message content
                cleaned_prompt = cleaned_prompt[1] if len(cleaned_prompt) > 1 else str(cleaned_prompt)

            # Prepare the messages
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": str(cleaned_prompt)}
            ]

            # Get model settings
            settings = settings_manager.get_settings("LM Studio", actual_model)

            # Prepare the request data
            data = {
                "model": actual_model,
                "messages": messages,
                "temperature": settings.temperature,
                "max_tokens": settings.max_tokens,
                "stream": True,
                "stop": settings.stop_sequences if settings.stop_sequences else None
            }

            self.update_terminal_console_signal.emit(f"Sending request to LM Studio with model: {actual_model}")

            response_text = ""
            first_chunk = True

            with requests.post(url, headers=headers, json=data, stream=True, timeout=60) as response:
                if response.status_code == 404:
                    return "Error: LM Studio endpoint not found. Please ensure the server is properly configured."
                response.raise_for_status()

                # Initialize buffer for small chunks
                buffer = ""
                chunk_count = 0
                first_token_received = False

                for line in response.iter_lines():
                    if line:
                        try:
                            line_text = line.decode('utf-8')
                            if line_text.startswith('data: '):
                                line_text = line_text[6:]  # Remove 'data: ' prefix

                            json_data = json.loads(line_text)
                            if json_data.get("choices") and json_data["choices"][0].get("delta", {}).get("content"):
                                chunk = json_data["choices"][0]["delta"]["content"]
                                response_text += chunk
                                self.agent_responses[agent_number] += chunk

                                # Start timer on first token
                                if not first_token_received:
                                    token_counter.start_generation_timer()
                                    first_token_received = True

                                # Count tokens in this chunk
                                n_tokens = 1
                                try:
                                    n_tokens, _ = token_counter.count_tokens(chunk, actual_model)
                                except Exception:
                                    n_tokens = 1  # fallback
                                token_counter.increment_output_tokens(n_tokens)

                                # Add to buffer
                                buffer += chunk
                                chunk_count += 1

                                # Emit buffer when it's large enough, contains a newline, or after several chunks
                                if first_chunk or chunk_count >= 5 or len(buffer) > 20 or '\n' in buffer:
                                    # Clean the buffered content before formatting
                                    cleaned_buffer = self.clean_agent_response(buffer)
                                    # Format and emit the buffered content
                                    conversation_entry = self.format_agent_response(
                                        agent_number,
                                        actual_model,
                                        cleaned_buffer,
                                        is_first_chunk=first_chunk
                                    )
                                    self.update_agents_discussion_signal.emit(conversation_entry)
                                    first_chunk = False
                                    buffer = ""
                                    chunk_count = 0
                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            self.update_terminal_console_signal.emit(f"Error processing chunk: {str(e)}")
                            continue

                # Emit any remaining buffered content
                if buffer:
                    conversation_entry = self.format_agent_response(
                        agent_number,
                        actual_model,
                        buffer,
                        is_first_chunk=first_chunk
                    )
                    self.update_agents_discussion_signal.emit(conversation_entry)

            if not response_text:
                error_msg = "No response received from LM Studio. Please check if the model is properly loaded and functioning."
                self.update_terminal_console_signal.emit(error_msg)
                return error_msg

            return response_text

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
        """Call the OpenRouter API with streaming support (OpenAI-compatible)"""
        try:
            api_key = self.config_manager.get('OPENROUTER_API_KEY', '')
            if not api_key:
                error_msg = "Error: OpenRouter API key not found. Please add OPENROUTER_API_KEY to your .env file or config.json."
                logger.error(error_msg)
                return error_msg

            # Initialize agent response storage
            if agent_number not in self.agent_responses:
                self.agent_responses[agent_number] = ""

            import openai
            openrouter_client = openai.OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )

            # Get model settings
            settings = settings_manager.get_settings("OpenRouter", model)
            
            # Use effective_max_tokens if provided, otherwise use settings
            max_tokens = effective_max_tokens if effective_max_tokens is not None else settings.max_tokens

            # Use settings for parameters
            response = openrouter_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=settings.temperature,
                max_tokens=max_tokens,  # Use the effective max_tokens
                top_p=settings.top_p,
                stream=True,
                stop=settings.stop_sequences if settings.stop_sequences else None
            )
            first_chunk = True
            for chunk in response:
                if chunk.choices[0].delta.content:
                    # Clean the chunk content before adding to agent responses
                    cleaned_content = self.clean_agent_response(chunk.choices[0].delta.content)
                    self.agent_responses[agent_number] += cleaned_content
                    conversation_entry = self.format_agent_response(
                        agent_number,
                        model,
                        cleaned_content,
                        is_first_chunk=first_chunk
                    )
                    self.update_agents_discussion_signal.emit(conversation_entry)
                    first_chunk = False
            return self.agent_responses[agent_number]
        except Exception as e:
            error_msg = f"OpenRouter API error: {str(e)}"
            self.update_terminal_console_signal.emit(error_msg)
            return f"Error: {str(e)}"

    def _handle_large_response(self, response: str, agent_number: int) -> str:
        """
        Handle large agent responses with size checks and appropriate logging.
        """
        if not response:
            return response
        
        content_length = len(response)
        
        # Check if response is large and log appropriate messages
        if content_length > 100000:  # 100KB threshold
            self.update_terminal_console_signal.emit(f"Large response from Agent {agent_number}: {content_length:,} characters")
        
        if content_length > 500000:  # 500KB threshold
            self.update_terminal_console_signal.emit(f"Very large response from Agent {agent_number}: {content_length:,} characters - this may cause validation issues")
        
        # Check conversation manager validation rules
        if hasattr(self, 'conversation_manager') and self.conversation_manager:
            size_info = self.conversation_manager.check_content_size(response)
            
            if size_info["is_too_large"]:
                if size_info["truncation_needed"]:
                    self.update_terminal_console_signal.emit(f"Agent {agent_number} response will be automatically truncated due to size")
                else:
                    self.update_terminal_console_signal.emit(f"Warning: Agent {agent_number} response exceeds maximum allowed size")
        
        return response

    def _validate_and_adjust_token_limits(self, agent: Dict, agent_number: int, agent_input: str = None) -> Dict[str, Any]:
        """
        Validate and adjust token limits for an agent based on user settings and API limits.
        
        Args:
            agent: Agent configuration dictionary
            agent_number: Agent number for logging
            agent_input: The input prompt for the agent (for dynamic calculation)
            
        Returns:
            Dict with validation results and adjusted token limits
        """
        provider = agent['provider']
        model = agent['model']
        
        # Get model settings
        settings = settings_manager.get_settings(provider, model)
        
        # Check if user has specified a custom max_tokens limit
        user_requested_tokens = None
        if 'max_tokens' in agent and agent['max_tokens']:
            try:
                user_requested_tokens = int(agent['max_tokens'])
            except (ValueError, TypeError):
                self.update_terminal_console_signal.emit(f"Warning: Invalid max_tokens value for Agent {agent_number}, using default")
        
        # Calculate dynamic max_tokens if agent_input is provided
        if agent_input:
            effective_tokens = self._calculate_dynamic_max_tokens(agent_input, provider, user_requested_tokens)
            
            # Log the dynamic calculation with safety margin info
            estimated_input_tokens = len(agent_input) // 4
            if provider == "OpenRouter":
                safe_context_limit = int(40960 * 0.95)  # 38,912 tokens
                self.update_terminal_console_signal.emit(f"Agent {agent_number} input: ~{estimated_input_tokens:,} tokens, safe context limit: {safe_context_limit:,} tokens, available output: {effective_tokens:,} tokens")
            else:
                self.update_terminal_console_signal.emit(f"Agent {agent_number} input: ~{estimated_input_tokens:,} tokens, available output: {effective_tokens:,} tokens")
        else:
            # Fallback to static validation
            validation_result = settings.validate_and_adjust_max_tokens(user_requested_tokens)
            effective_tokens = validation_result["effective_tokens"]
        
        # Log the results
        if user_requested_tokens and user_requested_tokens != effective_tokens:
            if agent_input:
                self.update_terminal_console_signal.emit(f"Agent {agent_number} token limit: Adjusted from {user_requested_tokens:,} to {effective_tokens:,} tokens due to context constraints")
            else:
                self.update_terminal_console_signal.emit(f"Agent {agent_number} token limit: {validation_result['adjustment_reason']}")
        
        # Log the effective token limit
        self.update_terminal_console_signal.emit(f"Agent {agent_number} using {effective_tokens:,} max tokens")
        
        return {
            "settings": settings,
            "effective_max_tokens": effective_tokens,
            "validation_result": {
                "user_requested": user_requested_tokens,
                "effective_tokens": effective_tokens,
                "was_adjusted": user_requested_tokens != effective_tokens if user_requested_tokens else False
            }
        }

    def _calculate_dynamic_max_tokens(self, agent_input: str, provider: str, user_requested_tokens: int = None) -> int:
        """
        Calculate dynamic max_tokens based on available input context and provider limits.
        
        Args:
            agent_input: The input prompt for the agent
            provider: The API provider name
            user_requested_tokens: User-specified token limit
            
        Returns:
            int: The calculated max_tokens value
        """
        # Get provider-specific context limits
        context_limits = {
            "OpenRouter": 40960,  # Total context limit (input + output)
            "OpenAI": 16384,      # Output limit only
            "Anthropic": 32768,   # Output limit only
            "Groq": 16384,        # Output limit only
            "Ollama": 32768,      # Output limit only
            "Google GenAI": 32768, # Output limit only
            "Grok": 32768,        # Output limit only
            "DeepSeek": 32768,    # Output limit only
            "LM Studio": 32768,   # Output limit only
        }
        
        total_context_limit = context_limits.get(provider, 16384)
        
        # Estimate input tokens (rough approximation: 1 token ≈ 4 characters)
        estimated_input_tokens = len(agent_input) // 4
        
        # For providers with total context limits (like OpenRouter)
        if provider == "OpenRouter":
            # Calculate available tokens for output with safety margin
            # Use 95% of the limit to ensure we don't exceed it
            safe_context_limit = int(total_context_limit * 0.95)  # 38,912 tokens
            available_output_tokens = safe_context_limit - estimated_input_tokens
            
            # Ensure we have at least some tokens for output
            if available_output_tokens < 1000:
                available_output_tokens = 1000
            
            # Use the minimum of: user request, available tokens, or provider max
            if user_requested_tokens:
                return min(user_requested_tokens, available_output_tokens, 32768)
            else:
                return min(available_output_tokens, 32768)
        
        # For other providers, use their output limits
        else:
            if user_requested_tokens:
                return min(user_requested_tokens, total_context_limit)
            else:
                return total_context_limit

    def _capture_agent_token_usage(self, agent_number: int, agent_input: str, response: str, provider: str, model: str) -> Dict[str, Any]:
        """
        Capture actual token usage for an agent and display it.
        
        Args:
            agent_number: The agent number
            agent_input: The input prompt sent to the agent
            response: The response received from the agent
            provider: The API provider
            model: The model used
            
        Returns:
            Dict with actual token usage information
        """
        try:
            # Count actual tokens used
            input_tokens, input_precise = token_counter.count_tokens(agent_input, model)
            output_tokens, output_precise = token_counter.count_tokens(response, model)
            total_tokens = input_tokens + output_tokens
            
            # Calculate cost
            cost = token_counter.calculate_cost(input_tokens, output_tokens, provider, model)
            
            # Display actual usage
            precision_note = " (precise)" if input_precise and output_precise else " (estimated)"
            self.update_terminal_console_signal.emit(
                f"Agent {agent_number} actual usage: {input_tokens:,} input + {output_tokens:,} output = {total_tokens:,} total tokens{precision_note} (${cost:.4f})"
            )
            
            return {
                "agent_number": agent_number,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost": cost,
                "is_precise": input_precise and output_precise,
                "provider": provider,
                "model": model
            }
            
        except Exception as e:
            self.update_terminal_console_signal.emit(f"Error capturing token usage for Agent {agent_number}: {str(e)}")
            return {
                "agent_number": agent_number,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "cost": 0.0,
                "is_precise": False,
                "provider": provider,
                "model": model,
                "error": str(e)
            }

    def _display_token_usage_summary(self, agent_token_usage: List[Dict[str, Any]]) -> None:
        """
        Display a summary of total token usage and cost for all agents.
        
        Args:
            agent_token_usage: List of token usage dictionaries for each agent
        """
        if not agent_token_usage:
            return
            
        try:
            # Calculate totals
            total_input_tokens = sum(usage.get('input_tokens', 0) for usage in agent_token_usage)
            total_output_tokens = sum(usage.get('output_tokens', 0) for usage in agent_token_usage)
            total_tokens = sum(usage.get('total_tokens', 0) for usage in agent_token_usage)
            total_cost = sum(usage.get('cost', 0.0) for usage in agent_token_usage)
            
            # Check if all measurements were precise
            all_precise = all(usage.get('is_precise', False) for usage in agent_token_usage)
            precision_note = " (precise)" if all_precise else " (estimated)"
            
            # Display summary
            self.update_terminal_console_signal.emit("")
            self.update_terminal_console_signal.emit("=== TOKEN USAGE SUMMARY ===")
            self.update_terminal_console_signal.emit(f"Total tokens: {total_input_tokens:,} input + {total_output_tokens:,} output = {total_tokens:,} total{precision_note}")
            self.update_terminal_console_signal.emit(f"Total cost: ${total_cost:.4f}")
            self.update_terminal_console_signal.emit("==========================")
            self.update_terminal_console_signal.emit("")
            
        except Exception as e:
            self.update_terminal_console_signal.emit(f"Error displaying token usage summary: {str(e)}")

    def call_deepseek_api(self, model, prompt, agent_number, effective_max_tokens=None):
        """Call the DeepSeek API and handle streaming and non-streaming responses."""
        try:
            self.update_terminal_console_signal.emit(f"Calling DeepSeek API with model: {model}")
            
            # Ensure effective_max_tokens is an integer
            max_tokens = int(effective_max_tokens) if effective_max_tokens is not None else 4096

            # Call the utility function
            response_generator = call_deepseek_api(
                model=model,
                prompt=prompt,
                max_tokens=max_tokens,
                stream=True  # Always stream
            )

            full_response = ""
            first_chunk = True
            buffer = ""
            chunk_count = 0

            for chunk in response_generator:
                if not self.is_running:
                    break
                
                buffer += chunk
                chunk_count += 1
                full_response += chunk
                
                # Emit buffer when it's large enough, contains a newline, or after several chunks
                if first_chunk or chunk_count >= 5 or len(buffer) > 20 or '\n' in buffer:
                    cleaned_buffer = self.clean_agent_response(buffer)
                    self.update_agents_discussion_signal.emit(
                        cleaned_buffer,
                        agent_number,
                        model,
                        first_chunk
                    )
                    first_chunk = False
                    buffer = ""
                    chunk_count = 0

            # Emit any remaining buffer
            if buffer:
                cleaned_buffer = self.clean_agent_response(buffer)
                self.update_agents_discussion_signal.emit(
                    cleaned_buffer,
                    agent_number,
                    model,
                    first_chunk
                )

            self.agent_responses[agent_number] = self.clean_agent_response(full_response)
            return self.agent_responses[agent_number]

        except Exception as e:
            error_message = f"Error calling DeepSeek API: {str(e)}"
            self.update_terminal_console_signal.emit(error_message)
            logger.error(error_message)
            logger.error(traceback.format_exc())
            # Emit error as part of the discussion
            self.update_agents_discussion_signal.emit(
                f"Error: {e}", agent_number, model, True
            )
            return f"Error: {e}"


    def call_ollama_api(self, model: str, prompt: str, agent_number: int, thinking_enabled: bool = False, effective_max_tokens=None) -> str:
        """Calls the Ollama API, supports streaming and non-streaming."""
        self.update_terminal_console_signal.emit(f"Connecting to Ollama with model: {model}")
        
        # Load custom Ollama URL from settings if available
        ollama_base_url = settings_manager.get_ollama_url()
        if not ollama_base_url:
            self.update_terminal_console_signal.emit("Warning: Ollama URL not found in settings. Using default.")
            ollama_base_url = "http://localhost:11434" # Default URL
        
        try:
            client = OpenAI(base_url=f"{ollama_base_url}/v1", api_key="ollama")
            
            # Prepare messages for chat completions
            messages = [{"role": "user", "content": prompt}]
            
            # Check if streaming is enabled for this model in settings
            use_streaming = settings_manager.is_streaming_enabled(model, "Ollama")

            if use_streaming:
                self.update_terminal_console_signal.emit("Using streaming response from Ollama...")
                
                response_stream = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    stream=True,
                    max_tokens=effective_max_tokens
                )
                
                full_response = ""
                first_chunk = True
                buffer = ""
                chunk_count = 0

                for chunk in response_stream:
                    if not self.is_running:
                        break
                    
                    content = chunk.choices[0].delta.content
                    if content:
                        buffer += content
                        chunk_count += 1
                        full_response += content

                        if first_chunk or chunk_count >= 5 or len(buffer) > 20 or '\n' in buffer:
                            cleaned_buffer = self.clean_agent_response(buffer)
                            self.update_agents_discussion_signal.emit(
                                cleaned_buffer,
                                agent_number,
                                model,
                                first_chunk
                            )
                            first_chunk = False
                            buffer = ""
                            chunk_count = 0
                
                # Emit any remaining buffer
                if buffer:
                    cleaned_buffer = self.clean_agent_response(buffer)
                    self.update_agents_discussion_signal.emit(
                        cleaned_buffer,
                        agent_number,
                        model,
                        first_chunk
                    )
                
                self.agent_responses[agent_number] = self.clean_agent_response(full_response)
                return self.agent_responses[agent_number]

            else: # Non-streaming
                self.update_terminal_console_signal.emit("Using non-streaming response from Ollama...")
                completion = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    stream=False,
                    max_tokens=effective_max_tokens
                )
                
                content = completion.choices[0].message.content
                self.agent_responses[agent_number] = self.clean_agent_response(content)
                
                # Emit the full response at once
                self.update_agents_discussion_signal.emit(
                    self.agent_responses[agent_number],
                    agent_number,
                    model,
                    True # It's the first and only chunk
                )
                
                return self.agent_responses[agent_number]

        except Exception as e:
            error_message = f"Error calling Ollama API: {e}"
            self.update_terminal_console_signal.emit(error_message)
            logger.error(error_message)
            logger.error(traceback.format_exc())
            self.update_agents_discussion_signal.emit(
                f"Error: {e}", agent_number, model, True
            )
            return f"Error: {e}"


    def call_openai_api(self, model, prompt, agent_number, effective_max_tokens=None):
        """Call OpenAI API, supporting streaming."""
        use_streaming = settings_manager.is_streaming_enabled(model, "OpenAI")
        
        if use_streaming:
            try:
                self.update_terminal_console_signal.emit(f"Streaming response from OpenAI model: {model}")
                stream = openai_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    stream=True,
                    max_tokens=effective_max_tokens
                )
                
                full_response = ""
                first_chunk = True
                buffer = ""
                chunk_count = 0

                for chunk in stream:
                    if not self.is_running:
                        break
                    
                    content = chunk.choices[0].delta.content
                    if content:
                        buffer += content
                        chunk_count += 1
                        full_response += content

                        if first_chunk or chunk_count >= 5 or len(buffer) > 20 or '\n' in buffer:
                            cleaned_buffer = self.clean_agent_response(buffer)
                            self.update_agents_discussion_signal.emit(
                                cleaned_buffer,
                                agent_number,
                                model,
                                first_chunk
                            )
                            first_chunk = False
                            buffer = ""
                            chunk_count = 0
                
                # Emit any remaining buffer
                if buffer:
                    cleaned_buffer = self.clean_agent_response(buffer)
                    self.update_agents_discussion_signal.emit(
                        cleaned_buffer,
                        agent_number,
                        model,
                        first_chunk
                    )
                
                self.agent_responses[agent_number] = self.clean_agent_response(full_response)
                return self.agent_responses[agent_number]
            
            except Exception as e:
                error_message = f"Error in OpenAI streaming: {str(e)}"
                self.update_terminal_console_signal.emit(error_message)
                self.update_agents_discussion_signal.emit(f"Error: {e}", agent_number, model, True)
                return f"Error: {e}"
        
        else: # Non-streaming
            try:
                self.update_terminal_console_signal.emit(f"Getting non-streaming response from OpenAI model: {model}")
                response = openai_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=effective_max_tokens
                )
                
                content = response.choices[0].message.content
                cleaned_content = self.clean_agent_response(content)
                self.agent_responses[agent_number] = cleaned_content
                
                self.update_agents_discussion_signal.emit(cleaned_content, agent_number, model, True)
                return cleaned_content
            
            except Exception as e:
                error_message = f"Error in OpenAI non-streaming: {str(e)}"
                self.update_terminal_console_signal.emit(error_message)
                self.update_agents_discussion_signal.emit(f"Error: {e}", agent_number, model, True)
                return f"Error: {e}"

    def call_gemini_api(self, model, prompt, agent_number, effective_max_tokens=None):
        """Call Gemini API, supporting streaming."""
        use_streaming = settings_manager.is_streaming_enabled(model, "Google GenAI")
        
        try:
            gemini_model = genai.GenerativeModel(model)
            
            if use_streaming:
                self.update_terminal_console_signal.emit(f"Streaming response from Gemini model: {model}")
                responses = gemini_model.generate_content(prompt, stream=True)
                
                full_response = ""
                first_chunk = True
                buffer = ""
                chunk_count = 0

                for response in responses:
                    if not self.is_running:
                        break
                    
                    if response.text:
                        buffer += response.text
                        chunk_count += 1
                        full_response += response.text

                        if first_chunk or chunk_count >= 5 or len(buffer) > 20 or '\n' in buffer:
                            cleaned_buffer = self.clean_agent_response(buffer)
                            self.update_agents_discussion_signal.emit(
                                cleaned_buffer,
                                agent_number,
                                model,
                                first_chunk
                            )
                            first_chunk = False
                            buffer = ""
                            chunk_count = 0
                
                # Emit any remaining buffer
                if buffer:
                    cleaned_buffer = self.clean_agent_response(buffer)
                    self.update_agents_discussion_signal.emit(
                        cleaned_buffer,
                        agent_number,
                        model,
                        first_chunk
                    )
                
                self.agent_responses[agent_number] = self.clean_agent_response(full_response)
                return self.agent_responses[agent_number]
            
            else: # Non-streaming
                self.update_terminal_console_signal.emit(f"Getting non-streaming response from Gemini model: {model}")
                response = gemini_model.generate_content(prompt)
                
                content = response.text
                cleaned_content = self.clean_agent_response(content)
                self.agent_responses[agent_number] = cleaned_content
                
                self.update_agents_discussion_signal.emit(cleaned_content, agent_number, model, True)
                return cleaned_content
        
        except Exception as e:
            error_message = f"Error calling Gemini API: {str(e)}"
            self.update_terminal_console_signal.emit(error_message)
            self.update_agents_discussion_signal.emit(f"Error: {e}", agent_number, model, True)
            return f"Error: {e}"

    def call_grok_api(self, model, prompt, agent_number, effective_max_tokens=None):
        """Call Grok API, supporting streaming."""
        use_streaming = settings_manager.is_streaming_enabled(model, "Grok")
        
        try:
            if use_streaming:
                self.update_terminal_console_signal.emit(f"Streaming response from Grok model: {model}")
                stream = grok_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    stream=True,
                    max_tokens=effective_max_tokens
                )
                
                full_response = ""
                first_chunk = True
                buffer = ""
                chunk_count = 0

                for chunk in stream:
                    if not self.is_running:
                        break
                    
                    content = chunk.choices[0].delta.content
                    if content:
                        buffer += content
                        chunk_count += 1
                        full_response += content

                        if first_chunk or chunk_count >= 5 or len(buffer) > 20 or '\n' in buffer:
                            cleaned_buffer = self.clean_agent_response(buffer)
                            self.update_agents_discussion_signal.emit(
                                cleaned_buffer,
                                agent_number,
                                model,
                                first_chunk
                            )
                            first_chunk = False
                            buffer = ""
                            chunk_count = 0
                
                # Emit any remaining buffer
                if buffer:
                    cleaned_buffer = self.clean_agent_response(buffer)
                    self.update_agents_discussion_signal.emit(
                        cleaned_buffer,
                        agent_number,
                        model,
                        first_chunk
                    )
                
                self.agent_responses[agent_number] = self.clean_agent_response(full_response)
                return self.agent_responses[agent_number]

            else: # Non-streaming
                self.update_terminal_console_signal.emit(f"Getting non-streaming response from Grok model: {model}")
                response = grok_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=effective_max_tokens
                )
                
                content = response.choices[0].message.content
                cleaned_content = self.clean_agent_response(content)
                self.agent_responses[agent_number] = cleaned_content
                
                self.update_agents_discussion_signal.emit(cleaned_content, agent_number, model, True)
                return cleaned_content
        
        except Exception as e:
            error_message = f"Error calling Grok API: {str(e)}"
            self.update_terminal_console_signal.emit(error_message)
            self.update_agents_discussion_signal.emit(f"Error: {e}", agent_number, model, True)
            return f"Error: {e}"

    def call_anthropic_api(self, model, prompt, agent_number, effective_max_tokens=None):
        """Call Anthropic API, supporting streaming."""
        use_streaming = settings_manager.is_streaming_enabled(model, "Anthropic")
        
        try:
            if use_streaming:
                self.update_terminal_console_signal.emit(f"Streaming response from Anthropic model: {model}")
                with anthropic_client.messages.stream(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=effective_max_tokens or 4096
                ) as stream:
                    full_response = ""
                    first_chunk = True
                    buffer = ""
                    chunk_count = 0

                    for text in stream.text_stream:
                        if not self.is_running:
                            break
                        
                        buffer += text
                        chunk_count += 1
                        full_response += text

                        if first_chunk or chunk_count >= 5 or len(buffer) > 20 or '\n' in buffer:
                            cleaned_buffer = self.clean_agent_response(buffer)
                            self.update_agents_discussion_signal.emit(
                                cleaned_buffer,
                                agent_number,
                                model,
                                first_chunk
                            )
                            first_chunk = False
                            buffer = ""
                            chunk_count = 0
                    
                    # Emit any remaining buffer
                    if buffer:
                        cleaned_buffer = self.clean_agent_response(buffer)
                        self.update_agents_discussion_signal.emit(
                            cleaned_buffer,
                            agent_number,
                            model,
                            first_chunk
                        )
                
                self.agent_responses[agent_number] = self.clean_agent_response(full_response)
                return self.agent_responses[agent_number]
            
            else: # Non-streaming
                self.update_terminal_console_signal.emit(f"Getting non-streaming response from Anthropic model: {model}")
                response = anthropic_client.messages.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=effective_max_tokens or 4096
                )
                
                content = response.content[0].text
                cleaned_content = self.clean_agent_response(content)
                self.agent_responses[agent_number] = cleaned_content
                
                self.update_agents_discussion_signal.emit(cleaned_content, agent_number, model, True)
                return cleaned_content

        except Exception as e:
            error_message = f"Error calling Anthropic API: {str(e)}"
            self.update_terminal_console_signal.emit(error_message)
            self.update_agents_discussion_signal.emit(f"Error: {e}", agent_number, model, True)
            return f"Error: {e}"

    def call_groq_api(self, model, prompt, agent_number, effective_max_tokens=None):
        """Call Groq API, supporting streaming."""
        use_streaming = settings_manager.is_streaming_enabled(model, "Groq")
        
        try:
            with groq_rate_limiter:
                if use_streaming:
                    self.update_terminal_console_signal.emit(f"Streaming response from Groq model: {model}")
                    stream = groq_client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        stream=True,
                        max_tokens=effective_max_tokens
                    )
                    
                    full_response = ""
                    first_chunk = True
                    buffer = ""
                    chunk_count = 0

                    for chunk in stream:
                        if not self.is_running:
                            break
                        
                        content = chunk.choices[0].delta.content
                        if content:
                            buffer += content
                            chunk_count += 1
                            full_response += content

                            if first_chunk or chunk_count >= 5 or len(buffer) > 20 or '\n' in buffer:
                                cleaned_buffer = self.clean_agent_response(buffer)
                                self.update_agents_discussion_signal.emit(
                                    cleaned_buffer,
                                    agent_number,
                                    model,
                                    first_chunk
                                )
                                first_chunk = False
                                buffer = ""
                                chunk_count = 0
                    
                    # Emit any remaining buffer
                    if buffer:
                        cleaned_buffer = self.clean_agent_response(buffer)
                        self.update_agents_discussion_signal.emit(
                            cleaned_buffer,
                            agent_number,
                            model,
                            first_chunk
                        )
                    
                    self.agent_responses[agent_number] = self.clean_agent_response(full_response)
                    return self.agent_responses[agent_number]

                else: # Non-streaming
                    self.update_terminal_console_signal.emit(f"Getting non-streaming response from Groq model: {model}")
                    response = groq_client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=effective_max_tokens
                    )
                    
                    content = response.choices[0].message.content
                    cleaned_content = self.clean_agent_response(content)
                    self.agent_responses[agent_number] = cleaned_content
                    
                    self.update_agents_discussion_signal.emit(cleaned_content, agent_number, model, True)
                    return cleaned_content
        
        except Exception as e:
            error_message = f"Error calling Groq API: {str(e)}"
            self.update_terminal_console_signal.emit(error_message)
            self.update_agents_discussion_signal.emit(f"Error: {e}", agent_number, model, True)
            return f"Error: {e}"

    def __del__(self):
        self.stop()

    def _extract_content(self, text_edit):
        """Extract both text and images from QTextEdit"""
        doc = text_edit.document()
        content = []
        current_block = doc.begin()

        while current_block.isValid():
            fragment = current_block.begin()
            while fragment.isValid():
                char_format = fragment.charFormat()
                if char_format.background().style() != Qt.BrushStyle.NoBrush:
                    # This fragment contains an image
                    image = QImage(char_format.background().texture())
                    if not image.isNull():
                        # Convert image to base64
                        byte_array = QByteArray()
                        buffer = QBuffer(byte_array)
                        buffer.open(QIODevice.OpenModeFlag.WriteOnly)

                        # Determine format and save
                        if image.save(buffer, "PNG"):
                            img_format = "PNG"
                        elif image.save(buffer, "JPG"):
                            img_format = "JPG"
                        elif image.save(buffer, "JPEG"):
                            img_format = "JPEG"
                        elif image.save(buffer, "GIF"):
                            img_format = "GIF"
                        else:
                            print("Error: Could not determine image format.")
                            fragment = fragment.next()
                            continue

                        img_base64 = base64.b64encode(byte_array.data()).decode()

                        content.append({
                            'type': 'image',
                            'data': img_base64,
                            'format': img_format  # Store the format
                        })
                        print(f"Extracted image in format: {img_format}")  # Debugging print
                    else:
                        print("Error: Could not extract image from QTextEdit.")

                text = fragment.text()
                if text and text != "\u200B":  # Ignore zero-width spaces used for images
                    content.append({
                        'type': 'text',
                        'data': text
                    })

                fragment = fragment.next()
            current_block = current_block.next()

        return content

    def process_prompt(self, prompt_text_edit):
        """Process the prompt including both text and images"""
        content = self._extract_content(prompt_text_edit)

        # Construct message for API
        message = ""
        for item in content:
            if item['type'] == 'text':
                message += item['data']
            elif item['type'] == 'image':
                # Add image reference in markdown format with format
                message += f"\n![Image](data:image/{item['format'].lower()};base64,{item['data']})\n"

        print(f"Processed prompt: {message}")  # Debugging print
        return message

    def call_lmstudio_api(self, model: str, prompt: str, agent_number: int, effective_max_tokens=None) -> str:
        """Calls the LM-Studio compatible API, supports streaming and non-streaming."""
        self.update_terminal_console_signal.emit(f"Connecting to LM Studio with model: {model}")

        # Get base URL from settings
        base_url = settings_manager.get_lmstudio_url()
        if not base_url:
            self.update_terminal_console_signal.emit("Warning: LM Studio URL not found in settings. Using default.")
            base_url = "http://localhost:1234/v1" # Default URL

        client = OpenAI(base_url=base_url, api_key="lm-studio")
        messages = [{"role": "user", "content": prompt}]
        use_streaming = settings_manager.is_streaming_enabled(model)

        if use_streaming:
            try:
                self.update_terminal_console_signal.emit("Using streaming response from LM Studio...")
                response_stream = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    stream=True,
                    max_tokens=effective_max_tokens
                )
                
                full_response = ""
                first_chunk = True
                buffer = ""
                chunk_count = 0

                for chunk in response_stream:
                    if not self.is_running:
                        break
                    
                    content = chunk.choices[0].delta.content
                    if content:
                        buffer += content
                        chunk_count += 1
                        full_response += content

                        if first_chunk or chunk_count >= 5 or len(buffer) > 20 or '\n' in buffer:
                            cleaned_buffer = self.clean_agent_response(buffer)
                            self.update_agents_discussion_signal.emit(
                                cleaned_buffer,
                                agent_number,
                                model,
                                first_chunk
                            )
                            first_chunk = False
                            buffer = ""
                            chunk_count = 0
                
                # Emit any remaining buffer
                if buffer:
                    cleaned_buffer = self.clean_agent_response(buffer)
                    self.update_agents_discussion_signal.emit(
                        cleaned_buffer,
                        agent_number,
                        model,
                        first_chunk
                    )
                
                self.agent_responses[agent_number] = self.clean_agent_response(full_response)
                return self.agent_responses[agent_number]

            except Exception as e:
                error_message = f"Error calling LM Studio API (streaming): {str(e)}"
                self.update_terminal_console_signal.emit(error_message)
                self.update_agents_discussion_signal.emit(f"Error: {e}", agent_number, model, True)
                return f"Error: {e}"

        else: # Non-streaming
            try:
                self.update_terminal_console_signal.emit("Using non-streaming response from LM Studio...")
                completion = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    stream=False,
                    max_tokens=effective_max_tokens
                )
                
                content = completion.choices[0].message.content
                cleaned_content = self.clean_agent_response(content)
                self.agent_responses[agent_number] = cleaned_content
                
                self.update_agents_discussion_signal.emit(cleaned_content, agent_number, model, True)
                return cleaned_content
            
            except Exception as e:
                error_message = f"Error calling LM Studio API (non-streaming): {str(e)}"
                self.update_terminal_console_signal.emit(error_message)
                self.update_agents_discussion_signal.emit(f"Error: {e}", agent_number, model, True)
                return f"Error: {e}"

    def call_openrouter_api(self, model, prompt, agent_number, effective_max_tokens=None):
        """Call OpenRouter API, supporting streaming."""
        use_streaming = settings_manager.is_streaming_enabled(model)
        api_key = self.config_manager.get('OPENROUTER_API_KEY')
        if not api_key:
            return "Error: OpenRouter API key not found."

        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

        if use_streaming:
            try:
                self.update_terminal_console_signal.emit(f"Streaming response from OpenRouter model: {model}")
                stream = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    stream=True,
                    max_tokens=effective_max_tokens
                )
                
                full_response = ""
                first_chunk = True
                buffer = ""
                chunk_count = 0

                for chunk in stream:
                    if not self.is_running:
                        break
                    
                    content = chunk.choices[0].delta.content
                    if content:
                        buffer += content
                        chunk_count += 1
                        full_response += content

                        if first_chunk or chunk_count >= 5 or len(buffer) > 20 or '\n' in buffer:
                            cleaned_buffer = self.clean_agent_response(buffer)
                            self.update_agents_discussion_signal.emit(
                                cleaned_buffer,
                                agent_number,
                                model,
                                first_chunk
                            )
                            first_chunk = False
                            buffer = ""
                            chunk_count = 0
                
                # Emit any remaining buffer
                if buffer:
                    cleaned_buffer = self.clean_agent_response(buffer)
                    self.update_agents_discussion_signal.emit(
                        cleaned_buffer,
                        agent_number,
                        model,
                        first_chunk
                    )
                
                self.agent_responses[agent_number] = self.clean_agent_response(full_response)
                return self.agent_responses[agent_number]
            
            except Exception as e:
                error_message = f"Error in OpenRouter streaming: {str(e)}"
                self.update_terminal_console_signal.emit(error_message)
                self.update_agents_discussion_signal.emit(f"Error: {e}", agent_number, model, True)
                return f"Error: {e}"
        
        else: # Non-streaming
            try:
                self.update_terminal_console_signal.emit(f"Getting non-streaming response from OpenRouter model: {model}")
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=effective_max_tokens
                )
                
                content = response.choices[0].message.content
                cleaned_content = self.clean_agent_response(content)
                self.agent_responses[agent_number] = cleaned_content
                
                self.update_agents_discussion_signal.emit(cleaned_content, agent_number, model, True)
                return cleaned_content
            
            except Exception as e:
                error_message = f"Error in OpenRouter non-streaming: {str(e)}"
                self.update_terminal_console_signal.emit(error_message)
                self.update_agents_discussion_signal.emit(f"Error: {e}", agent_number, model, True)
                return f"Error: {e}"

    def _handle_large_response(self, response: str, agent_number: int) -> str:
        """
        Handle large agent responses with size checks and appropriate logging.
        """
        if not response:
            return response
        
        content_length = len(response)
        
        # Check if response is large and log appropriate messages
        if content_length > 100000:  # 100KB threshold
            self.update_terminal_console_signal.emit(f"Large response from Agent {agent_number}: {content_length:,} characters")
        
        if content_length > 500000:  # 500KB threshold
            self.update_terminal_console_signal.emit(f"Very large response from Agent {agent_number}: {content_length:,} characters - this may cause validation issues")
        
        # Check conversation manager validation rules
        if hasattr(self, 'conversation_manager') and self.conversation_manager:
            size_info = self.conversation_manager.check_content_size(response)
            
            if size_info["is_too_large"]:
                if size_info["truncation_needed"]:
                    self.update_terminal_console_signal.emit(f"Agent {agent_number} response will be automatically truncated due to size")
                else:
                    self.update_terminal_console_signal.emit(f"Warning: Agent {agent_number} response exceeds maximum allowed size")
        
        return response

    def _validate_and_adjust_token_limits(self, agent: Dict, agent_number: int, agent_input: str = None) -> Dict[str, Any]:
        """
        Validate and adjust token limits for an agent based on user settings and API limits.
        
        Args:
            agent: Agent configuration dictionary
            agent_number: Agent number for logging
            agent_input: The input prompt for the agent (for dynamic calculation)
            
        Returns:
            Dict with validation results and adjusted token limits
        """
        provider = agent['provider']
        model = agent['model']
        
        # Get model settings
        settings = settings_manager.get_settings(provider, model)
        
        # Check if user has specified a custom max_tokens limit
        user_requested_tokens = None
        if 'max_tokens' in agent and agent['max_tokens']:
            try:
                user_requested_tokens = int(agent['max_tokens'])
            except (ValueError, TypeError):
                self.update_terminal_console_signal.emit(f"Warning: Invalid max_tokens value for Agent {agent_number}, using default")
        
        # Calculate dynamic max_tokens if agent_input is provided
        if agent_input:
            effective_tokens = self._calculate_dynamic_max_tokens(agent_input, provider, user_requested_tokens)
            
            # Log the dynamic calculation with safety margin info
            estimated_input_tokens = len(agent_input) // 4
            if provider == "OpenRouter":
                safe_context_limit = int(40960 * 0.95)  # 38,912 tokens
                self.update_terminal_console_signal.emit(f"Agent {agent_number} input: ~{estimated_input_tokens:,} tokens, safe context limit: {safe_context_limit:,} tokens, available output: {effective_tokens:,} tokens")
            else:
                self.update_terminal_console_signal.emit(f"Agent {agent_number} input: ~{estimated_input_tokens:,} tokens, available output: {effective_tokens:,} tokens")
        else:
            # Fallback to static validation
            validation_result = settings.validate_and_adjust_max_tokens(user_requested_tokens)
            effective_tokens = validation_result["effective_tokens"]
        
        # Log the results
        if user_requested_tokens and user_requested_tokens != effective_tokens:
            if agent_input:
                self.update_terminal_console_signal.emit(f"Agent {agent_number} token limit: Adjusted from {user_requested_tokens:,} to {effective_tokens:,} tokens due to context constraints")
            else:
                self.update_terminal_console_signal.emit(f"Agent {agent_number} token limit: {validation_result['adjustment_reason']}")
        
        # Log the effective token limit
        self.update_terminal_console_signal.emit(f"Agent {agent_number} using {effective_tokens:,} max tokens")
        
        return {
            "settings": settings,
            "effective_max_tokens": effective_tokens,
            "validation_result": {
                "user_requested": user_requested_tokens,
                "effective_tokens": effective_tokens,
                "was_adjusted": user_requested_tokens != effective_tokens if user_requested_tokens else False
            }
        }

    def _calculate_dynamic_max_tokens(self, agent_input: str, provider: str, user_requested_tokens: int = None) -> int:
        """
        Calculate dynamic max_tokens based on available input context and provider limits.
        
        Args:
            agent_input: The input prompt for the agent
            provider: The API provider name
            user_requested_tokens: User-specified token limit
            
        Returns:
            int: The calculated max_tokens value
        """
        # Get provider-specific context limits
        context_limits = {
            "OpenRouter": 40960,  # Total context limit (input + output)
            "OpenAI": 16384,      # Output limit only
            "Anthropic": 32768,   # Output limit only
            "Groq": 16384,        # Output limit only
            "Ollama": 32768,      # Output limit only
            "Google GenAI": 32768, # Output limit only
            "Grok": 32768,        # Output limit only
            "DeepSeek": 32768,    # Output limit only
            "LM Studio": 32768,   # Output limit only
        }
        
        total_context_limit = context_limits.get(provider, 16384)
        
        # Estimate input tokens (rough approximation: 1 token ≈ 4 characters)
        estimated_input_tokens = len(agent_input) // 4
        
        # For providers with total context limits (like OpenRouter)
        if provider == "OpenRouter":
            # Calculate available tokens for output with safety margin
            # Use 95% of the limit to ensure we don't exceed it
            safe_context_limit = int(total_context_limit * 0.95)  # 38,912 tokens
            available_output_tokens = safe_context_limit - estimated_input_tokens
            
            # Ensure we have at least some tokens for output
            if available_output_tokens < 1000:
                available_output_tokens = 1000
            
            # Use the minimum of: user request, available tokens, or provider max
            if user_requested_tokens:
                return min(user_requested_tokens, available_output_tokens, 32768)
            else:
                return min(available_output_tokens, 32768)
        
        # For other providers, use their output limits
        else:
            if user_requested_tokens:
                return min(user_requested_tokens, total_context_limit)
            else:
                return total_context_limit

    def _capture_agent_token_usage(self, agent_number: int, agent_input: str, response: str, provider: str, model: str) -> Dict[str, Any]:
        """
        Capture actual token usage for an agent and display it.
        
        Args:
            agent_number: The agent number
            agent_input: The input prompt sent to the agent
            response: The response received from the agent
            provider: The API provider
            model: The model used
            
        Returns:
            Dict with actual token usage information
        """
        try:
            # Count actual tokens used
            input_tokens, input_precise = token_counter.count_tokens(agent_input, model)
            output_tokens, output_precise = token_counter.count_tokens(response, model)
            total_tokens = input_tokens + output_tokens
            
            # Calculate cost
            cost = token_counter.calculate_cost(input_tokens, output_tokens, provider, model)
            
            # Display actual usage
            precision_note = " (precise)" if input_precise and output_precise else " (estimated)"
            self.update_terminal_console_signal.emit(
                f"Agent {agent_number} actual usage: {input_tokens:,} input + {output_tokens:,} output = {total_tokens:,} total tokens{precision_note} (${cost:.4f})"
            )
            
            return {
                "agent_number": agent_number,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost": cost,
                "is_precise": input_precise and output_precise,
                "provider": provider,
                "model": model
            }
            
        except Exception as e:
            self.update_terminal_console_signal.emit(f"Error capturing token usage for Agent {agent_number}: {str(e)}")
            return {
                "agent_number": agent_number,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "cost": 0.0,
                "is_precise": False,
                "provider": provider,
                "model": model,
                "error": str(e)
            }

    def _display_token_usage_summary(self, agent_token_usage: List[Dict[str, Any]]) -> None:
        """
        Displays a summary of token usage for all agents in the terminal console.
        """
        summary_lines = ["\n--- Token Usage Summary ---"]
        total_input = 0
        total_output = 0
        total_cost = 0.0

        for usage in agent_token_usage:
            agent_num = usage.get('agent_number', 'N/A')
            model = usage.get('model', 'N/A')
            input_tokens = usage.get('input_tokens', 0)
            output_tokens = usage.get('output_tokens', 0)
            cost = usage.get('cost', 0.0)

            total_input += input_tokens
            total_output += output_tokens
            total_cost += cost

            summary_lines.append(
                f"Agent {agent_num} ({model}): "
                f"Input: {input_tokens}, Output: {output_tokens}, Cost: ${cost:.6f}"
            )
        
        summary_lines.append("---------------------------")
        summary_lines.append(f"Total: Input: {total_input}, Output: {total_output}, Cost: ${total_cost:.6f}")
        summary_lines.append("---------------------------\n")

        self.update_terminal_console_signal.emit("\n".join(summary_lines))
