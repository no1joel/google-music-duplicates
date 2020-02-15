"""Remove duplicate tracks from google play music."""
from groups import get_similar_groups


def main():
    """Just print all the songs."""

    import pprint

    pprint.pprint(get_similar_groups())


if __name__ == "__main__":
    main()
