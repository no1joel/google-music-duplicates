"""Functions for acting with groups of songs."""
import logging
from itertools import combinations
from typing import Dict, Generator, List, Optional, Tuple

from fuzzywuzzy.fuzz import ratio  # type: ignore
from tqdm import tqdm  # type: ignore

from cache import get_cached, store_cache, use_cache
from songs import get_all_songs, summarise_song


class SongPair:
    """A pair of songs."""

    def __init__(self, song1: dict, song2: dict):
        self.song1 = song1
        self.song2 = song2

    def get_score(self, key: str) -> int:
        """Return how similar songs are by key out of 100."""

        values = {self.song1[key], self.song2[key]}
        if len(values) == 1:
            score = 100
        else:
            score = ratio(*values)

        return score

    @property
    def album_score(self) -> int:
        """Return the album score."""

        return self.get_score("album")

    @property
    def album_artist_score(self) -> int:
        """Return the album artist score."""

        return self.get_score("albumArtist")

    @property
    def artist_score(self) -> int:
        """Return the artist score."""

        return self.get_score("artist")

    @property
    def title_score(self) -> int:
        """Return the title score."""

        return self.get_score("title")

    @property
    def duration_score(self) -> int:
        """Return the duration score."""

        durations = {int(song["durationMillis"]) for song in (self.song1, self.song2)}
        if len(durations) == 1:
            return 100

        return 100 * int(min(durations) / max(durations))

    def get_names_and_scores(self) -> Generator[Tuple[str, int], None, None]:
        """Return name and score for that name."""

        score_names = ("album", "album_artist", "artist", "title", "duration")
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
