from google_music import _get_api
from groups import delete_duplicates, get_similar_groups


def main():
    groups = get_similar_groups()
    api = _get_api()
    delete_duplicates(groups, api)


if __name__ == "__main__":
    main()
