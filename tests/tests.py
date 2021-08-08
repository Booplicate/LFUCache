"""
Modules with tests
"""

import unittest
from string import ascii_letters
import random
from itertools import count

from lfu_cache import LFUCache, create_lfu_cache
from lfu_cache.models import LFUCacheException


class LFUCacheTest(unittest.TestCase):
    """
    Test case for lfu_cache
    """

    def setUp(self) -> None:
        limit = 5
        self.cache = self.generate_cache(limit)

    def tearDown(self) -> None:
        try:
            del self.cache

        except AttributeError:
            pass

    @classmethod
    def setUpClass(cls) -> None:
        pass

    @classmethod
    def tearDownClass(cls) -> None:
        pass

    @staticmethod
    def generate_str(length: int) -> str:
        pool = ascii_letters + "_"
        return "".join(random.choice(pool) for i in range(length))

    @classmethod
    def generate_cache(cls, limit: int) -> LFUCache:
        cache = LFUCache(limit=limit)
        for i in range(limit):
            cache.add(
                str(i),
                cls.generate_str(5)
            )

        return cache

    @classmethod
    def fill_cache(cls, cache: LFUCache, size: int) -> None:
        filled = 0
        inc = count(len(cache))
        while filled < size:
            has_added = cache.add(
                str(next(inc)),
                cls.generate_str(5)
            )
            filled += int(has_added)

        return cache

    def test_cache_limit(self) -> None:
        cache = self.cache
        limit = cache.limit
        cache_entries = cache.retrieve()
        over_limit_key = "over_limit_key"

        self.assertEqual(len(cache_entries), limit)

        cache.add(
            over_limit_key,
            self.generate_str(5)
        )

        new_cache_entries = cache.retrieve()

        # Size should remain
        self.assertEqual(len(new_cache_entries), limit)

        # Last key was replaced
        self.assertEqual(new_cache_entries[4].key, over_limit_key)
        # The rest should remain in place
        self.assertEqual(new_cache_entries[0].key, cache_entries[0].key)
        self.assertEqual(new_cache_entries[3].key, cache_entries[3].key)
        del new_cache_entries

        self.fill_cache(cache, 10)
        new_cache_entries = cache.retrieve()

        # Size should remain
        self.assertEqual(len(new_cache_entries), limit)
        # The key should be removed
        self.assertNotIn(over_limit_key, [entry.key for entry in new_cache_entries])

        # Test limit 0, should clear the cache
        cache.limit = 0
        self.assertEqual(len(cache), 0)

        # Invalid values
        with self.assertRaises(LFUCacheException):
            cache.limit = -1
        with self.assertRaises(LFUCacheException):
            cache.limit = "whoops"

        cache.limit = None

        self.fill_cache(cache, 25)
        self.assertEqual(len(cache), 25)

    def test_cache_add(self) -> None:
        cache = self.cache
        check_key = "check_key"

        for i in range(5):
            with self.subTest():
                has_added = cache.add(
                    check_key,
                    self.generate_str(5)
                )
                # We add it only once
                if i > 0:
                    self.assertFalse(has_added)

                else:
                    self.assertTrue(has_added)

        cache_entries = cache.retrieve()
        key_count = [entry.key for entry in cache_entries].count(check_key)

        self.assertEqual(key_count, 1)
        self.assertEqual(cache_entries[-1].key, check_key)

    def test_cache_get(self) -> None:
        cache = self.cache
        check_key = "check_key"
        check_value = self.generate_str(5)
        cache.add(check_key, check_value)

        for i in range(5):
            with self.subTest():
                self.assertEqual(check_value, cache.get(check_key))

        # 5 missed from init, plus 1 from the later added key
        self.assertEqual(cache.misses, 6)
        # 5 hits from the loop
        self.assertEqual(cache.hits, 5)

        cache_entries = cache.retrieve()
        # The key should have the top priority
        self.assertEqual(cache_entries[0].key, check_key)
        self.assertEqual(cache_entries[0].access_count, 6)

    def test_cache_remove(self) -> None:
        cache = self.cache
        check_key = "check_key"
        check_value = "check_value"

        cache.add(check_key, check_value)
        cache.get(check_key)
        cache_entries = cache.retrieve()

        # The check key should have top priority (2) now
        self.assertEqual(cache_entries[0].key, check_key)

        cache.remove(check_key)
        cache_entries = cache.retrieve()

        # The cache should contain 4 items sinse 1 was removed
        self.assertEqual(len(cache), 4)
        # The top item was removed
        self.assertNotEqual(cache_entries[0].key, check_key)

        cache.clear()
        # This should clear the cache
        self.assertEqual(len(cache), 0)
