# utils.py
import sys
import json
import os
import time
import ssl
import logging
import warnings
import tempfile
import chardet
import traceback
import concurrent.futures
from pathlib import Path
from random import uniform
from typing import Dict, Any, List, Optional, Union, Iterator, Tuple
from concurrent.futures import ThreadPoolExecutor
from requests.exceptions import RequestException, Timeout, SSLError

# Third-party imports
import openai
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import googleapiclient.discovery
import google.generativeai as genai
from anthropic import Anthropic

# Local imports
from model_settings import settings_manager
from config import config_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Filter out specific logging messages
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('openai').setLevel(logging.WARNING)
warnings.filterwarnings('ignore', message='file_cache is only supported with oauth2client<4.0.0')

logger = logging.getLogger(__name__)


# Configuration loading is now handled by the global config_manager
# The load_config function has been removed - use config_manager directly

def get_ollama_models():
    """Fetch available models from local Ollama instance"""
    import requests
    import subprocess
    import json

    try:
        # Get base URL from settings manager
        ollama_base_url = settings_manager.get_ollama_url()
        ollama_api_tags_url = f"{ollama_base_url.rstrip('/')}/api/tags"
        
        # First try the API endpoint
        response = requests.get(ollama_api_tags_url)
        if response.status_code == 200:
            return [model['name'] for model in response.json().get('models', [])]
    except:
        # Fallback to command line
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            if result.returncode == 0:
                # Parse the output, skipping the header line
                lines = result.stdout.strip().split('\n')[1:]
                # Extract model names from the first column
                models = [line.split()[0] for line in lines if line.strip()]
                return models
            return []
        except:
            return []

class RateLimiter:
    """
    A rate limiter class that implements exponential backoff and jitter for API rate limiting.

    Attributes:
        delay (float): Minimum delay between requests in seconds
        last_request (float): Timestamp of the last request
        backoff_time (float): Current backoff time in seconds
        max_backoff (float): Maximum backoff time in seconds
    """

    def __init__(self, requests_per_second: float = 1.0, max_backoff: float = 32.0):
        """
        Initialize the rate limiter.

        Args:
            requests_per_second (float): Maximum number of requests allowed per second
            max_backoff (float): Maximum backoff time in seconds
        """
        if requests_per_second <= 0:
            raise ValueError("requests_per_second must be positive")
        self.delay = 1.0 / requests_per_second
        self.last_request = 0
        self.backoff_time = 1.0  # Initial backoff time
        self.max_backoff = max_backoff

    def wait(self) -> None:
        """
        Wait if necessary to respect the rate limit.
        Adds random jitter to prevent thundering herd problems.
        """
        now = time.time()
        diff = now - self.last_request
        if diff < self.delay:
            wait_time = self.delay - diff + uniform(0.1, 0.3)  # Add random jitter
            time.sleep(wait_time)
        self.last_request = time.time()

    def backoff(self) -> None:
        """
        Implement exponential backoff when rate limits are hit.
        Resets backoff time after successful request.
        """
        time.sleep(self.backoff_time)
        self.backoff_time = min(self.backoff_time * 2, self.max_backoff)

    def reset_backoff(self) -> None:
        """Reset the backoff time to initial value after successful request."""
        self.backoff_time = 1.0


# Create separate rate limiters for different services
google_rate_limiter = RateLimiter(1)  # 1 request per second for Google
groq_rate_limiter = RateLimiter(1)  # 0.5 requests per second for Groq (more conservative)
deepseek_rate_limiter = RateLimiter(0.5)  # 0.5 requests per second for DeepSeek
general_rate_limiter = RateLimiter(1)

rate_limiter = RateLimiter()


def create_unverified_ssl_context():
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


# Use global config_manager for all API keys
OPENAI_API_KEY = config_manager.get('OPENAI_API_KEY')
GOOGLE_API_KEY = config_manager.get('GOOGLE_API_KEY')
GOOGLE_SEARCH_ENGINE_ID = config_manager.get('GOOGLE_SEARCH_ENGINE_ID')
GEMINI_API_KEY = config_manager.get('GEMINI_API_KEY')
ANTHROPIC_API_KEY = config_manager.get('ANTHROPIC_API_KEY')
GROQ_API_KEY = config_manager.get('GROQ_API_KEY')
GROK_API_KEY = config_manager.get('GROK_API_KEY')
DEEPSEEK_API_KEY = config_manager.get('DEEPSEEK_API_KEY')
OPENROUTER_API_KEY = config_manager.get('OPENROUTER_API_KEY')

