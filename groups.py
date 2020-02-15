"""Functions for acting with groups of songs."""
import logging
from typing import Dict, List, Optional

from fuzzywuzzy.fuzz import partial_ratio

from cache import get_cached, store_cache, use_cache
from songs import get_all_songs, summarise_song


def get_similarity_score(song1: dict, song2: dict) -> Dict[str, int]:
    """Return a dict of the scores."""

    def get_score(key):
        return partial_ratio(song1[key], song2[key])

    album_score = get_score("album")
    album_artist_score = get_score("albumArtist")
    artist_score = get_score("artist")
    title_score = get_score("title")

    durations = (int(song1["durationMillis"]), int(song2["durationMillis"]))
    duration_score = 100 * int(min(durations) / max(durations))

    return {
        "album": album_score,
        "album_artist": album_artist_score,
        "artist": artist_score,
        "title": title_score,
        "duration": duration_score,
    }


def is_similar_to_other_songs(song, other_songs) -> bool:
    """Return true if song is similar to all others."""

    all_scores = (get_similarity_score(song, other_song) for other_song in other_songs)
    all_similar = all(
        (score > 90 for song_scores in all_scores for score in song_scores.values())
    )

    return all_similar


def get_similar_song_id(song: dict, groups: dict) -> Optional[str]:
    """Return song_id in groups which is similar to song."""

    for song_id, other_songs in groups.items():
        if is_similar_to_other_songs(song, other_songs):
            return song_id

    return None


def cache_partial_groups(groups: dict) -> None:
    """Store groups partially completed."""

    store_cache(list(groups.values()), "partial_groups")


def add_song_to_correct_group(song: dict, groups: Dict[str, List[dict]]) -> None:
    """Add song to the correct group within groups."""

    song_id = song["id"]
    similar_id = get_similar_song_id(song, groups)
    key = song_id if similar_id is None else similar_id
    try:
        groups[key].append(song)
    except KeyError:
        groups[key] = [song]


def build_groups(songs: List[dict]) -> dict:
    """Return groups of similar songs."""

    partial_groups: List[List[dict]] = get_cached("partial_groups") or []
    groups: Dict[str, List[dict]] = {songs[0]["id"]: songs for songs in partial_groups}
    seen_ids = {song["id"] for songs in groups.values() for song in songs}

    try:
        for index, song in enumerate(songs):
            output = (
                f"Processed {index:05d}/{len(songs):05d}, got {len(groups):03d} groups"
            )
            print(output, end="\r")

            song_id = song["id"]
            if song_id in seen_ids:
                continue

            if index % 50 == 0:
                cache_partial_groups(groups)

            add_song_to_correct_group(song, groups)
    except KeyboardInterrupt:
        logging.debug("Interrupted, storing data so far")
        cache_partial_groups(groups)
        raise

    print(" " * len(output))

    return groups


def generate_similar_groups() -> List[List[dict]]:
    """Return all groups of similar songs."""

    songs = get_all_songs()
    groups = build_groups(songs)

    return list(groups.values())


def get_similar_groups() -> List[List[dict]]:
    """Return similar groups."""

    return use_cache("groups", generate_similar_groups)


def summarise_similar(groups: List[List[dict]]):
    """Output similar songs."""

    have_similar = (group for group in groups if len(group) > 1)

    for group in have_similar:
        print(f"Group Size: {len(group)}")
        for song in group:
            print(f" - {summarise_song(song)}")
        print("-" * 32)
