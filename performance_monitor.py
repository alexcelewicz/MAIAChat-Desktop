# performance_monitor.py
import time
import logging
import functools
import threading
from typing import Dict, List, Any, Optional, Callable
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """
    A utility class for monitoring and profiling application performance.
    
    Features:
    - Function execution time tracking
    - Memory usage monitoring
    - API call latency tracking
    - Performance metrics reporting
    """
    
    def __init__(self, enabled: bool = True, log_dir: str = ".performance_logs"):
        self.enabled = enabled
        self.log_dir = log_dir
        self.metrics: Dict[str, List[Dict[str, Any]]] = {
            "function_calls": [],
            "api_calls": [],
            "ui_updates": [],
            "memory_usage": []
        }
        self.lock = threading.Lock()
        
        # Create log directory if it doesn't exist
        if enabled:
            os.makedirs(log_dir, exist_ok=True)
    
    def track_function(self, func: Callable) -> Callable:
        """
        Decorator to track function execution time.
        
        Args:
            func: The function to track
            
        Returns:
            Wrapped function with performance tracking
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not self.enabled:
                return func(*args, **kwargs)
                
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                success = True
            except Exception as e:
                success = False
                error = str(e)
                raise
            finally:
                end_time = time.time()
                execution_time = end_time - start_time
                
                with self.lock:
                    self.metrics["function_calls"].append({
                        "function": func.__name__,
                        "module": func.__module__,
                        "execution_time": execution_time,
                        "timestamp": datetime.now().isoformat(),
                        "success": success,
                        "error": error if not success else None
                    })
                    
                    # Log slow functions (>1 second)
                    if execution_time > 1.0:
                        logger.warning(f"Slow function: {func.__name__} took {execution_time:.2f}s to execute")
                
            return result
        return wrapper
    
    def track_api_call(self, provider: str, model: str, prompt_length: int, start_time: float, 
                      end_time: float, success: bool, error: Optional[str] = None) -> None:
        """
        Track API call performance.
        
        Args:
            provider: The API provider (e.g., "OpenAI", "Ollama")
            model: The model used
            prompt_length: Length of the prompt in characters
            start_time: Call start time (timestamp)
            end_time: Call end time (timestamp)
            success: Whether the call was successful
            error: Error message if the call failed
        """
        if not self.enabled:
            return
            
        latency = end_time - start_time
        
        with self.lock:
            self.metrics["api_calls"].append({
                "provider": provider,
                "model": model,
                "prompt_length": prompt_length,
                "latency": latency,
                "timestamp": datetime.now().isoformat(),
                "success": success,
                "error": error
            })
            
            # Log slow API calls (>5 seconds)
            if latency > 5.0:
                logger.warning(f"Slow API call: {provider}/{model} took {latency:.2f}s")
    
    def track_ui_update(self, update_type: str, content_length: int, batch_size: int = 1) -> None:
        """
        Track UI update performance.
        
        Args:
            update_type: Type of UI update (e.g., "discussion", "terminal")
            content_length: Length of the content in characters
            batch_size: Number of updates batched together
        """
        if not self.enabled:
            return
            
        with self.lock:
            self.metrics["ui_updates"].append({
                "update_type": update_type,
                "content_length": content_length,
                "batch_size": batch_size,
                "timestamp": datetime.now().isoformat()
            })
    
    def track_memory_usage(self, component: str, memory_mb: float) -> None:
        """
        Track memory usage.
        
        Args:
            component: Component being measured
            memory_mb: Memory usage in MB
        """
        if not self.enabled:
            return
            
        with self.lock:
            self.metrics["memory_usage"].append({
                "component": component,
                "memory_mb": memory_mb,
                "timestamp": datetime.now().isoformat()
            })
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current performance metrics.
        
        Returns:
            Dictionary of performance metrics
        """
        if not self.enabled:
            return {}
            
        with self.lock:
            # Calculate summary statistics
            summary = {
                "function_calls": {
                    "count": len(self.metrics["function_calls"]),
                    "avg_execution_time": self._calculate_average(
                        [call["execution_time"] for call in self.metrics["function_calls"]]
                    ),
                    "slowest_functions": self._get_slowest_functions(5)
                },
                "api_calls": {
                    "count": len(self.metrics["api_calls"]),
                    "avg_latency": self._calculate_average(
                        [call["latency"] for call in self.metrics["api_calls"]]
                    ),
                    "by_provider": self._group_by_provider()
                },
                "ui_updates": {
                    "count": len(self.metrics["ui_updates"]),
                    "avg_content_length": self._calculate_average(
                        [update["content_length"] for update in self.metrics["ui_updates"]]
                    ),
                    "avg_batch_size": self._calculate_average(
                        [update["batch_size"] for update in self.metrics["ui_updates"]]
                    )
                }
            }
            
            return {
                "summary": summary,
                "detailed": self.metrics
            }
    
    def save_metrics(self, filename: Optional[str] = None) -> str:
        """
        Save metrics to a JSON file.
        
        Args:
            filename: Optional filename, defaults to timestamp-based name
            
        Returns:
            Path to the saved file
        """
        if not self.enabled:
            return ""
            
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_metrics_{timestamp}.json"
        
        file_path = os.path.join(self.log_dir, filename)
        
        with self.lock:
            metrics = self.get_metrics()
            
            with open(file_path, 'w') as f:
                json.dump(metrics, f, indent=2)
        
        return file_path
    
    def reset(self) -> None:
        """Reset all metrics."""
        if not self.enabled:
            return
            
        with self.lock:
            for key in self.metrics:
                self.metrics[key] = []
    
    def _calculate_average(self, values: List[float]) -> float:
        """Calculate average of a list of values."""
        if not values:
            return 0.0
        return sum(values) / len(values)
    
    def _get_slowest_functions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get the slowest functions."""
        if not self.metrics["function_calls"]:
            return []
            
        sorted_calls = sorted(
            self.metrics["function_calls"],
            key=lambda x: x["execution_time"],
            reverse=True
        )
        
        return [
            {
                "function": call["function"],
                "execution_time": call["execution_time"]
            }
            for call in sorted_calls[:limit]
        ]
    
    def _group_by_provider(self) -> Dict[str, Dict[str, Any]]:
        """Group API call metrics by provider."""
        result = {}
        
        for call in self.metrics["api_calls"]:
            provider = call["provider"]
            if provider not in result:
                result[provider] = {
                    "count": 0,
                    "avg_latency": 0.0,
                    "success_rate": 0.0,
                    "calls": []
                }
            
            result[provider]["count"] += 1
            result[provider]["calls"].append(call)
        
        # Calculate averages
        for provider, data in result.items():
            if data["count"] > 0:
                data["avg_latency"] = sum(call["latency"] for call in data["calls"]) / data["count"]
                success_count = sum(1 for call in data["calls"] if call["success"])
                data["success_rate"] = success_count / data["count"]
            
            # Remove detailed calls to reduce size
            del data["calls"]
        
        return result


# Create a global instance for easy import
performance_monitor = PerformanceMonitor()

# Decorator for easy function tracking
def track_performance(func):
    """Decorator to track function performance."""
    return performance_monitor.track_function(func)