# Check if any API keys are available and log a warning if none are found
if not any([OPENAI_API_KEY, GEMINI_API_KEY, ANTHROPIC_API_KEY, 
           GROQ_API_KEY, GROK_API_KEY, DEEPSEEK_API_KEY, OPENROUTER_API_KEY]):
    logger.warning("Groq API key not found. Groq features will be disabled.")
    logger.warning("OpenAI API key not found. OpenAI features will be disabled.")
    logger.warning("Anthropic API key not found. Anthropic features will be disabled.")
    logger.warning("Grok API key not found. Grok features will be disabled.")

# Configure API clients with proper error handling
try:
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
    else:
        logger.warning("Gemini API key not found. Gemini features will be disabled.")
except Exception as e:
    logger.warning(f"Error configuring Gemini client: {e}")

try:
    if GROQ_API_KEY:
        groq_client = openai.OpenAI(base_url=settings_manager.get_groq_url(), api_key=GROQ_API_KEY)
    else:
        groq_client = None
        logger.warning("Groq API key not found. Groq features will be disabled.")
except Exception as e:
    groq_client = None
    logger.warning(f"Error initializing Groq client: {e}")

try:
    from openai import OpenAI
    if OPENAI_API_KEY:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
    else:
        openai_client = None
        logger.warning("OpenAI API key not found. OpenAI features will be disabled.")
except ImportError:
    if OPENAI_API_KEY:
        openai_client = openai
        openai_client.api_key = OPENAI_API_KEY
    else:
        openai_client = None
        logger.warning("OpenAI API key not found. OpenAI features will be disabled.")
except Exception as e:
    openai_client = None
    logger.warning(f"Error initializing OpenAI client: {e}")

try:
    if ANTHROPIC_API_KEY:
        anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
    else:
        anthropic_client = None
        logger.warning("Anthropic API key not found. Anthropic features will be disabled.")
except ImportError:
    anthropic_client = None
    logger.warning("Anthropic library not found. Anthropic features will be disabled.")
except Exception as e:
    anthropic_client = None
    logger.warning(f"Error initializing Anthropic client: {e}")

try:
    if GROK_API_KEY:
        grok_client = OpenAI(api_key=GROK_API_KEY, base_url=settings_manager.get_grok_url())
    else:
        grok_client = None
        logger.warning("Grok API key not found. Grok features will be disabled.")
except ImportError:
    grok_client = None
    logger.warning("OpenAI library not found. Grok features will be disabled.")
except Exception as e:
    grok_client = None
    logger.warning(f"Error initializing Grok client: {e}")

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'DNT': '1'
    })
    return session


def is_relevant_url(url):
    """
    Check if a URL is relevant for scraping based on domain exclusions.
    """
    irrelevant_domains = [
        'youtube.com', 'facebook.com', 'instagram.com',
        'ncbi.nlm.nih.gov', 'pinterest.com', 'reddit.com',
        'tiktok.com'
    ]
    return not any(domain in url.lower() for domain in irrelevant_domains)


def google_search(query, num_results=3, internet_enabled=True):
    """
    Perform Google search using the global config_manager for API credentials.
    
    Args:
        query (str): Search query
        num_results (int): Number of results to return
        internet_enabled (bool): Whether internet search is enabled
        
    Returns:
        Tuple[List, List]: Search results and URLs
    """
    if not internet_enabled:
        return [], []

    # Get keys from the global config manager
    api_key = config_manager.get('GOOGLE_API_KEY')
    search_engine_id = config_manager.get('GOOGLE_SEARCH_ENGINE_ID')
    
    if not api_key or not search_engine_id:
        logger.error("Google Search API key or Search Engine ID is missing.")
        return [], []

    try:
        google_rate_limiter.wait()
        service = googleapiclient.discovery.build(
            "customsearch",
            "v1",
            developerKey=api_key,
            cache_discovery=False  # Disable discovery cache
        )
        res = service.cse().list(
            q=query,
            cx=search_engine_id,
            num=num_results
        ).execute()

        urls = []
        if 'items' in res:
            urls = [item['link'] for item in res['items']]

        return res.get('items', []), urls
    except Exception as e:
        logger.error(f"Google Search error: {str(e)}")
        return [], []

