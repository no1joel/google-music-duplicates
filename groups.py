"""Functions for acting with groups of songs."""
import logging
from datetime import datetime
from itertools import combinations
from typing import Dict, Generator, List, Optional, Set, Tuple

import keyboard
from fuzzywuzzy.fuzz import ratio  # type: ignore
from gmusicapi import Mobileclient  # type: ignore
from tqdm import tqdm  # type: ignore

from cache import get_cached, store_cache, use_cache
from songs import get_all_songs, summarise_song


class SongPair:
    """A pair of songs."""

    def __init__(self, song1: dict, song2: dict):
        self.song1 = song1
        self.song2 = song2

    @property
    def songs(self) -> List[dict]:
        """Return all values."""

        return [self.song1, self.song2]

    def _get_values(self, key: str) -> Set[str]:
        """Return values for key."""

        return {song[key] for song in self.songs}

    def _get_string_score(self, key: str) -> int:
        """Return how similar songs are by key out of 100."""

        values = self._get_values(key)
        if len(values) == 1:
            score = 100
        else:
            score = ratio(*values)

        return score

    @property
    def track_score(self) -> int:
        """Return the track score."""

        values = self._get_values("trackNumber")
        if len(values) == 1:
            return 100
        try:
            int_values = {int(value) for value in values}
        except TypeError:
            pass
        else:
            if (len(int_values)) == 1:
                return 50
        return 0

    @property
    def album_score(self) -> int:
        """Return the album score."""

        return self._get_string_score("album")

    @property
    def album_artist_score(self) -> int:
        """Return the album artist score."""

        return self._get_string_score("albumArtist")

    @property
    def artist_score(self) -> int:
        """Return the artist score."""

        return self._get_string_score("artist")

    @property
    def title_score(self) -> int:
        """Return the title score."""

        return self._get_string_score("title")

    @property
    def duration_score(self) -> int:
        """Return the duration score."""

        durations = {int(song["durationMillis"]) for song in (self.song1, self.song2)}
        if len(durations) == 1:
            return 100

        return 100 * int(min(durations) / max(durations))

    def get_names_and_scores(self) -> Generator[Tuple[str, int], None, None]:
        """Return name and score for that name."""

        score_names = ("track", "duration", "album", "album_artist", "artist", "title")
        for name in score_names:
            yield name, getattr(self, f"{name}_score")

    def get_scores(self) -> Generator[int, None, None]:
        """Return only scores."""

        for _name, score in self.get_names_and_scores():
            yield score

    def is_similar(self) -> bool:
        """Return whether the pair is similar."""

        return all((score > 90 for score in self.get_scores()))

    def final_score(self) -> float:
        """Return the average of all scores."""

        scores = [score for score in self.get_scores()]

        return sum(scores) / len(scores)


def get_similarity_score(song1: dict, song2: dict) -> Dict[str, int]:
    """Return a dict of the scores."""

    pair = SongPair(song1, song2)

    return {key: value for key, value in pair.get_names_and_scores()}


def is_similar_to_other_songs(song, other_songs) -> bool:
    """Return true if song is similar to all others."""

    all_pairs = (SongPair(song, other_song) for other_song in other_songs)
    all_similar = all((pair.is_similar() for pair in all_pairs))

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
    songs_to_process = [song for song in songs if song["id"] not in seen_ids]

    try:
        for index, song in enumerate(tqdm(songs_to_process)):
            if index % 100 == 0:
                cache_partial_groups(groups)

            add_song_to_correct_group(song, groups)
    except KeyboardInterrupt:
        logging.debug("Interrupted, storing data so far")
        cache_partial_groups(groups)
        raise

    return groups


def generate_similar_groups() -> List[List[dict]]:
    """Return all groups of similar songs."""

    songs = get_all_songs()
    groups = build_groups(songs)

    return list(groups.values())


def get_similar_groups() -> List[List[dict]]:
    """Return similar groups."""

    return use_cache("groups", generate_similar_groups)


