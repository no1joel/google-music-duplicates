"""Functions for working with cache."""

import json
import logging
import time
from json.decoder import JSONDecodeError
from typing import Any, Callable, Optional


def _get_cached_filename(key: str) -> str:
    return f"./cached_{key}.json"


def cache_outdated(cache_timestamp: int) -> bool:
    """Return true if a timestamp indicates outdated."""

    now = time.time()
    age_seconds = now - cache_timestamp
    hour_in_seconds = 60 * 60
    day_in_seconds = 24 * hour_in_seconds
    threshold = day_in_seconds

    return age_seconds > threshold


def get_cached(key: str) -> Optional[Any]:
    """Return data from the cache file."""
    filename = _get_cached_filename(key)

    logging.debug("Attempting from cache")

    try:
        with open(filename) as cache_file:
            cached = json.load(cache_file)
    except (JSONDecodeError, IOError):
        logging.debug("Cannot read cache file, returning None")
        return None

    timestamp = cached["timestamp"]
    if cache_outdated(timestamp):
        logging.debug("Cache is older than an hour, returning None")
        return None

    logging.debug("Got cached %s", key)

    return cached[key]


def store_cache(data: Any, key: str):
    """Store data in the cache file."""

    logging.debug("Storing %s in cache", key)
    filename = _get_cached_filename(key)

    with open(filename, "w") as cache_file:
        timestamp = time.time()
        data = {"timestamp": timestamp, key: data}
        json.dump(data, cache_file)


def use_cache(key: str, func: Callable[[], Any]) -> Any:
    """Return data from cache, or generate and then store."""

    data = get_cached(key)
    if data is None:
        data = func()
        store_cache(data, key)
    return data