def call_ollama_api(model: str, prompt: str, base_url: str = None) -> str:
    """
    Call the Ollama API to generate a response with optimized performance.

    Args:
        model (str): Name of the Ollama model to use
        prompt (str): Input prompt text
        base_url (str): Base URL for Ollama API (defaults to settings manager URL)

    Returns:
        str: Generated response text
    """
    import requests
    import json

    # Use settings manager URL if not provided
    if base_url is None:
        base_url = settings_manager.get_ollama_url()

    try:
        url = f"{base_url}/api/generate"

        # Simplified payload with minimal parameters
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9
            }
        }

        # Use a session with shorter timeouts
        session = requests.Session()
        response = session.post(url, json=payload, timeout=(5, 30))
        response.raise_for_status()

        result = response.json()
        return result.get('response', '')

    except requests.exceptions.RequestException as e:
        logging.error(f"Ollama API error: {str(e)}")
        raise Exception(f"Ollama API error: {str(e)}")
    finally:
        # Ensure session is closed
        if 'session' in locals():
            session.close()

def call_deepseek_api(model: str, prompt: str, api_key: str, stream: bool = True,
                  temperature: float = 0.7, max_tokens: int = 4000, top_p: float = 0.9,
                  stop: Optional[List[str]] = None) -> Union[str, Iterator[str]]:
    """
    Call the DeepSeek API to generate a response using OpenAI SDK.

    Args:
        model (str): Name of the DeepSeek model to use
        prompt (str): Input prompt text
        api_key (str): DeepSeek API key
        stream (bool): Whether to stream the response or not
        temperature (float): Controls randomness in generation (0.0 to 1.0)
        max_tokens (int): Maximum number of tokens to generate
        top_p (float): Controls diversity via nucleus sampling (0.0 to 1.0)
        stop (List[str], optional): List of strings that stop generation when encountered

    Returns:
        Union[str, Iterator[str]]: Generated response text if stream=False, or a generator of response chunks if stream=True

    Raises:
        ValueError: If API key is missing
        Exception: For other API errors
    """
    try:
        if not api_key:
            raise ValueError("DeepSeek API key is missing")

        from openai import OpenAI
        client = OpenAI(
            api_key=api_key,
            base_url=settings_manager.get_deepseek_url()
        )

        # Prepare messages and truncate if needed
        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": prompt[:4000] if len(prompt) > 4000 else prompt}
        ]

        # Apply rate limiting
        deepseek_rate_limiter.wait()

        # Create parameters dictionary
        params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "stream": stream
        }

        # Add stop sequences if provided
        if stop and len(stop) > 0:
            params["stop"] = stop

        # Make the API call
        response = client.chat.completions.create(**params)

        if stream:
            return response  # Return the stream object for processing by the worker
        else:
            content = response.choices[0].message.content
            logger.info(f"[DeepSeek] Response received, length: {len(content)} characters")
            return sanitize_response(content)

    except ValueError as e:
        logger.error(f"[DeepSeek] Configuration error: {str(e)}")
        raise
    except Exception as e:
        error_msg = f"DeepSeek API error: {str(e)}"
        logger.error(f"[DeepSeek] {error_msg}")
        return f"Error: {error_msg}"

def scrape_content(url: str, timeout: int = 15, max_retries: int = 3) -> str:
    """
    Scrape content from a URL with retry mechanism and content cleaning.

    Args:
        url (str): URL to scrape
        timeout (int): Request timeout in seconds
        max_retries (int): Maximum number of retry attempts

    Returns:
        str: Extracted and cleaned content, or empty string if failed
    """
    session = create_session()

    for attempt in range(max_retries):
        try:
            rate_limiter.wait()
            response = session.get(url, timeout=timeout)
            response.raise_for_status()

            # Handle encoding
            if response.encoding == 'ISO-8859-1':
                encodings = chardet.detect(response.content)
                if encodings['encoding']:
                    response.encoding = encodings['encoding']

            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove unwanted elements
            for element in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'iframe', 'noscript']):
                element.decompose()

            # Try multiple content extraction methods
            content = []

            # Method 1: Main content area
            main_content = soup.find(['main', 'article', 'div[role="main"]', 'div[class*="content"]'])
            if main_content:
                content.extend(main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']))

            # Method 2: All content if main area not found
            if not content:
                content = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])

            # Extract and clean text
            text = ' '.join([p.get_text().strip() for p in content])
            text = ' '.join(text.split())

            # Limit content length and add source attribution
            return f"{text[:5000]}... (Source: {url})"

        except SSLError:
            logger.warning(f"SSL Error for {url}, attempting unverified context")
            try:
                ssl_context = create_unverified_ssl_context()
                response = session.get(url, timeout=timeout, verify=False)
                response.raise_for_status()
                logger.warning(f"Successfully accessed {url} with unverified SSL context")
            except Exception as e:
                logger.warning(f"Failed to access {url} even with unverified SSL: {e}")
                if attempt == max_retries - 1:
                    return ""
                continue

        except RequestException as e:
            wait_time = (attempt + 1) * 2  # Exponential backoff
            if isinstance(e, Timeout):
                logger.warning(f"Timeout error scraping {url} (attempt {attempt + 1}/{max_retries})")
            elif response and response.status_code in [403, 429]:
                logger.warning(f"Access denied ({response.status_code}) to {url}")
                time.sleep(wait_time)  # Wait longer for rate limit errors
            else:
                logger.warning(f"Error scraping content from {url}: {e}")
            if attempt == max_retries - 1:
                return ""
            time.sleep(wait_time)
            continue

    return ""

