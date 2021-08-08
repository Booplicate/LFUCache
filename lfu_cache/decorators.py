"""
Sub-module contains LFU cache decorators
"""

from functools import wraps, _make_key
from typing import (
    Optional,
    Any,
    Callable
)


from .models import LFUCache


funcs_cache_map = dict()

def create_lfu_cache(limit: Optional[int] = 128, typed: bool = False) -> Callable:
    """
    Decorator to create LFU cache for a function
    NOTE: Arguments to the cached function must be hashable
    NOTE: The original function can be accessed using the __wrapped__ property
    NOTE: the cache can be accessed using the __cache__ property

    IN:
        limit - max number of entries in the cache,
            If None, the cache can grow infinitely
            (Default: 128)
        typed - whether or not we respect types of parameters,
            which allows more precise caching, but demands more performance
            (Default: False)

    OUT:
        decorated function
    """
    def decorator(func: Callable) -> Callable:
        """
        The decorator

        IN:
            func - function

        OUT:
            decorated function
        """
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            """
            The wrapper

            IN:
                args - function position arguments
                kwargs - function keyword arguments

            OUT:
                value returned by the function
            """
            cache = funcs_cache_map[func]
            key = _make_key(args, kwargs, typed)

            if cache.has_cache(key):
                return cache.get(key)

            value = func(*args, **kwargs)
            cache.add(key, value)

            return value

        if func in funcs_cache_map:
            raise Exception(f"Function '{func}' already has an associated LFU cache object.")

        cache = LFUCache(limit)
        funcs_cache_map[func] = cache
        setattr(wrapper, "__wrapped__", func)
        setattr(wrapper, "__cache__", cache)

        return wrapper

    return decorator
