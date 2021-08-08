"""
Sub-module contains main classes
"""

from threading import RLock
from collections import namedtuple
from typing import (
    Optional,
    Any,
    List,
    Dict
)


_CacheEntry = namedtuple("CacheEntry", ("key", "value", "access_count"))

class LFUCacheException(Exception): pass

class LFUCache():
    """
    Python implementation of LFU (Least Frequently Used) cache

    PROPERTIES:
        limit - (int/None) maximum number of entries in the cache
            (if we exceed, we start removing the least used ones)
            None - unlimited, 0 - blocked for writing new entries
            NOTE: It is safe to adjust limit after init
        hits - (int) number of times the cache was reused
        misses - (int) number of times the cache was written
    """
    def __init__(self, limit: int = 128) -> None:
        """
        Constructor for cache instances

        IN:
            limit - maximum number of entries in this cache, unlimited if None
                (NOTE: if not None, it must be more or equal to zero)
                (Default: 128)
        """
        if not (
            limit is None
            or (
                isinstance(limit, int)
                and limit >= 0
            )
        ):
            raise LFUCacheException(
                f"LFUCache expects its limit to be an intenger >= 0 or NoneType, got {limit}."
            )

        self._limit = limit
        # key: [queue_id, value]
        self._cache_entries: Dict[str, List[int, str]] = dict()
        # queue_id: [key, access_count]
        self._priority_queue: List[List[str, int]] = list()
        self._hits = 0
        self._misses = 0
        self._lock = RLock()

    def __get_hex_id(self) -> str:
        """
        Returns id of this object
        """
        return hex(int(id(self))).upper()

    def __str__(self) -> str:
        """
        Representation of this object
        """
        return f"<LFUCache ({len(self)}/{self._limit} entries) at {self.__get_hex_id()}>"

    def __repr__(self) -> str:
        """
        Representation of this object
        """
        return f"<LFUCache(limit={self._limit}) at {self.__get_hex_id()}>"

    def __len__(self) -> int:
        """
        Returns size of this cache
        """
        return len(self._priority_queue)

    @property
    def limit(self) -> Optional[int]:
        return self._limit

    @limit.setter
    def limit(self, new_limit: Optional[int]) -> None:
        with self._lock:
            # If the new limit is smaller than the current,
            # we may need to remove some of our cache entries
            if new_limit is not None:
                if not isinstance(new_limit, int) or new_limit < 0:
                    raise LFUCacheException("limit must be >= 0 or be NoneType.")

                excessive_entries = len(self) - new_limit
                while excessive_entries > 0:
                    item = self._priority_queue.pop()
                    del self._cache_entries[item[0]]
                    excessive_entries -= 1

            # Set the limit
            self._limit = new_limit

    @property
    def hits(self) -> int:
        return self._hits

    @property
    def misses(self) -> int:
        return self._misses

    def clear(self) -> None:
        """
        Clears this cache
        """
        with self._lock:
            self._cache_entries.clear()
            self._priority_queue.clear()

    def add(self, key, value, update=False) -> bool:
        """
        Adds a new entry with the given key and value.

        IN:
            key - key to save entry to
            value - value to save
            update - whether or not we should update the value if the key
                already exists
                (Default: False)

        OUT:
            boolean whether or not the entry was added to the cache
        """
        with self._lock:
            if self._limit == 0:
                return False

            if not self.has_cache(key):
                queue_len = len(self)
                if self._limit is not None and queue_len >= self._limit:
                    self._remove_by_id(self._limit - 1)
                    queue_len -= 1

                self._priority_queue.append([key, 1])
                self._cache_entries[key] = [queue_len, value]
                self._misses += 1
                return True

            elif update:
                self._increment_access_count(key)
                self._cache_entries[key][1] = value
                self._misses += 1
                return True

            return False

    def has_cache(self, key: str) -> bool:
        """
        Checks if we have a cache for the given key
        """
        with self._lock:
            return key in self._cache_entries

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieves an entry by key

        IN:
            key - key to get
            default - value to return if the key doesn't exist
                (Default: None)

        OUT:
            cached value
        """
        with self._lock:
            if not self.has_cache(key):
                return default

            self._hits += 1
            self._increment_access_count(key)
            return self._cache_entries[key][1]

    def remove(self, key: str) -> bool:
        """
        Removes an entry by key

        IN:
            key - key to remove

        OUT:
            boolean whether or not the entry was removed from the cache
        """
        with self._lock:
            if not self.has_cache(key):
                return False

            queue_id = self._cache_entries[key][0]

            del self._priority_queue[queue_id]
            del self._cache_entries[key]

            # We need to update the ids for the keys after this one because of potential shift
            for item in self._priority_queue[queue_id:]:
                # Access each entry and "increment" its priority
                self._cache_entries[item[0]][0] -= 1

            return True

    def _remove_by_id(self, queue_id: int) -> bool:
        """
        Removes an entry by id

        IN:
            queue_id - entry id in queue

        OUT:
            boolean whether or not the entry was removed from the cache
        """
        with self._lock:
            if not (len(self) > queue_id >= 0):
                return False

            key = self._priority_queue[queue_id][0]

            del self._cache_entries[key]
            del self._priority_queue[queue_id]

            for item in self._priority_queue[queue_id:]:
                self._cache_entries[item[0]][0] -= 1

            return True

    def _increment_access_count(self, key: str) -> None:
        """
        Increments counter for the entry with the given key
        and adjusts its priority

        IN:
            key - key to use
                (NOTE: must exist)
        """
        with self._lock:
            queue_id = self._cache_entries[key][0]
            next_queue_id = queue_id - 1
            # Kick up access count
            self._priority_queue[queue_id][1] += 1
            # Move this entry in the queue if needed
            while (
                queue_id > 0
                and self._priority_queue[queue_id][1] > self._priority_queue[next_queue_id][1]
            ):
                # Update cache for the next entry
                next_entry_key = self._priority_queue[next_queue_id][0]
                self._cache_entries[next_entry_key][0] = next_queue_id + 1
                # Swap positions in the queue
                self._priority_queue[queue_id], self._priority_queue[next_queue_id] = self._priority_queue[next_queue_id], self._priority_queue[queue_id]

                queue_id -= 1
                next_queue_id -= 1

            # Update cache for this entry
            value = self._cache_entries[key][1]
            self._cache_entries[key] = [queue_id, value]

    def retrieve(self, start: Optional[int] = None, end: Optional[int] = None) -> List[_CacheEntry]:
        """
        Retrieves keys, their values and access counters
        NOTE: this may be very slow depending on size
        NOTE: NOT thread safe

        IN:
            start - start position. If None, retrieves from 0
                (Default: None)
            end - end position. If None, retrieves to -1
                (Default: None)

        OUT:
            list with cache entries
        """
        return [
            _CacheEntry(key, self._cache_entries[key][1], access_count)
            for key, access_count in self._priority_queue[start:end]
        ]