def sanitize_response(response_text):
    """Sanitize and decode response text safely."""
    if not isinstance(response_text, str):
        try:
            if isinstance(response_text, bytes):
                return response_text.decode('utf-8', errors='ignore')
            return str(response_text)
        except Exception as e:
            logging.error(f"Error sanitizing response: {e}")
            return "Error: Unable to process response"
    return response_text


def extract_info_from_web(query: str, internet_enabled: bool = True) -> Tuple[str, List[str]]:
    """
    Extract information from web search results using global config_manager.

    Args:
        query (str): Search query
        internet_enabled (bool): Whether internet access is enabled

    Returns:
        Tuple[str, List[str]]: Tuple containing extracted content and list of relevant URLs
    """
    if not internet_enabled:
        return "Internet access is currently disabled.", []

    try:
        content = ""
        search_results, urls = google_search(query, internet_enabled=internet_enabled)

        if not search_results:
            logger.warning(f"No search results found for query: {query}")
            return content, []

        relevant_urls = [url for url in urls if is_relevant_url(url)]

        if not relevant_urls:
            logger.warning(f"No relevant URLs found for query: {query}")
            return content, []

        # Use ThreadPoolExecutor for parallel processing
        max_workers = min(len(relevant_urls), 3)  # Limit concurrent requests
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {
                executor.submit(scrape_content, url): url
                for url in relevant_urls
            }

            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    data = future.result()
                    if data:
                        content += f"\n{data}\n\n"
                except Exception as e:
                    logger.error(f"Error fetching {url}: {e}")
                    continue

        return content, relevant_urls

    except Exception as e:
        logger.error(f"Error in web extraction: {e}")
        return "", []


# --- OpenRouter Model Fetch ---
def get_openrouter_models(api_key=None):
    """Fetch available models from OpenRouter API"""
    import requests
    openrouter_base_url = settings_manager.get_openrouter_url()
    url = f"{openrouter_base_url}/models"
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            # The models are usually in the 'data' key as a list
            return [model['id'] for model in data.get('data', [])]
        else:
            logger.error(f"OpenRouter API error: {response.status_code} {response.text}")
            return []
    except Exception as e:
        logger.error(f"OpenRouter API error: {str(e)}")
        return []


def get_groq_models(api_key=None):
    """Fetch available models from Groq API"""
    import requests
    groq_base_url = "https://api.groq.com/openai/v1"  # Groq's OpenAI-compatible endpoint
    url = f"{groq_base_url}/models"
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            # The models are usually in the 'data' key as a list
            return [model['id'] for model in data.get('data', [])]
        else:
            logger.error(f"Groq API error: {response.status_code} {response.text}")
            return []
    except Exception as e:
        logger.error(f"Groq API error: {str(e)}")
        return []


def get_requesty_models(api_key=None):
    """Fetch available models from Requesty API"""
    import requests
    requesty_base_url = "https://router.requesty.ai/v1"  # Base URL for Requesty
    url = f"{requesty_base_url}/models"
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            # Assuming Requesty follows the OpenAI format with a 'data' key
            return [model['id'] for model in data.get('data', [])]
        else:
            logger.error(f"Requesty API error: {response.status_code} {response.text}")
            return []
    except Exception as e:
        logger.error(f"Requesty API error: {str(e)}")
        return []


