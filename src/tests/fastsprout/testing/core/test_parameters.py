from inspect import Signature

import pytest

from fastsprout.testing.core import given, then, when
from fastsprout.testing.core.contracts import checked_signature
from fastsprout.testing.core.parameters import StepPattern


@given("a typed step signature")
def contract() -> Signature:
    def inputs(product_name: str, count: int, price: float) -> None:
        pass

    return checked_signature(inputs)


@given("a pytest project using typed steps")
def step_project(pytester: pytest.Pytester) -> pytest.Pytester:
    pytester.makeini("[pytest]\nasyncio_default_fixture_loop_scope = function")
    pytester.makeconftest('pytest_plugins = ["fastsprout.testing.core.plugin"]')
    return pytester


class TestParameters:
    @when("typed and legacy modules with shadowed fixtures are run")
    def shadowed_run(self, step_project: pytest.Pytester) -> pytest.RunResult:
        step_project.makeconftest(
            'pytest_plugins = ["fastsprout.testing.core.plugin"]\n'
            "import pytest\n@pytest.fixture\ndef count(): return 'legacy'\n"
        )
        step_project.makepyfile(
            test_typed="import pytest\nfrom fastsprout.testing.core import then\n"
            "@pytest.mark.steps(('contains 1',))\n@then('contains {count:d}')\n"
            "def test_count(count: int) -> None: assert count == 1\n",
            test_legacy="def test_legacy(count): assert count == 'legacy'\n",
        )
        return step_project.runpytest("--no-cov")

    @then("parsed fields do not validate shadowed legacy fixtures")
    def test_shadowed_fixture(self, shadowed_run: pytest.RunResult) -> None:
        shadowed_run.assert_outcomes(passed=2)

    @when("text is matched against the compiled step pattern")
    def matched(
        self, contract: Signature, pattern: str, text: str
    ) -> dict[str, str | int | float] | None:
        return StepPattern.compile(pattern, contract).match(text)

    @then("step fields match literal text and preserve converted types")
    @pytest.mark.parametrize(
        "pattern, text, expected",
        [
            ('adds "{product_name}"', 'adds "book"', {"product_name": "book"}),
            ('adds "{product_name}"', 'adds ""', {"product_name": ""}),
            ("contains {count:d}", "contains -2", {"count": -2}),
            ("costs {price:f}", "costs +1.5e2", {"price": 150.0}),
            ("{{cart}} contains {count:d}", "{cart} contains 1", {"count": 1}),
            ("contains {count:d}", "contains 1 extra", None),
            ("contains {count:d}", "contains text", None),
        ],
    )
    def test_matching(
        self,
        matched: dict[str, str | int | float] | None,
        expected: dict[str, str | int | float] | None,
    ) -> None:
        assert matched == expected

    @when("an invalid step declaration is compiled")
    def compilation_error(
        self, contract: Signature, pattern: str
    ) -> ValueError | None:
        try:
            StepPattern.compile(pattern, contract)
        except ValueError as error:
            return error
        return None

    @then("invalid step declarations fail before parametrization")
    @pytest.mark.parametrize(
        "pattern",
        [
            "{missing}",
            "{count:d} {count:d}",
            "{count:x}",
            "{count!r}",
            "{count",
        ],
    )
    def test_invalid_patterns(
        self, compilation_error: ValueError | None
    ) -> None:
        assert isinstance(compilation_error, ValueError)

    @when("a project containing invalid step cases is collected")
    def invalid_run(
        self,
        step_project: pytest.Pytester,
        cases: tuple[tuple[str, ...], ...],
        description: str,
    ) -> pytest.RunResult:
        step_project.makepyfile(
            "import pytest\nfrom fastsprout.testing.core import given, then\n"
            "@given('plain step')\ndef context() -> int: return 1\n"
            f"@pytest.mark.steps(*{cases!r})\n@then({description!r})\n"
            "def test_count(context: int, count: int) -> None: pass\n"
        )
        return step_project.runpytest("--no-cov")

    @then("invalid text cases report a collection error")
    @pytest.mark.parametrize(
        "cases, description, error",
        [
            ((("plain step",),), "plain step", "exactly one declared phase"),
            (
                (("unknown step",),),
                "contains {count:d}",
                "exactly one declared phase",
            ),
            (
                (("contains 1", "contains 2"),),
                "contains {count:d}",
                "Conflicting step values",
            ),
            (
                (("contains 1",), ("plain step",)),
                "contains {count:d}",
                "same named fields",
            ),
            ((), "contains {count:d}", "at least one case"),
            (
                (("contains 1",),),
                "contains {count:x}",
                "Unsupported step format",
            ),
        ],
    )
    def test_invalid_cases(
        self,
        invalid_run: pytest.RunResult,
        error: str,
    ) -> None:
        invalid_run.assert_outcomes(errors=1)
        assert error in invalid_run.stdout.str()

    @when("a step with an incompatible converted parameter is run")
    def wrong_type_run(self, step_project: pytest.Pytester) -> pytest.RunResult:
        step_project.makepyfile(
            "import pytest\nfrom fastsprout.testing.core import then\n"
            "@pytest.mark.steps(('contains 1',))\n@then('contains {count}')\n"
            "def test_count(count: int) -> None: pass\n"
        )
        return step_project.runpytest("--no-cov")

    @then("converted parameters still obey the consumer's annotation")
    def test_wrong_type(self, wrong_type_run: pytest.RunResult) -> None:
        wrong_type_run.assert_outcomes(failed=1)
        assert "TypeCheckError" in wrong_type_run.stdout.str()
