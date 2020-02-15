"""Functions for working with songs."""
import logging
from typing import List

from cache import use_cache
from google_music import get_all_songs as get_all_songs_from_server


def get_all_songs() -> List[dict]:
    """Return songs."""

    logging.debug("Getting songs")

    songs = use_cache("songs", lambda: list(get_all_songs_from_server()))

    return songs


def summarise_song(song: dict) -> str:
    """Return a string representation of a song."""

    artist = song["artist"]
    title = song["title"]
    album = song["album"]
    duration_millis = int(song["durationMillis"])
    duration_seconds = duration_millis / 1000
    duration_minutes, seconds = divmod(duration_seconds, 60)
    hours, minutes = divmod(duration_minutes, 60)

    return (
        f"{artist} - {album} - {title} [{hours:02.0f}:{minutes:02.0f}:{seconds:02.0f}]"
    )
