import dataclasses


@dataclasses.dataclass()
class Stats:
    count_deleted_tweets: int = 0
    count_deleted_dm: int = 0
    count_unlike: int = 0
    count_not_found: int = 0
    count_forbidden: int = 0
    count_skipped: int = 0
