import pprint
from typing import Dict, List

from fuzzywuzzy import fuzz, process
from fuzzywuzzy.string_processing import StringProcessor
from pick import pick
from tqdm import tqdm

from cache import use_cache
from songs import get_all_songs

AlbumGroupMap = Dict[str, List[dict]]


def partial_process(s, force_ascii=False):
    """Process string by
        -- removing all but letters and numbers
        -- trim whitespace
        -- force to lower case
        if force_ascii == True, force convert to ascii"""

    # Force into lowercase.
    string_out = StringProcessor.to_lower_case(s)
    # Remove leading and trailing whitespaces.
    string_out = StringProcessor.strip(string_out)
    return string_out


def generate_album_groups() -> AlbumGroupMap:
    songs = get_all_songs()
    albums: AlbumGroupMap = {}
    for song in tqdm(songs):
        album = song["album"]
        if album in albums:
            # print(f"Found exact match", end="\r")
            albums[album].append(song)
            continue

        match = process.extractOne(
            album, albums.keys(), score_cutoff=95, processor=partial_process
        )
        if match is not None:
            # print(f"Found fuzzy match {match}", end="\r")
            group, _score = match
            albums[group].append(song)
            continue

        # print(f"No match found.", end="\r")
        albums[album] = [song]
    return albums


def get_album_groups() -> AlbumGroupMap:
    return use_cache("albums", generate_album_groups)


def get_display(option):
    return option[1]


def get_track_number(song):
    try:
        return int(song["trackNumber"])
    except TypeError:
        return 0


def main():
    songs = get_all_songs()
    # unique_albums = set(song["album"] for song in songs)
    grouped_albums = get_album_groups()
    for songs in grouped_albums.values():
        albums = set(song["album"] for song in songs)
        if len(albums) == 1:
            continue

        song_titles = [
            f"{song['trackNumber']:2d} - {song['artist']} - {song['title']}"
            for song in sorted(songs, key=get_track_number)
        ]
        songs_output = "\n".join(song_titles)
        album_titles = sorted(albums)
        values = [(None, "None"), *((album, album) for album in album_titles)]
        prompt = f"{songs_output}\nWhich title do you like?"
        pick(values, prompt, options_map_func=get_display)


if __name__ == "__main__":
    main()
