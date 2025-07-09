# conversation_manager.py
import logging
import yaml
import threading
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Union, Callable, Iterator
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import json
import gzip
import shutil

# --- Optional Dependencies ---
try:
    from token_counter import token_counter
except ImportError:
    token_counter = None

try:
    import frontmatter
except ImportError:
    raise ImportError("The 'python-frontmatter' library is required to use the new Markdown format. "
                      "Please install it with: pip install python-frontmatter PyYAML")

try:
    import asyncio
    HAS_ASYNC = True
except ImportError:
    HAS_ASYNC = False

# --- Constants ---
TOKEN_ESTIMATION_FACTOR = 1.3
MESSAGE_SEPARATOR = "\n\n---\n\n"
DEFAULT_WORKING_CONTEXT_SIZE = 24000
MAX_CONVERSATION_CACHE_SIZE = 100
BACKUP_RETENTION_DAYS = 30
COMPRESSION_THRESHOLD_DAYS = 7

@dataclass
class ConversationMetrics:
    """Metrics for conversation performance tracking."""
    message_count: int = 0
    total_tokens: int = 0
    avg_response_time: float = 0.0
    last_activity: Optional[datetime] = None
    file_size_bytes: int = 0
    load_time_ms: float = 0.0

@dataclass
class MessageValidationRule:
    """Rules for validating messages."""
    max_content_length: int = 500000  # Increased from 50000 to handle large agent responses
    max_content_length_warning: int = 100000  # Warning threshold for large content
    allowed_roles: List[str] = field(default_factory=lambda: ['user', 'assistant', 'system', 'agent_1', 'agent_2', 'agent_3', 'agent_4', 'agent_5'])
    required_fields: List[str] = field(default_factory=lambda: ['role', 'content'])
    custom_validator: Optional[Callable[[Dict], bool]] = None
    enable_content_truncation: bool = True  # Enable automatic truncation for extremely large content
    truncation_suffix: str = "\n\n[Content truncated due to size limitations]"  # Suffix for truncated content