def robust_scrape_url(url: str, timeout: int = 15, max_retries: int = 2, 
                      main_content_selectors: Optional[List[str]] = None) -> Optional[str]:
    """
    Robust web scraping function that consolidates scraping logic from multiple modules.
    
    Args:
        url: The URL to scrape
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        main_content_selectors: Custom CSS selectors for main content
        
    Returns:
        Extracted text content with source attribution, or None if failed
    """
    session = create_session()
    if main_content_selectors is None:
        main_content_selectors = ['main', 'article', 'div[role="main"]', 
                                  'div[class*="content"]', 'div[class*="article"]', 
                                  'div[class*="post"]'] # Common selectors

    for attempt in range(max_retries):
        try:
            general_rate_limiter.wait()
            response = session.get(url, timeout=timeout, allow_redirects=True)
            response.raise_for_status()

            # Encoding detection
            content_bytes = response.content
            detected_encoding = chardet.detect(content_bytes)['encoding']
            html_text = content_bytes.decode(detected_encoding or response.encoding or 'utf-8', errors='replace')

            soup = BeautifulSoup(html_text, 'html.parser')

            for noisy_tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript', 'link', 'meta']):
                noisy_tag.decompose()
            
            extracted_text = ""
            # Try specific selectors first
            for selector in main_content_selectors:
                main_area = soup.select_one(selector)
                if main_area:
                    extracted_text = main_area.get_text(separator=' ', strip=True)
                    break
            
            if not extracted_text: # Fallback to body if no specific selector worked
                body = soup.find('body')
                if body:
                    extracted_text = body.get_text(separator=' ', strip=True)
            
            if not extracted_text:
                logger.warning(f"Could not extract meaningful text from {url}")
                return None

            cleaned_text = ' '.join(extracted_text.split()) # Normalize whitespace
            
            # Limit length and add source
            max_len = 5000
            if len(cleaned_text) > max_len:
                # Try to truncate at a sentence boundary
                truncated_text = cleaned_text[:max_len]
                last_period = truncated_text.rfind('.')
                if last_period != -1:
                    cleaned_text = truncated_text[:last_period+1] + "..."
                else:
                    cleaned_text = truncated_text + "..."
            
            return f"{cleaned_text} (Source: {url})"

        except requests.exceptions.SSLError as ssl_e:
            logger.warning(f"SSL Error for {url} (Attempt {attempt+1}/{max_retries}): {ssl_e}. Trying with verify=False.")
            try:
                response = session.get(url, timeout=timeout, verify=False, allow_redirects=True) # One attempt with verify=False
                response.raise_for_status()
                
                # Repeat encoding and parsing for unverified request
                content_bytes = response.content
                detected_encoding = chardet.detect(content_bytes)['encoding']
                html_text = content_bytes.decode(detected_encoding or response.encoding or 'utf-8', errors='replace')
                
                soup = BeautifulSoup(html_text, 'html.parser')
                
                for noisy_tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript', 'link', 'meta']):
                    noisy_tag.decompose()
                
                extracted_text = ""
                for selector in main_content_selectors:
                    main_area = soup.select_one(selector)
                    if main_area:
                        extracted_text = main_area.get_text(separator=' ', strip=True)
                        break
                
                if not extracted_text:
                    body = soup.find('body')
                    if body:
                        extracted_text = body.get_text(separator=' ', strip=True)
                
                if not extracted_text:
                    logger.warning(f"Could not extract meaningful text from {url} (unverified)")
                    return None

                cleaned_text = ' '.join(extracted_text.split())
                
                max_len = 5000
                if len(cleaned_text) > max_len:
                    truncated_text = cleaned_text[:max_len]
                    last_period = truncated_text.rfind('.')
                    if last_period != -1:
                        cleaned_text = truncated_text[:last_period+1] + "..."
                    else:
                        cleaned_text = truncated_text + "..."
                
                return f"{cleaned_text} (Source: {url})"
                
            except Exception as unverified_e:
                logger.error(f"Failed to access {url} even with verify=False: {unverified_e}")
                if attempt == max_retries - 1: 
                    return None
            # No time.sleep here, as SSLError is not typically a rate limit issue
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request error scraping {url} (Attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt) # Exponential backoff
            else:
                return None # Max retries reached
        except Exception as e: # Catch other parsing errors
            logger.error(f"Unexpected error processing {url} (Attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                return None

# Update the imports section at the end
__all__ = ['OPENAI_API_KEY', 'GOOGLE_API_KEY', 'GOOGLE_SEARCH_ENGINE_ID',
           'GEMINI_API_KEY', 'ANTHROPIC_API_KEY', 'GROQ_API_KEY', 'GROK_API_KEY', 'DEEPSEEK_API_KEY',
           'OPENROUTER_API_KEY', 'SERPER_API_KEY', 'google_search', 'extract_info_from_web',
           'groq_rate_limiter', 'call_deepseek_api', 'get_openrouter_models', 'get_requesty_models', 'get_groq_models']