"""Simple in-memory cache service for API responses."""
import time
from typing import Any, Optional
from functools import wraps


class CacheService:
    """In-memory cache with TTL support."""
    
    _cache = {}
    
    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        """Get a value from cache if it exists and hasn't expired."""
        if key in cls._cache:
            value, expiry = cls._cache[key]
            if time.time() < expiry:
                return value
            else:
                del cls._cache[key]
        return None
    
    @classmethod
    def set(cls, key: str, value: Any, ttl: int = 60) -> None:
        """Set a value in cache with a TTL (time-to-live) in seconds."""
        expiry = time.time() + ttl
        cls._cache[key] = (value, expiry)
    
    @classmethod
    def clear(cls) -> None:
        """Clear all cached values."""
        cls._cache.clear()


def cached(ttl: int = 60):
    """Decorator to cache function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            
            # Check cache
            result = CacheService.get(key)
            if result is not None:
                return result
            
            # Call function and cache result
            result = func(*args, **kwargs)
            if result is not None:
                CacheService.set(key, result, ttl)
            
            return result
        return wrapper
    return decorator
