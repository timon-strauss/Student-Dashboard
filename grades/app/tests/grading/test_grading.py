import pytest

from app.Grading import (
    InvalidPointsError,
    UnsupportedMaxPointsError,
    grade_for,
    is_supported,
    passing_points,
    supported_max_points,
    thresholds,
)


def test_supported_max_points():
    assert supported_max_points() == [60, 90, 100, 120, 150, 180]


@pytest.mark.parametrize("max_points, expected", [(60, True), (100.0, True), (75, False), (0, False)])
def test_is_supported(max_points, expected):
    assert is_supported(max_points) is expected


@pytest.mark.parametrize("max_points", [60, 90, 100, 120, 150, 180])
def test_every_table_covers_all_grades_once(max_points):
    grades = [grade for _, grade in thresholds(max_points)]

    assert grades == [round(1.0 + i / 10, 1) for i in range(41)]


@pytest.mark.parametrize("max_points", [60, 90, 100, 120, 150, 180])
def test_full_points_is_best_grade(max_points):
    assert grade_for(max_points, max_points) == 1.0


@pytest.mark.parametrize("max_points", [60, 90, 100, 120, 150, 180])
def test_half_points_is_passing_limit(max_points):
    assert grade_for(max_points, max_points / 2) == 4.0
    assert grade_for(max_points, max_points / 2 - 0.5) == 4.1
    assert passing_points(max_points) == max_points / 2


@pytest.mark.parametrize("max_points", [60, 90, 100, 120, 150, 180])
def test_zero_points_fails(max_points):
    assert grade_for(max_points, 0) == 5.0


@pytest.mark.parametrize(
    "max_points, reached, grade",
    [
        (60, 59.5, 1.0),
        (60, 59, 1.1),
        (60, 20.5, 4.9),
        (60, 20, 5.0),
        (90, 89, 1.0),
        (90, 88.5, 1.1),
        (90, 44.5, 4.1),
        (90, 42.5, 4.1),
        (90, 42, 4.2),
        (90, 30, 5.0),
        (100, 98.5, 1.0),
        (100, 98, 1.1),
        (100, 83.5, 1.9),
        (100, 49.5, 4.1),
        (100, 47, 4.1),
        (100, 33.5, 4.9),
        (100, 33, 5.0),
        (120, 118, 1.1),
        (120, 59.5, 4.1),
        (120, 56.5, 4.1),
        (120, 40, 5.0),
        (150, 148, 1.0),
        (150, 147.5, 1.1),
        (150, 100, 3.0),
        (150, 74.5, 4.1),
        (150, 50, 5.0),
        (180, 177.5, 1.0),
        (180, 102, 3.6),
        (180, 89.5, 4.1),
        (180, 60.5, 4.9),
        (180, 60, 5.0),
    ],
)
def test_grade_matches_table(max_points, reached, grade):
    assert grade_for(max_points, reached) == grade


def test_points_between_half_steps_use_lower_bound():
    assert grade_for(100, 98.4) == 1.1
    assert grade_for(100, 98.49) == 1.1
    assert grade_for(60, 30.2) == 4.0


def test_unsupported_max_points_raises():
    with pytest.raises(UnsupportedMaxPointsError) as exc:
        grade_for(75, 50)

    assert exc.value.max_points == 75
    assert exc.value.supported == [60, 90, 100, 120, 150, 180]


@pytest.mark.parametrize("reached", [-0.5, 100.5])
def test_points_out_of_range_raise(reached):
    with pytest.raises(InvalidPointsError):
        grade_for(100, reached)


def test_thresholds_returns_copy():
    thresholds(60).clear()

    assert len(thresholds(60)) == 41
