"""Remove duplicate tracks from google play music."""
import pprint

from groups import get_similar_groups


def main():
    """Just print all the songs."""

    pprint.pprint(get_similar_groups())


if __name__ == "__main__":
    main()
