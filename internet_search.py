# internet_search.py
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Set
import concurrent.futures
import logging
import json
import time
import math
import hashlib
import re
from pathlib import Path
import tempfile
from datetime import datetime
from urllib.parse import urlparse

# Third-party imports
import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Represents a single search result with metadata and content."""
    content: str
    url: str
    relevance_score: float
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_real_time: bool = False
    source_type: str = 'web'

    def __post_init__(self):
        """Validate and clean up the data after initialization."""
        if not isinstance(self.metadata, dict):
            self.metadata = {}
        if not isinstance(self.relevance_score, (int, float)):
            self.relevance_score = 0.0
        if not isinstance(self.timestamp, str):
            self.timestamp = datetime.now().isoformat()

class EnhancedSearchManager:
    """
    Enhanced search manager that handles multiple search sources and real-time data.

    Attributes:
        config_manager: Configuration manager instance
        output_dir: Directory for caching search results
        retrieval_modules: List of configured search modules
        session: Requests session for HTTP requests
        real_time_apis: Dictionary of real-time API endpoints
    """

    def __init__(self, config_manager):
        """
        Initialize the search manager.

        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self._setup_output_directory()
        self._setup_retrieval_modules()
        self._setup_session()
        self._setup_real_time_apis()

    def _setup_output_directory(self) -> None:
        """Set up the output directory for caching results."""
        self.output_dir = Path(tempfile.mkdtemp()) / "search_results"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _setup_session(self) -> None:
        """Set up the requests session with appropriate headers."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    def _setup_real_time_apis(self) -> None:
        """Set up real-time API endpoints configuration."""
        self.real_time_apis = {
            # Finance & Crypto
            'crypto': 'https://api.coingecko.com/api/v3',
            'exchange_rates': 'https://open.er-api.com/v6',
            'stocks': 'https://api.polygon.io/v2',

            # Time & Date
            'timezone': 'http://worldtimeapi.org/api',
            'holidays': 'https://date.nager.at/api/v3',

            # General Data
            'ip_info': 'https://ipapi.co',
            'countries': 'https://restcountries.com/v3.1',

            # Weather & Environment
            'weather': 'https://api.openweathermap.org/data/2.5',
            'air_quality': 'https://api.waqi.info/feed'
        }

    def _setup_retrieval_modules(self) -> None:
        """Initialize available search services based on API keys."""
        self.retrieval_modules = []

        if serper_api_key := self.config_manager.get('SERPER_API_KEY'):
            self.retrieval_modules.append({
                'name': 'serper',
                'api_key': serper_api_key,
                'params': {'autocorrect': True, 'num': 3, 'page': 1}
            })

        if google_api_key := self.config_manager.get('GOOGLE_API_KEY'):
            self.retrieval_modules.append({
                'name': 'google',
                'api_key': google_api_key,
                'search_engine_id': self.config_manager.get('GOOGLE_SEARCH_ENGINE_ID'),
                'params': {'num': 3}
            })

    def search(self, query: str) -> List[SearchResult]:
        """
        Perform an enhanced search with real-time data priority.

        Args:
            query (str): Search query

        Returns:
            List[SearchResult]: List of search results
        """
        try:
            # Check if query requires real-time data
            if self._is_time_sensitive_query(query):
                real_time_results = self._get_real_time_data(query)
                if real_time_results:
                    return real_time_results

            # Check cache with shorter expiry for time-sensitive queries
            cache_duration = 60 if self._is_time_sensitive_query(query) else 3600
            cached_results = self.get_cached_results(query, max_age=cache_duration)
            if cached_results:
                return cached_results

            # Perform web search
            all_results = self._perform_web_search(query)
            if not all_results:
                return []

            # Process and cache results
            final_results = self._process_results(all_results, query)
            self.cache_results(query, final_results)
            return final_results

        except Exception as e:
            logger.error(f"Error in search: {str(e)}")
            return []

    def _perform_web_search(self, query: str) -> List[SearchResult]:
        """Perform web search using configured modules."""
        all_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.retrieval_modules)) as executor:
            future_to_module = {
                executor.submit(self._search_with_module, module, query): module
                for module in self.retrieval_modules
            }

            for future in concurrent.futures.as_completed(future_to_module):
                module = future_to_module[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    logger.error(f"Error with {module['name']} search: {str(e)}")

        return all_results

    def _search_with_module(self, module: Dict[str, Any], query: str) -> List[SearchResult]:
        """Execute search using specific module"""
        try:
            if module['name'] == 'serper':
                return self._search_serper(query, module)
            elif module['name'] == 'google':
                return self._search_google(query, module)
        except Exception as e:
            logging.error(f"Error in {module['name']} search: {str(e)}")
            return []

    def _search_serper(self, query: str, module: Dict[str, Any]) -> List[SearchResult]:
        """Execute search using Serper API"""
        try:
            headers = {
                'X-API-KEY': module['api_key'],
                'Content-Type': 'application/json'
            }
            payload = {
                'q': query,
                'num': module['params']['num'],
                'autocorrect': True,
                'gl': 'us',
                'hl': 'en'
            }
            response = requests.post(
                'https://google.serper.dev/search',
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            results = []

            # Process knowledge graph if available
            if 'knowledge_graph' in data:
                kg = data['knowledge_graph']
                if kg.get('title') and kg.get('description'):
                    results.append(SearchResult(
                        content=f"{kg['title']}\n\n{kg['description']}",
                        url=kg.get('link', ''),
                        relevance_score=0.9,
                        timestamp=datetime.now().isoformat(),
                        metadata={'type': 'knowledge_graph', 'source': 'Serper'},
                        is_real_time=True,
                        source_type='api'
                    ))

            # Process organic results
            for item in data.get('organic', []):
                url = item.get('link')
                if url and self._is_valid_url(url):
                    content = self._extract_content(url)
                    if content:
                        results.append(SearchResult(
                            content=content,
                            url=url,
                            relevance_score=0.8,
                            timestamp=datetime.now().isoformat(),
                            metadata={
                                'title': item.get('title'),
                                'snippet': item.get('snippet'),
                                'source': 'Serper'
                            }
                        ))

            # Process answer box if available
            if 'answer_box' in data:
                answer = data['answer_box']
                if answer.get('answer'):
                    results.append(SearchResult(
                        content=answer['answer'],
                        url=answer.get('link', ''),
                        relevance_score=0.95,
                        timestamp=datetime.now().isoformat(),
                        metadata={'type': 'answer_box', 'source': 'Serper'},
                        is_real_time=True,
                        source_type='api'
                    ))

            return results
        except Exception as e:
            logger.error(f"Serper search error: {str(e)}")
            return []

    def _search_google(self, query: str, module: Dict[str, Any]) -> List[SearchResult]:
        """Execute search using Google Custom Search API"""
        try:
            # Log API key and search engine ID for debugging
            logger.info(f"Google Search API Key: {module['api_key'][:5]}...")
            # Modify the CX ID logging:
            cx_to_log = module['search_engine_id']
            if cx_to_log and len(cx_to_log) > 10:
                cx_display = f"{cx_to_log[:5]}...{cx_to_log[-5:]}"
            else:
                cx_display = cx_to_log
            logger.info(f"Google Search Engine ID: {cx_display}")

            service = build(
                "customsearch", "v1",
                developerKey=module['api_key'],
                cache_discovery=False
            )

            # Log the query being executed
            logger.info(f"Executing Google search query: {query}")

            results = service.cse().list(
                q=query,
                cx=module['search_engine_id'],
                num=module['params']['num'],
                gl='us',
                lr='lang_en'
            ).execute()

            search_results = []
            for item in results.get('items', []):
                url = item.get('link')
                if url and self._is_valid_url(url):
                    content = self._extract_content(url)
                    if content:
                        search_results.append(SearchResult(
                            content=content,
                            url=url,
                            relevance_score=0.9,
                            timestamp=datetime.now().isoformat(),
                            metadata={
                                'title': item.get('title'),
                                'snippet': item.get('snippet'),
                                'source': 'Google'
                            }
                        ))
            return search_results
        except Exception as e:
            logger.error(f"Google search error: {str(e)}")
            return []

    def _is_time_sensitive_query(self, query: str) -> bool:
        """
        Check if the query requires real-time data.

        Args:
            query (str): Search query

        Returns:
            bool: True if query requires real-time data
        """
        time_sensitive_keywords: Set[str] = {
            'price', 'current', 'today', 'now', 'latest', 'live',
            'weather', 'temperature', 'stock', 'crypto', 'bitcoin',
            'exchange rate', 'score', 'game', 'match'
        }
        return any(keyword in query.lower() for keyword in time_sensitive_keywords)

    def _get_real_time_data(self, query: str) -> Optional[List[SearchResult]]:
        """
        Get real-time data from appropriate API.

        Args:
            query (str): Search query

        Returns:
            Optional[List[SearchResult]]: List of real-time results if available
        """
        try:
            search_terms = self._extract_search_terms(query)

            if search_terms['type'] == 'market':
                return self._get_market_data(search_terms['symbol'])
            elif search_terms['type'] == 'weather':
                return self._get_weather_data(search_terms['location'])
            return None

        except Exception as e:
            logger.error(f"Error getting real-time data: {str(e)}")
            return None

    def _get_market_data(self, symbol: Optional[str]) -> Optional[List[SearchResult]]:
        """
        Get market data for stocks and crypto.

        Args:
            symbol (Optional[str]): Market symbol

        Returns:
            Optional[List[SearchResult]]: List of market data results
        """
        try:
            if not symbol:
                return None

            # Handle cryptocurrency queries
            if symbol.lower() in ['btc', 'bitcoin', 'eth', 'ethereum', 'crypto']:
                url = f"{self.real_time_apis['crypto']}/simple/price"
                params = {
                    'ids': 'bitcoin,ethereum',
                    'vs_currencies': 'usd',
                    'include_24hr_change': 'true',
                    'include_market_cap': 'true'
                }

                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                # Format the response in a more readable way
                formatted_content = []
                for coin, info in data.items():
                    price = info.get('usd', 0)
                    change = info.get('usd_24h_change', 0)
                    market_cap = info.get('usd_market_cap', 0)
                    formatted_content.append(
                        f"{coin.title()} Price: ${price:,.2f}\n"
                        f"24h Change: {change:+.2f}%\n"
                        f"Market Cap: ${market_cap:,.0f}"
                    )

                return [SearchResult(
                    content="\n\n".join(formatted_content),
                    url=response.url,
                    relevance_score=1.0,
                    timestamp=datetime.now().isoformat(),
                    metadata={
                        'type': 'market',
                        'symbol': symbol,
                        'source': 'CoinGecko'
                    },
                    is_real_time=True,
                    source_type='api'
                )]

            # Handle stock queries
            else:
                url = f"{self.real_time_apis['stocks']}/v1/last/stocks/{symbol}"
                params = {
                    'apiKey': self.config_manager.get('POLYGON_API_KEY')
                }

                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                # Format stock data
                price = data.get('last', {}).get('price', 0)
                volume = data.get('last', {}).get('volume', 0)
                timestamp = data.get('last', {}).get('timestamp', '')

                formatted_content = (
                    f"Stock: {symbol}\n"
                    f"Price: ${price:,.2f}\n"
                    f"Volume: {volume:,.0f}\n"
                    f"Last Updated: {timestamp}"
                )

                return [SearchResult(
                    content=formatted_content,
                    url=response.url,
                    relevance_score=1.0,
                    timestamp=datetime.now().isoformat(),
                    metadata={
                        'type': 'market',
                        'symbol': symbol,
                        'source': 'Polygon'
                    },
                    is_real_time=True,
                    source_type='api'
                )]

        except requests.exceptions.RequestException as e:
            logger.error(f"API request error for {symbol}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {str(e)}")
            return None

    def _get_weather_data(self, query: str) -> Optional[List[SearchResult]]:
        """Get weather data"""
        # Implement weather data retrieval
        pass

    def _process_results(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        """Enhanced result processing with real-time priority and content deduplication"""
        # Remove duplicates based on content similarity
        seen_contents = set()
        unique_results = []

        # Prioritize real-time and knowledge graph results
        real_time_results = [r for r in results if r.is_real_time]
        web_results = [r for r in results if not r.is_real_time]

        # Process real-time results first
        for result in real_time_results:
            content_hash = hashlib.md5(result.content.encode()).hexdigest()
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                unique_results.append(result)

        # Then process web results
        for result in web_results:
            content_hash = hashlib.md5(result.content.encode()).hexdigest()
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                unique_results.append(result)

        # Adjust relevance scores based on freshness and content quality
        current_time = time.time()
        for result in unique_results:
            # Time-based adjustment
            result_time = datetime.fromisoformat(result.timestamp).timestamp()
            time_diff_hours = (current_time - result_time) / 3600
            freshness_factor = math.exp(-0.1 * time_diff_hours)

            # Content quality adjustment
            content_length = len(result.content)
            quality_factor = min(1.0, content_length / 1000)  # Prefer longer content

            # Combine factors
            result.relevance_score *= (freshness_factor * 0.6 + quality_factor * 0.4)

        return sorted(unique_results, key=lambda x: (x.is_real_time, x.relevance_score), reverse=True)

    def _extract_content(self, url: str) -> Optional[str]:
        """Extract and clean content from URL using the consolidated scraping function."""
        try:
            from utils import robust_scrape_url
            return robust_scrape_url(url, timeout=10, max_retries=3)
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {str(e)}")
            return None

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid for scraping"""
        excluded_domains = {
            'youtube.com', 'facebook.com', 'instagram.com', 'twitter.com',
            'tiktok.com', 'pinterest.com', 'reddit.com'
        }
        return not any(domain in url.lower() for domain in excluded_domains)

    def cache_results(self, query: str, results: List[SearchResult]):
        """Cache search results for future use"""
        cache_file = self.output_dir / f"{hashlib.md5(query.encode()).hexdigest()}.json"

        try:
            cache_data = {
                'query': query,
                'timestamp': time.time(),
                'results': [asdict(result) for result in results]
            }

            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)

        except Exception as e:
            logging.error(f"Error caching results: {str(e)}")

    def get_cached_results(self, query: str, max_age: int = 3600) -> Optional[List[SearchResult]]:
        """Enhanced cache retrieval with real-time considerations"""
        # Adjust cache duration for time-sensitive queries
        if self._is_time_sensitive_query(query):
            max_age = 60  # 1 minute cache for time-sensitive queries

        cache_file = self.output_dir / f"{hashlib.md5(query.encode()).hexdigest()}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)

            if time.time() - cache_data['timestamp'] > max_age:
                return None

            results = [SearchResult(**result) for result in cache_data['results']]

            # For time-sensitive queries, validate result timestamps
            if self._is_time_sensitive_query(query):
                current_time = time.time()
                results = [
                    result for result in results
                    if (current_time - datetime.fromisoformat(result.timestamp).timestamp()) <= max_age
                ]
                if not results:  # If all results are too old
                    return None

            return results

        except Exception as e:
            logging.error(f"Error reading cached results: {str(e)}")
            return None

    def cleanup(self):
        """Clean up temporary files"""
        try:
            import shutil
            shutil.rmtree(self.output_dir)
        except Exception as e:
            logging.error(f"Error cleaning up search manager: {str(e)}")

    def _extract_search_terms(self, query: str) -> Dict[str, str]:
        """Extract relevant search terms from query"""
        terms = {
            'type': None,
            'symbol': None,
            'location': None
        }

        query_lower = query.lower()

        # Detect market-related queries
        if any(word in query_lower for word in ['stock', 'price', 'market']):
            terms['type'] = 'market'
            # Look for stock symbols (uppercase words 1-4 characters)
            import re
            symbols = re.findall(r'\b[A-Z]{1,4}\b', query)
            if symbols:
                terms['symbol'] = symbols[0]

        # Detect weather-related queries
        elif any(word in query_lower for word in ['weather', 'temperature']):
            terms['type'] = 'weather'
            # Look for location after "in" or "at"
            for prep in ['in', 'at', 'for']:
                if prep in query_lower:
                    location = query_lower.split(prep)[1].strip()
                    if location:
                        terms['location'] = location
                        break

        return terms