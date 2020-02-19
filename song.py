class Song:
    """Wrapper around song data from the api."""

    def __init__(self, song: dict):
        self.id = song["id"]
        self.track_number = song["trackNumber"]
        self.artist = song["artist"]
        self.title = song["title"]
        self.album = song["album"]
        self.play_count = int(song["playCount"])
        self.duration_millis = int(song["durationMillis"])
        self.creation_timestamp = int(song["creationTimestamp"])
        self.recent_timestamp = int(song["recentTimestamp"])

    def get_summary(self) -> str:
        """Return a summary of the song."""

        track = self.track_number
        artist = self.artist
        album = self.album
        title = self.title
        duration_millis = int(self.duration_millis)
        duration_seconds = duration_millis / 1000
        duration_minutes, seconds = divmod(duration_seconds, 60)
        hours, minutes = divmod(duration_minutes, 60)
        plays = self.play_count

        return (
            f"{track} - {artist} - {album} - {title} "
            f"[{hours:02.0f}:{minutes:02.0f}:{seconds:02.0f}] "
            f"({plays} plays)"
        )
