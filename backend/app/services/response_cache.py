"""In-memory response caches for expensive enrollment reads."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable, Hashable
from threading import Lock
from typing import TypeVar

T = TypeVar("T")

DEFAULT_MAX_ENTRIES = 32

_lock = Lock()
_data_version = 0


class BoundCache:
    """Simple LRU cache with a fixed maximum size."""

    def __init__(self, max_entries: int = DEFAULT_MAX_ENTRIES) -> None:
        self._max_entries = max_entries
        self._entries: OrderedDict[Hashable, object] = OrderedDict()

    def get(self, key: Hashable) -> object | None:
        if key not in self._entries:
            return None
        self._entries.move_to_end(key)
        return self._entries[key]

    def set(self, key: Hashable, value: object) -> None:
        if key in self._entries:
            self._entries.move_to_end(key)
        self._entries[key] = value
        while len(self._entries) > self._max_entries:
            self._entries.popitem(last=False)

    def clear(self) -> None:
        self._entries.clear()

    def __len__(self) -> int:
        return len(self._entries)


dashboard_cache = BoundCache()
forecast_cache = BoundCache()
sections_cache = BoundCache()
enrollment_list_cache = BoundCache()
filter_options_cache = BoundCache()

_ALL_CACHES = (
    dashboard_cache,
    forecast_cache,
    sections_cache,
    enrollment_list_cache,
    filter_options_cache,
)


def data_version() -> int:
    with _lock:
        return _data_version


def bump_data_version() -> int:
    global _data_version
    with _lock:
        _data_version += 1
        for cache in _ALL_CACHES:
            cache.clear()
        return _data_version


def invalidate_all() -> None:
    bump_data_version()


def reset_for_tests() -> None:
    """Clear caches and reset version — test helper only."""
    global _data_version
    with _lock:
        _data_version = 0
        for cache in _ALL_CACHES:
            cache.clear()


def cache_key(*parts: Hashable) -> tuple[Hashable, ...]:
    return (data_version(), *parts)


def get_or_set(cache: BoundCache, key: Hashable, factory: Callable[[], T]) -> T:
    with _lock:
        cached = cache.get(key)
        if cached is not None:
            return cached  # type: ignore[return-value]

    value = factory()

    with _lock:
        # Another thread may have filled the same key; prefer existing entry.
        cached = cache.get(key)
        if cached is not None:
            return cached  # type: ignore[return-value]
        cache.set(key, value)
        return value
