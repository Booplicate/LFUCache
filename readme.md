# LFUCache

## Description.
This module implements LFU cache in python using just one class, nevertheless, for the most basic operations (add/get) should be still quite fast.
You can also remove cache entries by priority or key, although, this may be slow depending on the size.
Uneless you're making something fancy, usually it should be enough to just use the `create_lfu_cache` decorator on your function.

## Example
```python
from lfu_cache import create_lfu_cache

@create_lfu_cache(limit=1024, typed=True)
def expensive_function(arg):
    *heavy processing*
    return arg
```
That'll cache 1024 precisely stored inputs (since `typed` is set `True`) and outputs. Bear in mind, the first execution may take more time, but you save more time with each next call.
You can access the original (w/o the decorator, not affected by the cache system) function using the `__wrapped__` property, the `__cache__` property can be used to access the LFUCache object of the function.
The cache object has 2 useful property for debugging: `hits` and `misses`, showing how effective the cache was reused.

## Limitations.
Arguments to the cached function must be hashable.
