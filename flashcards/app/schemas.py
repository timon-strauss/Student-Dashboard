from enum import IntEnum


class CardState(IntEnum):
    LEARNING = 1
    REVIEW = 2
    RELEARNING = 3


class Rating(IntEnum):
    AGAIN = 1
    HARD = 2
    GOOD = 3
    EASY = 4
