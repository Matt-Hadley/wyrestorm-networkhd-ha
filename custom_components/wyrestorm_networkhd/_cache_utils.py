"""Caching utilities for the WyreStorm NetworkHD integration."""

import time
from collections.abc import Callable
from functools import wraps
from typing import Any


def cache_for_seconds(seconds: int) -> Callable:
    """Cache async function results for specified seconds.

    This decorator provides time-based caching for expensive async operations,
    particularly useful for API calls that return rarely-changing data.

    Args:
        seconds: Number of seconds to cache the result (e.g., 600 for 10 minutes).
                Must be positive integer.

    Returns:
        Decorator function that adds caching behavior to async methods.

    Example:
        @cache_for_seconds(600)  # Cache for 10 minutes
        async def get_device_info(self):
            return await self.api.expensive_call()

    Note:
        - Cache is keyed by function name and arguments
        - Each decorated method has independent cache storage
        - Use method.clear_cache() to manually invalidate cache
        - Memory usage scales with number of unique argument combinations
    """

    def decorator(func: Callable) -> Callable:
        cache: dict[tuple, Any] = {}
        cache_time: dict[tuple, float] = {}

        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Create cache key from function name and args
            cache_key = (func.__name__, args, tuple(sorted(kwargs.items())))

            # Check if we have a valid cached result
            if cache_key in cache and cache_key in cache_time:
                elapsed = time.time() - cache_time[cache_key]
                if elapsed < seconds:
                    return cache[cache_key]

            # Call the actual function
            result = await func(self, *args, **kwargs)

            # Store in cache
            cache[cache_key] = result
            cache_time[cache_key] = time.time()

            return result

        # Add method to clear cache if needed
        def clear_cache() -> None:
            cache.clear()
            cache_time.clear()

        wrapper.clear_cache = clear_cache  # type: ignore[attr-defined]

        return wrapper

    return decorator
