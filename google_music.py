"""Wrappers for interacting with google music."""
import logging
import os
from typing import Generator

from gmusicapi import Mobileclient  # type: ignore
from gmusicapi.exceptions import InvalidDeviceId  # type: ignore


def _get_device_id_from_environment() -> str:
    """Return device ID from environment vars."""

    return os.environ["GOOGLE_MUSIC_DEVICE_ID"]


def _get_device_id_from_registered(api) -> str:
    """Return the last known registered device ID."""

    try:
        api.oauth_login("bad")
    except InvalidDeviceId as original_exception:
        error_message = original_exception.args[0]

    device_ids_str = error_message.split("Your valid device IDs are:")[-1]
    device_ids = device_ids_str.split("\n")
    device_ids = [device_id.replace("* ", "") for device_id in device_ids]
    return device_ids[-1]


def _get_device_id(api: Mobileclient) -> str:
    """Get the device ID to log in with."""

    try:
        _get_device_id_from_environment()
    except KeyError:
        pass

    return _get_device_id_from_registered(api)


def _get_api() -> Mobileclient:
    """Return an API client."""

    api = Mobileclient()
    device_id = _get_device_id(api)
    api.oauth_login(device_id)

    return api


def get_all_songs() -> Generator[dict, None, None]:
    """Fetch songs from the server, incrementally."""

    logging.debug("Fetching from server")

    api = _get_api()

    for song_page in api.get_all_songs(incremental=True):
        for song in song_page:
            yield song