class SongGroup:
    """A group of songs."""

    def __init__(self, group: List[dict]):
        self.group = group

    def get_keep_song(self) -> dict:
        """Return the song that we think should be kept."""

        def _get_play_count(song: dict) -> int:
            return song["playCount"]

        def _get_creation(song: dict) -> int:
            return int(song["creationTimestamp"])

        by_added_date = sorted(self.group, key=_get_creation)
        by_play_count = sorted(by_added_date, key=_get_play_count, reverse=True)
        return by_play_count[0]

    def get_discard_songs(self) -> List[dict]:
        """Return the songs that we think should be removed."""

        keep_song = self.get_keep_song()

        return [song for song in self.group if song != keep_song]

    def get_all_pairs(self) -> List[SongPair]:
        """Return all possible pairs of songs."""

        return [
            SongPair(song, other_song)
            for song, other_song in combinations(self.group, 2)
        ]

    def get_similarity(self) -> float:
        """Return the average similarity score of all pairs."""

        pairs = self.get_all_pairs()

        return sum((pair.final_score()) for pair in pairs) / len(pairs)

    def __len__(self) -> int:
        """Return the number of songs in the group."""

        return len(self.group)

    def __iter__(self) -> Generator[dict, None, None]:
        """Return each song in the group."""

        for song in self.group:
            yield song

    def _combine_play_counts(self, api: Mobileclient) -> None:
        """Combine play counts on to keep song."""

        discard_songs = self.get_discard_songs()
        extra_plays = sum(int(song["playCount"]) for song in discard_songs)
        if not extra_plays:
            return

        keep_song = self.get_keep_song()
        timestamps = [int(song["recentTimestamp"]) for song in self.group]
        most_recent_timestamp = max(timestamps)
        playtime = datetime.fromtimestamp(most_recent_timestamp / 10 ** 6)
        api.increment_song_playcount(keep_song["id"], extra_plays, playtime=playtime)

    def _delete_duplicates(self, api: Mobileclient) -> None:
        """Delete duplicates."""

        self._combine_play_counts(api)
        discard_ids = [song["id"] for song in self.get_discard_songs()]
        api.delete_songs(discard_ids)

    def auto_manage(self, api: Mobileclient) -> bool:
        """Automatically remove duplicates if the score is high enough."""

        if self.get_similarity() < 100:
            return False

        self._delete_duplicates(api)
        return True

    def confirm_delete(self, api: Mobileclient) -> bool:
        """Ask the user if we can delete."""

        keep_song = self.get_keep_song()
        print(f"Keep:\n - {summarise_song(keep_song)}")
        print(f"Delete:")
        for song in self.get_discard_songs():
            print(f" - {summarise_song(song)}")

        while True:
            print("Delete? (y/N)")
            key = keyboard.read_key()
            if key in ["n", "enter", "return"]:
                print("Not deleting.")
                return False
            if key == "y":
                print("Deleting.")
                self._delete_duplicates(api)
                return True


def summarise_similar(groups: List[List[dict]]):
    """Output similar songs."""

    song_groups = (SongGroup(group) for group in groups)
    have_similar = [group for group in song_groups if len(group) > 1]
    guesses_last = sorted(have_similar, key=lambda x: x.get_similarity(), reverse=True)

    for group in guesses_last:
        print(f"Group Size: {len(group)}")
        for song in group:
            print(f" - {summarise_song(song)}")
        print("-" * 32)
        group_similarity = group.get_similarity()
        print(f"Group simiarity: {group_similarity:03.2f}%")
        print("=" * 32)

    print(f"Total Groups: {len(have_similar)}")


def delete_duplicates(groups: List[List[dict]], api: Mobileclient):
    """Delete duplicate songs."""

    song_groups = [SongGroup(group) for group in groups]
    have_similar = [group for group in song_groups if len(group) > 1]

    for group in have_similar:
        if not group.auto_manage(api):
            group.confirm_delete(api)
