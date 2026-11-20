import pytest

from app.Database.schemas import ModuleResponse, SubmoduleResponse
from app.Services import InvalidDataError
from app.Services._grading import (
    ModuleResult,
    check_module_state,
    check_submodule_allowed,
    module_grade,
    require_supported_max_points,
    resolve,
    submodule_grade,
)


def _submodule(max_points=100, reached_points=None, weight=1.0):
    return SubmoduleResponse(
        id=1, module_id=1, name="s", max_points=max_points, reached_points=reached_points, weight=weight
    )


def _module(grade=None, passed=False):
    return ModuleResponse(id=1, year_id=1, name="m", grade=grade, ects=5, passed=passed)


@pytest.mark.parametrize(
    "max_points, reached, grade",
    [(100, 100, 1.0), (100, 83.5, 1.9), (100, 50, 4.0), (100, 33, 5.0), (60, 30, 4.0), (90.0, 42, 4.2)],
)
def test_submodule_grade_from_table(max_points, reached, grade):
    assert submodule_grade(_submodule(max_points, reached)) == grade


def test_submodule_without_points_has_no_grade():
    assert submodule_grade(_submodule(100, None)) is None


def test_module_grade_is_weighted_by_submodule_weight():
    assert module_grade([_submodule(100, 100, weight=3), _submodule(60, 30, weight=1)]) == 1.75


def test_module_grade_needs_all_submodules_graded():
    assert module_grade([_submodule(100, 100), _submodule(100, None)]) is None


def test_module_grade_without_submodules():
    assert module_grade([]) is None


class TestResolve:
    def test_manual_grade_without_submodules(self):
        assert resolve(_module(grade=2.0), []) == ModuleResult(2.0, True, False)

    def test_manual_failing_grade_is_not_passed(self):
        assert resolve(_module(grade=4.1), []) == ModuleResult(4.1, False, False)

    def test_ungraded_module_uses_passed_flag(self):
        assert resolve(_module(passed=True), []) == ModuleResult(None, True, False)
        assert resolve(_module(passed=False), []) == ModuleResult(None, False, False)

    def test_submodules_decide_grade_and_passed(self):
        assert resolve(_module(), [_submodule(100, 50)]) == ModuleResult(4.0, True, True)
        assert resolve(_module(), [_submodule(100, 49.5)]) == ModuleResult(4.1, False, True)

    def test_incomplete_submodules_are_not_passed(self):
        assert resolve(_module(), [_submodule(100, 100), _submodule(100)]) == ModuleResult(None, False, True)


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

    @pytest.mark.parametrize("max_points", [60, 90, 100, 120, 150, 180, 100.0])
    def test_supported_max_points(self, max_points):
        require_supported_max_points(max_points)

    @pytest.mark.parametrize("max_points", [20, 99.5, 200])
    def test_unsupported_max_points(self, max_points):
        with pytest.raises(InvalidDataError, match="max_points must be one of"):
            require_supported_max_points(max_points)
