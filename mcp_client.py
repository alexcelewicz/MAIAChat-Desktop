"""
MCP Client - Model Context Protocol Client Implementation

WARNING: This implementation uses direct API endpoints (Google Search, GitHub, etc.) 
with special handling rather than true MCP server implementations. While functional, 
this is not a standard MCP architecture. The "servers" configured here are actually 
direct API endpoints with custom logic for discover_capabilities and query_mcp_server.

For true MCP architecture, consider implementing proper MCP servers that abstract 
these API details and follow the MCP specification.

This design choice was made for simplicity and direct API access, but should be 
documented for users who expect standard MCP behavior.
"""

import os
import json
import logging
import requests
import traceback
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field, asdict
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MCP Client")

@dataclass
class MCPServer:
    """Class representing an MCP server configuration."""
    name: str
    url: str
    description: str = ""
    enabled: bool = True
    auth_token: str = ""
    capabilities: List[str] = field(default_factory=list)
    cx: str = ""  # Custom Search Engine ID for Google Search API
    server_type: str = ""  # Type of server (e.g., "filesystem")
    config_data: Dict[str, Any] = field(default_factory=dict)  # Additional configuration data

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        # Only include non-empty fields to keep JSON clean
        if not self.server_type:
            result.pop('server_type', None)
        if not self.config_data:
            result.pop('config_data', None)
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPServer':
        """Create an MCPServer instance from a dictionary."""
        # Use get() with default values to handle missing keys gracefully
        server = cls(
            name=data.get('name', ''),
            url=data.get('url', ''),
            description=data.get('description', ''),
            enabled=data.get('enabled', True),
            auth_token=data.get('auth_token', ''),
            capabilities=data.get('capabilities', []),
            cx=data.get('cx', ''),
            server_type=data.get('server_type', ''),
            config_data=data.get('config_data', {})
        )
        return server

    def __post_init__(self):
        """Post-initialization to validate data."""
        if not self.name:
            logger.warning("MCPServer created with empty name.")
        if not self.url:
            logger.warning(f"MCPServer '{self.name}' created with empty URL.")