class ConversationManager:
    """
    Advanced conversation manager with enhanced features:
    - Thread-safe operations with caching
    - Automatic backup and compression
    - Performance metrics and monitoring
    - Async support for I/O operations
    - Advanced search and filtering
    - Memory optimization for large conversations
    - Comprehensive error handling and recovery
    - Plugin system for extensibility
    """

    def __init__(self, 
                 history_dir: str = "conversation_history",
                 working_context_size: int = DEFAULT_WORKING_CONTEXT_SIZE,
                 enable_compression: bool = True,
                 enable_backup: bool = True,
                 cache_size: int = MAX_CONVERSATION_CACHE_SIZE,
                 validation_rules: Optional[MessageValidationRule] = None,
                 enable_metrics: bool = True):
        """
        Initializes the ConversationManager with enhanced features.

        Args:
            history_dir (str): Directory to store conversation history files
            working_context_size (int): Default maximum tokens for context window
            enable_compression (bool): Enable automatic compression of old conversations
            enable_backup (bool): Enable automatic backup creation
            cache_size (int): Maximum number of conversations to keep in memory
            validation_rules (Optional[MessageValidationRule]): Custom validation rules
            enable_metrics (bool): Enable performance metrics collection
        """
        # Core setup
        self.history_dir = Path(history_dir)
        self.backup_dir = self.history_dir / "backups"
        self.compressed_dir = self.history_dir / "compressed"
        
        # Create directories
        for directory in [self.history_dir, self.backup_dir, self.compressed_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Configuration
        self.working_context_size = working_context_size
        self.enable_compression = enable_compression
        self.enable_backup = enable_backup
        self.enable_metrics = enable_metrics
        self.validation_rules = validation_rules or MessageValidationRule()
        
        # Thread safety
        self._lock = threading.RLock()
        self._file_locks: Dict[str, threading.Lock] = {}
        
        # Caching system
        self._conversation_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_access_times: Dict[str, datetime] = {}
        self._max_cache_size = cache_size
        
        # Performance tracking
        self._metrics: Dict[str, ConversationMetrics] = {}
        self._operation_times: List[Tuple[str, float]] = []
        
        # Current conversation state
        self.current_conversation = self._get_new_conversation_structure()
        
        # Background tasks
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_cleanup = threading.Event()
        
        # Plugin system
        self._plugins: List[Callable] = []
        self._event_handlers: Dict[str, List[Callable]] = {
            'message_added': [],
            'conversation_saved': [],
            'conversation_loaded': [],
        }
        
        # Start background tasks
        self._start_background_tasks()
        
        # Logger setup
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info(f"ConversationManager initialized. History: '{self.history_dir.resolve()}'")
    
    def _get_file_lock(self, conversation_id: str) -> threading.Lock:
        """Get or create a file-specific lock for thread safety."""
        if conversation_id not in self._file_locks:
            self._file_locks[conversation_id] = threading.Lock()
        return self._file_locks[conversation_id]
    
    def _start_background_tasks(self) -> None:
        """Start background maintenance tasks."""
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            return
        
        self._stop_cleanup.clear()
        self._cleanup_thread = threading.Thread(target=self._background_maintenance, daemon=True)
        self._cleanup_thread.start()
    
    def _background_maintenance(self) -> None:
        """Background thread for maintenance tasks."""
        while not self._stop_cleanup.wait(3600):  # Run every hour
            try:
                self._cleanup_cache()
                if self.enable_compression:
                    self._compress_old_conversations()
                if self.enable_backup:
                    self._cleanup_old_backups()
                self._update_metrics()
            except Exception as e:
                self.logger.error(f"Error in background maintenance: {e}")
    
    def _cleanup_cache(self) -> None:
        """Remove least recently used conversations from cache."""
        with self._lock:
            if len(self._conversation_cache) <= self._max_cache_size:
                return
            
            # Sort by access time and remove oldest
            sorted_by_access = sorted(
                self._cache_access_times.items(),
                key=lambda x: x[1]
            )
            
            to_remove = len(self._conversation_cache) - self._max_cache_size
            for conv_id, _ in sorted_by_access[:to_remove]:
                self._conversation_cache.pop(conv_id, None)
                self._cache_access_times.pop(conv_id, None)
    
    def _compress_old_conversations(self) -> None:
        """Compress conversations older than threshold."""
        threshold_date = datetime.now() - timedelta(days=COMPRESSION_THRESHOLD_DAYS)
        
        for file_path in self.history_dir.glob("conversation_*.md"):
            try:
                if file_path.stat().st_mtime < threshold_date.timestamp():
                    compressed_path = self.compressed_dir / f"{file_path.stem}.md.gz"
                    
                    if not compressed_path.exists():
                        with open(file_path, 'rb') as f_in:
                            with gzip.open(compressed_path, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        
                        file_path.unlink()  # Remove original
                        self.logger.info(f"Compressed conversation: {file_path.stem}")
            except Exception as e:
                self.logger.error(f"Error compressing {file_path}: {e}")
    
    def _cleanup_old_backups(self) -> None:
        """Remove backups older than retention period."""
        cutoff_date = datetime.now() - timedelta(days=BACKUP_RETENTION_DAYS)
        
        for backup_file in self.backup_dir.glob("*.md"):
            try:
                if datetime.fromtimestamp(backup_file.stat().st_mtime) < cutoff_date:
                    backup_file.unlink()
                    self.logger.debug(f"Removed old backup: {backup_file.name}")
            except Exception as e:
                self.logger.error(f"Error removing backup {backup_file}: {e}")
    
    def _update_metrics(self) -> None:
        """Update performance metrics for all conversations."""
        if not self.enable_metrics:
            return
        
        for file_path in self.history_dir.glob("conversation_*.md"):
            try:
                conv_id = file_path.stem.replace("conversation_", "")
                if conv_id not in self._metrics:
                    self._metrics[conv_id] = ConversationMetrics()
                
                stat = file_path.stat()
                self._metrics[conv_id].file_size_bytes = stat.st_size
                self._metrics[conv_id].last_activity = datetime.fromtimestamp(stat.st_mtime)
                
            except Exception as e:
                self.logger.error(f"Error updating metrics for {file_path}: {e}")
    
    def _get_new_conversation_structure(self) -> Dict[str, Any]:
        """Returns a dictionary representing a new, empty conversation."""
        return {
            "id": None,
            "timestamp": None,
            "messages": [],
            "metadata": {},
            "token_usage": {
                "input_tokens": 0, "system_tokens": 0, "output_tokens": 0,
                "total_tokens": 0, "estimated_cost": 0.0,
            },
            "performance": {
                "message_count": 0,
                "avg_response_time": 0.0,
                "total_processing_time": 0.0,
            }
        }
    
    @staticmethod
    def _truncate_content_if_needed(content: str, max_length: int, suffix: str) -> Tuple[str, bool]:
        """Helper to truncate content and indicate if truncation occurred."""
        if len(content) > max_length:
            actual_max_len = max_length - len(suffix)
            truncated_content = content[:actual_max_len] + suffix
            return truncated_content, True # True means content was truncated
        return content, False

    def _validate_message(self, content: str, role: str, metadata: Optional[Dict] = None) -> Tuple[bool, str]:
        """
        Validate message against defined rules.
        Returns a tuple: (is_valid: bool, processed_content: str)
        processed_content might be truncated if validation passed but content was too long.
        """
        # Basic validation
        if not content or not content.strip():
            self.logger.warning("Empty message content")
            return False, content # Return original content even on failure
        
        if role not in self.validation_rules.allowed_roles:
            self.logger.warning(f"Invalid role: {role}")
            return False, content

        # Handle large content with truncation
        content_length = len(content)
        
        if content_length > self.validation_rules.max_content_length_warning:
            self.logger.warning(f"Large message content detected: {content_length} chars for role '{role}'")
        
        processed_content = content
        if content_length > self.validation_rules.max_content_length:
            if self.validation_rules.enable_content_truncation:
                max_len = self.validation_rules.max_content_length
                suffix = self.validation_rules.truncation_suffix
                processed_content, truncated = self._truncate_content_if_needed(content, max_len, suffix)
                if truncated:
                    self.logger.warning(f"Message content truncated from {content_length} to {len(processed_content)} chars for role '{role}'")
                # Validation passes, but content is modified (truncated)
            else:
                self.logger.error(f"Message content too long: {content_length} chars (max: {self.validation_rules.max_content_length})")
                return False, content # Validation fails
        
        # Custom validation (using processed_content)
        if self.validation_rules.custom_validator:
            message_dict = {
                "content": processed_content, # Validate with potentially truncated content
                "role": role,
                "metadata": metadata or {}
            }
            if not self.validation_rules.custom_validator(message_dict):
                self.logger.warning("Custom validation failed")
                return False, content # Return original content on custom validation failure
        
        return True, processed_content # Validation passed, return (potentially modified) content
    
    def _trigger_event(self, event_name: str, *args, **kwargs) -> None:
        """Trigger event handlers."""
        handlers = self._event_handlers.get(event_name, [])
        for handler in handlers:
            try:
                handler(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Error in event handler for {event_name}: {e}")
    
    def add_event_handler(self, event_name: str, handler: Callable) -> None:
        """Add an event handler."""
        if event_name not in self._event_handlers:
            self._event_handlers[event_name] = []
        self._event_handlers[event_name].append(handler)
    
    def remove_event_handler(self, event_name: str, handler: Callable) -> None:
        """Remove an event handler."""
        if event_name in self._event_handlers:
            try:
                self._event_handlers[event_name].remove(handler)
            except ValueError:
                pass
    
    def start_new_conversation(self, initial_prompt: str, metadata: Optional[Dict] = None) -> str:
        """
        Starts a new conversation with enhanced features and validation.
        """
        is_valid, _ = self._validate_message(initial_prompt, "user")
        if not is_valid:
            raise ValueError("Invalid initial prompt")
        
        with self._lock:
            conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:17]  # Include microseconds
            
            # Ensure unique ID
            counter = 1
            original_id = conversation_id
            while self._conversation_file_exists(conversation_id):
                conversation_id = f"{original_id}_{counter}"
                counter += 1
            
            self.current_conversation = self._get_new_conversation_structure()
            self.current_conversation.update({
                "id": conversation_id,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {},
            })
            
            # Create backup if enabled
            if self.enable_backup:
                self._create_backup(conversation_id)
            
            self.add_message(initial_prompt, "user")
            
            # Initialize metrics
            if self.enable_metrics:
                self._metrics[conversation_id] = ConversationMetrics(
                    message_count=1,
                    last_activity=datetime.now()
                )
            
            self.logger.info(f"Started new conversation: {conversation_id}")
            return conversation_id
    
    def _conversation_file_exists(self, conversation_id: str) -> bool:
        """Check if conversation file exists (including compressed)."""
        regular_path = self.history_dir / f"conversation_{conversation_id}.md"
        compressed_path = self.compressed_dir / f"conversation_{conversation_id}.md.gz"
        return regular_path.exists() or compressed_path.exists()
    
    def _create_backup(self, conversation_id: str) -> None:
        """Create a backup of the conversation."""
        try:
            source_path = self.history_dir / f"conversation_{conversation_id}.md"
            if source_path.exists():
                backup_path = self.backup_dir / f"conversation_{conversation_id}_{int(time.time())}.md"
                shutil.copy2(source_path, backup_path)
        except Exception as e:
            self.logger.error(f"Failed to create backup for {conversation_id}: {e}")
    
    def add_message(self, content: str, role: str, metadata: Optional[Dict] = None) -> None:
        """
        Adds a message to the current conversation with enhanced validation and processing.
        """
        # Validate the message and get processed (potentially truncated) content
        is_valid, processed_content = self._validate_message(content, role, metadata)
        
        if not is_valid:
            # If validation failed entirely (not just truncation), raise an error.
            # The _validate_message method now handles logging the specific reason.
            raise ValueError(f"Message validation failed for role '{role}'. Check logs for details.")
        
        # If validation passed, processed_content is either original or truncated. Use it.
        content_to_add = processed_content
        
        if not self.current_conversation.get("id"):
            raise ValueError("Cannot add message. No active conversation.")
        
        start_time = time.time()
        
        with self._lock:
            message = {
                "role": role,
                "content": content_to_add, # Use the processed content
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {},
                "id": hashlib.md5(f"{content_to_add}{role}{time.time()}".encode()).hexdigest()[:8]
            }
            
            message["metadata"]["content_length"] = len(content_to_add)
            if len(content_to_add) != len(content): # Original content was modified (truncated)
                message["metadata"]["original_content_length"] = len(content)
                message["metadata"]["was_truncated"] = True

            if len(content_to_add) > self.validation_rules.max_content_length_warning:
                message["metadata"]["large_content_warning"] = True # Based on added content size
            
            self.current_conversation["messages"].append(message)
            self._update_token_usage(message) # This method needs `token_info` in message metadata
            
            processing_time = time.time() - start_time
            self.current_conversation["performance"]["total_processing_time"] += processing_time
            self.current_conversation["performance"]["message_count"] += 1
            
            if self.enable_metrics:
                conv_id = self.current_conversation["id"]
                if conv_id in self._metrics:
                    self._metrics[conv_id].message_count += 1
                    self._metrics[conv_id].last_activity = datetime.now()
            
            self.save_current_conversation()
            self._trigger_event('message_added', message, self.current_conversation["id"])
    
    def _update_token_usage(self, new_message: Dict) -> None:
        """Enhanced token usage tracking with better error handling."""
        if not token_counter:
            return

        try:
            conv_meta = self.current_conversation.get("metadata", {})
            provider = conv_meta.get("provider", "Unknown")
            model = conv_meta.get("model", "Unknown")
            conv_id = self.current_conversation["id"]
            usage = self.current_conversation["token_usage"]

            # For token_counter.track_tokens, we need user_input_text, system_prompt_text, and output_text
            user_input_for_track = ""
            system_prompt_for_track = ""
            output_for_track = ""

            if new_message['role'] == 'user':
                user_input_for_track = new_message['content']
                # System prompt is not part of user message in this context, it's global or per-agent
                # For the conversation manager, we can get the general instructions if they exist
                # This might require accessing a global config_manager instance if it's available
                # For now, we'll leave it empty as it's primarily tracked by the worker for each LLM call.
                # However, if this method is also for loading historical user messages, we need to account for system tokens already used by agents.
                # This method is for *adding* messages, so initial system tokens are from the *agent's first turn*.
                # The very first user message implies no prior system prompt *for that turn*.

            elif new_message['role'] in ['assistant', 'agent_1', 'agent_2', 'agent_3', 'agent_4', 'agent_5']:
                # For agent/assistant responses, this is the output
                output_for_track = new_message['content']
                # The input for this output would be the full context + user prompt provided to the agent
                # For simplicity here, we assume the worker manages the full input context for counting.
                # So, for the conversation manager's perspective of *its own* message, we just count the output.
                # The track_tokens method will sum the input/system based on what the worker sends.
                # So for this method, we only increment the *output* count directly if it's an agent/assistant message.
                # The actual `track_tokens` call is in worker.py and handles the full input/system/output breakdown.
                # This `_update_token_usage` in ConversationManager is primarily for *saving* message details and accumulating totals from `token_counter` calls.
                # It should *not* call `token_counter.track_tokens` itself, but rather *read* the current session totals from `token_counter`
                # and ensure `new_message` has `token_info` from the worker.

                # The logic `token_info = token_counter.track_tokens(...)`
                # from worker.py should be responsible for updating the `token_counter`'s internal session.
                # Here, we only *read* from token_counter and ensure `new_message` metadata is consistent.

                # Corrected logic for _update_token_usage:
                # It should take the `token_info` directly as a parameter from the worker.
                # For now, let's assume `new_message` already has `metadata["token_info"]` from the worker.

                if "token_info" in new_message["metadata"]:
                    exchange_token_info = new_message["metadata"]["token_info"]
                    usage["input_tokens"] += exchange_token_info.get("user_input_tokens", 0)
                    usage["system_tokens"] += exchange_token_info.get("system_prompt_tokens", 0)
                    usage["output_tokens"] += exchange_token_info.get("output_tokens", 0)
                    usage["estimated_cost"] += exchange_token_info.get("cost", 0.0)

                    # If any precise flag is False, mark session as estimated
                    if not exchange_token_info.get("is_precise", True):
                        self.current_conversation["token_usage"]["cost_is_estimated"] = True

                    usage["total_tokens"] = sum([
                        usage["input_tokens"],
                        usage["output_tokens"],
                        usage["system_tokens"]
                    ])
                else:
                    self.logger.warning(f"Message for role '{new_message['role']}' added without token_info metadata. Token usage may be inaccurate.")
            else:
                # Other roles (e.g., system for initial prompt) might not have direct tokens in this context.
                return

        except Exception as e:
            self.logger.error(f"Error updating token usage in conversation manager: {e}")
    
    def save_current_conversation(self) -> None:
        """Enhanced conversation saving with atomic operations and error recovery."""
        conv_id = self.current_conversation.get("id")
        if not conv_id:
            self.logger.warning("Attempted to save conversation with no ID")
            return
        
        file_lock = self._get_file_lock(conv_id)
        
        with file_lock:
            file_path = self.history_dir / f"conversation_{conv_id}.md"
            temp_path = file_path.with_suffix('.tmp')
            
            try:
                # Create frontmatter post
                post = frontmatter.Post("")
                post.metadata = {
                    "id": self.current_conversation["id"],
                    "timestamp": self.current_conversation["timestamp"],
                    "metadata": self.current_conversation["metadata"],
                    "token_usage": self.current_conversation["token_usage"],
                    "performance": self.current_conversation["performance"],
                    "version": "2.0",  # Version for future compatibility
                }
                
                # Build message content
                message_chunks = []
                for msg in self.current_conversation["messages"]:
                    msg_meta = msg.get("metadata", {})
                    # Convert dict to YAML string, ensure it's not empty before creating block
                    msg_meta_str = yaml.dump(msg_meta, default_flow_style=False).strip() if msg_meta else ""
                    
                    # Use standard Markdown YAML code block
                    yaml_block_content = f"```yaml\n{msg_meta_str}\n```\n\n" if msg_meta_str else ""
                    
                    header = f"### {msg['role'].upper()} ({msg['timestamp']})"
                    if 'id' in msg:
                        header += f" [ID: {msg['id']}]"
                    
                    # Construct the message content
                    # Place yaml_block_content *after* the header and an empty line,
                    # but *before* the main message content.
                    content = f"{header}\n\n{yaml_block_content}{msg['content']}"
                    message_chunks.append(content)

                post.content = MESSAGE_SEPARATOR.join(message_chunks)

                # Atomic write: write to temp file first, then rename
                with temp_path.open('wb') as f:
                    frontmatter.dump(post, f)
                
                # Atomic move
                temp_path.replace(file_path)
                
                # Update cache
                with self._lock:
                    self._conversation_cache[conv_id] = self.current_conversation.copy()
                    self._cache_access_times[conv_id] = datetime.now()
                
                self._trigger_event('conversation_saved', conv_id, file_path)
                
            except Exception as e:
                # Clean up temp file on error
                if temp_path.exists():
                    try:
                        temp_path.unlink()
                    except:
                        pass
                
                self.logger.error(f"Failed to save conversation {conv_id}: {e}")
                raise
    
    def load_conversation(self, conversation_id: str, use_cache: bool = True) -> bool:
        """
        Enhanced conversation loading with caching and compressed file support.
        """
        # Check cache first
        if use_cache:
            with self._lock:
                if conversation_id in self._conversation_cache:
                    self.current_conversation = self._conversation_cache[conversation_id].copy()
                    self._cache_access_times[conversation_id] = datetime.now()
                    self.logger.debug(f"Loaded conversation from cache: {conversation_id}")
                    return True
        
        file_lock = self._get_file_lock(conversation_id)
        start_time = time.time()
        
        with file_lock:
            # Try regular file first
            file_path = self.history_dir / f"conversation_{conversation_id}.md"
            compressed_path = self.compressed_dir / f"conversation_{conversation_id}.md.gz"
            
            content = None
            
            if file_path.exists():
                try:
                    with file_path.open('r', encoding='utf-8') as f:
                        content = f.read()
                except Exception as e:
                    self.logger.error(f"Error reading conversation file {file_path}: {e}")
                    return False
            
            elif compressed_path.exists():
                try:
                    with gzip.open(compressed_path, 'rt', encoding='utf-8') as f:
                        content = f.read()
                    self.logger.info(f"Loaded compressed conversation: {conversation_id}")
                except Exception as e:
                    self.logger.error(f"Error reading compressed file {compressed_path}: {e}")
                    return False
            
            else:
                self.logger.error(f"Conversation file not found: {conversation_id}")
                return False
            
            # Parse content
            try:
                # Handle both frontmatter and plain text content
                if content.startswith('---'):
                    import io
                    post = frontmatter.load(io.StringIO(content))
                else:
                    # Legacy format fallback
                    post = frontmatter.Post(content)
                    post.metadata = {}
                
                self.current_conversation = self._get_new_conversation_structure()
                
                # Load metadata
                if post.metadata:
                    self.current_conversation.update(post.metadata)
                    # Ensure ID is set
                    if not self.current_conversation.get("id"):
                        self.current_conversation["id"] = conversation_id
                
                # Parse messages with enhanced error handling
                messages = []
                if post.content:
                    message_chunks = post.content.split(MESSAGE_SEPARATOR)
                    for i, chunk in enumerate(message_chunks):
                        if not chunk.strip():
                            continue
                        
                        try:
                            message = self._parse_message_chunk(chunk, i)
                            if message:
                                messages.append(message)
                        except Exception as e:
                            self.logger.warning(f"Skipping malformed message chunk {i} in {conversation_id}: {e}")
                            continue

                self.current_conversation['messages'] = messages
                
                # Update cache
                with self._lock:
                    self._conversation_cache[conversation_id] = self.current_conversation.copy()
                    self._cache_access_times[conversation_id] = datetime.now()
                
                # Update metrics
                load_time = (time.time() - start_time) * 1000  # Convert to ms
                if self.enable_metrics:
                    if conversation_id not in self._metrics:
                        self._metrics[conversation_id] = ConversationMetrics()
                    self._metrics[conversation_id].load_time_ms = load_time
                    self._metrics[conversation_id].message_count = len(messages)
                
                self._trigger_event('conversation_loaded', conversation_id, self.current_conversation)
                self.logger.info(f"Successfully loaded conversation: {conversation_id} ({load_time:.1f}ms)")
                return True
                
            except Exception as e:
                self.logger.error(f"Error parsing conversation {conversation_id}: {e}")
                self.current_conversation = self._get_new_conversation_structure()
                return False
    
    def _parse_message_chunk(self, chunk: str, index: int) -> Optional[Dict]:
        """Parse a single message chunk with enhanced error handling."""
        try:
            lines = chunk.strip().split('\n')
            if not lines:
                return None
            
            # Parse header
            header = lines[0]
            if not header.startswith('###'):
                self.logger.warning(f"Invalid message header at index {index}: {header}")
                return None
            
            # Extract role and timestamp
            header_parts = header[3:].strip().split('(')
            if len(header_parts) < 2:
                self.logger.warning(f"Malformed header at index {index}: {header}")
                return None
            
            role = header_parts[0].strip().lower()
            timestamp_part = header_parts[1].rstrip(')')
            
            # Extract message ID if present
            message_id = None
            if '[ID:' in timestamp_part:
                parts = timestamp_part.split('[ID:')
                timestamp_part = parts[0].strip()
                message_id = parts[1].rstrip(']').strip()
            
            # Find content start and parse optional YAML metadata block
            content_lines = lines[1:] # Skip the header line
            content_start_idx = 0
            metadata_parsed = {} # Initialize parsed metadata

            # Look for YAML block (```yaml ... ```)
            # Allow for an empty line between header and YAML block
            if len(content_lines) > 0 and content_lines[0].strip() == '':
                content_start_idx = 1 # Skip the empty line

            if (len(content_lines) > content_start_idx and
                content_lines[content_start_idx].strip().startswith('```yaml')):
                yaml_block_lines = []
                # Start from the line after '```yaml'
                yaml_start_line_idx = content_start_idx + 1
                
                for i in range(yaml_start_line_idx, len(content_lines)):
                    if content_lines[i].strip() == '```':
                        # End of YAML block found
                        try:
                            yaml_str = "\n".join(yaml_block_lines)
                            if yaml_str.strip(): # Only parse if there's content
                                metadata_parsed = yaml.safe_load(yaml_str) or {}
                        except yaml.YAMLError as ye:
                            self.logger.warning(f"Malformed YAML metadata in chunk {index}: {ye}")
                        
                        # Update content_start_idx to be after the YAML block
                        content_start_idx = i + 1
                        # Skip potential empty line after YAML block
                        if content_start_idx < len(content_lines) and content_lines[content_start_idx].strip() == '':
                            content_start_idx += 1
                        break
                    yaml_block_lines.append(content_lines[i])
                else: # else for the 'for' loop (if '```' was not found)
                    self.logger.warning(f"Unclosed YAML block found in chunk {index}")
                    # Treat the block as part of content if not properly closed
                    # content_start_idx remains at the start of '```yaml'

            # Extract content
            content = '\n'.join(content_lines[content_start_idx:]).strip()
            
            message = {
                "role": role,
                "timestamp": timestamp_part,
                "content": content,
                "metadata": metadata_parsed # Use parsed metadata
            }
            
            if message_id:
                message["id"] = message_id
            
            return message
            
        except Exception as e:
            self.logger.error(f"Error parsing message chunk at index {index}: {e}")
            return None
    
    def get_conversation_list(self, 
                            include_compressed: bool = True,
                            sort_by: str = "timestamp",
                            reverse: bool = True,
                            filter_func: Optional[Callable[[Dict], bool]] = None) -> List[Dict]:
        """
        Enhanced conversation listing with filtering and sorting options.
        """
        conversations = []
        
        # Regular conversations
        file_pattern = "conversation_*.md"
        for file_path in self.history_dir.glob(file_pattern):
            try:
                conv_info = self._extract_conversation_info(file_path, compressed=False)
                if conv_info:
                    conversations.append(conv_info)
            except Exception as e:
                self.logger.error(f"Error reading metadata from {file_path}: {e}")
        
        # Compressed conversations
        if include_compressed:
            for file_path in self.compressed_dir.glob("conversation_*.md.gz"):
                try:
                    conv_info = self._extract_conversation_info(file_path, compressed=True)
                    if conv_info:
                        conversations.append(conv_info)
                except Exception as e:
                    self.logger.error(f"Error reading compressed metadata from {file_path}: {e}")
        
        # Apply filter
        if filter_func:
            conversations = [conv for conv in conversations if filter_func(conv)]
        
        # Sort conversations
        if sort_by in ["timestamp", "message_count", "total_tokens", "estimated_cost"]:
            conversations.sort(
                key=lambda x: x.get(sort_by, 0) or 0,
                reverse=reverse
            )
        
        return conversations
    
    def _extract_conversation_info(self, file_path: Path, compressed: bool = False) -> Optional[Dict]:
        """Extract conversation metadata efficiently."""
        try:
            if compressed:
                with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                    content = f.read(1000)  # Read only first part for metadata
            else:
                with file_path.open('r', encoding='utf-8') as f:
                    content = f.read(1000)  # Read only first part for metadata
            
            # Quick metadata extraction
            if content.startswith('---'):
                import io
                try:
                    post = frontmatter.load(io.StringIO(content))
                    meta = post.metadata or {}
                except:
                    meta = {}
            else:
                meta = {}
            
            # Extract conversation ID from filename
            conv_id = file_path.stem.replace("conversation_", "")
            if conv_id.endswith(".md"):
                conv_id = conv_id[:-3]
            
            # Get first message preview
            first_message = ""
            if hasattr(post, 'content') and post.content:
                lines = post.content.split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('#') and not line.startswith('```'):
                        first_message = line.strip()[:100]
                        break
            
            # File stats
            stat = file_path.stat()
            
            conv_info = {
                "id": conv_id,
                "timestamp": meta.get("timestamp", datetime.fromtimestamp(stat.st_ctime).isoformat()),
                "message_count": len(post.content.split(MESSAGE_SEPARATOR)) if hasattr(post, 'content') and post.content else 0,
                "first_message": first_message + ('...' if len(first_message) == 100 else ''),
                "total_tokens": meta.get("token_usage", {}).get("total_tokens", 0),
                "estimated_cost": meta.get("token_usage", {}).get("estimated_cost", 0.0),
                "file_size": stat.st_size,
                "compressed": compressed,
                "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            }
            
            # Add performance metrics if available
            if self.enable_metrics and conv_id in self._metrics:
                metrics = self._metrics[conv_id]
                conv_info.update({
                    "avg_response_time": metrics.avg_response_time,
                    "load_time_ms": metrics.load_time_ms,
                })
            
            return conv_info
            
        except Exception as e:
            self.logger.error(f"Error extracting info from {file_path}: {e}")
            return None
    
    def search_conversations(self, 
                           query: str,
                           search_content: bool = True,
                           search_metadata: bool = True,
                           case_sensitive: bool = False,
                           limit: Optional[int] = None) -> List[Dict]:
        """
        Search conversations by content or metadata.
        """
        results = []
        search_query = query if case_sensitive else query.lower()
        
        conversations = self.get_conversation_list(include_compressed=True)
        
        for conv in conversations:
            matches = []
            
            # Search in first message
            first_message = conv.get("first_message", "")
            if first_message:
                search_text = first_message if case_sensitive else first_message.lower()
                if search_query in search_text:
                    matches.append("first_message")
            
            # Search in metadata if enabled
            if search_metadata:
                # This would require loading the full conversation, so we'll check basic fields
                conv_id = conv.get("id", "")
                search_id = conv_id if case_sensitive else conv_id.lower()
                if search_query in search_id:
                    matches.append("id")
            
            if matches:
                conv_result = conv.copy()
                conv_result["match_fields"] = matches
                results.append(conv_result)
        
        # Apply limit
        if limit:
            results = results[:limit]
        
        return results
    
    # Enhanced context window method
    def get_context_window(self, max_tokens: Optional[int] = None, 
                          strategy: str = "recent_first",
                          preserve_first: bool = True) -> str:
        """
        Enhanced context window generation with multiple strategies.
        
        Args:
            max_tokens: Maximum tokens (uses working_context_size if None)
            strategy: 'recent_first', 'importance_based', or 'balanced'
            preserve_first: Always include the first message if possible
        """
        messages = self.current_conversation.get("messages", [])
        if not messages:
            return ""

        limit = max_tokens or self.working_context_size
        
        if strategy == "recent_first":
            return self._get_context_recent_first(messages, limit, preserve_first)
        elif strategy == "importance_based":
            return self._get_context_importance_based(messages, limit, preserve_first)
        elif strategy == "balanced":
            return self._get_context_balanced(messages, limit, preserve_first)
        else:
            return self._get_context_recent_first(messages, limit, preserve_first)
    
    def get_context_window_messages(self, max_tokens: Optional[int] = None,
                                   strategy: str = "recent_first",
                                   preserve_first: bool = True) -> List[Dict]:
        """
        Get the raw message list for context window, with optional filtering.
        
        Args:
            max_tokens: Maximum tokens (uses working_context_size if None)
            strategy: 'recent_first', 'importance_based', or 'balanced'
            preserve_first: Always include the first message if possible
            
        Returns:
            List of message dictionaries
        """
        messages = self.current_conversation.get("messages", [])
        if not messages:
            return []

        limit = max_tokens or self.working_context_size
        
        if strategy == "recent_first":
            return self._get_context_messages_recent_first(messages, limit, preserve_first)
        elif strategy == "importance_based":
            return self._get_context_messages_importance_based(messages, limit, preserve_first)
        elif strategy == "balanced":
            return self._get_context_messages_balanced(messages, limit, preserve_first)
        else:
            return self._get_context_messages_recent_first(messages, limit, preserve_first)
    
    def _get_context_recent_first(self, messages: List[Dict], limit: int, preserve_first: bool) -> str:
        """Original recent-first strategy with enhancements."""
        context_messages = []
        token_count = 0

        def _count_tokens(message_content: str) -> int:
            if token_counter:
                try:
                    model_name = self.current_conversation.get("metadata", {}).get("model", "cl100k_base")
                    result = token_counter.count_tokens(message_content, model_name=model_name)
                    
                    if isinstance(result, tuple):
                        return int(result[0])  # Take first element if tuple
                    return int(result)
                except Exception as e:
                    self.logger.warning(f"Token counter failed: {e}. Using estimation.")
                    return int(len(message_content.split()) * TOKEN_ESTIMATION_FACTOR)
            
            return int(len(message_content.split()) * TOKEN_ESTIMATION_FACTOR)

        # Handle first message if preserve_first is enabled
        if preserve_first and messages:
            first_message = messages[0]
            first_msg_tokens = _count_tokens(first_message['content'])
            if first_msg_tokens <= limit:
                context_messages.append(first_message)
                token_count += first_msg_tokens

        # Add recent messages in reverse order
        for message in reversed(messages[1:] if preserve_first else messages):
            message_tokens = _count_tokens(message['content'])
            if token_count + message_tokens > limit:
                self.logger.debug("Context window limit reached. Truncating older messages.")
                break
            context_messages.append(message)
            token_count += message_tokens
        
        # Reorder messages chronologically
        if preserve_first and len(context_messages) > 1:
            final_messages = [context_messages[0]] + list(reversed(context_messages[1:]))
        else:
            final_messages = list(reversed(context_messages))
        
        return "\n".join(f"{msg['role'].upper()}: {msg['content']}" for msg in final_messages)
    
    def _get_context_importance_based(self, messages: List[Dict], limit: int, preserve_first: bool) -> str:
        """Importance-based context selection (placeholder for future enhancement)."""
        # For now, fall back to recent_first
        return self._get_context_recent_first(messages, limit, preserve_first)
    
    def _get_context_balanced(self, messages: List[Dict], limit: int, preserve_first: bool) -> str:
        """Balanced context selection (placeholder for future enhancement)."""
        # For now, fall back to recent_first  
        return self._get_context_recent_first(messages, limit, preserve_first)
    
    def _get_context_messages_recent_first(self, messages: List[Dict], limit: int, preserve_first: bool) -> List[Dict]:
        """Get recent messages as dictionary list with token limit."""
        context_messages = []
        token_count = 0

        def _count_tokens(message_content: str) -> int:
            if token_counter:
                try:
                    model_name = self.current_conversation.get("metadata", {}).get("model", "cl100k_base")
                    result = token_counter.count_tokens(message_content, model_name=model_name)
                    
                    if isinstance(result, tuple):
                        return int(result[0])  # Take first element if tuple
                    return int(result)
                except Exception as e:
                    self.logger.warning(f"Token counter failed: {e}. Using estimation.")
                    return int(len(message_content.split()) * TOKEN_ESTIMATION_FACTOR)
            
            return int(len(message_content.split()) * TOKEN_ESTIMATION_FACTOR)

        # Handle first message if preserve_first is enabled
        if preserve_first and messages:
            first_message = messages[0]
            first_msg_tokens = _count_tokens(first_message['content'])
            if first_msg_tokens <= limit:
                context_messages.append(first_message)
                token_count += first_msg_tokens

        # Add recent messages in reverse order
        for message in reversed(messages[1:] if preserve_first else messages):
            message_tokens = _count_tokens(message['content'])
            if token_count + message_tokens > limit:
                self.logger.debug("Context window limit reached. Truncating older messages.")
                break
            context_messages.append(message)
            token_count += message_tokens
        
        # Reorder messages chronologically
        if preserve_first and len(context_messages) > 1:
            final_messages = [context_messages[0]] + list(reversed(context_messages[1:]))
        else:
            final_messages = list(reversed(context_messages))
        
        return final_messages
    
    def _get_context_messages_importance_based(self, messages: List[Dict], limit: int, preserve_first: bool) -> List[Dict]:
        """Importance-based context selection (placeholder for future enhancement)."""
        # For now, fall back to recent_first
        return self._get_context_messages_recent_first(messages, limit, preserve_first)
    
    def _get_context_messages_balanced(self, messages: List[Dict], limit: int, preserve_first: bool) -> List[Dict]:
        """Balanced context selection (placeholder for future enhancement)."""
        # For now, fall back to recent_first  
        return self._get_context_messages_recent_first(messages, limit, preserve_first)
    
    # Enhanced utility methods
    def get_conversation_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about all conversations."""
        stats = {
            "total_conversations": 0,
            "total_messages": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "avg_messages_per_conversation": 0.0,
            "compressed_conversations": 0,
            "cache_hit_rate": 0.0,
            "storage_usage_mb": 0.0,
        }
        
        conversations = self.get_conversation_list(include_compressed=True)
        stats["total_conversations"] = len(conversations)
        
        for conv in conversations:
            stats["total_messages"] += conv.get("message_count", 0)
            stats["total_tokens"] += conv.get("total_tokens", 0)
            stats["total_cost"] += conv.get("estimated_cost", 0.0)
            stats["storage_usage_mb"] += conv.get("file_size", 0) / (1024 * 1024)
            
            if conv.get("compressed", False):
                stats["compressed_conversations"] += 1
        
        if stats["total_conversations"] > 0:
            stats["avg_messages_per_conversation"] = stats["total_messages"] / stats["total_conversations"]
        
        # Calculate cache statistics
        with self._lock:
            total_requests = len(self._cache_access_times)
            cache_hits = len(self._conversation_cache)
            if total_requests > 0:
                stats["cache_hit_rate"] = cache_hits / total_requests
        
        return stats
    
    def export_conversation(self, 
                          conversation_id: str,
                          format: str = "json",
                          include_metadata: bool = True) -> Optional[str]:
        """
        Export a conversation in various formats.
        
        Args:
            conversation_id: ID of conversation to export
            format: Export format ('json', 'markdown', 'txt')
            include_metadata: Whether to include metadata
        """
        if not self.load_conversation(conversation_id, use_cache=True):
            return None
        
        if format.lower() == "json":
            export_data = self.current_conversation.copy()
            if not include_metadata:
                export_data.pop("metadata", None)
                export_data.pop("token_usage", None)
                export_data.pop("performance", None)
            return json.dumps(export_data, indent=2, default=str)
        
        elif format.lower() == "markdown":
            lines = []
            if include_metadata:
                lines.append(f"# Conversation {conversation_id}")
                lines.append(f"**Created:** {self.current_conversation.get('timestamp', 'Unknown')}")
                lines.append("")
            
            for msg in self.current_conversation.get("messages", []):
                lines.append(f"## {msg['role'].title()}")
                lines.append(f"*{msg.get('timestamp', 'Unknown')}*")
                lines.append("")
                lines.append(msg['content'])
                lines.append("")
            
            return "\n".join(lines)
        
        elif format.lower() == "txt":
            lines = []
            for msg in self.current_conversation.get("messages", []):
                lines.append(f"{msg['role'].upper()}: {msg['content']}")
                lines.append("")
            return "\n".join(lines)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def cleanup_resources(self) -> None:
        """Clean up resources and stop background tasks."""
        self._stop_cleanup.set()
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=2.0)
        
        with self._lock:
            self._conversation_cache.clear()
            self._cache_access_times.clear()
            self._file_locks.clear()
    
    # Maintain all backward compatibility methods
    def set_max_response_context(self, max_tokens: int) -> None:
        """Backward compatibility method."""
        if max_tokens > 0:
            self.working_context_size = max_tokens
            self.logger.info(f"Working context size set to {max_tokens} tokens.")
        else:
            self.logger.warning(f"Invalid token size provided: {max_tokens}.")

    def delete_conversation(self, conversation_id: str) -> bool:
        """Enhanced conversation deletion with backup cleanup."""
        file_lock = self._get_file_lock(conversation_id)
        
        with file_lock:
            regular_path = self.history_dir / f"conversation_{conversation_id}.md"
            compressed_path = self.compressed_dir / f"conversation_{conversation_id}.md.gz"
            
            deleted = False
            
            try:
                # Delete regular file
                if regular_path.exists():
                    regular_path.unlink()
                    deleted = True
                
                # Delete compressed file
                if compressed_path.exists():
                    compressed_path.unlink()
                    deleted = True
                
                # Clean up cache
                with self._lock:
                    self._conversation_cache.pop(conversation_id, None)
                    self._cache_access_times.pop(conversation_id, None)
                    self._metrics.pop(conversation_id, None)
                
                # Clean up backups
                for backup_file in self.backup_dir.glob(f"conversation_{conversation_id}_*.md"):
                    try:
                        backup_file.unlink()
                    except Exception as e:
                        self.logger.warning(f"Failed to delete backup {backup_file}: {e}")
                
                if deleted:
                    self.logger.info(f"Deleted conversation: {conversation_id}")
                else:
                    self.logger.warning(f"Conversation not found: {conversation_id}")
                
                return deleted
                
            except OSError as e:
                self.logger.error(f"Error deleting conversation {conversation_id}: {e}")
                return False

    def delete_all_conversations(self) -> Tuple[int, int]:
        """Enhanced bulk deletion with progress tracking."""
        success_count, fail_count = 0, 0
        
        # Delete regular conversations
        for file_path in self.history_dir.glob("conversation_*.md"):
            try:
                file_path.unlink()
                success_count += 1
            except OSError as e:
                self.logger.error(f"Error deleting file {file_path}: {e}")
                fail_count += 1
        
        # Delete compressed conversations
        for file_path in self.compressed_dir.glob("conversation_*.md.gz"):
            try:
                file_path.unlink()
                success_count += 1
            except OSError as e:
                self.logger.error(f"Error deleting compressed file {file_path}: {e}")
                fail_count += 1
        
        # Clean up all caches and metrics
        with self._lock:
            self._conversation_cache.clear()
            self._cache_access_times.clear()
            self._metrics.clear()
            self._file_locks.clear()
        
        # Clean up backups
        for backup_file in self.backup_dir.glob("conversation_*.md"):
            try:
                backup_file.unlink()
            except Exception as e:
                self.logger.warning(f"Failed to delete backup {backup_file}: {e}")
        
        self.logger.info(f"Deleted all conversations. Succeeded: {success_count}, Failed: {fail_count}")
        self.current_conversation = self._get_new_conversation_structure()
        return success_count, fail_count

    # All other backward compatibility methods remain the same
    def get_current_conversation_id(self) -> Optional[str]:
        return self.current_conversation.get("id")

    def is_conversation_active(self) -> bool:
        return bool(self.current_conversation.get("id"))

    def get_token_usage(self) -> Dict:
        return self.current_conversation.get("token_usage", {})
    
    def optimize_rag_content(self, rag_content: str, max_tokens: int = 6000) -> str:
        """
        Optimize RAG content by truncating it to fit within token limits.
        
        Args:
            rag_content: The RAG content to optimize
            max_tokens: Maximum number of tokens allowed
            
        Returns:
            Optimized RAG content that fits within the token limit
        """
        if not rag_content or not rag_content.strip():
            return rag_content
            
        # Estimate current token count (rough approximation: 1 token ≈ 4 characters)
        estimated_tokens = len(rag_content) // 4
        
        if estimated_tokens <= max_tokens:
            # Content is already within limits
            return rag_content
            
        # Calculate target character count
        target_chars = max_tokens * 4
        
        # Truncate with some buffer for safety
        safety_buffer = int(target_chars * 0.1)  # 10% safety buffer
        safe_char_limit = target_chars - safety_buffer
        
        if safe_char_limit <= 0:
            return ""
            
        # Try to truncate at natural boundaries (paragraphs, then sentences)
        truncated_content = rag_content[:safe_char_limit]
        
        # Try to end at a paragraph boundary
        last_double_newline = truncated_content.rfind('\n\n')
        if last_double_newline > safe_char_limit // 2:  # Must be at least halfway through
            truncated_content = truncated_content[:last_double_newline]
        else:
            # Try to end at a sentence boundary
            last_period = truncated_content.rfind('. ')
            if last_period > safe_char_limit // 2:  # Must be at least halfway through
                truncated_content = truncated_content[:last_period + 1]
        
        # Add truncation notice if content was actually truncated
        if len(truncated_content) < len(rag_content):
            truncated_content += f"\n\n[RAG content truncated to fit {max_tokens} token limit - {len(rag_content) - len(truncated_content)} characters removed]"
            
        self.logger.info(f"RAG content optimized: {len(rag_content)} → {len(truncated_content)} characters (target: ~{max_tokens} tokens)")
        return truncated_content

    def _calculate_section_importance(self, section: str) -> float:
        """Placeholder for section importance calculation - maintain compatibility."""
        return 0.0
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        try:
            self.cleanup_resources()
        except Exception:
            pass  # Ignore cleanup errors during destruction

    def get_validation_rules(self) -> MessageValidationRule:
        """Get current validation rules."""
        return self.validation_rules
    
    def update_validation_rules(self, **kwargs) -> None:
        """Update validation rules dynamically."""
        for key, value in kwargs.items():
            if hasattr(self.validation_rules, key):
                setattr(self.validation_rules, key, value)
                self.logger.info(f"Updated validation rule '{key}' to {value}")
            else:
                self.logger.warning(f"Unknown validation rule: {key}")
    
    def check_content_size(self, content: str) -> Dict[str, Any]:
        """Check content size and provide recommendations."""
        content_length = len(content)
        return {
            "content_length": content_length,
            "is_large": content_length > self.validation_rules.max_content_length_warning,
            "is_too_large": content_length > self.validation_rules.max_content_length,
            "max_allowed": self.validation_rules.max_content_length,
            "warning_threshold": self.validation_rules.max_content_length_warning,
            "truncation_needed": content_length > self.validation_rules.max_content_length and self.validation_rules.enable_content_truncation,
            "truncated_length": self.validation_rules.max_content_length - len(self.validation_rules.truncation_suffix) if self.validation_rules.enable_content_truncation else None
        }