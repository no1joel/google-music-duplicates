from unittest import TestCase

from song import Song


class TestSong(TestCase):
    def setUp(self):
        super().setUp()
        # Example data from gmusicapi docs
        self.song_data = {
            "comment": "",
            "rating": "0",
            "albumArtRef": [{"url": "http://lh6.ggpht.com/..."}],
            "artistId": ["Aod62yyj3u3xsjtooghh2glwsdi"],
            "composer": "",
            "year": 2011,
            "creationTimestamp": "1330879409467830",
            "id": "5924d75a-931c-30ed-8790-f7fce8943c85",
            "album": "Heritage ",
            "totalDiscCount": 0,
            "title": "Haxprocess",
            "recentTimestamp": "1372040508935000",
            "albumArtist": "",
            "trackNumber": 6,
            "discNumber": 0,
            "deleted": False,
            "storeId": "Txsffypukmmeg3iwl3w5a5s3vzy",
            "nid": "Txsffypukmmeg3iwl3w5a5s3vzy",
            "totalTrackCount": 10,
            "estimatedSize": "17229205",
            "albumId": "Bdkf6ywxmrhflvtasnayxlkgpcm",
            "beatsPerMinute": 0,
            "genre": "Progressive Metal",
            "playCount": 7,
            "artistArtRef": [{"url": "http://lh3.ggpht.com/..."}],
            "kind": "sj#track",
            "artist": "Opeth",
            "lastModifiedTimestamp": "1330881158830924",
            "clientId": "+eGFGTbiyMktbPuvB5MfsA",
            "durationMillis": "418000",
        }

    def test_id(self):
        """Should store id."""

        song = Song(self.song_data)

        self.assertEqual(song.id, self.song_data["id"])

    def test_track_number(self):
        """Should store track number."""

        song = Song(self.song_data)

        self.assertEqual(song.track_number, self.song_data["trackNumber"])

    def test_artist(self):
        """Should store artist."""

        song = Song(self.song_data)

        self.assertEqual(song.artist, self.song_data["artist"])

    def test_title(self):
        """Should store title."""

        song = Song(self.song_data)

        self.assertEqual(song.title, self.song_data["title"])

    def test_album(self):
        """Should store album."""

        song = Song(self.song_data)

        self.assertEqual(song.album, self.song_data["album"])

    def test_duration_millis(self):
        """Should store duration_millis."""

        song = Song(self.song_data)

        self.assertEqual(song.duration_millis, int(self.song_data["durationMillis"]))

    def test_creation_timestamp(self):
        """Should store creation_timestamp."""

        song = Song(self.song_data)

        self.assertEqual(
            song.creation_timestamp, int(self.song_data["creationTimestamp"])
        )

    def test_recent_timestamp(self):
        """Should store recent_timestamp."""

        song = Song(self.song_data)

        self.assertEqual(song.recent_timestamp, int(self.song_data["recentTimestamp"]))

    def test_play_count(self):
        """Should store play_count."""

        song = Song(self.song_data)

        self.assertEqual(song.play_count, int(self.song_data["playCount"]))

    def test_get_summary(self):
        """Should return string representation of song."""

        song = Song(self.song_data)

        summary = song.get_summary()

        self.assertEqual(
            summary, "6 - Opeth - Heritage  - Haxprocess [00:06:58] (7 plays)"
        )