class MCPClient:
    """Client for interacting with MCP servers."""

    def __init__(self, config_dir: str = "mcp_config"):
        """Initialize the MCP client.

        Args:
            config_dir: Directory to store MCP server configurations
        """
        self.config_dir = config_dir
        os.makedirs(config_dir, exist_ok=True)
        self.servers: Dict[str, MCPServer] = {}
        self._available_servers_list: List[Dict[str, Any]] = [] # Cache for available servers
        self._context7_libraries_list: List[Dict[str, Any]] = [] # Cache for Context7 libraries
        self.load_servers()
        self._load_static_data() # Load hardcoded lists

    def _load_static_data(self):
        """Load hardcoded lists for available servers and Context7 libraries."""
        # This could be expanded to fetch from a central registry or API
        self._available_servers_list = [
            {
                "name": "GitHub",
                "url": "http://localhost:8080/github", # Example URL, replace with actual MCP server URL
                "description": "Access GitHub repositories, issues, and pull requests"
            },
            {
                "name": "Brave Search",
                "url": "https://api.search.brave.com/res/v1/web/search",
                "description": "Search the web with Brave Search"
            },
             {
                "name": "Google Search",
                "url": "https://www.googleapis.com/customsearch/v1",
                "description": "Search the web with Google Custom Search API (Requires API Key and CX)"
            },
            {
                "name": "Google Drive",
                "url": "http://localhost:8080/google-drive", # Example URL
                "description": "Access files and folders in Google Drive"
            },
            {
                "name": "Slack",
                "url": "http://localhost:8080/slack", # Example URL
                "description": "Interact with Slack channels and messages"
            },
            {
                "name": "Docker",
                "url": "http://localhost:8080/docker", # Example URL
                "description": "Execute code in isolated Docker containers"
            },
            {
                "name": "DuckDuckGo",
                "url": "http://localhost:8080/duckduckgo", # Example URL
                "description": "Search the web with DuckDuckGo"
            },
            {
                "name": "Vectorize",
                "url": "http://localhost:8080/vectorize", # Example URL
                "description": "Perform vector searches on your data"
            },
             {
                "name": "Serper Search",
                "url": "https://api.serper.dev/search",
                "description": "Fast and affordable Google Search API alternative (Requires API Key)"
            },
             {
                "name": "Context7",
                "url": "https://api.context7.com/v1", # Example URL, replace with actual Context7 MCP server URL
                "description": "Access up-to-date documentation and code examples for popular libraries (Requires API Key)"
            }
        ]

        # In a real implementation, this would call the Context7 API
        # For now, we'll use a static list of popular libraries
        self._context7_libraries_list = [
            {
                "name": "React",
                "description": "A JavaScript library for building user interfaces",
                "capabilities": ["documentation", "code_examples", "api_reference"]
            },
            {
                "name": "TensorFlow",
                "description": "An end-to-end open source platform for machine learning",
                "capabilities": ["documentation", "code_examples", "api_reference"]
            },
            {
                "name": "PyTorch",
                "description": "An open source machine learning framework",
                "capabilities": ["documentation", "code_examples", "api_reference"]
            },
            {
                "name": "Django",
                "description": "A high-level Python web framework",
                "capabilities": ["documentation", "code_examples", "api_reference"]
            },
            {
                "name": "Flask",
                "description": "A lightweight WSGI web application framework in Python",
                "capabilities": ["documentation", "code_examples", "api_reference"]
            },
            {
                "name": "Node.js",
                "description": "A JavaScript runtime built on Chrome's V8 JavaScript engine",
                "capabilities": ["documentation", "code_examples", "api_reference"]
            },
            {
                "name": "Pandas",
                "description": "A fast, powerful, flexible and easy to use open source data analysis and manipulation tool",
                "capabilities": ["documentation", "code_examples", "api_reference"]
            },
            {
                "name": "Scikit-learn",
                "description": "A machine learning library for Python",
                "capabilities": ["documentation", "code_examples", "api_reference"]
            }
        ]


    def load_servers(self) -> None:
        """Load MCP server configurations from disk."""
        config_file = os.path.join(self.config_dir, "servers.json")
        self.servers = {} # Clear existing servers
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    servers_data = json.load(f)

                for server_data in servers_data:
                    try:
                        server = MCPServer.from_dict(server_data)
                        self.servers[server.name] = server
                    except Exception as e:
                        logger.error(f"Error loading server data: {server_data}. Error: {e}")

                logger.info(f"Loaded {len(self.servers)} MCP server configurations from {config_file}")
            except json.JSONDecodeError:
                logger.error(f"Error decoding JSON from {config_file}. File might be corrupted.")
            except FileNotFoundError:
                 logger.warning(f"Config file not found: {config_file}. Starting with no servers.")
            except Exception as e:
                logger.error(f"An unexpected error occurred loading MCP server configurations from {config_file}: {e}")
        else:
            logger.info(f"No MCP server configurations file found at {config_file}")

    def save_servers(self) -> None:
        """Save MCP server configurations to disk."""
        config_file = os.path.join(self.config_dir, "servers.json")
        try:
            servers_data = [server.to_dict() for server in self.servers.values()]
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(servers_data, f, indent=2)

            logger.info(f"Saved {len(self.servers)} MCP server configurations to {config_file}")
        except Exception as e:
            logger.error(f"Error saving MCP server configurations to {config_file}: {e}")
            logger.error(traceback.format_exc()) # Log traceback for saving errors

    def add_server(self, server: MCPServer) -> None:
        """Add or update an MCP server configuration.

        If a server with the same name exists, it will be updated.

        Args:
            server: The MCP server configuration to add
        """
        if not server or not server.name:
            logger.warning("Attempted to add a server with no name.")
            return

        # Preserve capabilities if updating an existing server
        existing_server = self.servers.get(server.name)
        if existing_server and not server.capabilities:
             server.capabilities = existing_server.capabilities

        self.servers[server.name] = server
        self.save_servers()
        logger.info(f"Server '{server.name}' added/updated.")


    def remove_server(self, server_name: str) -> bool:
        """Remove an MCP server configuration.

        Args:
            server_name: Name of the server to remove

        Returns:
            bool: True if the server was removed, False otherwise
        """
        if not server_name:
             logger.warning("Attempted to remove a server with no name specified.")
             return False

        if server_name in self.servers:
            del self.servers[server_name]
            self.save_servers()
            logger.info(f"Server '{server_name}' removed.")
            return True
        else:
            logger.warning(f"Attempted to remove non-existent server: '{server_name}'")
        return False

    def get_server(self, server_name: str) -> Optional[MCPServer]:
        """Get an MCP server configuration by name.

        Args:
            server_name: Name of the server to get

        Returns:
            Optional[MCPServer]: The server configuration, or None if not found
        """
        return self.servers.get(server_name)

    def get_enabled_servers(self) -> List[MCPServer]:
        """Get all enabled MCP server configurations.

        Returns:
            List[MCPServer]: List of enabled server configurations
        """
        return [server for server in self.servers.values() if server.enabled]

    def discover_capabilities(self, server: MCPServer) -> List[str]:
        """Discover the capabilities of an MCP server."""
        logger.info(f"Discovering capabilities for server: {server.name}")
        
        # Check if it's a filesystem server
        if hasattr(server, 'server_type') and server.server_type == 'filesystem':
            return self._test_filesystem_connection(server)
        
        # Check URL patterns to determine server type
        if "googleapis.com/customsearch" in server.url:
            return self._test_google_search_connection(server)
        elif "github" in server.url.lower():
            return self._test_github_connection(server)
        elif "serper.dev" in server.url:
            return self._test_serper_connection(server)
        elif "context7" in server.url.lower():
            return self._test_context7_connection(server)
        elif "unsplash" in server.url.lower():
            return self._test_unsplash_connection(server)
        elif "slack" in server.url.lower():
            return self._test_slack_connection(server)
        elif "search.brave.com" in server.url:
            return self._test_brave_search_connection(server)
        else:
            # Default to standard MCP connection test
            return self._test_standard_mcp_connection(server)

    def _test_standard_mcp_connection(self, server: MCPServer) -> List[str]:
        """Test connection to a standard MCP server by checking /capabilities."""
        try:
            headers = {}
            if server.auth_token:
                headers["Authorization"] = f"Bearer {server.auth_token}"

            # Try the standard MCP capabilities endpoint
            capabilities_url = f"{server.url.rstrip('/')}/capabilities" # Ensure no double slash
            logger.info(f"Testing standard MCP capabilities endpoint: {capabilities_url}")
            response = requests.get(
                capabilities_url,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                capabilities = data.get("capabilities", [])
                if not isinstance(capabilities, list):
                     logger.warning(f"Capabilities endpoint for {server.name} returned non-list data: {capabilities}")
                     capabilities = [] # Ensure it's a list

                # Also check for a basic GET to the root if capabilities endpoint isn't 200
                # This helps confirm basic reachability even if capabilities isn't implemented
                if not capabilities:
                     logger.info(f"Capabilities endpoint returned empty or non-list. Trying base URL: {server.url}")
                     base_response = requests.get(
                        server.url,
                        headers=headers,
                        timeout=10
                     )
                     if base_response.status_code < 400:
                         logger.info(f"Base URL {server.url} reachable ({base_response.status_code}). Assuming 'api_access' capability.")
                         capabilities = ["api_access"] # Assume basic access if root is reachable

                return capabilities
            else:
                logger.warning(f"Standard MCP capabilities endpoint for {server.name} returned status {response.status_code}. Trying base URL.")
                # If capabilities endpoint fails, try a simple GET request to the base URL
                base_response = requests.get(
                    server.url,
                    headers=headers,
                    timeout=10
                )

                if base_response.status_code < 400:  # Any non-error response
                    logger.info(f"Base URL {server.url} reachable ({base_response.status_code}). Assuming 'api_access' capability.")
                    return ["api_access"] # Assume basic access if root is reachable
                else:
                    logger.error(f"Base URL {server.url} also failed with status {base_response.status_code}.")
                    return []
        except requests.exceptions.Timeout:
            logger.error(f"Connection to {server.name} timed out.")
            return []
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error to {server.name}. Is the server running and accessible?")
            return []
        except Exception as e:
            logger.error(f"Error testing standard MCP connection for {server.name}: {e}")
            logger.error(traceback.format_exc())
            return []


    # --- Specific API Test Connection Methods (kept from original) ---
    # These methods test connectivity for non-standard MCP endpoints by making
    # a minimal API call specific to that service.
    def _test_google_search_connection(self, server: MCPServer) -> List[str]:
        """Test connection to Google Custom Search API."""
        logger.info(f"Testing Google Search connection for '{server.name}'")
        try:
            if not server.auth_token:
                 logger.warning("Google Search requires an API Key (auth_token).")
                 return []
            if not server.cx:
                 logger.warning("Google Search requires a Custom Search Engine ID (cx).")
                 return []

            params = {
                "key": server.auth_token,
                "cx": server.cx,
                "q": "test",
                "num": 1
            }
            response = requests.get(server.url, params=params, timeout=10)

            # Google API returns 200 on success, but might return 400 for invalid CX or other issues
            # A 400 might still indicate the API key is valid but the request parameters are wrong.
            # We'll consider 200 or 400 as a sign that the endpoint is reachable and key is potentially valid.
            if response.status_code in [200, 400]:
                logger.info(f"Google Search test connection status: {response.status_code}")
                # Check response body for specific errors if needed, but for a basic test, status is often enough.
                # If status is 400, the error message might indicate invalid CX or API key.
                if response.status_code == 400:
                     logger.warning(f"Google Search test returned 400. Check API Key and CX. Response: {response.text[:200]}...")
                return ["web_search", "image_search"] # Assume these capabilities if connection is possible
            else:
                logger.error(f"Google Search test connection failed with status: {response.status_code}. Response: {response.text[:200]}...")
                return []
        except requests.exceptions.Timeout:
            logger.error(f"Google Search test connection timed out.")
            return []
        except requests.exceptions.ConnectionError:
            logger.error(f"Google Search test connection error. Is the URL correct?")
            return []
        except Exception as e:
            logger.error(f"Error testing Google Search connection: {e}")
            logger.error(traceback.format_exc())
            return []

    def _test_github_connection(self, server: MCPServer) -> List[str]:
        """Test connection to GitHub API."""
        logger.info(f"Testing GitHub connection for '{server.name}'")
        try:
            headers = {}
            if server.auth_token:
                headers["Authorization"] = f"token {server.auth_token}"

            # Try to get user information (requires auth for private info, but works for public with token)
            response = requests.get(f"{server.url.rstrip('/')}/user", headers=headers, timeout=10)

            if response.status_code == 200:
                logger.info("GitHub test connection successful (authenticated).")
                return ["repo_access", "issue_management", "pr_review", "public_repo_access"]
            elif response.status_code == 401:
                logger.warning("GitHub test connection failed (401 Unauthorized). Check auth token permissions.")
                # Still try a public endpoint to see if the service is generally reachable
                public_response = requests.get(f"{server.url.rstrip('/')}/zen", timeout=10)
                if public_response.status_code == 200:
                     logger.info("GitHub public endpoint reachable.")
                     return ["public_repo_access"] # Can access public info
                else:
                     logger.error(f"GitHub public endpoint also failed with status {public_response.status_code}.")
                     return []
            else:
                logger.error(f"GitHub test connection failed with status: {response.status_code}. Response: {response.text[:200]}...")
                return []
        except requests.exceptions.Timeout:
            logger.error(f"GitHub test connection timed out.")
            return []
        except requests.exceptions.ConnectionError:
            logger.error(f"GitHub test connection error. Is the URL correct?")
            return []
        except Exception as e:
            logger.error(f"Error testing GitHub connection: {e}")
            logger.error(traceback.format_exc())
            return []

    def _test_serper_connection(self, server: MCPServer) -> List[str]:
        """Test connection to Serper.dev API."""
        logger.info(f"Testing Serper connection for '{server.name}'")
        try:
            if not server.auth_token:
                 logger.warning("Serper Search requires an API Key (auth_token).")
                 return []

            headers = {
                "X-API-KEY": server.auth_token,
                "Content-Type": "application/json"
            }
            payload = {"q": "test", "num": 1}
            response = requests.post(server.url, headers=headers, json=payload, timeout=10)

            if response.status_code == 200:
                logger.info("Serper test connection successful.")
                return ["web_search", "news_search"]
            else:
                logger.error(f"Serper test connection failed with status: {response.status_code}. Response: {response.text[:200]}...")
                return []
        except requests.exceptions.Timeout:
            logger.error(f"Serper test connection timed out.")
            return []
        except requests.exceptions.ConnectionError:
            logger.error(f"Serper test connection error. Is the URL correct?")
            return []
        except Exception as e:
            logger.error(f"Error testing Serper connection: {e}")
            logger.error(traceback.format_exc())
            return []

    def _test_context7_connection(self, server: MCPServer) -> List[str]:
        """Test connection to Context7 API."""
        logger.info(f"Testing Context7 connection for '{server.name}'")
        # NOTE: This assumes a specific Context7 MCP server implementation.
        # The original code had a placeholder test. We'll use the standard MCP test.
        # If Context7 requires a specific test, this method should be updated.
        return self._test_standard_mcp_connection(server)


    def _test_unsplash_connection(self, server: MCPServer) -> List[str]:
        """Test connection to Unsplash API."""
        logger.info(f"Testing Unsplash connection for '{server.name}'")
        try:
            if not server.auth_token:
                 logger.warning("Unsplash requires an API Key (auth_token).")
                 return []

            params = {
                "client_id": server.auth_token,
                "query": "test",
                "per_page": 1
            }
            response = requests.get(f"{server.url.rstrip('/')}/search/photos", params=params, timeout=10)

            if response.status_code == 200:
                logger.info("Unsplash test connection successful.")
                return ["image_search", "image_download"]
            else:
                logger.error(f"Unsplash test connection failed with status: {response.status_code}. Response: {response.text[:200]}...")
                return []
        except requests.exceptions.Timeout:
            logger.error(f"Unsplash test connection timed out.")
            return []
        except requests.exceptions.ConnectionError:
            logger.error(f"Unsplash test connection error. Is the URL correct?")
            return []
        except Exception as e:
            logger.error(f"Error testing Unsplash connection: {e}")
            logger.error(traceback.format_exc())
            return []

    def _test_slack_connection(self, server: MCPServer) -> List[str]:
        """Test connection to Slack API."""
        logger.info(f"Testing Slack connection for '{server.name}'")
        try:
            if not server.auth_token:
                 logger.warning("Slack requires an API Token (auth_token).")
                 return []

            headers = {"Authorization": f"Bearer {server.auth_token}"}
            # Use a simple test endpoint
            response = requests.get(f"{server.url.rstrip('/')}/api.test", headers=headers, timeout=10)

            if response.status_code == 200 and response.json().get("ok") is True:
                logger.info("Slack test connection successful.")
                return ["message_sending", "channel_management", "user_lookup"]
            else:
                logger.error(f"Slack test connection failed with status: {response.status_code}. Response: {response.text[:200]}...")
                return []
        except requests.exceptions.Timeout:
            logger.error(f"Slack test connection timed out.")
            return []
        except requests.exceptions.ConnectionError:
            logger.error(f"Slack test connection error. Is the URL correct?")
            return []
        except Exception as e:
            logger.error(f"Error testing Slack connection: {e}")
            logger.error(traceback.format_exc())
            return []

    def _test_brave_search_connection(self, server: MCPServer) -> List[str]:
        """Test connection to Brave Search API."""
        logger.info(f"Testing Brave Search connection for '{server.name}'")
        try:
            if not server.auth_token:
                 logger.warning("Brave Search requires a Subscription Token (auth_token).")
                 return []

            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": server.auth_token
            }
            params = {"q": "test", "count": 1}
            response = requests.get(server.url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                logger.info("Brave Search test connection successful.")
                return ["web_search", "image_search", "news_search"]
            else:
                logger.error(f"Brave Search test connection failed with status: {response.status_code}. Response: {response.text[:200]}...")
                return []
        except requests.exceptions.Timeout:
            logger.error(f"Brave Search test connection timed out.")
            return []
        except requests.exceptions.ConnectionError:
            logger.error(f"Brave Search test connection error. Is the URL correct?")
            return []
        except Exception as e:
            logger.error(f"Error testing Brave Search connection: {e}")
            logger.error(traceback.format_exc())
            return []

    def _test_filesystem_connection(self, server: MCPServer) -> List[str]:
        """Test connection to a filesystem server and return capabilities."""
        try:
            from mcp_filesystem_server import create_filesystem_server
            
            if not hasattr(server, 'config_data'):
                logger.error(f"Filesystem server {server.name} missing config_data")
                return []
            
            config = server.config_data
            filesystem_server = create_filesystem_server(
                allowed_directory=config.get('allowed_directory', ''),
                max_file_size=config.get('max_file_size', 10) * 1024 * 1024,
                allowed_extensions=config.get('allowed_extensions'),
                read_only=config.get('read_only', False),
                enable_logging=config.get('enable_logging', True)
            )
            
            capabilities = filesystem_server.get_capabilities()
            logger.info(f"Filesystem server {server.name} capabilities: {capabilities}")
            return capabilities
            
        except Exception as e:
            logger.error(f"Error testing filesystem server {server.name}: {e}")
            return []

    # --- Query Handling Methods (kept from original, note non-standard nature) ---
    # These methods contain logic specific to the *target APIs*, which is not
    # standard for a generic MCP client. A true MCP client would send a standard
    # query to an MCP server which would then translate it.
    def query_mcp_server(self, server: MCPServer, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Query an MCP server with a given query."""
        if not server.enabled:
            return {"error": "Server is disabled", "server": server.name}

        logger.info(f"Querying MCP server: {server.name} with query: {query[:100]}...")
        
        try:
            # Check if it's a filesystem server
            if hasattr(server, 'server_type') and server.server_type == 'filesystem':
                return self._handle_filesystem_query(server, query, context)
            
            # Check URL patterns to determine server type and handle accordingly
            if "googleapis.com/customsearch" in server.url:
                return self._handle_google_search_query(server, query)
            elif "serper.dev" in server.url:
                return self._handle_serper_search_query(server, query)
            elif "search.brave.com" in server.url:
                return self._handle_brave_search_query(server, query)
            elif "context7" in server.url.lower():
                return self._handle_context7_query(query, context)
            else:
                # Default handling for other servers
                return {"error": "Server type not supported", "server": server.name}
                
        except Exception as e:
            logger.error(f"Error querying MCP server {server.name}: {e}")
            return {"error": str(e), "server": server.name}

    # Helper function to fetch additional content from URLs (used by search handlers)
    def _fetch_additional_content(self, url: str) -> Optional[str]:
        """Attempts to fetch and parse content from a given URL using the consolidated scraping function."""
        try:
            from utils import robust_scrape_url
            return robust_scrape_url(url, timeout=10, max_retries=2)
        except Exception as e:
            logger.error(f"Error fetching content from {url}: {e}")
            return None


    # --- Specific API Query Handling Methods (kept from original) ---
    # These methods translate a generic query into specific API calls and format
    # the response. This should ideally be done by the MCP server implementation.
    def _handle_google_search_query(self, server: MCPServer, query: str) -> Dict[str, Any]:
        """Handle queries specifically for the Google Custom Search API."""
        logger.info(f"Handling Google Search query for '{server.name}': '{query[:100]}...'")
        try:
            if not server.auth_token:
                 return {"error": "Google Search API Key (auth_token) is not configured."}
            
            cx = server.cx
            if not cx:
                logger.error(f"Custom Search Engine ID (cx) is required for Google Search API server '{server.name}' and is not configured in its dedicated 'cx' field.")
                return {"error": "Custom Search Engine ID (cx) is not configured for this Google Search server. Please update it in the MCP Server Configuration."}

            params = {
                "key": server.auth_token,
                "cx": cx,
                "q": query,
                "num": 5 # Get 5 results by default
            }

            response = requests.get(server.url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                results = []
                if 'items' in data:
                    for item in data['items']:
                        url = item.get('link', '')
                        snippet = item.get('snippet', '')
                        additional_content = self._fetch_additional_content(url) if url else None

                        full_content = snippet
                        if additional_content:
                            full_content = f"{snippet}\n\n{additional_content}"

                        results.append({
                            "title": item.get('title', ''),
                            "link": url,
                            "snippet": snippet,
                            "content": full_content,
                            "source": "Google Search"
                        })

                return {
                    "query": query,
                    "results": results,
                    "total_results": data.get('searchInformation', {}).get('totalResults', '0'),
                    "search_time": data.get('searchInformation', {}).get('searchTime', 0)
                }
            else:
                logger.error(f"Error querying Google Search API: {response.status_code}. Response: {response.text}")
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error querying Google Search API: {e}")
            return {"error": f"Network error querying Google Search API: {e}"}
        except Exception as e:
            logger.error(f"Error handling Google Search query: {e}")
            logger.error(traceback.format_exc())
            return {"error": f"An unexpected error occurred: {e}"}

    def _handle_serper_search_query(self, server: MCPServer, query: str) -> Dict[str, Any]:
        """Handle queries specifically for the Serper.dev Search API."""
        logger.info(f"Handling Serper Search query for '{server.name}': '{query[:100]}...'")
        try:
            if not server.auth_token:
                 return {"error": "Serper Search API Key (auth_token) is not configured."}

            headers = {
                "X-API-KEY": server.auth_token,
                "Content-Type": "application/json"
            }
            payload = {"q": query, "num": 5}

            response = requests.post(server.url, headers=headers, json=payload, timeout=15)

            if response.status_code == 200:
                data = response.json()
                results = []
                if 'organic' in data:
                    for item in data['organic']:
                        url = item.get('link', '')
                        snippet = item.get('snippet', '')
                        additional_content = self._fetch_additional_content(url) if url else None

                        full_content = snippet
                        if additional_content:
                            full_content = f"{snippet}\n\n{additional_content}"

                        results.append({
                            "title": item.get('title', ''),
                            "link": url,
                            "snippet": snippet,
                            "content": full_content,
                            "source": "Serper Search"
                        })

                return {
                    "query": query,
                    "results": results,
                    "total_results": len(results),
                    "search_time": 0
                }
            else:
                logger.error(f"Error querying Serper Search API: {response.status_code}. Response: {response.text}")
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error querying Serper Search API: {e}")
            return {"error": f"Network error querying Serper Search API: {e}"}
        except Exception as e:
            logger.error(f"Error handling Serper Search query: {e}")
            logger.error(traceback.format_exc())
            return {"error": f"An unexpected error occurred: {e}"}

    def _handle_brave_search_query(self, server: MCPServer, query: str) -> Dict[str, Any]:
        """Handle queries specifically for the Brave Search API."""
        logger.info(f"Handling Brave Search query for '{server.name}': '{query[:100]}...'")
        try:
            if not server.auth_token:
                 return {"error": "Brave Search Subscription Token (auth_token) is not configured."}

            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": server.auth_token
            }
            params = {"q": query, "count": 5}

            response = requests.get(server.url, headers=headers, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                results = []

                # Brave API can return results in different top-level keys (web, news, etc.)
                # Prioritize 'web' results, then 'news', then look for a generic 'results' key.
                items = []
                if 'web' in data and 'results' in data['web']:
                    items = data['web']['results']
                    source_type = "Brave Search (Web)"
                elif 'news' in data and 'results' in data['news']:
                    items = data['news']['results']
                    source_type = "Brave Search (News)"
                elif 'results' in data: # Fallback for other types or formats
                     items = data['results']
                     source_type = "Brave Search"
                else:
                     logger.warning(f"Brave Search response did not contain expected 'web', 'news', or 'results' keys. Raw data keys: {data.keys()}")
                     # Return raw data if no expected structure found
                     return {
                        "query": query,
                        "results": [],
                        "raw_data": data,
                        "error": "Unexpected response format from Brave Search API.",
                        "total_results": 0,
                        "search_time": 0
                     }


                for item in items:
                    url = item.get('url', '') or item.get('link', '') # Brave uses 'url' in web, 'link' elsewhere sometimes
                    description = item.get('description', '') or item.get('snippet', '') # Brave uses 'description' in web, 'snippet' elsewhere sometimes
                    additional_content = self._fetch_additional_content(url) if url else None

                    full_content = description
                    if additional_content:
                        full_content = f"{description}\n\n{additional_content}"

                    results.append({
                        "title": item.get('title', ''),
                        "link": url,
                        "snippet": description,
                        "content": full_content,
                        "source": source_type
                    })

                return {
                    "query": query,
                    "results": results,
                    "total_results": len(results),
                    "search_time": 0
                }
            else:
                logger.error(f"Error querying Brave Search API: {response.status_code}. Response: {response.text}")
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error querying Brave Search API: {e}")
            return {"error": f"Network error querying Brave Search API: {e}"}
        except Exception as e:
            logger.error(f"Error handling Brave Search query: {e}")
            logger.error(traceback.format_exc())
            return {"error": f"An unexpected error occurred: {e}"}


    def _handle_context7_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle queries specifically for the Context7 MCP server (Simulated).

        Args:
            query: The query string, expected format: "library_name:request"
            context: Additional context for the query

        Returns:
            Dict[str, Any]: The response with documentation or code examples.
                            This is currently simulated.
        """
        logger.info(f"Handling simulated Context7 query: '{query}'")
        try:
            # Parse the query to extract library name and specific request
            if ":" in query:
                library_name, request = query.split(":", 1)
                library_name = library_name.strip()
                request = request.strip()
            else:
                library_name = query.strip()
                request = "general documentation"

            if not library_name:
                 return {
                     "error": "Context7 query format is 'library_name:request'. Please specify a library.",
                     "available_libraries": [lib["name"] for lib in self.get_context7_libraries()]
                 }


            # Get library details from the static list
            library = self.get_context7_library_details(library_name)
            if not library:
                return {
                    "error": f"Library '{library_name}' not found in Context7 (simulated).",
                    "available_libraries": [lib["name"] for lib in self.get_context7_libraries()]
                }

            # --- Simulated Response ---
            # In a real implementation, this would make an API call to the Context7 MCP server
            # using the library_name and request.
            simulated_content = f"""
Documentation for {library['name']} related to '{request}'

This is simulated content from the Context7 MCP client handler. In a real implementation,
this would contain actual documentation, API references, or code examples fetched
from a Context7 MCP server.

Example code for {library['name']} ({request}):
```python
# This is a simulated code example for {library['name']}
# Replace with actual code fetched from Context7
try:
    import {library['name'].lower().replace('.', '_')} # Example import
    print(f"Successfully imported {library['name']}")
    # Add more specific code based on 'request' here
    if "install" in request.lower():
        print(f"To install {library['name']}, use pip: pip install {library['name'].lower()}")
    elif "basic usage" in request.lower():
         print(f"Basic usage example for {library['name']}...")
         # Add a simple code snippet
    else:
         print(f"Simulated code for request: '{request}'")

except ImportError:
    print(f"Could not import {library['name']}. Make sure it is installed.")
except Exception as e:
    print(f"An error occurred during simulated {library['name']} usage: {e}")

```

For more details, visit the official documentation (simulated link):
https://context7.com/docs/{library['name'].lower().replace(' ', '-')}/{request.lower().replace(' ', '-') if request != 'general documentation' else ''}
"""

            return {
                "library": library["name"],
                "description": library["description"],
                "request": request,
                "content": simulated_content.strip(),
                "source": f"Context7 (Simulated)"
            }
        except Exception as e:
            logger.error(f"Error handling simulated Context7 query: {e}")
            logger.error(traceback.format_exc())
            return {"error": f"An unexpected error occurred handling Context7 query: {e}"}

    def _handle_filesystem_query(self, server: MCPServer, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle filesystem server queries using a robust JSON-based format."""
        try:
            from mcp_filesystem_server import create_filesystem_server
            import json
            import time
            
            if not hasattr(server, 'config_data'):
                return {"error": "Filesystem server missing configuration", "server": server.name}
            
            # --- Initialize the filesystem server ---
            config = server.config_data
            
            # Load folder permissions from folder_permissions.json
            folder_permissions = self._load_folder_permissions()
            
            filesystem_server = create_filesystem_server(
                allowed_directory=config.get('allowed_directory', ''),
                allowed_directories=folder_permissions,  # Pass the folder permissions
                max_file_size=config.get('max_file_size', 10) * 1024 * 1024,
                allowed_extensions=config.get('allowed_extensions'),
                read_only=config.get('read_only', False),
                enable_logging=config.get('enable_logging', True)
            )
            
            # --- Parse the JSON query ---
            try:
                request_data = json.loads(query)
                operation = request_data.get("operation")
                params = request_data.get("params", {})
            except json.JSONDecodeError:
                # For backward compatibility, also try to handle old colon-separated format
                logger.warning(f"Received non-JSON query, attempting legacy parsing: {query}")
                return {"error": "Invalid MCP request format. Please use JSON format: {\"operation\": \"operation_name\", \"params\": {\"param1\": \"value1\"}}", "query": query}
            except Exception as e:
                return {"error": f"Error parsing MCP request: {e}", "query": query}

            # --- Dispatch to the correct filesystem server method ---
            result = {}
            if operation == 'list_directory':
                directory = params.get("directory_path", "")
                result = filesystem_server.list_directory(directory)
                
            elif operation == 'read_file':
                file_path = params.get("file_path")
                if not file_path:
                    return {"error": "Missing 'file_path' parameter for read_file operation", "example": "{\"operation\": \"read_file\", \"params\": {\"file_path\": \"path/to/file.txt\"}}"}
                result = filesystem_server.read_file(file_path)
                
            elif operation == 'write_file':
                file_path = params.get("file_path")
                content = params.get("content")
                if not file_path or content is None:
                    return {"error": "Missing 'file_path' or 'content' parameter for write_file operation", "example": "{\"operation\": \"write_file\", \"params\": {\"file_path\": \"path/to/file.txt\", \"content\": \"file content\"}}"}
                result = filesystem_server.write_file(file_path, content, create_dirs=params.get("create_dirs", False))
                
            elif operation == 'delete_file':
                file_path = params.get("file_path")
                if not file_path:
                    return {"error": "Missing 'file_path' parameter for delete_file operation", "example": "{\"operation\": \"delete_file\", \"params\": {\"file_path\": \"path/to/file.txt\"}}"}
                result = filesystem_server.delete_file(file_path)
                
            elif operation == 'get_file_info':
                file_path = params.get("file_path")
                if not file_path:
                    return {"error": "Missing 'file_path' parameter for get_file_info operation", "example": "{\"operation\": \"get_file_info\", \"params\": {\"file_path\": \"path/to/file.txt\"}}"}
                result = filesystem_server.get_file_info(file_path)
                
            elif operation == 'search_files':
                pattern = params.get("pattern")
                if not pattern:
                    return {"error": "Missing 'pattern' parameter for search_files operation", "example": "{\"operation\": \"search_files\", \"params\": {\"pattern\": \"*.txt\", \"directory\": \"path/to/search\", \"recursive\": true}}"}
                directory = params.get("directory", "")
                recursive = params.get("recursive", True)
                result = filesystem_server.search_files(pattern, directory, recursive)
                
            elif operation == 'read_pdf_page':
                file_path = params.get("file_path")
                if not file_path:
                    return {"error": "Missing 'file_path' parameter for read_pdf_page operation", "example": "{\"operation\": \"read_pdf_page\", \"params\": {\"file_path\": \"path/to/file.pdf\", \"page_number\": 170}}"}
                page_number = params.get("page_number")
                start_page = params.get("start_page")
                end_page = params.get("end_page")
                result = filesystem_server.read_pdf_page(file_path, page_number, start_page, end_page)
                
            elif operation == 'search_pdf_content':
                file_path = params.get("file_path")
                search_term = params.get("search_term")
                if not file_path or not search_term:
                    return {"error": "Missing 'file_path' or 'search_term' parameter for search_pdf_content operation", "example": "{\"operation\": \"search_pdf_content\", \"params\": {\"file_path\": \"path/to/file.pdf\", \"search_term\": \"climate change\", \"case_sensitive\": false}}"}
                case_sensitive = params.get("case_sensitive", False)
                result = filesystem_server.search_pdf_content(file_path, search_term, case_sensitive)
                
            elif operation == 'get_pdf_info':
                file_path = params.get("file_path")
                if not file_path:
                    return {"error": "Missing 'file_path' parameter for get_pdf_info operation", "example": "{\"operation\": \"get_pdf_info\", \"params\": {\"file_path\": \"path/to/file.pdf\"}}"}
                result = filesystem_server.get_pdf_info(file_path)
                
            else:
                available_ops = ["list_directory", "read_file", "write_file", "delete_file", "get_file_info", "search_files", "read_pdf_page", "search_pdf_content", "get_pdf_info"]
                return {"error": f"Unknown or unsupported filesystem operation: '{operation}'", "available_operations": available_ops}
            
            # Add server info and metadata to result
            result["server"] = server.name
            result["server_type"] = "filesystem"
            result["timestamp"] = time.time()
            result["operation"] = operation
            
            return result
            
        except Exception as e:
            logger.error(f"Error handling filesystem query for {server.name}: {e}")
            return {"error": str(e), "server": server.name, "help": "Use JSON format: {\"operation\": \"operation_name\", \"params\": {\"param1\": \"value1\"}}"}

    def get_available_mcp_servers(self) -> List[Dict[str, Any]]:
        """Get a list of popular MCP servers that can be added."""
        # Returns the hardcoded list loaded during initialization
        return self._available_servers_list
    
    def move_server_to_available(self, server_name: str) -> bool:
        """Move a configured server back to available servers list.
        
        Args:
            server_name: Name of the server to move
            
        Returns:
            bool: True if successful, False otherwise
        """
        if server_name not in self.servers:
            logger.warning(f"Server '{server_name}' not found in configured servers")
            return False
        
        server = self.servers[server_name]
        
        # Create available server entry
        available_server = {
            "name": server.name,
            "url": server.url,
            "description": server.description,
            "capabilities": server.capabilities,
            "server_type": getattr(server, 'server_type', ''),
            "auth_token": server.auth_token,
            "cx": server.cx
        }
        
        # Add to available servers if not already there
        existing_names = [s.get('name') for s in self._available_servers_list]
        if server.name not in existing_names:
            self._available_servers_list.append(available_server)
        
        # Remove from configured servers
        del self.servers[server_name]
        self.save_servers()
        
        logger.info(f"Server '{server_name}' moved to available servers")
        return True
    
    def move_server_to_configured(self, server_data: Dict[str, Any]) -> bool:
        """Move an available server to configured servers.
        
        Args:
            server_data: Available server data dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        server_name = server_data.get('name')
        if not server_name:
            logger.warning("Available server data missing name")
            return False
        
        if server_name in self.servers:
            logger.warning(f"Server '{server_name}' already configured")
            return False
        
        # Create MCPServer instance
        server = MCPServer(
            name=server_data.get('name', ''),
            url=server_data.get('url', ''),
            description=server_data.get('description', ''),
            enabled=True,  # Default to enabled
            auth_token=server_data.get('auth_token', ''),
            capabilities=server_data.get('capabilities', []),
            cx=server_data.get('cx', ''),
            server_type=server_data.get('server_type', ''),
            config_data=server_data.get('config_data', {})
        )
        
        # Add to configured servers
        self.servers[server_name] = server
        self.save_servers()
        
        # Remove from available servers
        self._available_servers_list = [
            s for s in self._available_servers_list 
            if s.get('name') != server_name
        ]
        
        logger.info(f"Server '{server_name}' moved to configured servers")
        return True

    def get_context7_libraries(self) -> List[Dict[str, Any]]:
        """Get available libraries from Context7 (Simulated)."""
        # Returns the hardcoded list loaded during initialization
        return self._context7_libraries_list

    def get_context7_library_details(self, library_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific Context7 library (Simulated)."""
        libraries = self.get_context7_libraries()
        for library in libraries:
            if library["name"].lower() == library_name.lower():
                return library
        return {} # Return empty dict if not found


    def prepare_mcp_context(self, prompt: str) -> Dict[str, Any]:
        """Prepare MCP context for a given prompt.

        This analyzes the prompt and determines which MCP servers might be relevant.
        (Basic implementation - could be enhanced with NLP).

        Args:
            prompt: The user prompt

        Returns:
            Dict[str, Any]: MCP context information to include with agent requests
        """
        enabled_servers = self.get_enabled_servers()
        if not enabled_servers:
            return {}

        # Build a dictionary mapping server names to their capabilities
        server_capabilities = {
            server.name: server.capabilities for server in enabled_servers
        }

        # Basic relevance check (can be expanded)
        relevant_servers = []
        prompt_lower = prompt.lower()

        for server in enabled_servers:
            # Check if server name or description is in the prompt
            if server.name.lower() in prompt_lower or server.description.lower() in prompt_lower:
                relevant_servers.append(server.name)
                continue # Already added, move to next server

            # Check if any capability is mentioned in the prompt
            if any(cap.lower() in prompt_lower for cap in server.capabilities):
                 relevant_servers.append(server.name)
                 continue

            # Specific checks based on server type/name
            if server.name == "Google Search" or server.name == "Serper Search" or server.name == "Brave Search":
                 if any(word in prompt_lower for word in ["search", "find", "look up", "web", "internet"]):
                     relevant_servers.append(server.name)
                     continue
            elif server.name == "GitHub":
                 if any(word in prompt_lower for word in ["code", "repository", "repo", "issue", "pull request", "pr"]):
                     relevant_servers.append(server.name)
                     continue
            elif server.name == "Context7":
                 if any(word in prompt_lower for word in ["documentation", "docs", "how to", "example", "library", "api"]):
                     relevant_servers.append(server.name)
                     continue
            # Add more specific checks here for other server types

        # Remove duplicates and sort
        relevant_servers = sorted(list(set(relevant_servers)))

        context = {
            "available_servers": list(server_capabilities.keys()), # List all enabled servers
            "capabilities": server_capabilities, # Provide capabilities for all enabled servers
            "relevant_servers_for_prompt": relevant_servers, # Suggest servers based on prompt analysis
            "folder_permissions": self._get_folder_permissions_context(), # Available folder access
        }

        # Add specific instructions for Context7 if enabled
        context7_server = self.get_server("Context7")
        if context7_server and context7_server.enabled:
             context["context7_info"] = {
                 "available_libraries": [lib["name"] for lib in self.get_context7_libraries()],
                 "usage_instructions": "To access documentation or code examples from Context7, use a query like: [MCP:Context7:library_name:request]"
             }


        logger.info(f"Prepared MCP context. Relevant servers for prompt: {relevant_servers}")
        return context

    def _load_folder_permissions(self) -> Dict[str, Dict[str, bool]]:
        """Load folder permissions from folder_permissions.json."""
        try:
            permissions_file = os.path.join(self.config_dir, "folder_permissions.json")
            if os.path.exists(permissions_file):
                with open(permissions_file, 'r', encoding='utf-8') as f:
                    permissions = json.load(f)
                    logger.info(f"Loaded folder permissions for {len(permissions)} directories")
                    return permissions
        except Exception as e:
            logger.warning(f"Failed to load folder permissions: {e}")
        
        return {}

    def _get_folder_permissions_context(self) -> Dict[str, Any]:
        """Get folder permissions context for agent prompts."""
        try:
            permissions = self._load_folder_permissions()
            
            # Format folder permissions for agent context
            folder_context = {}
            for folder_path, permissions_dict in permissions.items():
                allowed_operations = [op for op, allowed in permissions_dict.items() if allowed]
                folder_context[folder_path] = {
                    "allowed_operations": allowed_operations,
                    "readable": permissions_dict.get("read_file", False),
                    "writable": permissions_dict.get("write_file", False),
                    "can_list": permissions_dict.get("list_directory", False)
                }
            
            return folder_context
        except Exception as e:
            logger.error(f"Error getting folder permissions context: {e}")
            return {}

# Create a global instance for easy access
# Ensure default servers are added only if the config file doesn't exist or is empty
mcp_client = MCPClient()

def add_default_servers_if_empty():
    """Add default MCP servers if no servers are currently loaded."""
    if not mcp_client.servers:
        logger.info("No servers loaded, adding default servers.")
        # GitHub MCP Server
        mcp_client.add_server(MCPServer(
            name="GitHub",
            url="https://api.github.com", # NOTE: This is the GitHub API URL, not an MCP server URL.
                                           # A real GitHub MCP server would sit in front of this.
            description="Access GitHub repositories, issues, and pull requests",
            capabilities=[], # Capabilities will be discovered on test/save
            auth_token=""  # Add your GitHub Personal Access Token here
        ))

        # Google Search MCP Server
        mcp_client.add_server(MCPServer(
            name="Google Search",
            url="https://www.googleapis.com/customsearch/v1", # NOTE: This is the Google API URL.
            description="Search the web with Google Custom Search API (Requires API Key and CX)",
            capabilities=[],
            auth_token="",  # Add your Google API Key here
            cx=""  # Add your Custom Search Engine ID here
        ))

        # Brave Search MCP Server
        mcp_client.add_server(MCPServer(
            name="Brave Search",
            url="https://api.search.brave.com/res/v1/web/search", # NOTE: This is the Brave API URL.
            description="Search the web with Brave Search",
            capabilities=[],
            auth_token=""  # Add your Brave Search API key here
        ))

        # Context7 MCP Server (Simulated)
        mcp_client.add_server(MCPServer(
            name="Context7",
            url="https://api.context7.com/v1",  # NOTE: This is a placeholder URL.
                                                # A real Context7 MCP server would have a specific endpoint.
            description="Access up-to-date documentation and code examples for popular libraries (Requires API Key)",
            capabilities=["documentation", "code_examples", "api_reference"], # Assume these for the simulated one
            auth_token=""  # Add your Context7 API token here
        ))

        # Serper.dev Search MCP Server (Alternative to Google Search)
        mcp_client.add_server(MCPServer(
            name="Serper Search",
            url="https://api.serper.dev/search", # NOTE: This is the Serper API URL.
            description="Fast and affordable Google Search API alternative (Requires API Key)",
            capabilities=[],
            auth_token=""  # Add your Serper API Key here
        ))
        mcp_client.save_servers() # Save after adding defaults
    else:
        logger.info("Servers already loaded, skipping adding default servers.")


# Add default servers if none are loaded initially
add_default_servers_if_empty()