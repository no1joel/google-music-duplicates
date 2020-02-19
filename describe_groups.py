from cache import get_cached
from groups import summarise_similar


def print_groups():
    groups = get_cached("groups")
    if groups is None:
        groups = get_cached("partial_groups")
    if groups is None:
        raise Exception("Can't get groups")
    summarise_similar(groups)


def main():
    print_groups()


if __name__ == "__main__":
    main()
