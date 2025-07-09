# cache_manager.py
import json
import os
import time
from typing import Dict, Any, Optional


class CacheManager:
    def __init__(self, cache_dir: str = ".cache", cache_duration: int = 3600):
        self.cache_dir = cache_dir
        self.cache_duration = cache_duration
        os.makedirs(cache_dir, exist_ok=True)

    def _get_cache_path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{key}.json")

    def set(self, key: str, value: Any) -> None:
        cache_data = {
            "timestamp": time.time(),
            "value": value
        }
        with open(self._get_cache_path(key), 'w') as f:
            json.dump(cache_data, f)

    def get(self, key: str) -> Optional[Any]:
        try:
            cache_path = self._get_cache_path(key)
            if not os.path.exists(cache_path):
                return None

            with open(cache_path, 'r') as f:
                cache_data = json.load(f)

            if time.time() - cache_data["timestamp"] > self.cache_duration:
                os.remove(cache_path)
                return None

            return cache_data["value"]
        except Exception:
            return None

    def clear(self) -> None:
        for file in os.listdir(self.cache_dir):
            try:
                os.remove(os.path.join(self.cache_dir, file))
            except Exception:
                pass
