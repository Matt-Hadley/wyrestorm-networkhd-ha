"""Caching utilities for the WyreStorm NetworkHD integration."""

import time
from collections.abc import Callable
from functools import wraps


def cache_for_seconds(seconds: int) -> Callable:
    """Cache async function results for specified seconds.

    Args:
        seconds: Number of seconds to cache the result

    Returns:
        Decorator that caches function results
    """

    def decorator(func: Callable) -> Callable:
        cache = {}
        cache_time = {}

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
        wrapper.clear_cache = lambda: (cache.clear(), cache_time.clear())

        return wrapper

    return decorator
