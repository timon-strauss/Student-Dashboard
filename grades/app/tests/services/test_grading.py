import pytest

from app.Database.schemas import ModuleResponse, SubmoduleResponse
from app.Services import InvalidDataError
from app.Services._grading import (
    ModuleResult,
    check_module_state,
    check_submodule_allowed,
    module_grade,
    resolve,
    total_points,
)


def _submodule(max_points=100, reached_points=None):
    return SubmoduleResponse(id=1, module_id=1, name="s", max_points=max_points, reached_points=reached_points)


def _module(grade=None, passed=False):
    return ModuleResponse(id=1, year_id=1, name="m", grade=grade, ects=5, passed=passed)


def test_total_points_skips_missing_reached_points():
    assert total_points([_submodule(120, 101), _submodule(60, None)]) == (101, 180)


def test_module_grade_uses_table_of_summed_max_points():
    assert module_grade([_submodule(120, 101), _submodule(60, 52)]) == 1.9


def test_module_grade_combines_points_not_grades():
    assert module_grade([_submodule(120, 120), _submodule(60, 0)]) == 3.0


def test_module_grade_allows_submodules_without_own_table():
    assert module_grade([_submodule(80, 70), _submodule(20, 15)]) == 1.9


def test_module_grade_needs_all_submodules_graded():
    assert module_grade([_submodule(60, 60), _submodule(60, None)]) is None


def test_module_grade_needs_table_for_sum():
    assert module_grade([_submodule(100, 100), _submodule(60, 60)]) is None


def test_module_grade_without_submodules():
    assert module_grade([]) is None


class TestResolve:
    def test_manual_grade_without_submodules(self):
        assert resolve(_module(grade=2.0), []) == ModuleResult(2.0, True, False, None, None)

    def test_manual_failing_grade_is_not_passed(self):
        assert resolve(_module(grade=4.1), []).passed is False

    def test_ungraded_module_uses_passed_flag(self):
        assert resolve(_module(passed=True), []).passed is True
        assert resolve(_module(passed=False), []).passed is False

    def test_submodules_decide_grade_and_passed(self):
        assert resolve(_module(), [_submodule(60, 30), _submodule(60, 30)]) == ModuleResult(4.0, True, True, 60, 120)
        assert resolve(_module(), [_submodule(100, 49.5)]) == ModuleResult(4.1, False, True, 49.5, 100)

    def test_incomplete_submodules_are_not_passed(self):
        assert resolve(_module(), [_submodule(60, 60), _submodule(60)]) == ModuleResult(None, False, True, 60, 120)


class TestChecks:
    @pytest.mark.parametrize(
        "grade, passed, has_submodules",
        [(None, False, False), (2.0, False, False), (None, True, False), (None, False, True)],
    )
    def test_valid_module_states(self, grade, passed, has_submodules):
        check_module_state(grade, passed, has_submodules)

    @pytest.mark.parametrize(
        "grade, passed, has_submodules, message",
        [
            (2.0, True, False, "passed can only be set"),
            (None, True, True, "passed can only be set"),
            (2.0, False, True, "calculated from the submodules"),
        ],
    )
    def test_invalid_module_states(self, grade, passed, has_submodules, message):
        with pytest.raises(InvalidDataError, match=message):
            check_module_state(grade, passed, has_submodules)

    def test_submodule_allowed_on_plain_module(self):
        check_submodule_allowed(_module())

    @pytest.mark.parametrize("module", [_module(grade=1.0), _module(passed=True)])
    def test_submodule_rejected_on_graded_or_passed_module(self, module):
        with pytest.raises(InvalidDataError):
            check_submodule_allowed(module)
