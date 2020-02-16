![Python application](https://github.com/no1joel/google-music-duplicates/workflows/Python%20application/badge.svg)

# Google Music Duplicate Manager

Allows for deleting duplicate songs from your google play library, thanks to the fantastic [gmusicapi](https://github.com/simon-weber/gmusicapi) and [fuzzywuzzy](https://github.com/seatgeek/fuzzywuzzy) libraries.

## Usage

_Note: There's some initial google account set up, see [gmusicapi](https://github.com/simon-weber/gmusicapi) docs for more details._

```
pip install poetry
poetry install
poetry run python delete_duplicates.py
```

## TODO:
- Multi-process/threading
- Combine duplicate albums
