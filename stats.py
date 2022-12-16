import dataclasses


@dataclasses.dataclass()
class Stats:
    count_deleted: int = 0
    count_unlike: int = 0
    count_not_found: int = 0
    count_forbidden: int = 0
    count_skipped: int = 0
