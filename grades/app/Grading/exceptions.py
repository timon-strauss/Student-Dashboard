class UnsupportedMaxPointsError(Exception):

    def __init__(self, max_points: float, supported: list[int]):
        super().__init__(f"No grade table for {max_points} max points, supported: {supported}")
        self.max_points = max_points
        self.supported = supported


class InvalidPointsError(Exception):

    def __init__(self, detail: str):
        super().__init__(detail)
